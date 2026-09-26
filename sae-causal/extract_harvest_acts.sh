#!/bin/bash
# extract_harvest_acts.sh GPU
# Teacher-forced residual extraction for the 200 harvested generations from the §F44
# causal run (100 base + 100 f655_neg), whose token streams were captured with manifests
# but never given activations. Queue item 3(b).
#
# llama.cpp path only -- extract_resid, not HF transformers. Requires a gpusched
# reservation on the target card (the guard below enforces it).
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; cd "$BASE"
GPU="${1:-0}"
GGUF="${GGUF:-$BASE/gguf/qwen3.5-27b.gguf}"
LAYERS="${LAYERS:-4,8,16,24,32,40,48,56}"
bash tools/require_reservation.sh sae-causal "$GPU" || exit 3
mkdir -p sae-causal/tokens/acts
for arm in base f655_neg; do
    MAN="sae-causal/tokens/manifest_${arm}.tsv"
    [ -f "$MAN" ] || { echo "missing $MAN"; exit 1; }
    echo "=== $arm: $(wc -l < "$MAN") streams ($(date)) ==="
    RESID_MANIFEST="$MAN" RESID_LAYERS="$LAYERS" CUDA_VISIBLE_DEVICES="$GPU" \
      "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
      --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
      > "sae-causal/extract_${arm}.log" 2>&1
    echo "  $arm: $(ls sae-causal/tokens/acts/${arm}_*.bin 2>/dev/null | wc -l) bins"
done
echo "TOTAL bins: $(ls sae-causal/tokens/acts/*.bin 2>/dev/null | wc -l) (expect 200) ($(date))"
