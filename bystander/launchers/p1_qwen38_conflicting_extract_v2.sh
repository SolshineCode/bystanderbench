#!/bin/bash
# Day 2026-09-14: (a) re-run qwen3.8:27b's Part 1 `conflicting` split (aborted 06:38, F165), same
# server flags as p1_qwen38.sh; (b) then residual extraction over the CPU-produced token tree
# (concealment-probe/data/qwen38/qwen38-27b/manifest.tsv, 75 episodes) at 12 layers
# linspace(1,64,12) for this 65-block qwen35 model. Server killed BY PID before extraction.
# v2 2026-09-14 19:12: relaunch after the session teardown killed the eval at 15/25 (16:44). Same eval_set log_dir, so inspect resumes the started log rather than regenerating the 15 finished samples.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
BLOB=/usr/share/ollama/.ollama/models/blobs/sha256-0c93661a3c1c70c7f6529bd6cd50240edd7d01af46afee33fd9594dc450d45a3
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-qwen38-conflicting 1 || exit 3
CUDA_VISIBLE_DEVICES=1 nohup "$HOME/llama.cpp/build/bin/llama-server" --model "$BLOB" --host 127.0.0.1 --port 8082 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on --reasoning off --reasoning-budget 0 -n 4096 > llamacpp_logs/p1_qwen38_conflicting_server.log 2>&1 < /dev/null &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8082/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8082/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
grep -m1 "n_ctx_slot" llamacpp_logs/p1_qwen38_conflicting_server.log
echo "=== conflicting start $(date) ==="
python run_eval_gpu.py --label part1-qwen38-conflicting --port 8082 --limit 25 --max-connections 1 --max-attempts 2 --splits conflicting --client-timeout 2400 > logs/part1-qwen38-conflicting.runlog 2>&1; echo "conflicting rc=$?"; tail -3 logs/part1-qwen38-conflicting.runlog | cut -c1-120
kill $SPID 2>/dev/null; sleep 8; kill -9 $SPID 2>/dev/null; sleep 4
echo "=== extract qwen38 residuals $(date) ==="
OUT=$BASE/concealment-probe/data/qwen38/qwen38-27b; mkdir -p "$OUT/acts"; echo "1,7,12,18,24,30,35,41,47,52,58,64" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=1,7,12,18,24,30,35,41,47,52,58,64 CUDA_VISIBLE_DEVICES=1 "$BASE/concealment-probe/tools/extract_resid" -m "$BLOB" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1; echo "extract rc=$?"
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
echo "=== QWEN38 CONFLICTING+EXTRACT DONE $(date) ==="
