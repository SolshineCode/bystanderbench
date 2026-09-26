#!/bin/bash
# Serve gemma-3-12b-it with a GemmaScope-2 feature steering vector, and REFUSE to
# hand back a server that silently failed to load it.
#
# llama-server logs "failed to load control vector file" / "no valid control vector
# files passed" and then serves anyway. An unsteered server answering as the steered
# arm would manufacture a null, so this script greps the server log for those lines
# and tears the server down if it finds them. (Guard checks the thing it claims to.)
set -uo pipefail
PORT="$1"; GPU="$2"; CV="$3"; SCALE="$4"; TAG="$5"
BASE=/home/darkstar/bluedot-unit2-impossiblebench
export RESV_TAG="sae-causal-steer" LOGTAG="_$TAG" PIDFILE="$BASE/sae-causal/server_gpu${GPU}.pid"
export EXTRA_ARGS="--control-vector-scaled ${CV}:${SCALE} --control-vector-layer-range 20 21"
bash "$BASE/gemma12b/serve_gemma12b.sh" "$PORT" "$GPU" || exit $?
LOG=$(ls -t "$BASE"/llamacpp_logs/gemma12b_${TAG}_attempt*.log | head -1)
if grep -qiE "failed to load control vector|no valid control vector" "$LOG"; then
    echo "REFUSING: control vector did NOT load (see $LOG). Killing server." >&2
    kill "$(cat "$PIDFILE")" 2>/dev/null; rm -f "$PIDFILE"; exit 5
fi
echo "CONTROL VECTOR LOADED OK: $CV scale=$SCALE (log $LOG)"
