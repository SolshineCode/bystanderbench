"""Dump every alert_oversight tool call from a BystanderBench Inspect log dir to JSONL.

One line per (sample, call): {batch, sid, epoch, call_index, alert_text, discovered_content,
alerted, n_messages}. Deterministic; no model involved. Used by the offline Hermes prescreen so
the local model only ever sees the alert text itself, never the whole log.
"""
import json, sys, glob, os
from inspect_ai.log import read_eval_log

def main(logdir, out):
    n = 0
    with open(out, "w") as fh:
        for path in sorted(glob.glob(os.path.join(logdir, "*.eval"))):
            log = read_eval_log(path)
            for s in (log.samples or []):
                sc = (s.scores or {}).get("bystander_scorer")
                val = getattr(sc, "value", {}) if sc else {}
                if not isinstance(val, dict):
                    val = {}
                k = 0
                for m in (s.messages or []):
                    for tc in (getattr(m, "tool_calls", None) or []):
                        if tc.function != "alert_oversight":
                            continue
                        args = tc.arguments if isinstance(tc.arguments, dict) else {"raw": str(tc.arguments)}
                        text = " ".join(str(v) for v in args.values())
                        fh.write(json.dumps({"batch": os.path.basename(logdir.rstrip("/")), "sid": s.id,
                                             "epoch": s.epoch, "call_index": k, "alert_text": text,
                                             "discovered_content": val.get("discovered_content"),
                                             "alerted": val.get("alerted"),
                                             "n_messages": len(s.messages or [])}) + "\n")
                        k += 1; n += 1
    print(f"{n} alert calls -> {out}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
