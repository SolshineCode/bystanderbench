#!/bin/bash
# W40 (2026-09-20 00:00, GPU 1, half speed): fresh HUMAN-perpetrator (blatant_wrongdoing) nex
# episodes with capture + pre-decision cut, so the fixed agent-arm direction of §F200 can be
# tested on human-arm episodes it never saw (§F199's 0.709 transfer was measured on trees the
# direction's training pool shares captures with). Also more control-arm volume for §F199's
# 35/78 vs 24.5% contrast. Pre-registration §F202. GPU 1 runs at ~0.5x, so a 12-episode batch
# is ~90 min and a pair with chain ~4.5 h; guards keep it inside the 09:25 reservation.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-ctrl 1 || exit 3
export FAIL_ON_ERROR=0.34
run_batches(){ # $1 tree suffix, then labels...
  local SUF=$1; shift; local LOGDIRS=""
  for LAB in "$@"; do
    echo "=== $LAB $(date) ==="
    GPU=1 PORT=8095 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing TOOL_ARMS=with_tool \
      bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
    echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
  done
  echo "=== CHAIN $SUF $(date) ==="
  GGUF="$GGUF" GPU=1 OUT="$BASE/bystander/acts_nex_ctrl_$SUF" LOGDIRS="$LOGDIRS" TAG=claude-bystander-ctrl \
    CAPPORT=8096 PDPORT=8097 FULL_EXTRACT=0 bash bystander/capture_chain.sh
  echo "chain $SUF rc=$? $(date)"
}
before(){ [ $((10#$(date +%H%M))) -lt $1 ]; }
run_batches holdout bystander-nex-ctrl-holdout-a bystander-nex-ctrl-holdout-b
if before 445; then run_batches holdout2 bystander-nex-ctrl-holdout-c bystander-nex-ctrl-holdout-d
elif before 615; then run_batches holdout2 bystander-nex-ctrl-holdout-c; fi
echo "=== W40 DONE $(date) ==="
