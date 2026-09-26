#!/bin/bash
# W4b (2026-09-15 04:45): nemotron-3.5-lightning THINKING-OFF incident-1 with_tool +12 (cell n 12 -> 24).
# Reproduces the 09-09 serving line of logs/bystander-nemotron-blatant (run_pilot_local.sh defaults:
# --reasoning off, --jinja, ctx 32768, q8 KV, flash-attn) plus -M responses_api=false (F154, as W4).
# Gate: the smoke episode's report.py key must be "mode=tools/native" WITHOUT +think, else abort --
# a thinking-on log would pool with the n=72 thinking cell, not the one this run is topping up.
# New logdir (-ext) so report.py pools by key and the original is never touched. Never edit while running.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
MID=NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
OUT=$BASE/bystander/acts_lightning_nothink_ext; PORT=8087; LOG=logs/bystander-nemotron-blatant-ext
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-lightning-nothink-ext 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port $PORT -ngl 999 -c 32768 -np 1 --no-webui --jinja --reasoning off \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > llamacpp_logs/lightning_nothink_ext_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:$PORT/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:$PORT/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
grep -o "n_ctx_slot *= *[0-9]*" llamacpp_logs/lightning_nothink_ext_server.log | tail -1
export OPENAI_BASE_URL=http://127.0.0.1:$PORT/v1 OPENAI_API_KEY=sk-local
C="-T affordance=native -T solver_kind=tools -T model_id=$MID --model openai/local-model --max-connections 1 --max-tool-output 16000 -M responses_api=false -M client_timeout=2400 --timeout 4800"
echo "=== SMOKE with_tool epochs=1 $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing -T tool_arm=with_tool -T epochs=1 $C --log-dir ${LOG}-smoke > logs/lightning_nothink_smoke.runlog 2>&1; echo "SMOKE rc=$?"
KEY=$(python bystander/report.py ${LOG}-smoke --cache bystander/.envcache 2>/dev/null | grep -oE "mode=tools/native(\+think)?" | head -1); echo "smoke key: $KEY"
[ "$KEY" = "mode=tools/native" ] || { echo "GATE: smoke keyed '$KEY', not the thinking-off condition; aborting"; kill $SPID; exit 2; }
echo "=== inc1 with_tool +12 thinking-off $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing -T tool_arm=with_tool -T epochs=12 $C --log-dir $LOG > logs/lightning_nothink_ext.runlog 2>&1; echo "inc1 rc=$?"
docker ps --format '{{.Names}}' | grep -ci bystander || true
KEY2=$(python bystander/report.py $LOG --cache bystander/.envcache 2>/dev/null | grep -oE "mode=tools/native(\+think)?" | head -1); echo "ext key: $KEY2"
echo "=== CAPTURE $(date) ==="
python bystander/capture_activations.py --port $PORT --eos "<|im_end|>" --out-dir "$OUT" --logdir $LOG > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines; $(wc -l < "$OUT/manifest.tsv" 2>/dev/null) manifest rows"
kill $SPID 2>/dev/null; sleep 8
[ -s "$OUT/manifest.tsv" ] || { echo "NO MANIFEST"; exit 1; }
mkdir -p "$OUT/acts"; echo "8,24,40" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=8,24,40 CUDA_VISIBLE_DEVICES=0 "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1; echo "extract rc=$?"
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py --expect 8,24,40 "$OUT"; echo "check_layers rc=$?"
echo "=== REPORT (pooled with original) ==="
python bystander/report.py logs/bystander-nemotron-blatant logs/bystander-floor-nemotron $LOG --cache bystander/.envcache | grep -A4 "blatant_wrongdoing / with_tool$" | head -6
gpusched release c898bce4; echo "=== W4b DONE $(date) ==="
