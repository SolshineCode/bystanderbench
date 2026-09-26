#!/bin/bash
# W37 (2026-09-19, checkpoint 2): more nex agent-arm volume, GPU 0. §F198's owed falsification
# test needs a FRESH batch never touched by the probe fit that produced AUC 0.868. This batch
# is captured and pre-decision cut but the probe is refit on it SEPARATELY, blind, not pooled
# into training data, once it lands.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm_holdout
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
export FAIL_ON_ERROR=0.34
LOGDIRS=""
for LAB in bystander-agentarm-nex-holdout-i bystander-agentarm-nex-holdout-j; do
  echo "=== $LAB $(date) ==="
  GPU=0 PORT=8094 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"; LOGDIRS="$LOGDIRS logs/$LAB"; sleep 15
done
echo "=== CAPTURE ==="
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8098 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w37_cap_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8098/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8098/health | grep -q ok || { echo "capture server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8098 --eos "<|im_end|>" --out-dir "$OUT" \
  $(for d in $LOGDIRS; do echo -n "--logdir $d "; done) > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
echo "=== PRE-DECISION CUT (holdout, quantile match) ==="
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8099 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w37_predecision_server.log 2>&1 &
SPID2=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8099/health 2>/dev/null | grep -q ok && break; sleep 10; done
PDOUT="$OUT.predecision"
python bystander/decision_index.py --port 8099 --dirs "$OUT" --capture-schema f151 --match quantile --out "$PDOUT" > "$PDOUT.index.log" 2>&1
RC=$?
grep -E "REFUSING TO WRITE|GATE PASS|AUC of position" "$PDOUT.index.log" | tail -4
kill $SPID2 2>/dev/null; sleep 8
[ $RC -ne 0 ] && { echo "holdout re-cut failed rc=$RC"; exit 1; }
mkdir -p "$PDOUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$PDOUT/requested_layers.txt"
RESID_MANIFEST="$PDOUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$PDOUT/extract.log" 2>&1
echo "bins: $(ls "$PDOUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$PDOUT/manifest.tsv")"
echo "=== W37 DONE $(date) ==="
