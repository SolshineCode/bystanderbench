#!/usr/bin/env python3
"""Recompute `considered_in_reasoning` over finished logs, without re-running anything.

The first reasoning-on run scored 0/12 because the scorer only looked for inline <think>
tags, while Inspect stores chain of thought in typed ContentReasoning blocks whose text
lives in `.summary`. The episodes are fine; only the scoring was blind. This reads the
stored logs directly, so the GPU work does not have to be repeated.

Prints per-episode so a zero can be checked against how much reasoning there actually was:
a model that produced two sentences of reasoning and a model that produced none are very
different, and an aggregate rate hides which one you have.
"""
import argparse
import re, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bystander.scorer import _keyword_hits
from inspect_ai.log import read_eval_log


def blocks(sample):
    out = []
    for m in (sample.messages or []):
        c = getattr(m, "content", None)
        if isinstance(c, str):
            # Inline <think> blocks arrive as plain string content, not typed parts.
            # Skipping strings outright made this script report zero reasoning for exactly
            # the providers that use the inline convention, while scorer.py read them fine.
            _m = re.findall(r"<think>(.*?)</think>", c, re.IGNORECASE | re.DOTALL)
            if _m:
                out.extend(t.strip() for t in _m if t.strip())
            continue
        for part in (c or []):
            if getattr(part, "type", None) == "reasoning":
                t = (getattr(part, "reasoning", "") or "") + " " + (getattr(part, "summary", "") or "")
                if t.strip():
                    out.append(t.strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdirs", nargs="+")
    ap.add_argument("--show", action="store_true", help="print each episode's reasoning")
    a = ap.parse_args()
    for d in a.logdirs:
        k = n = 0; chars = []
        for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
            log = read_eval_log(p)
            for i, s in enumerate(log.samples or [], 1):
                bs = blocks(s); txt = "\n".join(bs)
                hits = sorted(set(_keyword_hits(txt)))
                n += 1; k += 1 if hits else 0; chars.append(len(txt))
                if a.show:
                    print(f"  ep{i:02d} blocks={len(bs)} chars={len(txt):5d} hits={hits}")
                    if txt:
                        print(f"       {txt[:200]}".replace("\n", " "))
        med = sorted(chars)[len(chars)//2] if chars else 0
        print(f"{os.path.basename(d)}: considered_in_reasoning {k}/{n} | "
              f"median reasoning chars/episode = {med} | episodes with ANY reasoning = "
              f"{sum(1 for c in chars if c > 0)}/{n}")


if __name__ == "__main__":
    main()
