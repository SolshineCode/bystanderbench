#!/bin/bash
# W23 (2026-09-15): the replication F181 said was owed. A second INDEPENDENT 24-episode batch of
# the agent-perpetrator cell on nex-n2.5-mini, run on GPU 1 with its own label so it pools by
# report.py's key but can also be scored alone. F166 measured an observed sd of 0.14 for a
# 12-episode batch of a ~25% cell, so one batch at 58.3% is exactly the shape that can wander.
# If batch two lands near 24.5%, the headline result is a batch effect and must be withdrawn.
# Capture runs too, so the probe gets more episodes either way.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm_rep2
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-nex-vol 1 || exit 3
export FAIL_ON_ERROR=0.34
LOGDIRS=""
for LAB in bystander-agentarm-nex-rep-e bystander-agentarm-nex-rep-f; do
  echo "=== $LAB $(date) ==="
  GPU=1 PORT=8095 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"
  LOGDIRS="$LOGDIRS logs/$LAB"
  sleep 15
done
echo "=== BATCH-LEVEL READ $(date) ==="
python -m bystander.report $LOGDIRS logs/bystander-nex-incident2-floor 2>&1 | tail -10
echo "=== POOLED WITH BATCH ONE $(date) ==="
python -m bystander.report logs/bystander-agentarm-nex-a logs/bystander-agentarm-nex-b \
  logs/bystander-agentarm-smoke $LOGDIRS logs/bystander-nex-incident2-floor 2>&1 | tail -10
echo "=== CAPTURE $(date) ==="
CUDA_VISIBLE_DEVICES=1 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8096 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/agentarm_rep_cap_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8096/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8096/health | grep -q ok || { echo "capture server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8096 --eos "<|im_end|>" --out-dir "$OUT" \
  $(for d in $LOGDIRS; do echo -n "--logdir $d "; done) > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=1 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"
echo "=== W23 DONE $(date) ==="
