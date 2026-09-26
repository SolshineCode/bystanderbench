#!/usr/bin/env python3
"""One loader for samples.jsonl / transcripts.jsonl, with the unit made explicit.

## Why this exists

This project has produced the same class of counting error at least five times
(§F19, §F22, the probe_fit double-count, §F37, §F40). The cause is structural, not
carelessness at the call site:

1. **`sid` is a design-cell id being used as a generation id.** It is
   `{split}_{task_id}_e{epoch}`, stable by construction across waves and re-runs, so two
   genuinely different generations legitimately share one sid. No field in the data
   uniquely identifies a single generation.
2. **The correct handling is opposite for different consumers.** Activation analyses MUST
   collapse, because `acts/{sid}.bin` is keyed by sid and later writes overwrite earlier
   ones. Behavioural counts MUST NOT: §F22 found only 10 of 42 collisions were true
   copies, so collapsing discarded 32 real samples. Generation loops must dedupe before
   iterating or they re-run work (§F37).
3. **Nothing labels the unit of a number.** "15 positives" was simultaneously 15 rows,
   10 distinct solutions and 3 tasks (§F40). The largest denominator is the easiest to
   reach for.

So `unit` is a REQUIRED argument here. You cannot load this corpus without saying what
you intend to count, and `denominators()` reports all of them at once so a script can
print `rows=15 generations=15 solutions=10 tasks=3` instead of a bare N.

## Units

- `row`        every line as written. Correct for provenance and for auditing what a file
               literally contains. Wrong for almost every rate.
- `generation` distinct model outputs: rows sharing a sid are collapsed only when their
               `final_text` is byte-identical (a true copy read from two `.eval` files).
               **This is the right default for behavioural rates.**
- `activation` one row per sid, because the activation and token files are keyed by sid
               and overwrite. Loading two rows for one sid double-counts one `.bin`.
- `solution`   distinct extracted code, so N near-identical hardcodes of the same task
               count once. The honest unit for "how many distinct cheats do we have".
- `task`       one entry per task_id. The unit the volume gate counts.

`generation_id` (sha1 of sid + final_text) is added to every row, so "distinct
generation" becomes checkable rather than assumed.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
from collections import Counter, OrderedDict

UNITS = ("row", "generation", "activation", "solution", "task")


def _generation_content(r: dict) -> str:
    """The text that distinguishes one generation from another sharing its sid.

    `final_text` for samples.jsonl; the full message list for transcripts.jsonl, which
    has no `final_text` field. Raising when neither exists is deliberate: an earlier
    version fell back to the empty string, so `load(transcripts.jsonl, "generation")`
    hashed every row to sid alone and silently collapsed distinct generations — §F22
    reintroduced through the very loader written to prevent it. A row whose generation
    cannot be identified must stop the count, not quietly join another one.
    """
    t = r.get("final_text")
    if t is not None:
        return t
    msgs = r.get("messages")
    if isinstance(msgs, list) and msgs:
        return json.dumps(msgs, sort_keys=True, default=str)
    raise KeyError(
        f"corpus: row sid={r.get('sid')!r} has neither 'final_text' nor 'messages', so it "
        "cannot be identified as a generation. Count it at unit='row' or unit='activation', "
        "or load a file that carries the response."
    )


def _gen_id(r: dict) -> str:
    return hashlib.sha1(
        (r.get("sid", "") + "\x00" + _generation_content(r)).encode()
    ).hexdigest()[:16]


def _solution_key(r: dict) -> str:
    """Extracted code, normalised for whitespace. Falls back to the generation id when
    there is no code, so code-free rows are never silently merged together."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from screen_behavioral import visible_part, find_code
        code = find_code(visible_part(r.get("final_text") or "")) or ""
    except Exception:
        code = ""
    if not code.strip():
        return "nocode:" + r.get("generation_id", _gen_id(r))
    return "code:" + hashlib.sha1(" ".join(code.split()).encode()).hexdigest()[:16]


def read_raw(paths) -> list[dict]:
    """Every line from one path, a glob, or an iterable of either. No collapsing."""
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    rows, files_read = [], 0
    for p in paths:
        for f in sorted(glob.glob(str(p))) or [str(p)]:
            if not os.path.isfile(f):
                continue
            files_read += 1
            for line in open(f):
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                r.setdefault("_source_file", f)
                r["generation_id"] = _gen_id(r)
                rows.append(r)
    if files_read == 0:
        # A mistyped or stale path used to return [] here, and every count downstream
        # then reported a confident zero. A zero that means "no such file" must never
        # be indistinguishable from a zero that means "no such samples".
        raise FileNotFoundError(f"corpus: no readable file matched {list(paths)!r}")
    return rows


def collapse(rows: list[dict], unit: str) -> list[dict]:
    """Collapse ALREADY-LOADED rows to an explicit unit.

    Split out of `load` so that producers which build rows in memory — reading .eval
    logs directly rather than a samples.jsonl — get the SAME definition of a unit
    instead of hand-rolling a dedupe. Hand-rolled `{r["sid"]: r for r in rows}` is the
    specific line that caused §F22: sid is a design-cell id, so distinct generations
    share one and collapsing on it silently deletes real samples.

    Rows need not carry `generation_id`; it is computed here when missing.
    """
    if unit not in UNITS:
        raise ValueError(f"unit must be one of {UNITS}, got {unit!r}. "
                         "Pick the one that matches what you are counting; there is no default.")
    for r in rows:
        r.setdefault("generation_id", _gen_id(r))
    if unit == "row":
        return rows
    if unit == "generation":
        out = OrderedDict()
        for r in rows:
            out.setdefault(r["generation_id"], r)
        return list(out.values())
    if unit == "activation":
        # last write wins, matching the filesystem: acts/{sid}.bin is overwritten
        out = OrderedDict()
        for r in rows:
            out[r["sid"]] = r
        return list(out.values())
    if unit == "solution":
        out = OrderedDict()
        for r in rows:
            out.setdefault((r.get("task_id"), _solution_key(r)), r)
        return list(out.values())
    if unit == "task":
        out = OrderedDict()
        for r in rows:
            out.setdefault(r.get("task_id"), r)
        return list(out.values())


def load(paths, unit: str) -> list[dict]:
    """Load at an explicit unit. `unit` is required on purpose — see the module docstring."""
    return collapse(read_raw(paths), unit)


def denominators(paths, category: str | None = None) -> dict:
    """Every unit's count at once, so a report can state which one it means.

    `category` restricts to one taxonomy class (e.g. "concealed_cheat") before counting,
    which is the usual thing you actually want.
    """
    rows = read_raw(paths)
    if category is not None:
        rows = [r for r in rows if r.get("category") == category]
    gens = {r["generation_id"] for r in rows}
    sids = {r["sid"] for r in rows}
    sols = {(r.get("task_id"), _solution_key(r)) for r in rows}
    tasks = {r.get("task_id") for r in rows}
    dup_sids = {s: n for s, n in Counter(r["sid"] for r in rows).items() if n > 1}
    true_copies = sum(1 for s, n in dup_sids.items()
                      if len({r["generation_id"] for r in rows if r["sid"] == s}) == 1)
    return {
        "category": category,
        "rows": len(rows),
        "generations": len(gens),
        "activation_slots": len(sids),
        "solutions": len(sols),
        "tasks": len(tasks),
        "colliding_sids": len(dup_sids),
        "colliding_sids_that_are_true_copies": true_copies,
        "colliding_sids_that_are_distinct_generations": len(dup_sids) - true_copies,
    }


def summary_line(paths, category: str | None = None) -> str:
    d = denominators(paths, category)
    return (f"{d['category'] or 'all'}: rows={d['rows']} generations={d['generations']} "
            f"solutions={d['solutions']} tasks={d['tasks']} "
            f"activation_slots={d['activation_slots']} "
            f"(colliding sids {d['colliding_sids']}: "
            f"{d['colliding_sids_that_are_true_copies']} true copies, "
            f"{d['colliding_sids_that_are_distinct_generations']} distinct)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--category", default=None)
    a = ap.parse_args()
    print(summary_line(a.paths, a.category))
