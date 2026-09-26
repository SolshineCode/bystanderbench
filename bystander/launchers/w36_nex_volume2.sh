#!/bin/bash
# W36 (2026-09-19): more nex agent-arm volume on GPU 1, tightening the headline interval further
# and feeding future probe fits. Independent batches, own labels.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm_rep3
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-nex-vol 1 || exit 3
export FAIL_ON_ERROR=0.34
LOGDIRS=""
for LAB in bystander-agentarm-nex-rep-g bystander-agentarm-nex-rep-h; do
  echo "=== $LAB $(date) ==="
  GPU=1 PORT=8095 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
done
python -m bystander.report logs/bystander-agentarm-nex-a logs/bystander-agentarm-nex-b logs/bystander-agentarm-nex-rep-c logs/bystander-agentarm-nex-rep-d logs/bystander-agentarm-nex-rep-e logs/bystander-agentarm-nex-rep-f $LOGDIRS logs/bystander-nex-incident2-floor 2>&1 | tail -10
echo "=== CAPTURE ==="
CUDA_VISIBLE_DEVICES=1 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8096 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w36_cap_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8096/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8096/health | grep -q ok || { echo "capture server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8096 --eos "<|im_end|>" --out-dir "$OUT" \
  $(for d in $LOGDIRS; do echo -n "--logdir $d "; done) > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
echo "=== W36 DONE $(date) ==="
