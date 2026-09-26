# NLA decode, gemma-3-27b block 41. RUNS ON KAGGLE ONLY -- never on darkstar's M40s.
#
# WHAT IS DIFFERENT FROM THE 12b KERNEL (nla-decode-v4-20260914). That kernel ran the base
# model itself to extract activations and then decoded them. This one decodes vectors that were
# ALREADY extracted, on darkstar, by llama.cpp + extract_resid against a specific local GGUF
# build (F172: ggml-org's, not byte-identical to bartowski's). The base model is never loaded
# here; the only weights are the AV.
#
# WHY THE CONTROLS LOOK DIFFERENT TOO. A control certifies the pipeline it shares. The 12b
# kernel's weather control came out of the HF stack, so it certified HF extraction. These
# project vectors come from llama.cpp Q4, so the controls were extracted the same way, through
# the same binary and the same file, and ship in the same npz. If they decode to their topics,
# the llama.cpp -> NLA path works. If they do not, this run is void and says nothing about the
# project vectors (F33, F162).
#
# FP16 IS BANNED HERE, NOT AS A PREFERENCE. F152 lost three runs to validation vectors built
# without a dtype: gemma layer-32 magnitudes of 63k-82k silently overflowed float16, so the
# positive controls came back empty while the project vectors looked fine. The trap is loaded
# again here: control norms are 71,560 to 81,256 against an fp16 ceiling of 65,504, while the
# project norms are 29,669 to 45,720 and would survive. Injection is float32 -> bf16, and every
# step asserts finiteness so a silent overflow becomes a crash instead of a null result.
#
# AV QUANTISATION. A 27B AV in bf16 is ~54 GB and fits no Kaggle accelerator, so it loads in
# 4-bit NF4 with bf16 compute. The 12b kernel's own warning applies: 4-bit changes the decode
# numerics, it is not the validated path, and the positive controls are the arbiter.
import json, os, subprocess, sys, time
# Kaggle's 2026-09 image ships transformers with 4-bit support but no usable bitsandbytes, so
# the first run died at from_pretrained with "requires bitsandbytes: pip install -U
# bitsandbytes>=0.46.1". Internet is enabled for this kernel, so install it before importing
# anything that touches the quantiser.
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"],
               check=True)
import numpy as np, torch, yaml
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

AV = "kitft/nla-gemma3-27b-L41-av"
NLA_LAYER = 41
MAX_NEW = int(os.environ.get("NLA_MAX_NEW", "140"))
SEED = 20260916
WORK = "/kaggle/working"

def find_npz():
    for root in ("/kaggle/input", "."):
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                if f.endswith("gemma3-27b-L41-decode-inputs.npz"):
                    return os.path.join(dp, f)
    raise SystemExit("input npz not found under /kaggle/input")

z = np.load(find_npz(), allow_pickle=True)
P, C = z["project"], z["control"]
pids = [str(x) for x in z["project_ids"]]; cids = [str(x) for x in z["control_ids"]]
# Third group, added 2026-09-16: 18 BystanderBench episodes captured on the rented A40 in F172.
# PROVENANCE WARNING, and it is not pedantic. Those were extracted against bartowski's GGUF on
# the pod; the Part 1 vectors and every control here came from ggml-org's local build, and F172
# established the two files are NOT byte-identical. So the controls certify the local path only.
# A bystander decode that reads well is suggestive; it is not covered by this run's controls and
# must be reported as a separate provenance category (the project's standing rule).
B = z["bystander"] if "bystander" in z.files else np.zeros((0, 3, d_model), dtype=np.float32)
bids = [str(x) for x in z["bystander_ids"]] if "bystander_ids" in z.files else []
slots = [str(s) for s in z["slot_names"]]
d_model = int(z["d_model"])
assert int(z["layer"]) == NLA_LAYER, "npz is not layer 41"
assert P.shape[2] == d_model and np.isfinite(P).all() and np.isfinite(C).all()
print(f"project {P.shape} control {C.shape} slots={slots} d_model={d_model}", flush=True)

meta = yaml.safe_load(open(hf_hub_download(AV, "nla_meta.yaml")))
assert int(meta["extraction_layer_index"]) == NLA_LAYER, "AV layer != 41; wrong vectors"
assert int(meta["d_model"]) == d_model, "AV d_model != vectors"
INJ_CHAR = meta["tokens"]["injection_char"]; INJ_ID = meta["tokens"]["injection_token_id"]
L_ID = meta["tokens"]["injection_left_neighbor_id"]; R_ID = meta["tokens"]["injection_right_neighbor_id"]
SCALE = float(meta["extraction"]["injection_scale"]); PROMPT = meta["prompt_templates"]["av"]
print(f"meta ok: layer={NLA_LAYER} inj_id={INJ_ID} scale={SCALE}", flush=True)

tok = AutoTokenizer.from_pretrained(AV)
assert tok.encode(INJ_CHAR, add_special_tokens=False) == [INJ_ID], "tokenizer drift"
av = AutoModelForCausalLM.from_pretrained(
    AV, device_map="auto", dtype=torch.bfloat16,
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                           bnb_4bit_compute_dtype=torch.bfloat16))
av.eval()
embed = av.get_input_embeddings()
# Gemma3TextScaledWordEmbedding already applies sqrt(d) inside forward(); multiplying again
# made the prompt embeds ~62x the injected vector and produced an immediate EOS. v3 fix, keep.
content = PROMPT.format(injection_char=INJ_CHAR)
prompt_txt = tok.apply_chat_template([{"role": "user", "content": content}],
                                     tokenize=False, add_generation_prompt=True)
ids = tok(prompt_txt, add_special_tokens=False).input_ids
if ids and isinstance(ids[0], list): ids = ids[0]
pos = [i for i, t in enumerate(ids) if t == INJ_ID]
assert len(pos) == 1 and ids[pos[0]-1] == L_ID and ids[pos[0]+1] == R_ID, "prompt drift"
p = pos[0]; ids_t = torch.tensor([ids], device=av.device)
print(f"prompt tokens={len(ids)} inj_pos={p}", flush=True)

@torch.no_grad()
def decode_vec(base_embeds, vec):
    v = torch.tensor(np.asarray(vec, dtype=np.float32), dtype=torch.float32, device=av.device)
    assert torch.isfinite(v).all(), "non-finite vector BEFORE injection"
    v = v / (v.norm().clamp_min(1e-12) / SCALE)
    e = base_embeds.clone(); e[0, p] = v.to(e.dtype)
    assert torch.isfinite(e).all(), "non-finite embedding AFTER injection (fp16 overflow?)"
    gen = av.generate(inputs_embeds=e, attention_mask=torch.ones_like(ids_t),
                      do_sample=False, max_new_tokens=MAX_NEW, pad_token_id=tok.eos_token_id)
    return tok.decode(gen[0], skip_special_tokens=True)

with torch.no_grad():
    base_embeds = embed(ids_t)
    probe = av(inputs_embeds=base_embeds)
    assert bool(torch.isfinite(probe.logits[0, -1]).all()), "AV logits non-finite un-injected"
    del probe
print("un-injected logits finite", flush=True)

rng = np.random.default_rng(SEED)
rows = []; t0 = time.time()
def emit(kind, vid, slot, vec):
    txt = decode_vec(base_embeds, vec)
    rows.append(dict(kind=kind, id=vid, slot=slot, norm=float(np.linalg.norm(vec)), decode=txt))
    print(f"[{len(rows):3d}] {kind:9s} {vid:28s} {slot:10s} :: {txt[:110]}", flush=True)
    with open(os.path.join(WORK, "decodes.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")

# controls first: if the pipeline is dead, find out in three minutes rather than three hours
for i, cid in enumerate(cids):
    for s, slot in enumerate(slots):
        emit("control", cid, slot, C[i, s])
med = float(np.median(np.linalg.norm(P.reshape(-1, d_model), axis=1)))
for k in range(6):
    r = rng.normal(size=d_model).astype(np.float32); r = r / np.linalg.norm(r) * med
    emit("negative", f"rand_{k}", "random", r)
for i, pid in enumerate(pids):
    for s, slot in enumerate(slots):
        emit("project", pid, slot, P[i, s])
for i, bid in enumerate(bids):
    for s, slot in enumerate(slots):
        emit("bystander_podbuild", bid, slot, B[i, s])

kw = ("weather", "forecast", "rain", "wind", "storm", "coast")
cw = ("python", "function", "def", "test", "assert", "code")
pos_hits = [r for r in rows if r["kind"] == "control" and r["id"].startswith("ctl_weather")
            and any(w in r["decode"].lower() for w in kw)]
code_hits = [r for r in rows if r["kind"] == "control" and r["id"].startswith("ctl_code")
             and any(w in r["decode"].lower() for w in cw)]
neg_hits = [r for r in rows if r["kind"] == "negative"
            and any(w in r["decode"].lower() for w in kw)]
summary = dict(av=AV, layer=NLA_LAYER, quant="bnb4", n_rows=len(rows),
               n_project=len(pids)*len(slots), n_bystander=len(bids)*len(slots),
               bystander_provenance="pod bartowski GGUF, NOT covered by these controls (F172)",
               weather_control_hits=len(pos_hits), weather_control_total=6,
               code_control_hits=len(code_hits), code_control_total=6,
               negative_control_weather_hits=len(neg_hits), negative_total=6,
               minutes=round((time.time() - t0) / 60, 1),
               VERDICT=("USABLE" if pos_hits and not neg_hits else
                        "VOID: positive controls did not decode to topic" if not pos_hits else
                        "VOID: negative controls decoded to the positive topic"))
json.dump(summary, open(os.path.join(WORK, "run_meta.json"), "w"), indent=1)
print("\n=== SUMMARY ===\n" + json.dumps(summary, indent=1), flush=True)
