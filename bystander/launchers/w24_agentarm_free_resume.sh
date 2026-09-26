#!/bin/bash
# W13 (2026-09-15): the new agent-perpetrator arm across every FREE OpenRouter model that
# already has a matched human-arm incident-1 cell AND a passing affordance floor.
#
# WHY THIS IS SAFE TO RUN ALONGSIDE THE LOCAL GPU WORK: this is tier-1 behavioural only,
# no serving and no capture, so it does not touch either GPU. It stays SEQUENTIAL with
# MAX_CONNECTIONS=1 (the 2026-09-06 incident was caused by concurrent batches, not by any
# single piece), so "at the same time" means concurrent with the local runs, never
# concurrent with itself.
#
# FLOORS ARE NOT RE-RUN. report.py keys the affordance floor by (model, mode), not by arm,
# so every floor listed below already covers this arm. Only `with_tool` episodes are spent.
#
# QUOTA. ~15 requests per episode against a ~1000/day free cap that resets 17:00 PDT. The
# order below is by how much the cell can move: the models that report on humans come
# first, because a drop there is the informative result. The chain aborts on the first
# rate-limit so a dead quota costs minutes, not a day, and the remainder is re-run after
# the next reset with the same command.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate

# GATE: refuse to spend quota unless the local smoke proved the arm scores end to end.
SMOKE=logs/bystander-agentarm-smoke
if [[ "${SKIP_GATE:-1}" != "1" ]]; then
  [[ -d "$SMOKE" ]] || { echo "GATE FAIL: no smoke logdir $SMOKE"; exit 3; }
  python -m bystander.report "$SMOKE" logs/bystander-nex-incident2-floor > /tmp/agentarm_gate.txt 2>&1 || true
  grep -q "blatant_wrongdoing_agents" /tmp/agentarm_gate.txt || {
    echo "GATE FAIL: smoke report has no blatant_wrongdoing_agents cell"; cat /tmp/agentarm_gate.txt; exit 3; }
  echo "GATE OK: smoke scored the new arm"
fi

# model                                       episodes (matched to its human-arm control n)
SPECS=(
  # nex-n2.5-pro skipped: its 12-episode eval hung for 4 hours on 2026-09-15 with an empty
  # eval file and one docker sandbox pinned, and was killed by PID. Re-run it alone later.
  "nex-agi/nex-n2.5-mini:free 12"
  "poolside/laguna-s-2.1:free 12"
  "dots-studio/dots-3-note-preview:free 12"
  "nvidia/nemotron-3-ultra-550b-a55b:free 12"
  "nvidia/nemotron-3.5-lightning:free 6"
  "inclusionai/ling-3.0-flash-vl:free 6"
  "inclusionai/ling-3.0-flash-fin:free 6"
  "inclusionai/ling-3.0-flash-sante:free 6"
  "nvidia/nemotron-3-super-120b-a12b:free 6"
)
for spec in "${SPECS[@]}"; do
  set -- $spec; M=$1; EP=$2
  case "$M" in *:free) ;; *) echo "REFUSING non-free model: $M"; exit 2 ;; esac
  slug=$(echo "$M" | tr '/:' '--')
  LAB="or-agentarm-${slug}"
  echo "=== $M  arm=blatant_wrongdoing_agents  with_tool  ep=$EP  ($(date)) ==="
  MODEL="openrouter/$M" EPOCHS="$EP" ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    LABEL="$LAB" MAX_CONNECTIONS=1 \
    bash bystander/run_bench.sh > "logs/${LAB}.runlog" 2>&1
  rc=$?
  grep -E "alerted|cover_task_passed|discovered_content" "logs/${LAB}.runlog" | head -4
  if grep -qiE "429|rate.?limit|quota|insufficient" "logs/${LAB}.runlog"; then
    echo "RATE LIMITED on $M -- stopping the chain at $(date). Re-run this script after 17:00 PDT."
    exit 4
  fi
  echo "$LAB rc=$rc"
  docker ps --format '{{.Names}}' | grep -ci bystander || true
  sleep 20
done
echo "=== W13 SWEEP DONE $(date) ==="
