#!/bin/bash
# W8 (2026-09-14 12:50): +24 nex-n2.5-mini with_tool episodes on incident 2 and incident 3
# (two batches of 12 each, labels -depth-g / -depth-h continuing -depth-e/-f), GPU 0, then
# capture + extract with the nex layer set (4,8,16,24,30,34,37,39) into acts_nex_inc23_gh.
# Never edit this file while it runs; write a new one per launch.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_inc23_gh
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-nex-inc23 0 || exit 3
export FAIL_ON_ERROR=0.34
LOGDIRS=""
for SPEC in "bystander-nex-incident2-depth-g blatant_safety_falsification" "bystander-nex-incident2-depth-h blatant_safety_falsification" \
            "bystander-nex-incident3-depth-g blatant_oversight_evasion" "bystander-nex-incident3-depth-h blatant_oversight_evasion"; do
  set -- $SPEC; LAB=$1; ARM=$2
  echo "=== $LAB ($ARM) $(date) ==="
  GPU=0 PORT=8089 GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=$ARM TOOL_ARMS=with_tool \
    bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1
  echo "$LAB rc=$?"
  LOGDIRS="$LOGDIRS --logdir logs/$LAB"
  docker ps --format '{{.Names}} {{.RunningFor}}' | grep -i bystander || true
  sleep 15
done
echo "=== CAPTURE $(date) ==="
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8088 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/nex_inc23_gh_cap_server_gpu0.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8088/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8088/health | grep -q ok || { echo "capture server never came up"; kill $SPID; exit 1; }
python bystander/capture_activations.py --port 8088 --eos "<|im_end|>" --out-dir "$OUT" $LOGDIRS > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
[ -s "$OUT/manifest.tsv" ] || { echo "NO MANIFEST"; exit 1; }
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"
echo "=== W8 DONE $(date) ==="
