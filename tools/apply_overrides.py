#!/usr/bin/env python3
"""Apply (or check) hand-audit label overrides against the samples.jsonl they belong to.

## Why this exists (2026-09-07)

`label_overrides.json` is this project's mechanism for recording that a hand audit
changed a machine-assigned label. `prepare_dataset.py` reads it and applies it **at
generation time**. That means an override written *after* a run — which is the normal
case, since the audit happens after the data exists — never reaches `samples.jsonl`
unless the whole pipeline is re-run against a live llama-server.

The consequence was found in a published dataset: `bluedot-unit2-moe-floor-rung1` ships
`olmo2-7b/samples.jsonl` with `"category": "disclosed"` for a row whose
`label_overrides.json`, in the same folder, says `failed_silent`. Anyone reading the rows
directly gets the label the hand audit rejected.

A repo-wide check found this is not a one-off: **every non-empty `label_overrides.json`
in the project was unapplied to its sibling `samples.jsonl`.** The override mechanism was
working exactly as designed and still left the data wrong, because "the audit is
recorded" and "the data reflects the audit" were never the same operation.

This tool makes them the same operation, and makes the gap checkable:

    python3 tools/apply_overrides.py --check       # exit 1 if any override is unapplied
    python3 tools/apply_overrides.py --apply       # apply them, preserving the original

`--apply` never destroys the machine label: the pre-override value is preserved in a
`category_raw` field, and `category_override_applied` records the date. Row counts are
untouched — deduplication is deliberately NOT this tool's job (see FINDINGS §F22: most
of the apparent duplicates in this project are real distinct generations that share a
sample id, and collapsing them destroys data).
"""
import argparse
import glob
import json
import os
import sys

STAMP = "2026-09-07"


def find_pairs(root="."):
    """Yield (override_path, samples_path, overrides_dict) for every override file
    that has a sibling samples.jsonl."""
    for ov in sorted(glob.glob(os.path.join(root, "**", "label_overrides.json"),
                                recursive=True)):
        if ".venv" in ov:
            continue
        try:
            with open(ov) as f:
                data = json.load(f)
        except Exception as e:
            print(f"  !! {ov}: unreadable ({e})")
            continue
        if not data:
            continue
        sj = os.path.join(os.path.dirname(ov), "samples.jsonl")
        if not os.path.exists(sj):
            print(f"  ?? {ov}: {len(data)} override(s) but no sibling samples.jsonl "
                  f"-- cannot apply here, check where this file is meant to act")
            continue
        yield ov, sj, data


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true",
                   help="report unapplied overrides and exit 1 if any exist")
    g.add_argument("--apply", action="store_true",
                   help="apply overrides in place, preserving the original label")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    total_unapplied = 0
    total_applied = 0
    for ov, sj, overrides in find_pairs(args.root):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "concealment-probe", "tools"))
        from corpus import load
        # Unit is 'row' because this script audits and rewrites what a file literally contains.
        rows = load(sj, unit="row")
        pending = [r for r in rows
                   if r.get("sid") in overrides
                   and r.get("category") != overrides[r["sid"]]]
        absent = [k for k in overrides
                  if not any(r.get("sid") == k for r in rows)]

        if not pending and not absent:
            print(f"  ok      {sj}  ({len(overrides)} override(s) already applied)")
            continue

        for k in absent:
            print(f"  !! {sj}: override for '{k}' but that sid is not in the file")

        if not pending:
            continue

        total_unapplied += len(pending)
        if args.check:
            print(f"  UNAPPLIED {sj}  ({len(pending)} row(s))")
            for r in pending:
                print(f"      {r['sid']}: file='{r['category']}' "
                      f"override='{overrides[r['sid']]}'")
            continue

        # --apply: rewrite, preserving the machine label rather than overwriting it
        for r in rows:
            sid = r.get("sid")
            if sid in overrides and r.get("category") != overrides[sid]:
                r.setdefault("category_raw", r["category"])
                r["category"] = overrides[sid]
                r["category_override_applied"] = STAMP
        tmp = sj + ".tmp"
        with open(tmp, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp, sj)
        total_applied += len(pending)
        print(f"  applied {sj}  ({len(pending)} row(s); original kept in category_raw)")

    print()
    if args.check:
        if total_unapplied:
            print(f"FAIL: {total_unapplied} override(s) recorded but NOT reflected in "
                  f"the data. Run --apply, or re-run prepare_dataset.py.")
            return 1
        print("PASS: every recorded override is reflected in its samples.jsonl.")
        return 0
    print(f"Applied {total_applied} override(s). Row counts unchanged; "
          f"pre-override labels preserved in 'category_raw'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
