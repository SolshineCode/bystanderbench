#!/usr/bin/env python3
"""Write a positives-first extraction manifest for a prepare_dataset.py output dir.

Order: concealed_cheat -> disclosed -> failed_silent on tasks that also produced a cheat
-> remaining failed_silent -> original_*; within a tier, shortest transcripts first.
Rows that already have acts/{sid}.bin are skipped. Use when a full capture will not fit
the GPU window (north-mini transcripts: median ~86k tokens at ~185 tok/s on an M40).
Usage: prioritize_manifest.py <data/model_tag dir> [--out manifest_prioritized.tsv]
"""
import argparse, json, os
ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--out", default=None)
a = ap.parse_args(); D = a.dir
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import load
# Queueing extraction for acts/{sid}.bin keyed by sid, so unit is 'activation'.
rows = load(os.path.join(D, "samples.jsonl"), unit="activation")
man = {l.split("\t")[1].split("/")[-1]: l for l in open(os.path.join(D, "manifest.tsv")) if l.strip()}
cheat_tasks = {r["task_id"] for r in rows if r["category"] == "concealed_cheat"}
def pri(r):
    c = r["category"]
    tier = (0 if c == "concealed_cheat" else 1 if c == "disclosed"
            else 2 if c == "failed_silent" and r["task_id"] in cheat_tasks
            else 3 if c == "failed_silent" else 4)
    return (tier, r["n_total_tokens"])
acts = os.path.join(D, "acts"); os.makedirs(acts, exist_ok=True)
done = {f[:-4] for f in os.listdir(acts) if f.endswith(".bin")}
order = [r for r in sorted(rows, key=pri) if r["sid"] not in done]
out = a.out or os.path.join(D, "manifest_prioritized.tsv")
open(out, "w").write("".join(man[r["sid"]] for r in order))
print(f"{len(done)} already extracted, {len(order)} queued -> {out}")
for r in order[:12]:
    print(f"  {r['sid']:32s} {r['category']:16s} {r['n_total_tokens']:>7d} tok")
print(f"  total queued tokens: {sum(r['n_total_tokens'] for r in order):,}")
