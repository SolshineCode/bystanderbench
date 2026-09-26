#!/bin/bash
# W39 (2026-09-20 00:00, GPU 0): the SECOND independent probe holdout on the nex agent arm, which
# §F201 made load-bearing: same procedure as W37 (12+12 fresh episodes, capture, pre-decision cut,
# extract), same fixed direction, no refitting. Pre-registration is §F202. Pairs run
# eval -> capture_chain -> next pair; no new pair starts after 06:00 so the reservation (09:25)
# holds. holdout2 (k,l) is the pre-registered primary; holdout3/4 are extra replications,
# reported whatever they show.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
export FAIL_ON_ERROR=0.34
run_pair(){ # $1 tree suffix, $2 $3 labels
  local LOGDIRS=""
  for LAB in "$2" "$3"; do
    echo "=== $LAB $(date) ==="
    GPU=0 PORT=8094 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
      bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
    echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
  done
  echo "=== CHAIN $1 $(date) ==="
  GGUF="$GGUF" GPU=0 OUT="$BASE/bystander/acts_nex_agentarm_$1" LOGDIRS="$LOGDIRS" TAG=claude-bystander-agentarm \
    CAPPORT=8098 PDPORT=8099 FULL_EXTRACT=1 bash bystander/capture_chain.sh
  echo "chain $1 rc=$? $(date)"
}
before(){ [ $((10#$(date +%H%M))) -lt $1 ]; }
run_pair holdout2 bystander-agentarm-nex-holdout-k bystander-agentarm-nex-holdout-l
before 600 && run_pair holdout3 bystander-agentarm-nex-holdout-m bystander-agentarm-nex-holdout-n
before 600 && run_pair holdout4 bystander-agentarm-nex-holdout-o bystander-agentarm-nex-holdout-p
echo "=== W39 DONE $(date) ==="
