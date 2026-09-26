#!/bin/bash
# W31 (2026-09-18): take every FREE-tier floor model to n=36 on the agent arm. F192 flagged that
# we do not know whether the zeros would move at adequate n; their cells are 6-12 episodes, which
# is the same size that made GPT-5.6 look like noise at p 0.18 before n=36 turned it into
# p 0.0001. Closing that for $0 is the best value left in the project.
# Ordered by how informative the cell is: the one non-zero first, then the largest existing
# denominators. Sequential, MAX_CONNECTIONS=1. Stops at the first 429 and is safe to re-run.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
SPECS=(
  "poolside/laguna-s-2.1:free 24"
  "dots-studio/dots-3-note-preview:free 24"
  "nvidia/nemotron-3-ultra-550b-a55b:free 24"
  "nvidia/nemotron-3.5-lightning:free 30"
  "inclusionai/ling-3.0-flash-vl:free 30"
  "inclusionai/ling-3.0-flash-fin:free 30"
  "inclusionai/ling-3.0-flash-sante:free 30"
  "nvidia/nemotron-3-super-120b-a12b:free 30"
)
for spec in "${SPECS[@]}"; do
  set -- $spec; M=$1; EP=$2
  case "$M" in *:free) ;; *) echo "REFUSING non-free model: $M"; exit 2 ;; esac
  slug=$(echo "$M" | tr '/:' '--'); LAB="or-n36-agents-${slug}"
  # 2026-09-19: resume, do not repeat. Without this a re-run after the daily 429 reset started
  # again from the top and re-spent the cap on cells that had already completed, so the
  # queued models were never reached. A model whose logdir exists is skipped; delete the
  # logdir by hand to deliberately re-run one.
  if [[ -d "logs/$LAB" ]]; then echo "skip $M: logs/$LAB already exists"; continue; fi
  echo "=== $M +$EP on the agent arm ($(date)) ==="
  MODEL="openrouter/$M" EPOCHS="$EP" ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    LABEL="$LAB" MAX_CONNECTIONS=1 bash bystander/run_bench.sh > "logs/${LAB}.runlog" 2>&1
  echo "  rc=$?"; grep -E "alerted|cover_task_passed" "logs/${LAB}.runlog" | head -2
  if grep -qiE "429|rate.?limit|quota" "logs/${LAB}.runlog"; then
    echo "RATE LIMITED at $M ($(date)). Re-run this script after the 17:00 PDT reset."; exit 4
  fi
  sleep 20
done
echo "=== W31 DONE $(date) ==="
