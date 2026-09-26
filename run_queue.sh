#!/usr/bin/env bash
# Sequential queue of CPU-viable local models through ImpossibleBench (LiveCodeBench).
# Each model runs to completion (all 3 splits) before the next starts.
set -uo pipefail
cd /home/darkstar/bluedot-unit2-impossiblebench/repo
source /home/darkstar/bluedot-unit2-impossiblebench/.venv/bin/activate
export OLLAMA_BASE_URL=http://localhost:11434/v1

QUEUE_LOG=/home/darkstar/bluedot-unit2-impossiblebench/queue_status.log
RESULTS_LOG=/home/darkstar/bluedot-unit2-impossiblebench/results_summary.log

MODELS=("qwen:0.5b" "nemotron-3-nano:4b" "llama3-local:latest" "lfm2.5-cpu:latest")
LIMIT=12
MAX_CONN=4
MAX_ATTEMPTS=6

for MODEL in "${MODELS[@]}"; do
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') START $MODEL (limit=$LIMIT conn=$MAX_CONN attempts=$MAX_ATTEMPTS) ===" | tee -a "$QUEUE_LOG"
  python3 /home/darkstar/bluedot-unit2-impossiblebench/run_eval.py \
    --model "$MODEL" --limit "$LIMIT" --max-connections "$MAX_CONN" --max-attempts "$MAX_ATTEMPTS" \
    >> /home/darkstar/bluedot-unit2-impossiblebench/run_${MODEL//[:\/]/_}.log 2>&1
  RC=$?
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') DONE $MODEL exit=$RC ===" | tee -a "$QUEUE_LOG"
  grep -A1 "^accuracy" "/home/darkstar/bluedot-unit2-impossiblebench/run_${MODEL//[:\/]/_}.log" | tee -a "$RESULTS_LOG" || true
done

echo "=== $(date '+%Y-%m-%d %H:%M:%S') QUEUE COMPLETE ===" | tee -a "$QUEUE_LOG"
