#!/bin/bash
# W42 (2026-09-20 03:50, GPU 1): GPU 1 turned out to run nex at GPU 0's speed, so W40 ends ~04:30
# with five hours of reservation left. Waits for W40's DONE line, then runs agent-arm batches
# q, r -> tree holdout5, then s (and t if before 07:30) -> holdout6, pre-decision cut only.
# Same procedure and fixed direction as §F202/§F203; reported whatever it shows.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
until grep -q "W40 DONE" logs/launcher-runlogs/w40.log 2>/dev/null; do sleep 60; done
echo "=== W42 start $(date) ==="
tools/require_reservation.sh claude-bystander-ctrl 1 || exit 3
gpusched extend a76c7c0a 1h || echo "extend refused; time guards still apply"
export FAIL_ON_ERROR=0.34
before(){ [ $((10#$(date +%H%M))) -lt $1 ]; }
run_set(){ # $1 tree suffix, labels...
  local SUF=$1; shift; local LOGDIRS=""
  for LAB in "$@"; do
    before 730 || { echo "past 07:30, not starting $LAB"; break; }
    echo "=== $LAB $(date) ==="
    GPU=1 PORT=8095 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
      bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
    echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
  done
  [ -n "$LOGDIRS" ] || return 0
  echo "=== CHAIN $SUF $(date) ==="
  GGUF="$GGUF" GPU=1 OUT="$BASE/bystander/acts_nex_agentarm_$SUF" LOGDIRS="$LOGDIRS" TAG=claude-bystander-ctrl \
    CAPPORT=8096 PDPORT=8097 FULL_EXTRACT=0 bash bystander/capture_chain.sh
  echo "chain $SUF rc=$? $(date)"
}
run_set holdout5 bystander-agentarm-nex-holdout-q bystander-agentarm-nex-holdout-r
before 730 && run_set holdout6 bystander-agentarm-nex-holdout-s bystander-agentarm-nex-holdout-t
echo "=== W42 DONE $(date) ==="
