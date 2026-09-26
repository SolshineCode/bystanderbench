# Generate nla-decode/colab/nla_decode_v4.ipynb from script.py.
#
# The notebook embeds script.py's source VERBATIM in one cell, so "the Colab
# notebook and the Kaggle kernel are the same script" is a fact about the files
# rather than a claim in a comment.  Re-run this after every edit to script.py:
#
#   python gen_colab_notebook.py
#
# It prints the sha256 of the embedded source, which the notebook also prints at
# run time so a stale notebook is visible in its own output.
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "script.py")
OUT = os.path.join(HERE, "..", "..", "colab", "nla_decode_v4.ipynb")

src = open(SRC).read()
digest = hashlib.sha256(src.encode()).hexdigest()


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


INTRO = f"""# NLA decode v4 -- recruiter-pilot project vectors (free Colab T4)

Same script as the Kaggle kernel `nla-decode/kernels/nla-decode-v4-20260914/script.py`
(sha256 `{digest[:16]}...`), embedded verbatim in cell 3. Regenerate with
`python gen_colab_notebook.py` after any edit to the kernel.

**What it does.** Reconstructs each of the 24 recruiter-pilot episodes' exact
final-stage context from the private HF dataset, *verifies* the reconstruction
against the token counts the pilot itself recorded, runs one forward pass per
episode, reads `hidden_states[33]` (kitft layer 32) at three positions -- last
prompt token, first response token, mean over the response span -- and decodes
each through `kitft/nla-gemma3-12b-L32-av`. A weather positive control and two
norm-matched random-direction negative controls run in the same pass.

**Nothing is mounted.** Results go to `/content/out/` and the last cell prints
them in full so they survive the runtime being recycled. Copy that output.

**Memory reality on a free T4 (15 GB).** The AV is a 12B model: in bf16 its
weights are ~24 GB and do *not* fit one T4 (the Kaggle kernel gets 2x T4 = 30 GB,
RunPod got an A40). Cell 2 therefore sets `NLA_AV_QUANT=bnb4` automatically when
less than 26 GB of VRAM is visible. **4-bit changes the decode numerics and is
not the validated path** -- but it is not taken on trust either: the weather
positive control runs first and the script exits before the project vectors if
it does not decode to weather-like text. If it exits there, the answer is a
bigger GPU, not a looser threshold.

On a Colab Pro A100/L4 with >=26 GB the same cells run the validated bf16 path
with no changes.
"""

SETUP = '''# --- cell 2: environment ---------------------------------------------------
import os, subprocess, getpass

print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
                      "--format=csv,noheader"], capture_output=True, text=True).stdout)

# HF token: Colab secret "HF_TOKEN" (key icon in the sidebar) if present, else prompt.
# The recruiter pilot dataset is private, so this is required.
tokval = None
try:
    from google.colab import userdata
    tokval = userdata.get("HF_TOKEN")
    print("HF token: Colab secret")
except Exception:
    pass
if not tokval:
    tokval = getpass.getpass("HF token (write-not-needed, read access to "
                             "DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b): ")
os.environ["HF_TOKEN"] = tokval.strip()

os.environ["NLA_WORK"] = "/content/out"
os.makedirs("/content/out", exist_ok=True)

# bf16 12B AV weights are ~24 GB. Pick 4-bit only when bf16 cannot possibly fit,
# and say so loudly -- the positive control decides whether the result is usable.
try:
    import torch
    total_gb = sum(torch.cuda.get_device_properties(i).total_memory
                   for i in range(torch.cuda.device_count())) / 1e9
except Exception:
    total_gb = 0.0
os.environ["NLA_AV_QUANT"] = "bf16" if total_gb >= 26 else "bnb4"
print(f"visible VRAM: {total_gb:.1f} GB  ->  NLA_AV_QUANT={os.environ['NLA_AV_QUANT']}")
if os.environ["NLA_AV_QUANT"] == "bnb4":
    print("!! 4-bit AV fallback: numerics differ from the bf16 path validated on "
          "RunPod/Kaggle. Treat the weather positive control's decode as the "
          "evidence that this run means anything.")

# T4 (sm_75) has no bf16 tensor cores; PyTorch computes bf16 correctly via
# fallback kernels -- slower, numerically sound. That is the point: fp16 would be
# faster and would overflow gemma's 6e4-8e4 layer-32 activations to inf.
!pip install -q "transformers>=4.50" accelerate "bitsandbytes>=0.46.1" huggingface_hub pyyaml
os.environ["NLA_SKIP_PIP"] = "1"
print("environment ready")
'''

RUN_HDR = f'''# --- cell 3: the kernel, verbatim ------------------------------------------
# Identical to nla-decode/kernels/nla-decode-v4-20260914/script.py
# sha256: {digest}
# Expect roughly: base load 3-6 min, 24 extraction forwards 15-30 min,
# AV load 3-8 min, 79 decodes 20-60 min. Keep the tab alive.
'''

TAIL = '''# --- cell 4: print everything, so the results survive the runtime ----------
# Colab recycles /content without warning and nothing here is mounted. This cell
# is the artifact: copy its output into
# nla-decode/results/colab-<date>/decodes.jsonl.
import json, os

W = "/content/out"
for f in ("run_meta.json", "decodes.jsonl"):
    p = os.path.join(W, f)
    print("=" * 78)
    print(p, os.path.getsize(p) if os.path.exists(p) else "MISSING")
    print("=" * 78)
    if os.path.exists(p):
        print(open(p).read())

# Human-readable pass: controls first, then project vectors grouped by slot.
p = os.path.join(W, "decodes.jsonl")
if os.path.exists(p):
    rows = [json.loads(l) for l in open(p)]
    print("\\n\\n" + "#" * 78)
    print(f"# {len(rows)} decodes  "
          f"({sum(r['is_control'] for r in rows)} control, "
          f"{sum(not r['is_control'] for r in rows)} project)")
    print("#" * 78)
    for r in sorted(rows, key=lambda r: (not r["is_control"], r.get("slot") or "", r["name"])):
        print(f"\\n--- {r['name']}  slot={r.get('slot')} norm={r['norm']:.1f} "
              f"control={r['is_control']} arm={r.get('arm')} cat={r.get('category')}")
        print(r["decoded"])
'''

nb = {
    "nbformat": 4, "nbformat_minor": 0,
    "metadata": {
        "colab": {"provenance": [], "gpuType": "T4", "toc_visible": True},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
    },
    "cells": [md(INTRO), code(SETUP), code(RUN_HDR + src), code(TAIL)],
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(nb, f, indent=1)
print(f"wrote {os.path.abspath(OUT)}  (script.py sha256 {digest})")
