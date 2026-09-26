#!/usr/bin/env python3
"""Which locally-served episodes have NO activation capture?

The standing rule is that every inference run gets its activations captured. Nothing
enforced it, and nothing reported on it, so the backlog grew silently: on 2026-09-12 this
script found 478 episodes across 36 log directories with no capture at all, including the
entire addressee experiment run that same night and the benign specificity control.

A capture is matched by cid prefix: capture_run.sh names every stream
`<logdir>__<arm>_<tool_arm>_...`, so the set of captured logdirs is recoverable from the
sidecars without re-reading any .bin.

Hosted models are listed separately and are NOT a gap — there are no weights to replay.

Usage:  python bystander/capture_coverage.py [--quiet]
Exit 1 if any locally-served episode is uncaptured, so it can gate a commit or a check-in.
"""
from __future__ import annotations
import argparse, glob, json, os, sys
from inspect_ai.log import read_eval_log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    captured = set()
    for m in glob.glob("bystander/acts_*/*.meta.json"):
        try:
            captured.add(json.load(open(m))["cid"].split("__")[0])
        except Exception:
            continue

    gaps, hosted, ok = [], [], []
    for d in sorted(glob.glob("logs/bystander-*")):
        n, is_hosted = 0, False
        for f in glob.glob(f"{d}/*.eval"):
            try:
                log = read_eval_log(f)
            except Exception:
                continue
            if log.status != "success":
                continue
            mid = str((log.eval.task_args or {}).get("model_id") or log.eval.model or "")
            if not ("local-model" in mid or ".gguf" in mid.lower()):
                is_hosted = True
            n += len(log.samples or [])
        if not n:
            continue
        name = os.path.basename(d)
        (hosted if is_hosted else (ok if name in captured else gaps)).append((name, n))

    if not a.quiet:
        for name, n in gaps:
            print(f"UNCAPTURED  {name:46s} {n:4d} episodes")
        print(f"\ncaptured: {len(ok)} dirs | uncaptured LOCAL: {len(gaps)} dirs, "
              f"{sum(n for _, n in gaps)} episodes | hosted (no weights, not a gap): "
              f"{len(hosted)} dirs")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
