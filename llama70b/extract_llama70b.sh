#!/bin/bash
# extract_llama70b.sh — residual-stream extraction for Llama-3.3-70B (80 layers,
# d_model 8192), tensor-split across both M40s.
#
# Differences vs concealment-probe/tools/run_extraction.sh (qwen3.5, 64 layers):
#   - layer sweep generalized to the 80-layer llama graph: every 4th layer 4..76
#     (final layer 79 is unobservable by construction — llama.cpp slices the last
#     layer's graph to output rows; same limitation as documented for qwen)
#   - both GPUs + auto-fit offload (no -ngl: llama.cpp common_fit_params picks the
#     GPU/CPU split — extraction is prefill-only, partial offload is acceptable)
#   - same FA + q8_0 KV config as the server, -c 16384 so long samples fit
#
# Usage: extract_llama70b.sh <data/model_tag dir> [extra llama args...]
# Requires: <dir>/manifest.tsv from prepare_dataset.py; active gpusched reservation.
set -euo pipefail
DIR="$1"; shift || true
GGUF=/home/darkstar/gguf-downloads/llama-3.3-70b/Llama-3.3-70B-Instruct-Q4_K_M.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" llama70b both || exit 3

mkdir -p "$DIR/acts"
export RESID_MANIFEST="$DIR/manifest.tsv"
export RESID_LAYERS="${RESID_LAYERS:-4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76}"
CUDA_VISIBLE_DEVICES=0,1 exec "$TOOL" -m "$GGUF" -c 16384 -b 1024 \
  --tensor-split 1,1 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
