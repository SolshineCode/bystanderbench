#!/bin/bash
# W34 (2026-09-19): nemotron-3.5-lightning agent arm from n=24 to n=36, with capture. Lightning
# is the clean silent bystander (channel 20/20 when asked, job 84/84, 61 discovering control
# episodes, zero escalations). Its agent-arm upper bound is [0, 16.1%] at n=20; n=36 tightens it.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-nex-vol 1 || exit 3
export FAIL_ON_ERROR=0.34
LAB=bystander-agentarm-lightning-c
echo "=== $LAB $(date) ==="
GPU=1 PORT=8087 GGUF="$GGUF" EPOCHS=16 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
  bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
echo "rc=$?"
python -m bystander.report logs/bystander-agentarm-lightning logs/bystander-agentarm-lightning-b "logs/$LAB" logs/bystander-lightning-inc1-ext 2>&1 | tail -10
echo "=== W34 DONE $(date) ==="
