#!/bin/bash
# W4 (2026-09-14): nemotron-3.5-lightning +12 with_tool episodes on EACH of the three
# incidents, then capture + extract, so every lightning cell goes n=12 -> n=24.
# New logdirs (-ext) so report.py pools them with the originals by (model, mode, arm, tool_arm)
# and the originals are never touched. Floors already exist (6/6 each) and are not re-run.
# -M responses_api=false is required for this model (F154). Never edit this file while it runs;
# write a new one per launch.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
MID=NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
OUT=$BASE/bystander/acts_lightning_ext
PORT=8085
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-lightning-ext 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port $PORT -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/lightning_ext_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:$PORT/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:$PORT/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
grep -o "n_ctx_slot *= *[0-9]*" llamacpp_logs/lightning_ext_server.log | tail -1   # F121: must be 32768
export OPENAI_BASE_URL=http://127.0.0.1:$PORT/v1 OPENAI_API_KEY=sk-local
C="-T affordance=native -T solver_kind=tools -T model_id=$MID --model openai/local-model
   --max-connections 1 --max-tool-output 16000 -M responses_api=false"

for ARM in blatant_wrongdoing blatant_safety_falsification blatant_oversight_evasion; do
  case "$ARM" in
    blatant_wrongdoing)           TAG=inc1 ;;
    blatant_safety_falsification) TAG=inc2 ;;
    blatant_oversight_evasion)    TAG=inc3 ;;
  esac
  echo "=== $TAG +12 with_tool $(date) ==="
  inspect eval bystander/task.py -T arm=$ARM -T tool_arm=with_tool -T epochs=12 $C \
    --log-dir logs/bystander-lightning-$TAG-ext > "logs/lightning_${TAG}_ext.runlog" 2>&1
  echo "$TAG rc=$?"
  docker ps --format '{{.Names}} {{.RunningFor}}' | grep -i bystander || true
done

echo "=== CAPTURE $(date) ==="
python bystander/capture_activations.py --port $PORT --eos "<|im_end|>" --out-dir "$OUT" \
  --logdir logs/bystander-lightning-inc1-ext --logdir logs/bystander-lightning-inc2-ext \
  --logdir logs/bystander-lightning-inc3-ext > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $SPID 2>/dev/null; sleep 8
[ -s "$OUT/manifest.tsv" ] || { echo "NO MANIFEST"; exit 1; }
mkdir -p "$OUT/acts"
echo "4,8,16,24,32,40,48" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,32,40,48 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,32,40,48; echo "check_layers rc=$?"
echo "=== REPORT (pooled with originals) ==="
python bystander/report.py logs/bystander-lightning-dt2 logs/bystander-lightning-inc2 logs/bystander-lightning-inc3 \
  logs/bystander-lightning-inc1-ext logs/bystander-lightning-inc2-ext logs/bystander-lightning-inc3-ext --cache bystander/.envcache
echo "=== W4 DONE $(date) ==="
