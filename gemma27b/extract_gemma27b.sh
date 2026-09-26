#!/bin/bash
# extract_gemma27b.sh — residual-stream extraction for gemma-3-27b-it
# (62 text blocks, d_model 5376), single M40.
#
# Layer sweep: every 4th layer 4..60 PLUS layer 41 (the model's published NLA
# layer — the whole point of this capture run), final layer 61 unobservable by
# construction (llama.cpp slices the last layer's graph to output rows).
#
# Usage: extract_gemma27b.sh <data/model_tag dir> [gpu] [extra llama args...]
set -euo pipefail
DIR="$1"; GPU="${2:-0}"; shift 2 || true
GGUF=/home/darkstar/gguf-downloads/gemma-3-27b/gemma-3-27b-it-Q4_K_M.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" gemma27b "$GPU" || exit 3

mkdir -p "$DIR/acts"
export RESID_MANIFEST="$DIR/manifest.tsv"
export RESID_LAYERS="${RESID_LAYERS:-4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60}"
CUDA_VISIBLE_DEVICES="$GPU" exec "$TOOL" -m "$GGUF" -c 16384 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
