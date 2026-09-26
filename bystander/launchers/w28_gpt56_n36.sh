#!/bin/bash
# W28 (2026-09-17 overnight): take gpt-5.6-luna and gpt-5.6-luna-pro to n=36 on BOTH arms.
# These are the only hosted models that move at all: luna 0/6 -> 3/6 (p 0.18), luna-pro
# 0/18 -> 3/18 (p 0.23). At n=6 and n=18 a real 0% vs 17% gap is invisible; at n=36 per arm it
# is detectable. A null here is as useful as a hit: it says nex is genuinely the exception.
# Floors already exist for both models, so no floor episodes are spent.
# 2026-09-17: the grant has $13.83 left but the OpenRouter ACCOUNT only holds $5.273 of loaded
# credit, which is a different thing. Guards are set against the loaded credit, not the grant
# line: floor $1.00, cap $4.00. Deploying the rest of the grant needs a top-up from Caleb.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
MIN_BAL=1.00
CAP=4.00
bal() { ./check_balance.sh 2>/dev/null | grep -oE "remaining=\\\$[0-9.]+" | tail -1 | tr -d 'remaining=$'; }
START=$(bal); echo "start balance=\$$START  cap=\$$CAP  floor=\$$MIN_BAL"
# cheapest first, and the arm that already moved first within each model
for SPEC in "openai/gpt-5.6-luna blatant_wrongdoing_agents 30" \
            "openai/gpt-5.6-luna blatant_wrongdoing 30" \
            "openai/gpt-5.6-luna-pro blatant_wrongdoing_agents 18" \
            "openai/gpt-5.6-luna-pro blatant_wrongdoing 18"; do
  set -- $SPEC; M=$1; ARM=$2; EP=$3
  B=$(bal); SPENT=$(python3 -c "print(f'{float('$START')-float('$B'):.3f}')")
  echo "=== $M $ARM ep=$EP  balance=\$$B spent=\$$SPENT  ($(date)) ==="
  python3 -c "import sys; sys.exit(0 if float('$B') >= $MIN_BAL else 1)" || { echo "STOP: balance below \$$MIN_BAL"; exit 4; }
  python3 -c "import sys; sys.exit(0 if float('$SPENT') < $CAP else 1)" || { echo "STOP: cap \$$CAP reached"; exit 5; }
  slug=$(echo "$M" | tr '/:' '--')
  LAB="or-n36-${ARM}-${slug}"
  MODEL="openrouter/$M" EPOCHS="$EP" ARMS="$ARM" TOOL_ARMS=with_tool \
    LABEL="$LAB" MAX_CONNECTIONS=4 bash bystander/run_bench.sh > "logs/${LAB}.runlog" 2>&1
  echo "  rc=$?"; grep -E "alerted|cover_task_passed" "logs/${LAB}.runlog" | head -2
  if grep -qiE "429|rate.?limit|insufficient" "logs/${LAB}.runlog"; then echo "RATE/BALANCE stop"; exit 4; fi
  sleep 15
done
E=$(bal); echo "=== W28 DONE $(date) end=\$$E spent=\$$(python3 -c "print(f'{float('$START')-float('$E'):.3f}')") ==="
