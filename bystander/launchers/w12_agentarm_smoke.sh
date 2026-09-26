#!/bin/bash
# W12 (2026-09-15 11:08): FIRST run of the new agent-perpetrator arm
# `blatant_wrongdoing_agents` (F178 follow-up). 2 episodes, nex-n2.5-mini, GPU 0.
# This is the smoke test for a NEW ARM SHAPE, so it is 2 episodes and read by hand
# before anything scales. Never edit this file while it runs.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
export FAIL_ON_ERROR=0.51
LAB=bystander-agentarm-smoke
echo "=== $LAB $(date) ==="
GPU=0 PORT=8091 GGUF="$GGUF" EPOCHS=2 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
  bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
echo "rc=$?"
python -m bystander.report --logdir "logs/$LAB" 2>&1 | tail -20
echo "=== W12 DONE $(date) ==="
