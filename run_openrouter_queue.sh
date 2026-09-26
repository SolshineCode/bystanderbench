#!/bin/bash
# run_openrouter_queue.sh — serialized OpenRouter batch queue, one model at a
# time. The earlier 5-way-parallel attempt (each at max-connections=20) hit a
# real CPU wall on this 8-core box: 82 concurrent Docker sandbox containers,
# load average 27, causing SandboxTimeoutError to cascade and corrupt samples
# (wasted paid API spend on timeout-failed attempts, not genuine model
# behavior). Fix: run one model fully before starting the next, each at a
# concurrency level (6) that leaves real CPU headroom on 8 cores.
set -uo pipefail
cd /home/darkstar/bluedot-unit2-impossiblebench
source .venv/bin/activate

run_one () {
    local model="$1" label="$2" limit="$3" splits="$4"
    echo "=== [$(date +%T)] starting $label ($model, limit=$limit) ==="
    python3 run_eval_openrouter.py --model "$model" --label "$label" \
        --splits "$splits" --limit "$limit" --max-connections 6 --max-attempts 3 \
        2>&1 | tee "run_${label}.log"
    echo "=== [$(date +%T)] finished $label ==="
}

run_one "qwen/qwen3.5-27b"             "qwen35-27b-paidbatch-20260906"     100 "oneoff,conflicting"
run_one "nvidia/nemotron-3.5-lightning" "lightning-paidbatch-20260906"      150 "oneoff,conflicting"
run_one "google/gemma-3-12b-it"        "gemma12b-paidbatch-20260906"       100 "oneoff,conflicting"
run_one "google/gemma-3-27b-it"        "gemma27b-paidbatch-20260906"       100 "oneoff,conflicting"
run_one "cohere/north-mini-code:free"  "northmini-bigbatch-20260906"       150 "oneoff,conflicting"

echo "=== OPENROUTER QUEUE COMPLETE ($(date)) ==="
