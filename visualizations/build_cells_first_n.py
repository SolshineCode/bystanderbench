#!/usr/bin/env python3
"""Build docs/cells_first_n.csv: the leaderboard cell table with every model scored on only its
FIRST N episodes in each of the two main conditions.

WHAT IS CAPPED
  Only the two main conditions: arm `blatant_wrongdoing` (a person did it) and
  `blatant_wrongdoing_agents` (a pool of agents did it), both with tool_arm `with_tool`.
  Every other row (floor `tool_probe`, other incidents, `no_tool`, `with_tool_named`) is left
  exactly as the full table has it. The affordance floor is therefore the model's whole floor,
  not a capped one; the competence gate (cover_task_passed >= 75%) is evaluated on the capped
  episodes, because it is a property of the main-arm episodes that are being scored.

EPISODE ORDER (the whole selection rule; no other judgement is involved)
  Within one cell (model, mode, arm, tool_arm), episodes are ordered by
    1. the run start time of the log they came from (`eval.created` in the .eval header),
       oldest first, then the log's file path as a tie-break;
    2. inside one log, by epoch and then sample id.
  The first N episodes in that order are kept. Errored samples and non-`success` logs never
  count, exactly as in the full table (they are dropped by `report.countable_log` /
  `report.countable_samples`). An episode that hit the message limit is still one of the N;
  it is excluded from the rate denominator exactly as in the full table.

NO DEFINITION IS RE-IMPLEMENTED HERE
  This script imports the lab reporter `bystander/report.py` and runs ITS `main()` unchanged.
  The only thing replaced is `collect()`, which is wrapped: it calls the original `collect()`
  (evidence-found, alerted, limit exclusions, model/mode keys) and then drops the episodes
  beyond N from the two main conditions before the reporter aggregates. Refusal gates,
  floor, Wilson intervals and the CSV schema therefore cannot drift from the full table.
  With --n 0 (no cap) the output is the full table. Validation 2026-11-11: --n 0 reproduces
  docs/cells.csv in all 127 rows and every column (0 differences).

USAGE
  .venv/bin/python visualizations/build_cells_first_n.py --lab ~/bluedot-unit2-impossiblebench \
      --n 12 --out docs/cells_first_n.csv
  The lab repo is only READ. The environment cache is copied to --cache (default: a temp dir).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
MAIN_ARMS = ("blatant_wrongdoing", "blatant_wrongdoing_agents")
MAIN_TOOL_ARM = "with_tool"
# Same logdir rule as bystander/make_cells_csv.sh (content-defined, partial and steered dirs out).
EXCLUDE_DIR = ("-partial", "bystander-cvec", "bystander-cvecsmoke", "bystander-f211",
               "bystander-f211smoke", "bystander-f215")


def logdirs(lab: Path):
    dirs = set()
    for p in (lab / "logs").rglob("*bystander*.eval"):
        dirs.add(str(p.parent))
    keep = []
    for d in sorted(dirs):
        rel = os.path.relpath(d, lab)
        if "-partial" in rel:
            continue
        base = os.path.basename(d)
        if any(base.startswith(x) for x in EXCLUDE_DIR[1:]) or base in EXCLUDE_DIR[1:]:
            continue
        keep.append(d)
    return keep


def parse_created(s: str) -> datetime:
    return datetime.fromisoformat(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lab", default=os.path.expanduser("~/bluedot-unit2-impossiblebench"))
    ap.add_argument("--n", type=int, default=21, help="episodes kept per main condition; 0 = no cap")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=None, help="env cache dir (copied from the lab cache if empty)")
    ap.add_argument("--before", default="2026-10-13T00:00:00",
                    help="ignore logs whose run start (eval.created) is at or after this ISO time. Default "
                         "2026-10-13 reproduces docs/cells.csv (the 2026-10-12 table) exactly; the lab "
                         "repo has since gained 2026-10-24+ logs (free-tier fill) that are NOT in it. "
                         "Pass --before 2999-01-01 for everything currently on disk.")
    ap.add_argument("--skip-dir", action="append", default=[],
                    help="regex on the log directory name; matching dirs are not read (repeatable)")
    ap.add_argument("--order-out", default=None, help="write the per-episode order used to this CSV")
    a = ap.parse_args()

    lab = Path(a.lab).resolve()
    sys.path.insert(0, str(lab))
    os.chdir(lab)  # reporter paths are relative to the lab root; nothing is written there
    import bystander.report as R  # noqa: E402

    cache = Path(a.cache or tempfile.mkdtemp(prefix="bb_envcache_"))
    if not cache.exists() or not any(cache.iterdir()):
        cache.mkdir(parents=True, exist_ok=True)
        shutil.copytree(lab / "bystander/.envcache", cache, dirs_exist_ok=True)

    before = parse_created(a.before) if a.before else None
    seen_logs = []            # (path, created, [sample (epoch,id)]) in the order collect() reads them
    orig_countable = R.countable_log

    def countable(path):
        log = orig_countable(path)
        if log is None:
            return None
        created = parse_created(log.eval.created)
        if before is not None and created.replace(tzinfo=None) >= before.replace(tzinfo=None):
            return None
        samples = R.countable_samples(log)
        seen_logs.append((path, created, [(s.epoch, str(s.id)) for s in samples]))
        return log

    R.countable_log = countable
    orig_collect = R.collect

    def collect(dirs, cache_dir):
        rows = orig_collect(dirs, cache_dir)
        # rows were appended log by log, one per countable sample, in log.samples order
        assert sum(len(x[2]) for x in seen_logs) == len(rows), "row/log bookkeeping mismatch"
        i = 0
        for path, created, sids in seen_logs:
            for j, sid in enumerate(sids):
                rows[i]["_ord"] = (created, path, sid[0], sid[1])
                rows[i]["_log"] = os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path)
                i += 1
        if a.n <= 0:
            return rows
        groups = defaultdict(list)
        for r in rows:
            groups[(r["model"], r["mode"], r["arm"], r["tool_arm"])].append(r)
        keep, order_rows = [], []
        for key, rs in groups.items():
            rs.sort(key=lambda r: r["_ord"])
            capped = key[2] in MAIN_ARMS and key[3] == MAIN_TOOL_ARM
            for rank, r in enumerate(rs, 1):
                if capped:
                    order_rows.append((*key, rank, r["_ord"][0].isoformat(), r["_log"], r["_ord"][2],
                                       r["_ord"][3], rank <= a.n, r["alerted"], r["discovered"],
                                       r["limit_hit"], r["cover"]))
                if not capped or rank <= a.n:
                    keep.append(r)
        if a.order_out:
            with open(a.order_out, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["model", "mode", "arm", "tool_arm", "rank", "log_created", "log", "epoch",
                            "sample_id", "counted", "alerted", "discovered", "limit_hit", "cover"])
                w.writerows(sorted(order_rows, key=lambda t: t[:5]))
        # restore the reporter's original row order for the kept rows (aggregation is order-free)
        ids = {id(r) for r in keep}
        return [r for r in rows if id(r) in ids]

    R.collect = collect
    tmp_csv = str(Path(a.out).with_suffix(".tmp.csv"))
    import re
    dirs = [d for d in logdirs(lab) if not any(re.search(x, os.path.basename(d)) for x in a.skip_dir)]
    print(f"log dirs read: {len(dirs)}", file=sys.stderr)
    sys.argv = ["report.py", *dirs, "--cache", str(cache), "--csv", tmp_csv]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        R.main()
    Path(a.out).with_suffix(".report.txt").write_text(buf.getvalue())

    rows = list(csv.DictReader(open(tmp_csv)))
    os.remove(tmp_csv)
    fields = list(rows[0].keys()) + ["first_n"]
    for r in rows:
        capped = r["arm"] in MAIN_ARMS and r["tool_arm"] == MAIN_TOOL_ARM
        r["first_n"] = str(a.n) if (capped and a.n > 0) else ""
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    try:
        sha = subprocess.run(["sha256sum", str(lab / "bystander/report.py")], capture_output=True,
                             text=True).stdout.split()[0]
    except Exception:
        sha = "?"
    print(f"wrote {a.out}: {len(rows)} cells, n={a.n}, lab report.py sha256 {sha[:12]}")


if __name__ == "__main__":
    main()
