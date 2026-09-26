#!/bin/bash
# W20 (2026-09-15): an OpenAI ladder on BOTH arms, because the incident this project is
# about was an OpenAI agent population. Each model gets its own affordance floor first
# (these are new models, and report.py keys the floor by (model, mode), so there is nothing
# to inherit), then the human-wrongdoer control and the agent-wrongdoer treatment at n=6
# each, so every model contributes a within-model pair rather than a lone number.
#
# Cheapest models first. Spend guards are tighter than W15/W17 because that chain may still
# be running: this one refuses below MIN_BAL and stops at CAP, so the two together cannot
# drain the account.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
MIN_BAL=4.00
CAP=3.00
bal() { ./check_balance.sh 2>/dev/null | grep -oE "remaining=\\\$[0-9.]+" | tail -1 | tr -d 'remaining=$'; }
START=$(bal); echo "start balance=\$$START"
for M in openai/gpt-5.6-luna openai/gpt-5.4-mini openai/gpt-5-mini openai/gpt-5.6-sol; do
  B=$(bal); SPENT=$(python3 -c "print(f'{float('$START')-float('$B'):.3f}')")
  echo "=== $M  balance=\$$B  spent=\$$SPENT  ($(date)) ==="
  python3 -c "import sys; sys.exit(0 if float('$B') >= $MIN_BAL else 1)" || { echo "STOP: balance below \$$MIN_BAL"; exit 4; }
  python3 -c "import sys; sys.exit(0 if float('$SPENT') < $CAP else 1)" || { echo "STOP: cap \$$CAP reached"; exit 5; }
  slug=$(echo "$M" | tr '/:' '--')
  # floor first: without it both arms are refused and the episodes are wasted
  MODEL="openrouter/$M" EPOCHS=4 ARMS=blatant_wrongdoing TOOL_ARMS=tool_probe \
    LABEL="or-oa-floor-${slug}" MAX_CONNECTIONS=2 bash bystander/run_bench.sh > "logs/or-oa-floor-${slug}.runlog" 2>&1
  echo "  floor rc=$?"; grep -E "alerted" "logs/or-oa-floor-${slug}.runlog" | head -1
  for ARM in blatant_wrongdoing blatant_wrongdoing_agents; do
    MODEL="openrouter/$M" EPOCHS=6 ARMS=$ARM TOOL_ARMS=with_tool \
      LABEL="or-oa-${ARM}-${slug}" MAX_CONNECTIONS=2 bash bystander/run_bench.sh > "logs/or-oa-${ARM}-${slug}.runlog" 2>&1
    echo "  $ARM rc=$?"; grep -E "alerted|cover_task_passed" "logs/or-oa-${ARM}-${slug}.runlog" | head -2
    if grep -qiE "429|rate.?limit|insufficient" "logs/or-oa-${ARM}-${slug}.runlog"; then echo "RATE/BALANCE stop"; exit 4; fi
  done
  sleep 10
done
E=$(bal); echo "=== W20 DONE $(date) end=\$$E spent=\$$(python3 -c "print(f'{float('$START')-float('$E'):.3f}')") ==="
