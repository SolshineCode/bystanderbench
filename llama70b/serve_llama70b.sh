#!/bin/bash
# serve_llama70b.sh — launch Llama-3.3-70B-Instruct Q4_K_M (42.5GB) split across
# BOTH Tesla M40s with an automatic OOM back-off ladder.
#
# VRAM math (why this needs a ladder at all):
#   2 x 23040 MiB reported (ECC on) = 46080 MiB combined
#   weights ~40530 MiB + KV q8_0 @16384 ctx ~2790 MiB (80 layers x 2 x 8kv x 128d
#   x 1.0625 B/elem x 16384 tok) + CUDA ctx ~900 MiB + compute buffers ~1-1.5 GiB
#   = ~45.2-45.7 GiB vs 45.0 GiB usable -> full offload at 16k ctx is MARGINAL.
#
# Ladder (first config that loads + answers /health wins):
#   1. -ngl 999            -c 16384   (full offload, best case)
#   2. (auto-fit, no -ngl) -c 16384   (llama.cpp common_fit_params picks the split;
#                                      proven working on this rig for qwen3.6 36GB)
#   3. (auto-fit)          -c 12288
#   4. (auto-fit)          -c 8192    (last resort; ImpossibleBench transcripts with
#                                      max_attempts<=3 mostly stay under 8k, but the
#                                      qwen3.6 cheat sample hit ~10k total tokens, so
#                                      only use this if nothing else fits)
#
# Flags mirror the validated prior runs (see ps of qwen3.5/3.6 servers + NOTES.md):
#   --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0  (FA+q8_0 KV validated
#   on these exact M40s, ~/system-tuning-2026-07-10/NOTES.md), -np 1 (single slot:
#   -np 2 was measured throughput-NEGATIVE on this bandwidth-bound hardware).
#
# DO NOT run without an active gpusched reservation covering both GPUs.
#
# Usage: serve_llama70b.sh [port]      (default 8090)
# On success: prints "SERVER_READY port=... pid=... config=..." and exits 0,
# leaving the server running detached. PID recorded in llama70b/server.pid.
set -uo pipefail

PORT="${1:-8090}"
GGUF=/home/darkstar/gguf-downloads/llama-3.3-70b/Llama-3.3-70B-Instruct-Q4_K_M.gguf
BIN=/home/darkstar/llama.cpp/build/bin/llama-server
BASE=/home/darkstar/bluedot-unit2-impossiblebench
LOGDIR="$BASE/llamacpp_logs"
PIDFILE="$BASE/llama70b/server.pid"
mkdir -p "$LOGDIR"

# refuse to start if a previous instance is alive
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "server already running (pid $(cat "$PIDFILE"))" >&2
    exit 0
fi

# safety: require an active gpusched reservation mentioning llama70b
# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" llama70b both || exit 3

# Ladder entries: "<ngl-or-auto> <ctx>"
CONFIGS=(
    "999 16384"
    "auto 16384"
    "auto 12288"
    "auto 8192"
)

HEALTH_TIMEOUT=1800   # 30 min: 42.5GB cold read from disk can be slow
attempt=0
for cfg in "${CONFIGS[@]}"; do
    attempt=$((attempt+1))
    read -r NGL CTX <<< "$cfg"
    LOG="$LOGDIR/llama70b_attempt${attempt}_ngl${NGL}_c${CTX}.log"
    NGL_ARGS=()
    [[ "$NGL" != "auto" ]] && NGL_ARGS=(-ngl "$NGL")
    echo "[$(date +%T)] attempt $attempt: ngl=$NGL ctx=$CTX -> $LOG"

    CUDA_VISIBLE_DEVICES=0,1 nohup "$BIN" \
        --model "$GGUF" \
        --host 127.0.0.1 --port "$PORT" \
        "${NGL_ARGS[@]}" \
        --tensor-split 1,1 \
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
        READY="SERVER_READY port=$PORT pid=$PID config=ngl:$NGL,ctx:$CTX ${OFFL:+($OFFL)} ${NSLOT:+($NSLOT)}"
        echo "$READY" | tee "$(dirname "$0")/server_ready.log"
        echo "log: $LOG"
        exit 0
    fi

    # clean up failed attempt before next rung
    kill "$PID" 2>/dev/null; sleep 5; kill -9 "$PID" 2>/dev/null
    # verify VRAM actually freed before relaunching
    for ((w=0; w<12; w++)); do
        used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | paste -sd+ | bc)
        [[ "$used" -lt 2000 ]] && break
        sleep 10
    done
done

echo "ALL CONFIGS FAILED — model does not fit even at ctx=8192 with auto-fit." >&2
echo "Check the attempt logs in $LOGDIR/llama70b_attempt*.log" >&2
exit 1
