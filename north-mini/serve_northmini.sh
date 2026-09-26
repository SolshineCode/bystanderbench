#!/bin/bash
# serve_northmini.sh — launch north-mini-code (cohere2moe, 18GB Q4_K_M) on ONE M40,
# using the NEW llama.cpp build (~/llama.cpp-new) that adds cohere2moe support --
# NOT the main ~/llama.cpp build, which predates this architecture.
#
# Usage: serve_northmini.sh [port] [gpu]     (default 8097, GPU 0)
set -uo pipefail

PORT="${1:-8097}"
GPU="${2:-0}"
GGUF=/home/darkstar/gguf-downloads/north-mini-code/North-Mini-Code-1.0-UD-Q4_K_M.gguf
BIN=/home/darkstar/llama.cpp-new/build/bin/llama-server
BASE=/home/darkstar/bluedot-unit2-impossiblebench
LOGDIR="$BASE/llamacpp_logs"
PIDFILE="${PIDFILE:-$BASE/north-mini/server.pid}"
mkdir -p "$LOGDIR"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "server already running (pid $(cat "$PIDFILE"))" >&2
    exit 0
fi

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" north-mini "$GPU" || exit 3

if ss -tln | grep -q ":$PORT "; then
    echo "REFUSING: port $PORT already in use (pick another)." >&2
    exit 4
fi

CONFIGS=(
    "999 8192"
    "999 6144"
    "auto 8192"
    "auto 4096"
)

HEALTH_TIMEOUT=900
attempt=0
for cfg in "${CONFIGS[@]}"; do
    attempt=$((attempt+1))
    read -r NGL CTX <<< "$cfg"
    LOG="$LOGDIR/northmini${LOGTAG:-}_attempt${attempt}_ngl${NGL}_c${CTX}.log"
    NGL_ARGS=()
    [[ "$NGL" != "auto" ]] && NGL_ARGS=(-ngl "$NGL")
    echo "[$(date +%T)] attempt $attempt: gpu=$GPU ngl=$NGL ctx=$CTX -> $LOG"

    CUDA_VISIBLE_DEVICES="$GPU" nohup "$BIN" \
        --model "$GGUF" \
        --host 127.0.0.1 --port "$PORT" \
        "${NGL_ARGS[@]}" \
        -c "$CTX" -np 1 --no-webui \
        --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
        >"$LOG" 2>&1 &
    PID=$!

    ok=""
    for ((t=0; t<HEALTH_TIMEOUT; t+=10)); do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "  process died (see $LOG); tail:"; tail -5 "$LOG" | sed 's/^/    /'
            break
        fi
        if curl -sf -m 5 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q '"ok"'; then
            ok=1; break
        fi
        sleep 10
    done

    if [[ -n "$ok" ]]; then
        echo "$PID" > "$PIDFILE"
        OFFL=$(grep -oE "offloaded [0-9]+/[0-9]+ layers" "$LOG" | tail -1 || true)
        NSLOT=$(grep -oE "n_ctx_slot = [0-9]+" "$LOG" | tail -1 || true)
        READY="SERVER_READY port=$PORT pid=$PID gpu=$GPU config=ngl:$NGL,ctx:$CTX ${OFFL:+($OFFL)} ${NSLOT:+($NSLOT)}"
        echo "$READY" | tee "$(dirname "$0")/server_ready.log"
        echo "log: $LOG"
        exit 0
    fi

    kill "$PID" 2>/dev/null; sleep 5; kill -9 "$PID" 2>/dev/null
    for ((w=0; w<12; w++)); do
        used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")
        [[ "$used" -lt 1500 ]] && break
        sleep 10
    done
done

echo "ALL CONFIGS FAILED — see $LOGDIR/northmini_attempt*.log" >&2
exit 1
