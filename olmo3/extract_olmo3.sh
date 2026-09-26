#!/bin/bash
# extract_olmo3.sh — residual-stream extraction for the SAE-decode workstream.
#
# CHECKPOINT-EXACT DESIGN: extraction runs the BASE model Olmo-3-1025-7B (Q8_0),
# NOT the Instruct model that generated the transcripts — because the
# decoderesearch/olmo-3-saes SAEs were trained on the base checkpoint
# (cfg.json: model_name=allenai/Olmo-3-1025-7B, hook model.layers.{4,16,28},
# d_in 4096, fp32, prepend_bos=true, context_size 1024). Base-over-instruct-text
# is a distribution shift to note in writeups, but keeps the SAEs exactly valid
# for the activations they see (same lesson as the NLA layer-convention bug).
# Tokenizer is shared between base and instruct (vocab 100278), so token ids
# from the instruct server's /apply-template are valid here.
#
# Layers 4,16,28 = hook model.layers.k OUTPUT = local l_out-k convention,
# 0-indexed both sides — verified aligned, no off-by-one.
#
# Usage: extract_olmo3.sh <data/model_tag dir> [gpu] [extra llama args...]
set -euo pipefail
DIR="$1"; GPU="${2:-0}"; shift 2 || true
GGUF=/home/darkstar/gguf-downloads/olmo-3-1025-7b/Olmo-3-1025-7B-q8_0.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" olmo3 "$GPU" || exit 3

mkdir -p "$DIR/acts"
export RESID_MANIFEST="$DIR/manifest.tsv"
export RESID_LAYERS="${RESID_LAYERS:-4,16,28}"
CUDA_VISIBLE_DEVICES="$GPU" exec "$TOOL" -m "$GGUF" -c 16384 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
