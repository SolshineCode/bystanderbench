#!/bin/bash
# require_reservation.sh — GPU reservation guard that checks the thing that matters.
#
# Usage:  bash tools/require_reservation.sh <tag> <gpu-index>
#         bash tools/require_reservation.sh gemma12b 0
# Exit 0 if an ACTIVE gpusched reservation matches <tag> AND covers <gpu-index>.
# Exit 1 otherwise, loudly, naming what it did find.
#
# ## Why this exists (2026-09-07)
#
# Every capture/serve/pipeline script in this repo guarded itself with the same
# pattern:
#
#     if ! ~/bin/gpusched status | grep -qi "gemma12b"; then  REFUSE; fi
#
# That greps the whole status output for a substring. It never checks WHICH GPU
# the matching reservation is for. On 2026-09-06 that let a real job through
# wrongly: reservation 81eb22b3 was held on **GPU 1** for session
# `claude-gemma12b-ext`, while `run_full_pipeline.sh` launched with `GPU=0`. The
# grep matched, the guard passed, and the job ran ~7.5h on GPU 0 — overlapping
# reservation 8274ede6 (`claude-olmo3-saes`, GPU 0, active until 15:54) that it
# had no claim on. A proper GPU-0 reservation (e7c47fc6) was only taken at 20:55,
# well after the run started.
#
# Same failure shape as the 2026-09-06 OpenRouter incident: a guard that LOOKS
# like it enforces the rule while not actually checking the condition that makes
# the rule true. The fix is to verify the specific claim (this GPU, right now),
# not a substring that happens to appear nearby.
set -uo pipefail

TAG="${1:?usage: require_reservation.sh <tag> <gpu-index>}"
GPU="${2:?usage: require_reservation.sh <tag> <gpu-index>}"

STATUS_JSON="$(~/bin/gpusched status --json 2>/dev/null)" || {
    echo "REFUSING: could not read 'gpusched status --json'. Do not run GPU work blind." >&2
    exit 1
}

GPUSCHED_STATUS_JSON="$STATUS_JSON" python3 - "$TAG" "$GPU" <<'PY'
import json, os, sys
tag, gpu = sys.argv[1].lower(), str(sys.argv[2])
try:
    data = json.loads(os.environ["GPUSCHED_STATUS_JSON"])
except Exception as e:
    print(f"REFUSING: gpusched status --json was unparseable ({e}).", file=sys.stderr)
    sys.exit(1)

active = data.get("active") or []

def gpus_of(r):
    """Set of GPU indices a reservation covers."""
    g = str(r.get("gpu", "")).lower()
    return {"0", "1"} if g == "both" else {g}

# A job may need one GPU ("0"/"1") or the pair ("both"). "both" is satisfied
# either by one gpu=both reservation or by two single-GPU ones held together --
# so require the UNION of this tag's active reservations to cover every GPU the
# job will touch, rather than looking for a single matching row.
need = {"0", "1"} if gpu == "both" else {gpu}

def tagged(r):
    hay = f"{r.get('session','')} {r.get('purpose','')}".lower()
    return tag in hay

mine = [r for r in active if tagged(r)]
have = set().union(*(gpus_of(r) for r in mine)) if mine else set()
if need <= have:
    for r in mine:
        if gpus_of(r) & need:
            print(f"[reservation OK] id={r.get('id')} gpu={r.get('gpu')} "
                  f"session={r.get('session')} ends={r.get('end')}")
    sys.exit(0)

print(f"REFUSING: no ACTIVE gpusched reservation matching '{tag}' covering GPU(s) "
      f"{','.join(sorted(need))}.", file=sys.stderr)
if mine:
    print(f"  this tag holds GPU(s) {','.join(sorted(have)) or 'none'}; "
          f"missing {','.join(sorted(need - have))}.", file=sys.stderr)
    for r in mine:
        print(f"  !! '{tag}' reservation id={r.get('id')} is on GPU {r.get('gpu')} "
              f"-- this job needs {','.join(sorted(need))}. This is exactly the "
              f"2026-09-06 failure: reserve the GPU you will actually use.",
              file=sys.stderr)
other = [r for r in active if not tagged(r)]
if other:
    for r in other:
        print(f"  (someone else holds: id={r.get('id')} gpu={r.get('gpu')} "
              f"session={r.get('session')})", file=sys.stderr)
if not active:
    print("  (no active reservations at all -- reserve before starting.)", file=sys.stderr)
sys.exit(1)
PY
