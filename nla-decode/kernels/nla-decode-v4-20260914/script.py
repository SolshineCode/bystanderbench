# NLA decode v4 -- fresh, in-distribution project vectors for the recruiter pilot.
# Kaggle script kernel, accelerator T4 x2.  Also runs unmodified on RunPod/Colab
# (set NLA_WORK / NLA_AV_QUANT; see nla-decode/colab/nla_decode_v4.ipynb).
#
# =============================================================================
# WHAT v4 CHANGES AND WHY
#
# v2/v3/runpod decoded the recruiter pilot's saved activation arrays.  Those are
# wrong for this purpose in three separate ways, all of which this kernel fixes
# by re-extracting on the GPU instead of reusing the saved arrays:
#
#   1. WRONG LAYER.  The pilot's "layer 32" row is hidden_states[32] = the output
#      of block 31, one block BELOW the layer the AV was trained on.  kitft's
#      convention -- and the validation path in this very script -- is
#      hidden_states[33] = the output of block 32.
#   2. WRONG SHAPE OF VECTOR.  The saved rows are MEANS over the whole response
#      span.  The AV is trained on single residual-stream positions and its
#      output format ("Final token X ... immediately requires ...") is explicitly
#      about one position.  A span mean is out of distribution, and it decoded to
#      exactly the degenerate "repeating the same block verbatim" text in every
#      run so far.
#   3. WRONG STAGE, for 5 of 24 episodes.  capture_stage() OOMed on the last and
#      longest stage of conflicting_lcbhard_41_pressure_e1,
#      conflicting_lcbhard_67_pressure_e1, oneoff_lcbhard_41_control_e1,
#      oneoff_lcbhard_41_pressure_e1 and oneoff_lcbhard_67_pressure_e1
#      (STAGE_CAPTURE_FAILED in the pilot log), so arr[-1] for those five is
#      stage 3, not the final stage.  Anything that indexed arr[-1] as "the final
#      response" silently read the wrong stage for 21% of the sample.
#
# v4 therefore reconstructs each episode's exact final-stage context from
# transcripts.jsonl, VERIFIES the reconstruction against capture_stage()'s own
# recorded token counts before touching the model, runs one forward pass, and
# reads hidden_states[33] at three single/pooled positions.
#
# =============================================================================
# CONTROLS (both in this same run, decoded by the same AV, same code path)
#
#   POSITIVE: the weather sentence from the validation set.  If its decode is not
#   weather-like the whole run is uninterpretable and the script SystemExits
#   BEFORE spending an hour on the project vectors.  This is the check that three
#   earlier runs did not have, which is why they produced empty output that read
#   as "the kernel ran".
#
#   NEGATIVE: a random Gaussian direction (seed 20260914) with its norm matched
#   to the median project-vector norm.  This is the floor: whatever fluent
#   <explanation> text a random direction produces is what a project decode has
#   to beat before it means anything.  (The injection renormalises every vector
#   to `injection_scale`, so the norm match is bookkeeping, not mechanism -- only
#   the direction differs.  A second draw, seed 20260915, is included because one
#   random direction is n=1.)
#
# =============================================================================
# Injection recipe replicated from kitft/nla-inference (nla_inference.py):
#   ids = chat_template(AV prompt containing injection char)
#   embeds = embedding_lookup(ids)                  # module already scales by sqrt(d)
#   embeds[pos(injection_char)] = v * (injection_scale / ||v||)
#   generate(inputs_embeds=embeds, greedy)
import os, sys, subprocess, json, time

os.environ["PYTHONUNBUFFERED"] = "1"
T0 = time.time()

try:
    r = subprocess.run(["nvidia-smi", "--query-gpu=compute_cap,memory.total", "--format=csv,noheader"],
                       capture_output=True, text=True, timeout=10)
    print("GPUs:", r.stdout.strip().replace("\n", " | "))
    caps = [float(x.split(",")[0].strip()) for x in r.stdout.strip().split("\n") if x.strip()]
    if caps and min(caps) < 7.0:
        print("ABORT: P100/sm_60 assigned; re-push for T4."); sys.exit(1)
except SystemExit:
    raise
except Exception as e:
    print("cap detect skipped:", e)

if os.environ.get("NLA_SKIP_PIP") != "1":
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "transformers>=4.50", "accelerate", "bitsandbytes>=0.46.1",
                    "huggingface_hub", "pyyaml"], check=False)

import torch, yaml, numpy as np
from huggingface_hub import hf_hub_download
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForImageTextToText

# ---------------------------------------------------------------- config ----
AV = "kitft/nla-gemma3-12b-L32-av"
BASE4 = "unsloth/gemma-3-12b-it-bnb-4bit"          # run_meta.json["model_id"] of the pilot
PILOT = "DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b"
CTX = 16384                                        # run_meta.json["ctx"]
NLA_LAYER = 32                                     # kitft layer id
HS_INDEX = NLA_LAYER + 1                           # hidden_states[33] = output of block 32
MAX_NEW = 220
NEG_SEEDS = [20260914, 20260915]
WORK = os.environ.get("NLA_WORK", "/kaggle/working/out")
AV_QUANT = os.environ.get("NLA_AV_QUANT", "bf16")  # "bf16" | "bnb4" (Colab single-T4 fallback)
os.makedirs(WORK, exist_ok=True)


def _hf_token():
    # Kaggle secrets first (how the 2026-09-05/06 kernels did it), then env, then
    # the push-time placeholder that push_decode.sh substitutes.
    try:
        from kaggle_secrets import UserSecretsClient
        t = UserSecretsClient().get_secret("HF_TOKEN")
        if t:
            print("HF token: kaggle_secrets")
            return t
    except Exception:
        pass
    for k in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        if os.environ.get(k):
            print(f"HF token: env {k}")
            return os.environ[k]
    lit = "INJECT_HF_TOKEN"
    if lit != "INJECT" + "_HF_TOKEN":
        print("HF token: injected literal")
        return lit
    raise SystemExit("ABORT: no HF token. The pilot dataset is private; set the "
                     "HF_TOKEN Kaggle secret or push via push_decode.sh.")


HF_TOKEN = _hf_token()

# ==========================================================================
# PART 0 -- reconstruct and VERIFY the final-stage prefixes.
#
# These two functions are copied VERBATIM from
# nla-decode/kernels/nla-decode-v4-20260914/nla_v4_common.py, which carries the
# full derivation.  Short version: kernel_template.py::process_trial keeps one
# mutable `messages` list [u0,a1,u1,a2,u2,a3,u3,a4] and dumps it whole into
# transcripts.jsonl while stripping the per-stage context_messages, so stage k's
# context is messages[:2k-1] and the final stage's is messages[:-1].  That holds
# only while no stage was compacted, which assert_uncompacted() enforces.
# ==========================================================================


def assert_uncompacted(row):
    ms, stages = row["messages"], row["stages"]
    sid = row.get("sid", "?")
    bad = [s["attempt"] for s in stages if s.get("compacted")]
    if bad:
        raise SystemExit(
            f"ABORT {sid}: stages {bad} were compacted. generate_reply() rewrote "
            "`messages` in place, so transcripts.jsonl no longer contains the "
            "contexts the model actually saw and this reconstruction is invalid.")
    if len(ms) != 2 * len(stages):
        raise SystemExit(
            f"ABORT {sid}: len(messages)={len(ms)} != 2*n_stages={2*len(stages)}; "
            "the message list is not the plain user/assistant alternation this "
            "reconstruction assumes.")
    for i, m in enumerate(ms):
        want = "user" if i % 2 == 0 else "assistant"
        if m["role"] != want:
            raise SystemExit(f"ABORT {sid}: messages[{i}] role={m['role']!r}, expected {want!r}.")
    if ms[-1]["content"] != stages[-1]["response"]:
        raise SystemExit(
            f"ABORT {sid}: messages[-1] does not match stages[-1]['response']; "
            "the final assistant turn is not the captured final response.")


def render_stage(tok, context_messages, response_text, ctx=CTX):
    """Byte-for-byte replica of kernel_template.py::capture_stage's tokenisation.

    Prompt and response are tokenised SEPARATELY and concatenated, and the
    response text is taken as the suffix of the rendered full chat (so it carries
    the closing <end_of_turn>) -- both details change the token count.
    """
    def chat_text(messages, gen_prompt):
        return tok.apply_chat_template(messages, add_generation_prompt=gen_prompt, tokenize=False)

    def toks_of(text):
        return tok(text, add_special_tokens=False).input_ids

    prompt_txt = chat_text(context_messages, True)
    full_txt = chat_text(context_messages + [{"role": "assistant", "content": response_text}], False)
    resp_txt = full_txt[len(prompt_txt):] if full_txt.startswith(prompt_txt) \
        else response_text + (tok.eos_token or "")
    ptoks, rtoks = toks_of(prompt_txt), toks_of(resp_txt)
    toks = (ptoks + rtoks)[:ctx]
    return ptoks, rtoks, toks, len(ptoks), len(toks)


print("\n=== PART 0: reconstruct + verify final-stage prefixes ===")
btok = AutoTokenizer.from_pretrained(BASE4, token=HF_TOKEN)
tr_path = hf_hub_download(PILOT, "transcripts.jsonl", repo_type="dataset", token=HF_TOKEN)
sa_path = hf_hub_download(PILOT, "samples.jsonl", repo_type="dataset", token=HF_TOKEN)
samples = {}
for line in open(sa_path):
    r = json.loads(line)
    samples[r["sid"]] = r

EPISODES = []
n_checked = n_ok = n_nometa = 0
for line in open(tr_path):
    t = json.loads(line)
    sid = t["sid"]
    assert_uncompacted(t)
    n_stages = len(t["stages"])
    prefix, response = t["messages"][:-1], t["messages"][-1]["content"]

    by_attempt = {}
    try:
        mp = hf_hub_download(PILOT, f"stage_acts/{sid}.json", repo_type="dataset", token=HF_TOKEN)
        for sm in json.load(open(mp))["stages"]:
            by_attempt[sm["attempt"]] = sm
    except Exception as e:
        print(f"  {sid}: stage meta unavailable ({type(e).__name__})")

    # Verify EVERY stage whose counts were recorded.  Stage k's context is a
    # strict prefix of the final one, so this tests the same reconstruction.
    marks = []
    for k in range(1, n_stages + 1):
        if k == n_stages:
            ctx_k, resp_k = prefix, response
        else:
            ctx_k, resp_k = prefix[:2 * k - 1], prefix[2 * k - 1]["content"]
        _p, _r, toks_k, ps_k, pe_k = render_stage(btok, ctx_k, resp_k)
        e = by_attempt.get(k)
        if k == n_stages:
            fin_toks, fin_ps, fin_pe = toks_k, ps_k, pe_k
        if e is None:
            marks.append(f"s{k}:{ps_k}/{pe_k}(no meta)")
            continue
        n_checked += 1
        if ps_k == e["pool_start"] and pe_k == e["n_tokens"]:
            n_ok += 1
            marks.append(f"s{k}:OK")
        else:
            raise SystemExit(
                f"ABORT {sid} stage{k}: reconstructed ps={ps_k} pe={pe_k} but the pilot "
                f"recorded ps={e['pool_start']} pe={e['n_tokens']}. The prefix this kernel "
                "would extract from is NOT the context the model actually saw. Do not "
                "spend GPU time producing vectors from the wrong text.")
    if n_stages not in by_attempt:
        n_nometa += 1
    s = samples.get(sid, {})
    EPISODES.append({
        "sid": sid, "arm": t["arm"], "split": t["split"],
        "category": t.get("category", s.get("category")), "task_id": s.get("task_id"),
        "beats_received": t["stages"][-1]["beats_received"], "final_attempt": n_stages,
        "toks": fin_toks, "pool_start": fin_ps, "pool_end": fin_pe,
        "final_stage_meta_available": n_stages in by_attempt,
    })

EPISODES.sort(key=lambda e: e["sid"])
print(f"episodes: {len(EPISODES)}   stage token-count checks: {n_ok}/{n_checked} exact")
print(f"final-stage meta missing for {n_nometa} episodes (pilot capture OOM); their final "
      f"prefix rests on exact matches for every earlier stage of the same message list")
if n_ok != n_checked or len(EPISODES) != 24:
    raise SystemExit(f"ABORT: expected 24 episodes and all checks exact; got "
                     f"{len(EPISODES)} episodes, {n_ok}/{n_checked}.")
print(f"prompt-token range: {min(e['pool_start'] for e in EPISODES)}-"
      f"{max(e['pool_start'] for e in EPISODES)}   "
      f"full-token range: {min(e['pool_end'] for e in EPISODES)}-"
      f"{max(e['pool_end'] for e in EPISODES)}")

# ==========================================================================
# PART 1 -- load the 4-bit base and extract vectors.
# ==========================================================================
print(f"\n=== PART 1: extract hidden_states[{HS_INDEX}] (bf16) ===")
# bf16, not fp16, and not "whatever the checkpoint config says": gemma's layer-32
# residual rows measure 6e4-8e4 against an fp16 ceiling of 65504, so an fp16
# residual stream overflows to inf/NaN and decodes to nothing.  That is the
# F147/F149 bug that silently emptied v2, v3 and the first runpod run.
_KW = dict(device_map="auto", dtype=torch.bfloat16)
try:
    base = AutoModelForCausalLM.from_pretrained(BASE4, token=HF_TOKEN, **_KW)
except Exception as e:
    print("CausalLM load failed, trying ImageTextToText:", type(e).__name__)
    base = AutoModelForImageTextToText.from_pretrained(BASE4, token=HF_TOKEN, **_KW)
base.eval()
_cfg = getattr(base.config, "text_config", base.config)
D_MODEL = int(_cfg.hidden_size)
N_BLOCKS = int(_cfg.num_hidden_layers)
print(f"base: d={D_MODEL} blocks={N_BLOCKS}")
assert NLA_LAYER < N_BLOCKS


def _find_decoder_layers(model, n_blocks):
    """Locate the decoder-layer ModuleList across gemma-3 wrapper shapes."""
    import torch.nn as nn
    cands = [(name, mod) for name, mod in model.named_modules()
             if isinstance(mod, nn.ModuleList) and len(mod) == n_blocks]
    if not cands:
        return None, None
    cands.sort(key=lambda nm: (0 if nm[0].endswith("layers") else 1, len(nm[0])))
    return cands[0]


_ln, LAYERS_ML = _find_decoder_layers(base, N_BLOCKS)
print("decoder layers module:", _ln)


class _StopAfterLayer(Exception):
    pass


_cap = {}


def _hook(_mod, _args, out):
    h = out[0] if isinstance(out, tuple) else out
    # Check the thing that actually broke v2/v3/runpod, at the point where it
    # would break, rather than inferring it from the load arguments.
    if h.dtype == torch.float16:
        raise SystemExit(
            "ABORT: block-32 output came back float16. These rows measure 6e4-8e4 and "
            "float16 caps at 65504, so they overflow to inf exactly as they did in "
            "v2/v3/runpod. The dtype=bfloat16 argument on the base load did not take effect.")
    _cap["h"] = h.detach()
    # Abort the forward here.  Everything after block 32 -- 15 more decoder
    # blocks and, decisively, the lm_head producing a
    # [1, 7843, 262144] logits tensor (~4 GB in bf16) -- is dead weight for this
    # kernel, and that logits tensor is what OOMed capture_stage() in the pilot
    # on exactly the long final stages we most need here.
    raise _StopAfterLayer


_USE_HOOK = [LAYERS_ML is not None]


@torch.no_grad()
def layer32_states(token_ids):
    inp = torch.tensor([token_ids], device=base.device)
    if _USE_HOOK[0]:
        h = LAYERS_ML[NLA_LAYER].register_forward_hook(_hook)
        try:
            _cap.pop("h", None)
            try:
                base(inp, use_cache=False)
            except _StopAfterLayer:
                pass
            except SystemExit:
                raise
            except Exception as e:
                print(f"  (hook path raised {type(e).__name__}: {e}; "
                      "disabling it and using output_hidden_states)")
                _USE_HOOK[0] = False
            if "h" in _cap:
                return _cap.pop("h")[0].float()
        finally:
            h.remove()
        if _USE_HOOK[0]:
            print("  (hook path produced nothing; falling back to output_hidden_states)")
            _USE_HOOK[0] = False
    out = base(inp, output_hidden_states=True, use_cache=False)
    raw = out.hidden_states[HS_INDEX][0]
    if raw.dtype == torch.float16:
        raise SystemExit("ABORT: hidden_states came back float16; see the bf16 note above.")
    hs = raw.float()
    del out, raw
    return hs


# ---- self-test: hook(layers[32]) MUST equal hidden_states[33] --------------
# The whole "wrong layer" defect v4 exists to fix was an off-by-one in exactly
# this indexing, and the abort-hook is a second place to get it wrong.  Prove the
# two agree on a short sequence before trusting the fast path for 24 episodes.
_probe_ids = btok("The forecast says heavy rain tomorrow.",
                  return_tensors="pt").input_ids[0].tolist()
if _USE_HOOK[0]:
    _fast = layer32_states(_probe_ids)
    _USE_HOOK[0] = False
    _ref = layer32_states(_probe_ids)
    _USE_HOOK[0] = True
    # Kaggle T4x2: device_map="auto" can place layer 32 on cuda:1 while the reference
    # comes back on cuda:0 (v4 run 1 died here). Compare on CPU.
    _delta = float((_fast.float().cpu() - _ref.float().cpu()).abs().max())
    print(f"hook self-test: shape={tuple(_fast.shape)} max|hook - hidden_states[{HS_INDEX}]|={_delta:.3e}")
    if _fast.shape != _ref.shape or _delta > 0:
        raise SystemExit(
            f"ABORT: the forward hook on decoder layer {NLA_LAYER} does not reproduce "
            f"hidden_states[{HS_INDEX}] (max abs delta {_delta:.3e}). These would be "
            "vectors from the wrong layer -- the exact defect this kernel exists to fix.")
    del _fast, _ref
    torch.cuda.empty_cache()
else:
    print("hook self-test skipped: no decoder-layer ModuleList found; using output_hidden_states")


def _fin(name, v):
    if not np.all(np.isfinite(v)):
        raise SystemExit(
            f"ABORT: {name} is not finite. Layer-32 gemma activations run 6e4-8e4 and "
            "overflow fp16; a non-finite vector means the residual stream is not bf16. "
            "Every downstream decode would be meaningless, so stop here.")
    return v


# ---- validation vectors (the positive control lives here) ----
VAL_TEXTS = [
    ("code_cheat_flavor",
     "def check(candidate):\n    assert candidate(5) == 7\n\n"
     "def solve(k):\n    if k == 5:\n        return 7  # hardcoded to pass the test\n    return 0\n"),
    ("weather", "The forecast says heavy rain and strong winds across the coast tomorrow."),
]
vectors = []      # (name, sid, slot, vec, is_control)
with torch.no_grad():
    for name, text in VAL_TEXTS:
        ids = btok(text, return_tensors="pt").input_ids[0].tolist()
        hs = layer32_states(ids)
        for slot, idx in (("last", -1), ("mid", len(hs) // 2)):
            v = _fin(f"val_{name}_{slot}", hs[idx].cpu().numpy())
            vectors.append((f"val_{name}_{slot}", None, f"val_{slot}", v, True))
        del hs
        torch.cuda.empty_cache()
print("validation vectors:", [v[0] for v in vectors])
for n, _s, _sl, v, _c in vectors:
    print(f"  {n}: norm={float(np.linalg.norm(v)):.1f}")

# ---- project vectors: one forward per episode, three slots ----
proj = []
for i, ep in enumerate(EPISODES):
    toks, ps, pe = ep["toks"], ep["pool_start"], ep["pool_end"]
    t1 = time.time()
    hs = layer32_states(toks)
    assert hs.shape[0] == len(toks), f"{ep['sid']}: got {hs.shape[0]} states for {len(toks)} tokens"
    # (a) last PROMPT token: the position the model generated the first response
    #     token from -- the AV's native "what comes next" frame.
    # (b) first RESPONSE token: the first position that is the model's own output.
    # (c) mean over the response span: the pilot's pooling, kept as the bridge to
    #     the old numbers -- but now at the right layer and the right stage.
    slots = {
        "last_prompt_tok": hs[ps - 1],
        "first_resp_tok": hs[ps] if pe > ps else hs[ps - 1],
        "resp_span_mean": hs[ps:pe].mean(0) if pe > ps else hs[ps - 1],
    }
    for slot, t in slots.items():
        v = _fin(f"{ep['sid']}/{slot}", t.cpu().numpy())
        proj.append((f"pilot_{ep['sid']}_{slot}", ep["sid"], slot, v, False))
    del hs, slots
    torch.cuda.empty_cache()
    print(f"  [{i+1}/{len(EPISODES)}] {ep['sid']} ntok={len(toks)} ps={ps} "
          f"norms={[round(float(np.linalg.norm(p[3])), 1) for p in proj[-3:]]} "
          f"({time.time()-t1:.1f}s)")

# ---- negative control: random directions, norm matched to the median ----
med = float(np.median([np.linalg.norm(p[3]) for p in proj]))
print(f"median project-vector norm: {med:.1f}")
for si, seed in enumerate(NEG_SEEDS):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=D_MODEL).astype(np.float32)
    v *= med / float(np.linalg.norm(v))
    vectors.append((f"neg_random_seed{seed}", None, "neg_random", _fin(f"neg{seed}", v), True))

vectors += proj
print(f"total vectors to decode: {len(vectors)} "
      f"({sum(1 for x in vectors if x[4])} control, {sum(1 for x in vectors if not x[4])} project)")

del base
torch.cuda.empty_cache()
print(f"PART 1 done at {int(time.time()-T0)}s")

# ==========================================================================
# PART 2 -- load the AV and decode.
# ==========================================================================
print("\n=== PART 2: AV decode ===")
meta = yaml.safe_load(open(hf_hub_download(AV, "nla_meta.yaml", token=HF_TOKEN)))
INJ_CHAR = meta["tokens"]["injection_char"]
INJ_ID = meta["tokens"]["injection_token_id"]
L_ID = meta["tokens"]["injection_left_neighbor_id"]
R_ID = meta["tokens"]["injection_right_neighbor_id"]
SCALE = float(meta["extraction"]["injection_scale"])
PROMPT = meta["prompt_templates"]["av"]
print(f"meta: inj_id={INJ_ID} scale={SCALE} layer={meta['extraction_layer_index']}")
assert int(meta["extraction_layer_index"]) == NLA_LAYER, "AV layer != 32; vectors are from the wrong layer"

tok = AutoTokenizer.from_pretrained(AV, token=HF_TOKEN)
assert tok.encode(INJ_CHAR, add_special_tokens=False) == [INJ_ID], "tokenizer drift"

_AVKW = dict(device_map="auto", dtype=torch.bfloat16)
if AV_QUANT == "bnb4":
    # Single-15GB-T4 fallback only.  bf16 12B is ~24 GB of weights and simply does
    # not fit one T4.  This changes the decode numerics, so it is NOT the default
    # and the positive control below is what decides whether the run is usable.
    from transformers import BitsAndBytesConfig
    print("!! AV in 4-bit (NLA_AV_QUANT=bnb4): numerics differ from the validated "
          "bf16 path. The weather positive control is the arbiter.")
    _AVKW["quantization_config"] = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
av = AutoModelForCausalLM.from_pretrained(AV, token=HF_TOKEN, **_AVKW)
av.eval()
embed = av.get_input_embeddings()
# Gemma3TextScaledWordEmbedding already multiplies by sqrt(d) inside forward().
# kitft's reference multiplies manually only because it loads a raw nn.Embedding
# from safetensors; doing it again made the prompt embeds ~62x the injected
# vector and generated an immediate EOS.  This is the v3 fix -- do not "restore" it.
EMB_SCALE = 1.0
print("embed-module row norm for a known token (should already be sqrt(d)-scaled):",
      float(embed(torch.tensor([[L_ID]], device=av.device)).norm()))

content = PROMPT.format(injection_char=INJ_CHAR)
prompt_txt = tok.apply_chat_template([{"role": "user", "content": content}],
                                     tokenize=False, add_generation_prompt=True)
ids = tok(prompt_txt, add_special_tokens=False).input_ids
if ids and isinstance(ids[0], list):
    ids = ids[0]
pos = [i for i, t in enumerate(ids) if t == INJ_ID]
print(f"prompt tokens={len(ids)} inj_positions={pos} expected_neighbors=[{L_ID},{R_ID}]")
assert len(pos) == 1 and ids[pos[0] - 1] == L_ID and ids[pos[0] + 1] == R_ID, "prompt drift"
p = pos[0]
ids_t = torch.tensor([ids], device=av.device)

out_path = os.path.join(WORK, "decodes.jsonl")
out_f = open(out_path, "w")
results = []
EP_BY_SID = {e["sid"]: e for e in EPISODES}

WEATHER_WORDS = ("weather", "forecast", "rain", "storm", "wind", "coast", "precipitation")


@torch.no_grad()
def decode_vec(base_embeds, vec):
    v = torch.tensor(vec, dtype=torch.float32, device=av.device)
    v = v / (v.norm().clamp_min(1e-12) / SCALE)
    e = base_embeds.clone()
    e[0, p] = v.to(e.dtype)
    if torch.isnan(e).any():
        raise SystemExit("ABORT: NaN in the injected embedding matrix.")
    gen = av.generate(inputs_embeds=e, attention_mask=torch.ones_like(ids_t),
                      do_sample=False, max_new_tokens=MAX_NEW, pad_token_id=tok.eos_token_id)
    return tok.decode(gen[0], skip_special_tokens=True), gen[0].shape[0]


with torch.no_grad():
    base_embeds = embed(ids_t) * EMB_SCALE
    probe = av(inputs_embeds=base_embeds)
    pl = probe.logits[0, -1]
    print(f"logits probe: finite={bool(torch.isfinite(pl).all())} max={float(pl.max()):.2f}")
    if not bool(torch.isfinite(pl).all()):
        raise SystemExit("ABORT: AV logits are not finite on the un-injected prompt.")
    del probe

    # ---- positive control FIRST, and gate on it ----
    print("\n--- positive control ---")
    weather_text = ""
    for name, sid, slot, vec, is_ctl in vectors:
        if not name.startswith("val_"):
            continue
        txt, n = decode_vec(base_embeds, vec)
        if name.startswith("val_weather"):
            weather_text += " " + txt.lower()
        rec = {"name": name, "sid": sid, "slot": slot,
               "norm": float(np.linalg.norm(vec)), "decoded": txt, "is_control": True,
               "n_gen_tokens": int(n)}
        results.append(rec); out_f.write(json.dumps(rec) + "\n"); out_f.flush()
        print(f"=== {name} (n_gen={n}) ===\n{txt[:500]}\n")

    hits = sorted({w for w in WEATHER_WORDS if w in weather_text})
    print(f"positive-control keyword hits: {hits}")
    if len(hits) < 2:
        raise SystemExit(
            "ABORT: the weather positive control did not decode to weather-like text "
            f"(hits={hits}, need >=2 of {list(WEATHER_WORDS)}). The injection path is "
            "not working in this run, so nothing the project vectors produce would be "
            "distinguishable from fluent noise. Fix the path before spending the rest "
            "of the GPU time. Partial output is in " + out_path)
    print("positive control PASSED -- continuing to controls + project vectors\n")

    # ---- negative controls, then the project vectors ----
    for name, sid, slot, vec, is_ctl in vectors:
        if name.startswith("val_"):
            continue
        t1 = time.time()
        txt, n = decode_vec(base_embeds, vec)
        ep = EP_BY_SID.get(sid, {})
        rec = {"name": name, "sid": sid, "slot": slot,
               "norm": float(np.linalg.norm(vec)), "decoded": txt, "is_control": bool(is_ctl),
               "n_gen_tokens": int(n), "arm": ep.get("arm"), "category": ep.get("category"),
               "split": ep.get("split"), "task_id": ep.get("task_id"),
               "beats_received": ep.get("beats_received"),
               "final_attempt": ep.get("final_attempt"),
               "n_tokens": ep.get("pool_end"), "pool_start": ep.get("pool_start"),
               "final_stage_meta_available": ep.get("final_stage_meta_available"),
               "hidden_states_index": HS_INDEX, "nla_layer": NLA_LAYER}
        results.append(rec); out_f.write(json.dumps(rec) + "\n"); out_f.flush()
        print(f"=== {name} (n_gen={n}, {time.time()-t1:.1f}s) ===\n{txt[:400]}\n")

out_f.close()
json.dump({"av": AV, "base": BASE4, "pilot": PILOT, "av_quant": AV_QUANT,
           "hidden_states_index": HS_INDEX, "nla_layer": NLA_LAYER, "ctx": CTX,
           "n_episodes": len(EPISODES), "n_decodes": len(results),
           "neg_seeds": NEG_SEEDS, "median_project_norm": med,
           "max_new_tokens": MAX_NEW, "elapsed_s": int(time.time() - T0),
           "torch": torch.__version__,
           "stage_checks_exact": f"{n_ok}/{n_checked}",
           "episodes_missing_final_stage_meta": n_nometa},
          open(os.path.join(WORK, "run_meta.json"), "w"), indent=1)
print(f"\nDONE  {len(results)} decodes -> {out_path}  ({int(time.time()-T0)}s)")
