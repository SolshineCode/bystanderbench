#!/bin/bash
# W15 (2026-09-15): the agent-perpetrator arm on the four PAID frontier models, n=6 each,
# matching each model's human-wrongdoer control cell exactly (same arm slot, same n, same
# mode, same OpenRouter routing so report.py keys them identically and the pair is within
# model).
#
# PAID. Caleb's per-launch go-ahead given 2026-09-15 ~11:20 PDT ("I will reload openrouter
# now so you can run all those paid ones you mentioned too", then "Openrouter reloaded now").
# Balance at launch: $20.532.
#
# Guards, because run_bench.sh does NOT carry run_eval_openrouter.py's: balance is read
# before every cell and the chain refuses below MIN_BAL; cumulative spend is computed from
# the live balance and the chain stops at CAP; MAX_CONNECTIONS is 4, half the enforced cap
# of 8, because a local GPU eval and the free-tier chain are running concurrently on this
# 8-core box.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
MIN_BAL=3.00
CAP=12.00
bal() { ./check_balance.sh 2>/dev/null | grep -oE "remaining=\\\$[0-9.]+" | tail -1 | tr -d 'remaining=$'; }
START=$(bal); echo "start balance=\$$START"
for M in anthropic/claude-opus-5 anthropic/claude-sonnet-5 openai/gpt-5.6-luna-pro google/gemini-3.1-pro-preview; do
  B=$(bal)
  SPENT=$(python3 -c "print(f'{float('$START')-float('$B'):.3f}')")
  echo "=== $M  balance=\$$B  spent_so_far=\$$SPENT  ($(date)) ==="
  python3 -c "import sys; sys.exit(0 if float('$B') >= $MIN_BAL else 1)" || { echo "STOP: balance \$$B below \$$MIN_BAL"; exit 4; }
  python3 -c "import sys; sys.exit(0 if float('$SPENT') < $CAP else 1)" || { echo "STOP: spend cap \$$CAP reached"; exit 5; }
  slug=$(echo "$M" | tr '/:' '--')
  LAB="or-agentarm-paid-${slug}"
  MODEL="openrouter/$M" EPOCHS=6 ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    LABEL="$LAB" MAX_CONNECTIONS=4 \
    bash bystander/run_bench.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"
  grep -E "alerted|cover_task_passed|discovered_content" "logs/${LAB}.runlog" | head -4
  sleep 10
done
E=$(bal); echo "=== W15 DONE $(date)  end balance=\$$E  total spent=\$$(python3 -c "print(f'{float('$START')-float('$E'):.3f}')") ==="
