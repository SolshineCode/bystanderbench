#!/bin/bash
# serve_olmo3.sh — launch Olmo-3-7B-Instruct Q4_K_M (4.5 GiB) on ONE M40 with an
# auto back-off ladder. Olmo-3 loads via llama.cpp's extended olmo2 arch
# (per-layer SWA window 4096, pattern every-4th-full, + YaRN rope) — verify the
# startup log shows n_swa = 4096, or the GGUF/build combo is wrong.
# --chat-template chatml: Olmo-3-Instruct's bundled template is ChatML plus a
# tool-calling branch using the 'tojson' minja filter, which this build's
# template engine cannot parse. NOTE 2026-09-07: this comment previously cited
# "verified abort, olmo3/cpu_load_test.log" as its evidence. That file was checked before
# deletion and contained NO abort -- zero hits for error/abort/assert/minja across all
# 985M lines, only a clean load and a successful generation. The forced-chatml workaround
# below may still be correct, but it is currently UNSOURCED; if the abort is real, cite
# the log that actually shows it. See olmo3/cpu_load_test_SALVAGED.md. We
# never use tools, so the built-in chatml template is formatting-identical
# for our prompts. Single-GPU variant of llama70b/serve_llama70b.sh: this
# model fits the proven qwen3.5-27b single-GPU pattern (weights ~15.4 GiB +
# 16k q8_0 KV + buffers < 22.9 GiB usable), GPU0 (uncapped) by default.
#
# NOTE: gemma-3 alternates sliding-window/global attention layers, so the KV
# footprint at a given ctx is smaller than a same-size llama; 16384 should fit
# at full offload with room to spare.
#
# Usage: serve_olmo3.sh [port] [gpu]     (default 8095, GPU 0)
set -uo pipefail

PORT="${1:-8095}"
GPU="${2:-0}"
GGUF=/home/darkstar/gguf-downloads/olmo-3-7b-instruct/Olmo-3-7B-Instruct-Q4_K_M.gguf
BIN=/home/darkstar/llama.cpp/build/bin/llama-server
BASE=/home/darkstar/bluedot-unit2-impossiblebench
LOGDIR="$BASE/llamacpp_logs"
PIDFILE="$BASE/olmo3/server.pid"
mkdir -p "$LOGDIR"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "server already running (pid $(cat "$PIDFILE"))" >&2
    exit 0
fi

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" olmo3 "$GPU" || exit 3

if ss -tln | grep -q ":$PORT "; then
    echo "REFUSING: port $PORT already in use (pick another)." >&2
    exit 4
fi

CONFIGS=(
    "999 16384"
    "999 12288"
    "auto 16384"
    "auto 8192"
)

HEALTH_TIMEOUT=900   # 15 min is plenty for a 15.4 GiB load
attempt=0
for cfg in "${CONFIGS[@]}"; do
    attempt=$((attempt+1))
    read -r NGL CTX <<< "$cfg"
    LOG="$LOGDIR/olmo3_attempt${attempt}_ngl${NGL}_c${CTX}.log"
    NGL_ARGS=()
    [[ "$NGL" != "auto" ]] && NGL_ARGS=(-ngl "$NGL")
    echo "[$(date +%T)] attempt $attempt: gpu=$GPU ngl=$NGL ctx=$CTX -> $LOG"

    CUDA_VISIBLE_DEVICES="$GPU" nohup "$BIN" \
        --model "$GGUF" \
        --host 127.0.0.1 --port "$PORT" \
        "${NGL_ARGS[@]}" \
        -c "$CTX" -np 1 --no-webui \
        --chat-template chatml \
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

echo "ALL CONFIGS FAILED — see $LOGDIR/olmo3_attempt*.log" >&2
exit 1
