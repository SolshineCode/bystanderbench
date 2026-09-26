#!/bin/bash
# kaggle_queue.sh — feed kernels through Kaggle's 2-concurrent-session limit.
# Watches the ACTIVE set; when a slot frees, collects the finished kernel and
# pushes the next queued one. Emits AUDIT_NEEDED markers for the monitor.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
K=~/.kaggle/cli-venv/bin/kaggle

ACTIVE=("moe-floor-qwen15-moe-a27b-20260903" "moe-floor-olmoe-1b7b-ext-20260903")
QUEUE=("moe-floor-qwen15-14b-20260903" "moe-floor-olmo-0724-7b-ext-20260903"
       "moe-floor-olmo2-7b-ext-20260903" "moe-floor-qwen15-4b-20260903")

while true; do
    NEXT_ACTIVE=()
    for s in "${ACTIVE[@]}"; do
        st=$($K kernels status "calebdeleeuw/$s" 2>&1 || true)
        case "$st" in
            *RUNNING*|*QUEUED*|*queued*) NEXT_ACTIVE+=("$s");;
            *)
                echo "TERMINAL $s: $st"
                "$BASE/moe-floor/collect_results.sh" "$s" > "$BASE/moe-floor/results/${s}.collect.log" 2>&1 \
                    && echo "COLLECTED $s -- AUDIT_NEEDED" || echo "COLLECT_FAILED $s"
                ;;
        esac
    done
    ACTIVE=("${NEXT_ACTIVE[@]:-}")
    # drop empty placeholder
    [ "${#ACTIVE[@]}" -eq 1 ] && [ -z "${ACTIVE[0]}" ] && ACTIVE=()
    while [ "${#ACTIVE[@]}" -lt 2 ] && [ "${#QUEUE[@]}" -gt 0 ]; do
        s="${QUEUE[0]}"; QUEUE=("${QUEUE[@]:1}")
        out=$($K kernels push -p "$BASE/moe-floor/kernels/$s" --accelerator NvidiaTeslaT4 2>&1 | tail -1)
        echo "PUSH $s: $out"
        case "$out" in
            *successfully*) ACTIVE+=("$s");;
            *Maximum*) QUEUE=("$s" "${QUEUE[@]}"); break;;   # slot race; retry next tick
            *) echo "PUSH_FAILED $s (likely quota) -- leaving in queue"; QUEUE=("$s" "${QUEUE[@]}"); sleep 1800;;
        esac
    done
    if [ "${#ACTIVE[@]}" -eq 0 ] && [ "${#QUEUE[@]}" -eq 0 ]; then
        echo "KAGGLE_QUEUE_DONE"; break
    fi
    sleep 300
done