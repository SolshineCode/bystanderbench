#!/bin/bash
# W16 (2026-09-15): agent-perpetrator arm, n=12, on nemotron-3.5-lightning thinking-ON,
# GPU 1, with capture. Lightning is the clean silent bystander: on the human-wrongdoer
# control it drives the channel 20/20 when asked, finishes the job 84/84, finds the
# evidence in 61 episodes and escalates 0 times. If it breaks silence when the wrongdoer
# is an agent, that is the single most informative cell in the project.
# Defaults reproduce the thinking-on control's serving config (run_pilot_local.sh's
# `--reasoning off` controls tag parsing only; REASONING_BUDGET is left unset, as in W4).
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
OUT=$BASE/bystander/acts_lightning_agentarm
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-agentarm-lightning 1 || exit 3
export FAIL_ON_ERROR=0.34
LAB=bystander-agentarm-lightning
echo "=== $LAB $(date) ==="
GPU=1 PORT=8087 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
  bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
echo "rc=$?"
python -m bystander.report "logs/$LAB" logs/bystander-lightning-inc1-ext 2>&1 | tail -15
echo "=== CAPTURE $(date) ==="
CUDA_VISIBLE_DEVICES=1 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8088 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/lightning_agentarm_cap_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8088/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8088/health | grep -q ok || { echo "capture server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8088 --out-dir "$OUT" --logdir "logs/$LAB" > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
echo "=== W16 DONE $(date) ==="
