#!/bin/bash
# run_trial.sh — full splice-continuation trial, detached driver.
# Waits for any running extract_resid to finish, then:
#   serve 70B -> run continuations (both arms) -> stop server ->
#   L49/53/57 activation pass on the continuation token streams.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
HERE="$BASE/splice"
cd "$BASE"
source .venv/bin/activate

# STRUCTURAL FIX (2026-09-05): establish our OWN reservation instead of assuming
# one exists from an earlier, unrelated job (that assumption already caused one
# failed launch when the prior job's watcher correctly released its reservation).
# Reuse an existing 70B-scoped reservation if one is live; otherwise reserve, and
# release on exit only what we ourselves reserved.
OWN_RES=""
# Reuse-or-reserve (guard corrected 2026-09-07). This script's design is to reuse
# a live 70B-scoped window if there is one and otherwise take its own; that is
# kept. What changed is the reuse TEST: it used to be
# `gpusched status | grep -qiE "llama70b|..."`, which matches a reservation on
# ANY gpu, so a single-GPU window would have been read as covering this job's
# CUDA_VISIBLE_DEVICES=0,1. require_reservation.sh checks both GPUs are actually
# covered. If the reuse test fails we reserve, then re-check rather than assuming
# the reserve worked.
GUARD="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh"
if ! bash "$GUARD" llama70b both; then
    OUT=$(~/bin/gpusched reserve --gpu both --duration 4h --session claude-llama70b-splice \
          --harness claude-code --purpose "70B splice-continuation trial (auto-reserved by run_trial.sh)" 2>&1) || {
        echo "REFUSING: could not reserve GPUs: $OUT" >&2; exit 3; }
    OWN_RES=$(echo "$OUT" | grep -oE "release [a-f0-9]+" | head -1 | awk '{print $2}')
    echo "reserved own window: $OWN_RES"
    bash "$GUARD" llama70b both || {
        echo "REFUSING: reserved but the guard still says both GPUs are not covered." >&2
        exit 3; }
fi
cleanup() { [ -n "$OWN_RES" ] && ~/bin/gpusched release "$OWN_RES" 2>/dev/null && echo "released $OWN_RES"; }
trap cleanup EXIT

echo "=== waiting for any running extraction to finish ==="
while pgrep -f extract_resid >/dev/null; do sleep 20; done
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | paste -sd+ | bc)
    [ "$used" -lt 2000 ] && break; sleep 10
done

echo "=== launching 70B server ($(date)) ==="
"$BASE/llama70b/serve_llama70b.sh" 8091 || exit 1

echo "=== continuations ==="
python3 "$HERE/run_continuation.py" --port 8091 --n 6 2>&1 | tee "$HERE/run_continuation.log"

echo "=== stop server, extract continuation activations ==="
[ -f "$BASE/llama70b/server.pid" ] && kill "$(cat "$BASE/llama70b/server.pid")" 2>/dev/null
sleep 15; [ -f "$BASE/llama70b/server.pid" ] && kill -9 "$(cat "$BASE/llama70b/server.pid")" 2>/dev/null
rm -f "$BASE/llama70b/server.pid"
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | paste -sd+ | bc)
    [ "$used" -lt 2000 ] && break; sleep 10
done
export RESID_MANIFEST="$HERE/manifest_nla.tsv"
export RESID_LAYERS="49,53,57"
CUDA_VISIBLE_DEVICES=0,1 "$BASE/concealment-probe/tools/extract_resid" \
  -m /home/darkstar/gguf-downloads/llama-3.3-70b/Llama-3.3-70B-Instruct-Q4_K_M.gguf \
  -c 16384 -b 1024 --tensor-split 1,1 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  2>&1 | tee "$BASE/llamacpp_logs/splice_extraction.log"
echo "=== SPLICE TRIAL DONE ($(date)) ==="