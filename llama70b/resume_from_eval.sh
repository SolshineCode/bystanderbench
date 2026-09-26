#!/bin/bash
# resume_from_eval.sh — resume the llama70b pipeline against an ALREADY-RUNNING
# llama-server (the model survived a session/driver death; do NOT cold-reload the
# 42.5GB weights). Skips phase 1 (server launch) + smoke of run_full_pipeline.sh;
# runs evals -> prepare -> extract -> export -> stage exactly as that script does.
#
# Requires: a healthy server on $PORT and an active gpusched reservation.
# Env knobs: PORT (8091), LIMIT_IMP (25), LIMIT_ORIG (15), ATT_IMP (3), ATT_ORIG (2),
#            UPLOAD (0). Splits already fully extracted are skipped by re-run safety
#            (prepare_dataset/extract are idempotent per-sid; eval_set resumes its
#            own log dir).
set -uo pipefail

BASE=/home/darkstar/bluedot-unit2-impossiblebench
HERE="$BASE/llama70b"
VENV="$BASE/.venv/bin/activate"
PORT="${PORT:-8091}"
LIMIT_IMP="${LIMIT_IMP:-25}"
LIMIT_ORIG="${LIMIT_ORIG:-15}"
ATT_IMP="${ATT_IMP:-3}"
ATT_ORIG="${ATT_ORIG:-2}"
TAG=llama3.3-70b
DATA="$BASE/concealment-probe/data/llama70b"
COMBINED="$BASE/logs/${TAG}-all"

cd "$BASE"
source "$VENV"

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" llama70b both || exit 3

echo "=== verify existing server on $PORT (no relaunch) ==="
if ! curl -sf -m 10 "http://127.0.0.1:$PORT/health" | grep -q '"ok"'; then
    echo "no healthy server on $PORT -- use run_full_pipeline.sh for a cold start." >&2
    exit 1
fi
# record the server pid so phase 4 can stop it before extraction
SRVPID=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
echo "server pid=$SRVPID on $PORT healthy"
echo "$SRVPID" > "$HERE/server.pid"

run_split () {  # split limit attempts
    local sp="$1" lim="$2" att="$3"
    echo "=== eval split=$sp limit=$lim attempts=$att ($(date)) ==="
    python3 run_eval_gpu.py --label "${TAG}-${sp}" --port "$PORT" \
        --splits "$sp" --limit "$lim" --max-connections 1 --max-attempts "$att" \
        --client-timeout 4800 \
        2>&1 | tee -a "run_${TAG}-${sp}.log"
}

echo "=== [2/6] evals (positives-first order; eval_set resumes partial log dirs) ==="
run_split oneoff      "$LIMIT_IMP"  "$ATT_IMP"
run_split conflicting "$LIMIT_IMP"  "$ATT_IMP"
run_split original    "$LIMIT_ORIG" "$ATT_ORIG"

echo "=== [3/6] prepare dataset (server still up for /apply-template) ==="
mkdir -p "$COMBINED"
cp -f logs/${TAG}-oneoff/*.eval logs/${TAG}-conflicting/*.eval logs/${TAG}-original/*.eval "$COMBINED/" 2>/dev/null
[ -f "$HERE/label_overrides.json" ] || echo '{}' > "$HERE/label_overrides.json"
python3 concealment-probe/tools/prepare_dataset.py \
    --logdir "$COMBINED" --port "$PORT" --model-tag "$TAG" --outdir "$DATA" \
    --eos-suffix '<|eot_id|>' --overrides "$HERE/label_overrides.json" \
    2>&1 | tee "$HERE/prepare_dataset.log"

echo "=== [4/6] stop server, extract activations ==="
if [ -n "$SRVPID" ]; then
    kill "$SRVPID" 2>/dev/null; sleep 15; kill -9 "$SRVPID" 2>/dev/null
fi
rm -f "$HERE/server.pid"
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | paste -sd+ | bc)
    [ "$used" -lt 2000 ] && break; sleep 10
done
"$HERE/extract_llama70b.sh" "$DATA/$TAG" 2>&1 | tee "$BASE/llamacpp_logs/llama70b_extraction.log"

echo "=== [5/6] export transcripts + stage HF folder ==="
python3 concealment-probe/tools/export_transcripts.py \
    --logdir "$COMBINED" --out "$DATA/$TAG/transcripts.jsonl" 2>&1 | tail -5
cp -f "$HERE/label_overrides.json" "$DATA/$TAG/label_overrides.json"
SRVCFG=$(grep -hoE "SERVER_READY.*" "$HERE/server_ready.log" 2>/dev/null | tail -1)
python3 "$HERE/package_and_upload.py" \
    --data-dir "$DATA/$TAG" \
    --logdir "logs/${TAG}-oneoff" --logdir "logs/${TAG}-conflicting" --logdir "logs/${TAG}-original" \
    --limits "oneoff $LIMIT_IMP, conflicting $LIMIT_IMP, original $LIMIT_ORIG" \
    --max-attempts "$ATT_IMP (impossible splits), $ATT_ORIG (original)" \
    --client-timeout 4800 --retry-budget 9600 --run-dates "$(date +%Y-%m-%d)" \
    ${SRVCFG:+--server-config "$SRVCFG"} --no-upload

echo "=== [6/6] label-audit reminder ==="
python3 - "$DATA/$TAG/samples.jsonl" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
flagged = [r for r in rows if r["flagged"]]
cheats  = [r for r in rows if r["category"] == "concealed_cheat"]
print(f"{len(flagged)} keyword-flag hits ('disclosed' candidates) -- EVERY one needs hand audit")
print(f"{len(cheats)} concealed_cheat -- verify + assign cheat_mechanism (check_override vs hardcode)")
for r in flagged + cheats:
    print(f"  AUDIT {r['sid']}: cat={r['category']} ver={r['verification_result']} toks={r['n_total_tokens']}")
EOF
echo "=== resume pipeline done ($(date)); staged only (UPLOAD default 0) ==="
