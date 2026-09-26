#!/bin/bash
# W32 (2026-09-18): the OpenAI family on both arms. The incident this project exists to study
# was an OpenAI agent population, and two OpenAI models now show the species effect
# (gpt-5.6-luna p 0.0001, luna-pro p 0.0113). Whether that is a family property or two models is
# the most useful paid question left, and it is the last planned spend of the grant.
# Each model needs its own floor first: report.py keys the affordance floor by (model, mode) and
# these four have never been run.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
MIN_BAL=2.00
CAP=10.00
bal() { ./check_balance.sh 2>/dev/null | grep -oE "remaining=\\\$[0-9.]+" | tail -1 | tr -d 'remaining=$'; }
START=$(bal); echo "start balance=\$$START cap=\$$CAP floor=\$$MIN_BAL"
for M in openai/gpt-5.4 openai/gpt-5.2 openai/gpt-5.5 openai/gpt-5; do
  B=$(bal); SPENT=$(python3 -c "print(f'{float('$START')-float('$B'):.3f}')")
  echo "=== $M  balance=\$$B spent=\$$SPENT ($(date)) ==="
  python3 -c "import sys; sys.exit(0 if float('$B') >= $MIN_BAL else 1)" || { echo "STOP: below \$$MIN_BAL"; exit 4; }
  python3 -c "import sys; sys.exit(0 if float('$SPENT') < $CAP else 1)" || { echo "STOP: cap \$$CAP"; exit 5; }
  slug=$(echo "$M" | tr '/:' '--')
  MODEL="openrouter/$M" EPOCHS=4 ARMS=blatant_wrongdoing TOOL_ARMS=tool_probe \
    LABEL="or-fam-floor-${slug}" MAX_CONNECTIONS=3 bash bystander/run_bench.sh > "logs/or-fam-floor-${slug}.runlog" 2>&1
  echo "  floor rc=$?"; grep -E "alerted" "logs/or-fam-floor-${slug}.runlog" | head -1
  for ARM in blatant_wrongdoing_agents blatant_wrongdoing; do
    MODEL="openrouter/$M" EPOCHS=18 ARMS=$ARM TOOL_ARMS=with_tool \
      LABEL="or-fam-${ARM}-${slug}" MAX_CONNECTIONS=3 bash bystander/run_bench.sh > "logs/or-fam-${ARM}-${slug}.runlog" 2>&1
    echo "  $ARM rc=$?"; grep -E "alerted|cover_task_passed" "logs/or-fam-${ARM}-${slug}.runlog" | head -2
    if grep -qiE "429|rate.?limit|insufficient" "logs/or-fam-${ARM}-${slug}.runlog"; then echo "RATE/BALANCE stop"; exit 4; fi
  done
  sleep 15
done
E=$(bal); echo "=== W32 DONE $(date) end=\$$E spent=\$$(python3 -c "print(f'{float('$START')-float('$E'):.3f}')") ==="
