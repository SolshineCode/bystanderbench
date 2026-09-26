#!/usr/bin/env python3
"""Extract BystanderBench episodes as numbered turn sequences for causal, per-turn labelling.

AUTONOMOUS DRAFT (Claude, 2026-09-23, branch autonomous/2026-09-23). Part of item 8: labels that
could train or evaluate a behaviour-specialised SAE/NLA. See SCHEMA.md in this directory.

Keyed to the existing activation captures: `cid = <logdir>__<arm>_<tool_arm>_<affordance>_<solver>_ep<N>`
exactly as in `bystander/acts_*/manifest.tsv`, so every label can later be aligned to the stored
token stream (`<cid>.txt`) and its pre-decision pool range.

Scope decision, stated because §F38 was caused by leaving it implicit: labellers see the VISIBLE
transcript only. `<think>` content is stripped with the project's own `visible_part()` when
available; tool calls and (truncated) tool results are kept, because what a tool returned is
what the agent saw.

Usage: python extract_episodes.py LOGDIR [LOGDIR ...] --out episodes.jsonl
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "concealment-probe", "tools"))
try:
    from screen_behavioral import visible_part
except Exception:  # fall back to a strict strip; recorded in each row
    def visible_part(t):
        t = re.sub(r"<think>.*?</think>", "", t or "", flags=re.S)
        return re.sub(r"^.*?</think>", "", t, flags=re.S)
    FALLBACK = True
else:
    FALLBACK = False

# v2 (2026-09-23): NO truncation. v1 cut tool results at 1,500 chars while the task lets the agent
# see up to 16,000 (Inspect already applied that cap when it logged the message), so labellers
# could not see evidence the agent saw (pilot_v1/RESULT.md). The logged text IS what the agent saw.
TOOL_RESULT_CHARS = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from inspect_ai.log import read_eval_log
    n = 0
    with open(a.out, "w") as fh:
        for d in a.logdir:
            base = os.path.basename(d.rstrip("/"))
            for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
                log = read_eval_log(p)
                if log.status != "success":
                    continue
                ta = log.eval.task_args or {}
                for s in log.samples or []:
                    if s.error:
                        continue
                    arm, tool_arm = ta.get("arm"), ta.get("tool_arm")
                    aff, sk = ta.get("affordance", "native"), ta.get("solver_kind", "tools")
                    cid = f"{base}__{arm}_{tool_arm}_{aff}_{sk}_ep{s.epoch}"
                    turns = []
                    for i, m in enumerate(s.messages or []):
                        if m.role == "system":
                            continue
                        t = {"idx": i, "role": m.role}
                        if m.role == "assistant":
                            t["text"] = visible_part(m.text or "").strip()
                            t["tool_calls"] = [{"fn": tc.function,
                                                "args": json.dumps(tc.arguments)}
                                               for tc in (m.tool_calls or [])]
                        elif m.role == "tool":
                            txt = m.text or ""
                            t["text"] = txt
                            t["fn"] = getattr(m, "function", None)
                        else:
                            t["text"] = (m.text or "")[:4000]
                        turns.append(t)
                    fh.write(json.dumps({"cid": cid, "logdir": base, "model": ta.get("model_id") or log.eval.model,
                                         "arm": arm, "tool_arm": tool_arm, "epoch": s.epoch,
                                         "visible_part_fallback": FALLBACK, "turns": turns}) + "\n")
                    n += 1
    print(f"{n} episodes -> {a.out}  (visible_part fallback: {FALLBACK})")


if __name__ == "__main__":
    main()
