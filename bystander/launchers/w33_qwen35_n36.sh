#!/bin/bash
# W33 (2026-09-19): qwen3.5-27b agent arm from n=12 to n=36, with capture, then the probe re-cut
# chained behind it so GPU 0 never idles. F192 left open whether the floor models move at
# adequate n: qwen3.5 is 0/16 control against 0/11 agent, and 11 episodes is the same size that
# made GPT-5.6 look like noise before n=36 turned it into p 0.0001.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=$BASE/gguf/qwen3.5-27b.gguf
OUT=$BASE/bystander/acts_qwen35_agentarm
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
export FAIL_ON_ERROR=0.34
LOGDIRS=""
for LAB in bystander-agentarm-qwen35-b bystander-agentarm-qwen35-c; do
  echo "=== $LAB $(date) ==="
  GPU=0 PORT=8094 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
done
python -m bystander.report logs/bystander-agentarm-qwen35 $LOGDIRS logs/bystander-floor-qwen-n12 2>&1 | tail -10
echo "=== W33 DONE $(date) ==="
