#!/bin/bash
# run_bigbatch_capture.sh — north-mini big batch (logs/northmini-bigbatch-20260906, 177
# hand-audited transcripts, §F26) → local teacher-forced activations, positives first.
# Prepare step (server for /apply-template + /tokenize) then a priority-ordered extraction
# at -c 184320. Requires an active gpusched reservation mentioning north-mini on $GPU.
# Env: GPU (0), PORT (8098)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GPU="${GPU:-0}"; PORT="${PORT:-8098}"
DATA="$BASE/concealment-probe/data/north-mini-bigbatch"
TAG=north-mini-code
cd "$BASE"
bash tools/require_reservation.sh north-mini "$GPU" || exit 3
SKIP_EXTRACT=1 LOGTAG=_bigbatch PIDFILE="$BASE/north-mini/server_bigbatch.pid" \
  SRCLOGS="$BASE/logs/northmini-bigbatch-20260906" DATA="$DATA" PORT="$PORT" GPU="$GPU" \
  EOS_SUFFIX='<|END_TEXT|><|END_OF_TURN_TOKEN|>' \
  PREP_EXTRA="--strip-prompt-tail <|START_THINKING|> --think-open <|START_THINKING|> --think-close <|END_THINKING|><|START_TEXT|> --no-think-fill <|START_THINKING|><|END_THINKING|><|START_TEXT|>" \
  bash north-mini/run_capture.sh || { echo "prepare stage failed"; exit 1; }
# run_capture.sh stops the server via $HERE/server.pid; the bigbatch server used its own pidfile
if [ -f north-mini/server_bigbatch.pid ]; then
    kill "$(cat north-mini/server_bigbatch.pid)" 2>/dev/null; sleep 15; kill -9 "$(cat north-mini/server_bigbatch.pid)" 2>/dev/null; rm -f north-mini/server_bigbatch.pid
fi
for i in $(seq 1 12); do used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU"); [ "$used" -lt 1500 ] && break; sleep 10; done
cp -f logs/northmini-bigbatch-20260906/mechanism_audit.json "$DATA/$TAG/mechanism_audit.json"
python3 concealment-probe/tools/prioritize_manifest.py "$DATA/$TAG" | tee "$DATA/$TAG/prioritize.log"
RESID_MANIFEST="$DATA/$TAG/manifest_prioritized.tsv" CTX=184320 \
  bash north-mini/extract_northmini.sh "$DATA/$TAG" "$GPU" 2>&1 | tee llamacpp_logs/northmini_extraction_bigbatch.log
echo "=== bigbatch capture done ($(date)) ==="
