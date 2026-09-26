# First real NLA decode (workstream A): kitft/nla-gemma3-12b-L32-av on Kaggle T4x2.
#
# Phases:
#   1. VALIDATION: extract fresh layer-32 vectors (kitft convention:
#      hidden_states[33]) from the 4-bit gemma-3-12b base on known text, decode
#      them with the AV -- sanity-checks the whole injection path end to end.
#   2. PROJECT VECTORS: decode response-span vectors from the recruiter pilot
#      (DarkStarDeleeuw private dataset). CAVEAT carried into the output: those
#      arrays' "layer 32" row is hidden_states[32] = block 31 -- one block below
#      the NLA layer (pilot predates the convention fix), AND they are span
#      MEANS, not single positions. Interpret as adjacent-layer/pooled probes of
#      the verbalizer, not in-distribution decodes.
#
# Injection recipe replicated from kitft/nla-inference (nla_inference.py):
#   ids = chat_template(AV prompt containing injection char)
#   embeds = embedding_lookup(ids) * sqrt(d)        # gemma scales embeds in fwd
#   embeds[pos(injection_char)] = v * (injection_scale / ||v||)
#   generate(inputs_embeds=embeds, greedy)
import os, sys, subprocess, json, math

os.environ["PYTHONUNBUFFERED"] = "1"
try:
    r = subprocess.run(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
                       capture_output=True, text=True, timeout=10)
    caps = [float(x.strip()) for x in r.stdout.strip().split("\n") if x.strip()]
    print("GPU caps:", caps)
    if caps and min(caps) < 7.0:
        print("ABORT: P100; re-push for T4."); sys.exit(1)
except Exception as e:
    print("cap detect skipped:", e)

subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "transformers>=4.50", "accelerate", "bitsandbytes>=0.46.1",
                "huggingface_hub", "pyyaml"], check=False)

import torch, yaml, numpy as np
from huggingface_hub import hf_hub_download, snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

HF_TOKEN = "INJECT_HF_TOKEN"
AV = "kitft/nla-gemma3-12b-L32-av"
BASE4 = "unsloth/gemma-3-12b-it-bnb-4bit"
PILOT = "DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b"
WORK = "/kaggle/working"
out_f = open(os.path.join(WORK, "decodes.jsonl"), "w")

meta = yaml.safe_load(open(hf_hub_download(AV, "nla_meta.yaml")))
INJ_CHAR = meta["tokens"]["injection_char"]
INJ_ID = meta["tokens"]["injection_token_id"]
L_ID = meta["tokens"]["injection_left_neighbor_id"]
R_ID = meta["tokens"]["injection_right_neighbor_id"]
SCALE = float(meta["extraction"]["injection_scale"])
PROMPT = meta["prompt_templates"]["av"]
print(f"meta: inj_id={INJ_ID} scale={SCALE} layer={meta['extraction_layer_index']}")

tok = AutoTokenizer.from_pretrained(AV)
live = tok.encode(INJ_CHAR, add_special_tokens=False)
assert live == [INJ_ID], f"tokenizer drift: {live} != [{INJ_ID}]"

# ---------- phase 1: fresh validation vectors from the 4-bit base ----------
VAL_TEXTS = [
    ("code_cheat_flavor",
     "def check(candidate):\n    assert candidate(5) == 7\n\n"
     "def solve(k):\n    if k == 5:\n        return 7  # hardcoded to pass the test\n    return 0\n"),
    ("weather", "The forecast says heavy rain and strong winds across the coast tomorrow."),
]
from transformers import AutoModelForImageTextToText
try:
    base = AutoModelForCausalLM.from_pretrained(BASE4, device_map="auto")
except Exception as e:
    print("CausalLM load failed, trying ImageTextToText:", type(e).__name__)
    base = AutoModelForImageTextToText.from_pretrained(BASE4, device_map="auto")
base.eval()
btok = AutoTokenizer.from_pretrained(BASE4)
val_vecs = []
with torch.no_grad():
    for name, text in VAL_TEXTS:
        ids = btok(text, return_tensors="pt").input_ids.to(base.device)
        out = base(ids, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states[33][0]           # kitft layer 32 = hidden_states[33]
        val_vecs.append((f"val_{name}_last", hs[-1].float().cpu().numpy()))
        val_vecs.append((f"val_{name}_mid", hs[len(hs)//2].float().cpu().numpy()))
print("validation vectors:", [v[0] for v in val_vecs])
del base
torch.cuda.empty_cache()

# ---------- fetch project vectors (recruiter pilot, private) ----------
proj_vecs = []
try:
    for sid in ("oneoff_lcbhard_9_pressure_e1", "oneoff_lcbhard_9_control_e1",
                "oneoff_lcbhard_41_pressure_e1", "conflicting_lcbhard_9_control_e1"):
        jb = hf_hub_download(PILOT, f"stage_acts/{sid}.json", repo_type="dataset", token=HF_TOKEN)
        bb = hf_hub_download(PILOT, f"stage_acts/{sid}.bin", repo_type="dataset", token=HF_TOKEN)
        m = json.load(open(jb))
        arr = np.fromfile(bb, dtype=np.float32).reshape(m["shape"])
        li = m["layers"].index(32)
        proj_vecs.append((f"pilot_{sid}_finalstage_L32row", arr[-1, li]))
    print("project vectors:", [v[0] for v in proj_vecs])
except Exception as e:
    print("PROJECT VECTOR FETCH FAILED (continuing with validation only):", e)

# ---------- phase 2: load AV, decode ----------
# bf16, not fp16: gemma activations overflow fp16 (v3 generated 220x token id 0 =
# pad, logits NaN). T4/sm_75 has no bf16 tensor cores but PyTorch computes bf16
# correctly via fallback kernels -- slower, numerically sound.
av = AutoModelForCausalLM.from_pretrained(AV, torch_dtype=torch.bfloat16, device_map="auto")
av.eval()
d = av.config.hidden_size
embed = av.get_input_embeddings()
# v3 FIX: the model's own embedding module (Gemma3TextScaledWordEmbedding) ALREADY
# multiplies by sqrt(d) in forward(). The reference multiplies manually only
# because it loads a raw nn.Embedding from safetensors. Multiplying again made
# prompt embeds 62x too large vs the injected vector -> instant EOS, empty decodes.
EMB_SCALE = 1.0
probe = embed(torch.tensor([[L_ID]], device=av.device))
print("embed-module row norm for a known token (should be sqrt(d)-scaled already):",
      float(probe.norm()))
content = PROMPT.format(injection_char=INJ_CHAR)
prompt_txt = tok.apply_chat_template([{"role": "user", "content": content}],
                                     tokenize=False, add_generation_prompt=True)
ids = tok(prompt_txt, add_special_tokens=False).input_ids
if ids and isinstance(ids[0], list):
    ids = ids[0]
pos = [i for i, t in enumerate(ids) if t == INJ_ID]
print(f"prompt tokens={len(ids)} inj_positions={pos} "
      f"neighbors={[ids[pos[0]-1], ids[pos[0]+1]] if len(pos)==1 else None} "
      f"expected=[{L_ID},{R_ID}]")
assert len(pos) == 1 and ids[pos[0]-1] == L_ID and ids[pos[0]+1] == R_ID, "prompt drift"
p = pos[0]
ids_t = torch.tensor([ids], device=av.device)

with torch.no_grad():
    base_embeds = embed(ids_t) * EMB_SCALE      # [1, T, d]
    probe_out = av(inputs_embeds=base_embeds)
    pl = probe_out.logits[0, -1]
    print(f"logits probe: finite={bool(torch.isfinite(pl).all())} max={float(pl.max()):.2f} argmax={int(pl.argmax())}")
    del probe_out
    for name, vec in val_vecs + proj_vecs:
        v = torch.tensor(vec, dtype=torch.float32, device=av.device)
        v = v / (v.norm().clamp_min(1e-12) / SCALE)
        e = base_embeds.clone()
        e[0, p] = v.to(e.dtype)
        gen = av.generate(inputs_embeds=e, attention_mask=torch.ones_like(ids_t),
                          do_sample=False, max_new_tokens=220,
                          pad_token_id=tok.eos_token_id)
        raw_ids = gen[0].tolist()
        text = tok.decode(gen[0], skip_special_tokens=True)
        nan = bool(torch.isnan(e).any())
        print(f"=== {name} (nan_in={nan}, n_gen={len(raw_ids)}, first_ids={raw_ids[:6]}) ===")
        print(text[:600])
        out_f.write(json.dumps({"name": name, "decode": text,
                                "vec_norm": float(np.linalg.norm(vec))}) + "\n")
        out_f.flush()

print("DONE")
