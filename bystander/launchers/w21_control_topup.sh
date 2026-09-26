#!/bin/bash
# W21 (2026-09-15): top the HUMAN-WRONGDOER CONTROL cells up to n=18 for the frontier models
# whose treatment cells W17 already took to n=18. Without this the pair is 6 against 18 and
# any Fisher test is reading two different sample sizes. gpt-5.6-luna-pro first: it is the
# cheapest of the four and it is the only one whose treatment moved off its control value.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
MIN_BAL=3.00
bal() { ./check_balance.sh 2>/dev/null | grep -oE "remaining=\\\$[0-9.]+" | tail -1 | tr -d 'remaining=$'; }
for M in openai/gpt-5.6-luna-pro google/gemini-3.1-pro-preview anthropic/claude-sonnet-5; do
  B=$(bal); echo "=== control top-up $M  balance=\$$B  ($(date)) ==="
  python3 -c "import sys; sys.exit(0 if float('$B') >= $MIN_BAL else 1)" || { echo "STOP: balance below \$$MIN_BAL"; exit 4; }
  slug=$(echo "$M" | tr '/:' '--')
  MODEL="openrouter/$M" EPOCHS=12 ARMS=blatant_wrongdoing TOOL_ARMS=with_tool \
    LABEL="or-ctrl-ext-${slug}" MAX_CONNECTIONS=3 bash bystander/run_bench.sh > "logs/or-ctrl-ext-${slug}.runlog" 2>&1
  echo "  rc=$?"; grep -E "alerted|cover_task_passed" "logs/or-ctrl-ext-${slug}.runlog" | head -2
  sleep 10
done
echo "=== W21 DONE $(date) balance=\$$(bal) ==="
