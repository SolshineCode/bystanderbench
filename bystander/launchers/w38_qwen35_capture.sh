#!/bin/bash
# W38 (2026-09-19, checkpoint 2): W33's header promised capture and never ran it, so the n=36
# qwen3.5 agent-arm cell has no activations. Capture the existing episodes retroactively.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=$BASE/gguf/qwen3.5-27b.gguf
OUT=$BASE/bystander/acts_qwen35_agentarm
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-nex-vol 1 || exit 3
CUDA_VISIBLE_DEVICES=1 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8093 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w38_cap_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8093/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8093/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8093 --out-dir "$OUT" \
  --logdir logs/bystander-agentarm-qwen35 --logdir logs/bystander-agentarm-qwen35-b --logdir logs/bystander-agentarm-qwen35-c \
  > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
mkdir -p "$OUT/acts"; echo "4,8,16,24,32,40,48" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,32,40,48 CUDA_VISIBLE_DEVICES=1 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,32,40,48; echo "check_layers rc=$?"
echo "=== W38 DONE $(date) ==="
