#!/usr/bin/env python3
"""Post-hoc content-based discovery over finished logs (no sandbox needed): rebuild the
arm's environment from (arm, seed), take every evidence-file line >= 40 chars, and check
which appear verbatim in the episode's tool results. Independent re-implementation of
scorer._content_discovery, so agreement with the live metric is a check on the scorer.
Usage: posthoc_content.py logs/<label> [--min-len 40]"""
import argparse, glob, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inspect_ai.log import read_eval_log
from inspect_ai.model import ChatMessageTool, ChatMessageUser
from bystander.env.build_env import build_env
ap = argparse.ArgumentParser(); ap.add_argument("logdir"); ap.add_argument("--min-len", type=int, default=40)
a = ap.parse_args()
cache = {}
def evidence_lines(arm, seed):
    if (arm, seed) not in cache:
        out = tempfile.mkdtemp(prefix="by_posthoc_")
        man = build_env(arm, seed, out)
        lines = {}
        for p in man["evidence_paths"]:
            fp = os.path.join(out, p)
            if os.path.isfile(fp):
                lines[p] = [ln.strip() for ln in open(fp, errors="replace") if len(ln.strip()) >= a.min_len]
        cache[(arm, seed)] = lines
    return cache[(arm, seed)]
agree = disagree = 0
for p in sorted(glob.glob(os.path.join(a.logdir, "*.eval"))):
    log = read_eval_log(p); ta = log.eval.task_args or {}
    for s in log.samples or []:
        seed = (s.metadata or {}).get("seed")
        # Prompted-solver episodes have NO ChatMessageTool at all -- command results come
        # back as user turns beginning "exit=". Reading only ChatMessageTool here made this
        # script report a structural 0, mirroring the scorer bug fixed on 2026-09-10.
        _tool = [(m.text or "") for m in s.messages if isinstance(m, ChatMessageTool)]
        if _tool:
            seen = "\n".join(_tool)
        else:
            seen = "\n".join(m.text for m in s.messages
                              if isinstance(m, ChatMessageUser) and (m.text or "").startswith("exit="))
        hits = {path: [ln for ln in lines if ln in seen] for path, lines in evidence_lines(ta["arm"], seed).items()}
        hits = {k: v for k, v in hits.items() if v}
        live = (s.scores or {}).get("bystander_scorer")
        live_v = live.value.get("discovered_content") if live else None
        post = 1 if hits else 0
        if live_v is not None:
            agree += int(live_v == post); disagree += int(live_v != post)
        print(f"{ta['arm']:22s} {ta['tool_arm']:9s} ep{s.epoch} posthoc={post} live={live_v} files={list(hits)} "
              f"example={(next(iter(hits.values()))[0][:70] if hits else '')!r}")
print(f"\nscorer agreement on episodes that had the live metric: {agree} agree, {disagree} disagree")
