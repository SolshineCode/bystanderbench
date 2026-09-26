#!/bin/bash
# W41 (2026-09-20 03:50, GPU 0): fills the GPU 0 time left after W39's 06:00 guard blocks its third
# pair. Waits for W39's DONE line, then runs agent-arm batches o, p -> tree holdout4 (pre-decision
# only, no full extract, to fit the reservation); a batch starts only before 07:30. Same
# procedure and same fixed direction as §F202/§F203; reported whatever it shows.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
until grep -q "W39 DONE" logs/launcher-runlogs/w39.log 2>/dev/null; do sleep 60; done
echo "=== W41 start $(date) ==="
[ -d logs/bystander-agentarm-nex-holdout-o ] && { echo "holdout-o already exists (W39 ran it); nothing to do"; exit 0; }
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
gpusched extend 7d30f535 1h || echo "extend refused; time guards still apply"
export FAIL_ON_ERROR=0.34
before(){ [ $((10#$(date +%H%M))) -lt $1 ]; }
LOGDIRS=""
for LAB in bystander-agentarm-nex-holdout-o bystander-agentarm-nex-holdout-p; do
  before 730 || { echo "past 07:30, not starting $LAB"; break; }
  echo "=== $LAB $(date) ==="
  GPU=0 PORT=8094 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
done
[ -n "$LOGDIRS" ] && { echo "=== CHAIN holdout4 $(date) ==="
  GGUF="$GGUF" GPU=0 OUT="$BASE/bystander/acts_nex_agentarm_holdout4" LOGDIRS="$LOGDIRS" TAG=claude-bystander-agentarm \
    CAPPORT=8098 PDPORT=8099 FULL_EXTRACT=0 bash bystander/capture_chain.sh; echo "chain holdout4 rc=$? $(date)"; }
echo "=== W41 DONE $(date) ==="
