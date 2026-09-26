#!/bin/bash
# W27 (2026-09-16): qwen3.5-27b on the agent arm, a third local pair. Its human-wrongdoer
# control is tools/native n=25 with 0/16 conditional, and it is the project's pilot model with
# zero alerts across 286 control episodes, so it is the strongest test of whether the species
# effect reaches a model that has never reported anything.
# Chained behind W26 rather than run concurrently: one llama-server per GPU, and W26 holds GPU 0.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=$BASE/gguf/qwen3.5-27b.gguf
cd "$BASE"; source .venv/bin/activate
until grep -q "W26 DONE" /home/darkstar/.claude/jobs/8bfa76b1/tmp/w26_probe_n50.log 2>/dev/null; do sleep 60; done
echo "=== W26 finished, starting W27 $(date) ==="
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
export FAIL_ON_ERROR=0.34
LAB=bystander-agentarm-qwen35
GPU=0 PORT=8094 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
  bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
echo "rc=$?"
python -m bystander.report "logs/$LAB" logs/bystander-floor-qwen-n12 2>&1 | tail -12
echo "=== W27 DONE $(date) ==="
