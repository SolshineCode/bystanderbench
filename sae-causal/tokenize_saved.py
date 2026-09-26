#!/usr/bin/env python3
"""Rebuild token streams for ALREADY-GENERATED resample rows, so they can get activations.

Why this is needed separately from `run_resample.py --tokens-dir`: token capture was added
on 2026-09-08, after the runs that produced every one of the harvest's 15 positives
(§F40). Those generations cannot be recreated — the same sid and seed does not reproduce
the same text under llama.cpp (§F37) — but their text was saved, so the exact stream can
be rebuilt from the stored continuation without regenerating anything.

The stream is the rendered prompt for that row's truncated message prefix, plus the stored
continuation, plus the turn terminator: identical in construction to what
`run_resample.py` writes live. Provenance grade is teacher-forced, same as everything else
in this project's activation pipeline, and the weights and quantisation match the server
that produced the text as long as this is pointed at the UNSTEERED server.

**Point this at the unsteered server.** Reading a generation back through a server that
has a control vector applied would capture activations from a perturbed model and label
them as the base model's.
"""
import argparse, json, os, sys, urllib.request

BASE = "/home/darkstar/bluedot-unit2-impossiblebench"
sys.path.insert(0, os.path.join(BASE, "sae-causal"))
from run_resample import post, flatten  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True, help="UNSTEERED llama-server")
    ap.add_argument("--rows", action="append", required=True, help="resample_*.jsonl")
    ap.add_argument("--transcripts", default=os.path.join(
        BASE, "concealment-probe/data/gemma12b/gemma3-12b/transcripts.jsonl"))
    ap.add_argument("--categories", default="concealed_cheat")
    ap.add_argument("--max-per-category", type=int, default=0, help="0 = all")
    ap.add_argument("--eos", default="<end_of_turn>")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--manifest", required=True)
    a = ap.parse_args()

    tr = {}
    for line in open(a.transcripts):
        r = json.loads(line)
        tr.setdefault(r["sid"], r)          # first wins; prefix only, text comes from the row

    want = set(a.categories.split(","))
    rows, seen = [], set()
    for f in a.rows:
        for line in open(f):
            r = json.loads(line)
            if r["cid"] in seen or r["category"] not in want:
                continue
            seen.add(r["cid"]); rows.append(r)
    rows.sort(key=lambda r: r["cid"])
    if a.max_per_category:
        keep, cnt = [], {}
        for r in rows:
            c = cnt.get(r["category"], 0)
            if c < a.max_per_category:
                keep.append(r); cnt[r["category"]] = c + 1
        rows = keep
    print(f"{len(rows)} rows to tokenise -> {a.out_dir}", flush=True)

    os.makedirs(a.out_dir, exist_ok=True)
    man, skipped = [], 0
    for r in rows:
        t = tr.get(r["sid"])
        if not t:
            print(f"SKIP {r['cid']}: no transcript for {r['sid']}", flush=True); skipped += 1; continue
        msgs = t.get("messages") or []
        prefix = [{"role": m["role"], "content": flatten(m.get("content"))} for m in msgs[:-1]]
        try:
            ptxt = post(a.port, "/apply-template", {"messages": prefix})["prompt"]
            ptoks = post(a.port, "/tokenize", {"content": ptxt, "add_special": False,
                                               "parse_special": True})["tokens"]
            rtoks = post(a.port, "/tokenize", {"content": r["text"] + a.eos,
                                               "add_special": False,
                                               "parse_special": True})["tokens"]
        except Exception as e:
            print(f"ERR {r['cid']}: {type(e).__name__}: {e}", flush=True); skipped += 1; continue
        toks = ptoks + rtoks
        tf = os.path.join(a.out_dir, r["cid"] + ".txt")
        open(tf, "w").write("\n".join(map(str, toks)))
        man.append(f"{tf}\t{os.path.join(a.out_dir, 'acts', r['cid'])}\t{len(ptoks)}\t{len(toks)}")
        print(f"{r['cid']}: {r['category']} toks={len(toks)}", flush=True)

    with open(a.manifest, "w") as fh:
        fh.write("\n".join(man) + "\n")
    print(f"wrote {len(man)} streams, skipped {skipped} -> {a.manifest}")


if __name__ == "__main__":
    main()
