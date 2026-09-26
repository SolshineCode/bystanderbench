#!/usr/bin/env python3
"""Export FULL per-sample transcripts from Inspect .eval logs to transcripts.jsonl.

prepare_dataset.py stores only the final assistant text (the probed response);
this exporter preserves the complete record for the HF provenance archive:
every message (system/user/assistant/tool) with role, full content (including
reasoning blocks), tool calls if any, plus task input, score, and verification
metadata. Sample ids (sid) match prepare_dataset.py exactly
(f"{split}_{id}_e{epoch}") so rows join 1:1 with samples.jsonl / acts/.

Usage:
  export_transcripts.py --logdir logs/<label> [--logdir logs/<label2> ...] \
                        --out <outdir>/transcripts.jsonl
"""
import argparse, glob, json, os


def split_of(task_name):
    for s in ("conflicting", "oneoff", "original"):
        if s in task_name:
            return s
    return "unknown"


def jsonable(x):
    """Best-effort pydantic -> plain-json conversion."""
    if hasattr(x, "model_dump"):
        try:
            return x.model_dump(mode="json", exclude_none=True)
        except Exception:
            pass
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logdir", action="append", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from inspect_ai.log import read_eval_log

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    n = 0
    with open(args.out, "w") as fo:
        for d in args.logdir:
            for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
                log = read_eval_log(p)
                task = log.eval.task
                split = split_of(task)
                model = log.eval.model
                for s in (log.samples or []):
                    sid = f"{split}_{s.id}_e{s.epoch}"
                    scores = {}
                    for k, v in (s.scores or {}).items():
                        scores[k] = {
                            "value": jsonable(v.value),
                            "answer": jsonable(getattr(v, "answer", None)),
                            "metadata": jsonable(v.metadata or {}),
                        }
                    row = {
                        "sid": sid,
                        "task": task,
                        "split": split,
                        "task_id": str(s.id),
                        "epoch": s.epoch,
                        "model": model,
                        "input": jsonable(s.input),
                        "messages": [jsonable(m) for m in s.messages],
                        "n_messages": len(s.messages),
                        "scores": scores,
                        "error": jsonable(getattr(s, "error", None)),
                        "log_file": os.path.basename(p),
                        "log_dir": os.path.basename(os.path.normpath(d)),
                    }
                    fo.write(json.dumps(row) + "\n")
                    n += 1
                    print(f"{sid}: {len(s.messages)} messages, scores={list(scores)}")
    print(f"wrote {n} transcripts to {args.out}")


if __name__ == "__main__":
    main()
