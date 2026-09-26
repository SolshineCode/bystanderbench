#!/bin/bash
# W4c (2026-09-15 04:50): qwen3.5-27b tools/native (thinking-off) incident-1 with_tool +8 (cell n 16 -> 24).
# Reproduces the 09-09 serving line of logs/bystander-blatant-qwen35-27b (run_pilot_local.sh defaults:
# --reasoning off, --jinja, ctx 32768, q8 KV, flash-attn) + -M responses_api=false (transport only, F154).
# Gate: smoke key must be "mode=tools/native" without +think. New -ext logdir; original never touched.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=$BASE/gguf/qwen3.5-27b.gguf; MID=qwen3.5-27b.gguf
OUT=$BASE/bystander/acts_qwen_blatant_ext; PORT=8089; LOG=logs/bystander-blatant-qwen35-27b-ext
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-qwen35-ext 1 || exit 3
CUDA_VISIBLE_DEVICES=1 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port $PORT -ngl 999 -c 32768 -np 1 --no-webui --jinja --reasoning off \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > llamacpp_logs/qwen35_ext_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:$PORT/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:$PORT/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
grep -o "n_ctx_slot *= *[0-9]*" llamacpp_logs/qwen35_ext_server.log | tail -1
export OPENAI_BASE_URL=http://127.0.0.1:$PORT/v1 OPENAI_API_KEY=sk-local
C="-T affordance=native -T solver_kind=tools -T model_id=$MID --model openai/local-model --max-connections 1 --max-tool-output 16000 -M responses_api=false -M client_timeout=2400 --timeout 4800"
echo "=== SMOKE with_tool epochs=1 $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing -T tool_arm=with_tool -T epochs=1 $C --log-dir ${LOG}-smoke > logs/qwen35_ext_smoke.runlog 2>&1; echo "SMOKE rc=$?"
KEY=$(python bystander/report.py ${LOG}-smoke --cache bystander/.envcache 2>/dev/null | grep -oE "mode=tools/native(\+think)?" | head -1); echo "smoke key: $KEY"
[ "$KEY" = "mode=tools/native" ] || { echo "GATE: smoke keyed '$KEY', not the thinking-off condition; aborting"; kill $SPID; gpusched release f580cb51; exit 2; }
echo "=== inc1 with_tool +8 $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing -T tool_arm=with_tool -T epochs=8 $C --log-dir $LOG > logs/qwen35_ext.runlog 2>&1; echo "inc1 rc=$?"
docker ps --format '{{.Names}}' | grep -ci bystander || true
KEY2=$(python bystander/report.py $LOG --cache bystander/.envcache 2>/dev/null | grep -oE "mode=tools/native(\+think)?" | head -1); echo "ext key: $KEY2"
echo "=== CAPTURE $(date) ==="
python bystander/capture_activations.py --port $PORT --eos "<|im_end|>" --out-dir "$OUT" --logdir $LOG > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines; $(wc -l < "$OUT/manifest.tsv" 2>/dev/null) manifest rows"
kill $SPID 2>/dev/null; sleep 8
[ -s "$OUT/manifest.tsv" ] || { echo "NO MANIFEST"; gpusched release f580cb51; exit 1; }
mkdir -p "$OUT/acts"; echo "4,8,16,24,32,40,48,56" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,32,40,48,56 CUDA_VISIBLE_DEVICES=1 "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1; echo "extract rc=$?"
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py --expect 4,8,16,24,32,40,48,56 "$OUT"; echo "check_layers rc=$?"
echo "=== REPORT (pooled) ==="
python bystander/report.py logs/bystander-blatant-qwen35-27b logs/bystander-floor-qwen-n12 $LOG --cache bystander/.envcache | grep -A4 "blatant_wrongdoing / with_tool$" | head -6
gpusched release f580cb51; echo "=== W4c DONE $(date) ==="
