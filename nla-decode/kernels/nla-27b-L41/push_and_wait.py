#!/usr/bin/env python3
"""Push the 27b L41 NLA kernel when a Kaggle GPU slot frees, then wait and pull results.

Kaggle allows 2 concurrent batch GPU sessions per account. On 2026-09-16 both were held by
nla-v9-lfm25-reeval-fixed and nla-v9-qwen35-reeval-fixed, which belong to other work, so this
queues politely instead of cancelling them. It never cancels anything it did not start.
"""
import json, os, sys, time, shutil
from pathlib import Path
os.environ.setdefault("KAGGLE_CONFIG_DIR", os.path.expanduser("~/.kaggle"))
from kaggle.api.kaggle_api_extended import KaggleApi

KDIR = Path("nla-decode/kernels/nla-27b-L41")
REF = json.load(open(KDIR / "kernel-metadata.json"))["id"]
OUT = Path("nla-decode/results/kaggle-27b-L41-2026-09-16")
POLL_PUSH, POLL_RUN, MAX_WAIT_H = 600, 180, 14  # 600s: a 50-kernel status scan drew a 429 on 2026-09-16, so be patient rather than clever

api = KaggleApi(); api.authenticate()

def status(ref):
    try:
        return str(getattr(api.kernels_status(ref), "status", ""))
    except Exception as e:
        return f"unknown:{type(e).__name__}"

t0 = time.time()
pushed = False
while time.time() - t0 < MAX_WAIT_H * 3600:
    try:
        r = api.kernels_push(str(KDIR))
        err = getattr(r, "error", None)
        if err:
            print(f"[{time.strftime('%H:%M')}] push refused: {err}", flush=True)
            if "session count" not in str(err):
                sys.exit(f"push failed for a reason other than the slot cap: {err}")
        else:
            print(f"[{time.strftime('%H:%M')}] pushed {REF} -> {getattr(r,'url','')}", flush=True)
            pushed = True
            break
    except Exception as e:
        print(f"[{time.strftime('%H:%M')}] push exception: {type(e).__name__} {str(e)[:160]}", flush=True)
    time.sleep(POLL_PUSH)
if not pushed:
    sys.exit("gave up waiting for a free Kaggle GPU slot")

while time.time() - t0 < MAX_WAIT_H * 3600:
    s = status(REF)
    print(f"[{time.strftime('%H:%M')}] {REF}: {s}", flush=True)
    u = s.upper()
    if "COMPLETE" in u or "ERROR" in u or "CANCEL" in u:
        break
    time.sleep(POLL_RUN)

OUT.mkdir(parents=True, exist_ok=True)
try:
    api.kernels_output(REF, path=str(OUT), force=True, quiet=False)
    print("pulled output to", OUT, flush=True)
except Exception as e:
    print("output pull failed:", type(e).__name__, str(e)[:200], flush=True)
try:
    log = api.kernels_output(REF, path=str(OUT), force=True, quiet=True)
except Exception:
    pass
meta = OUT / "run_meta.json"
if meta.exists():
    print("=== run_meta.json ===", flush=True)
    print(json.dumps(json.load(open(meta)), indent=1), flush=True)
else:
    print("no run_meta.json in the output; check the kernel log", flush=True)
print("final status:", status(REF), flush=True)
