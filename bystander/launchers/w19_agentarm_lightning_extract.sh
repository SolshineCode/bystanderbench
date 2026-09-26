#!/bin/bash
# W19 (2026-09-15): residual extraction for the lightning agent-arm capture tree (W16 left
# token streams but no bins). Same layer set as every other lightning tree so the agent-arm
# activations are directly comparable with the control's.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
OUT=$BASE/bystander/acts_lightning_agentarm
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-agentarm-lightning 1 || exit 3
mkdir -p "$OUT/acts"; echo "4,8,16,24,32,40,48" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,32,40,48 CUDA_VISIBLE_DEVICES=1 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,32,40,48; echo "check_layers rc=$?"
echo "=== W19 DONE $(date) ==="
