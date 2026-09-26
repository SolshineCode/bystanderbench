#!/bin/bash
# extract_northmini.sh — residual-stream extraction for north-mini-code
# (cohere2moe), single M40, standard every-4th-layer probe sweep.
# Uses extract_resid_new (built against ~/llama.cpp-new for cohere2moe support,
# verified bit-identical to the original extract_resid binary on shared arches).
# No published SAE/NLA checkpoint for this model -- feeds the pooled cross-model
# probe (positioning doc section 18), not an SAE decode.
#
# Usage: extract_northmini.sh <data/model_tag dir> [gpu] [extra llama args...]
set -euo pipefail
DIR="$1"; GPU="${2:-0}"; shift 2 || true
GGUF=/home/darkstar/gguf-downloads/north-mini-code/North-Mini-Code-1.0-UD-Q4_K_M.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid_new

# Reservation guard (2026-09-07): checks the reservation actually covers the GPU
# this job will use. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" north-mini "$GPU" || exit 3

mkdir -p "$DIR/acts"
export RESID_MANIFEST="${RESID_MANIFEST:-$DIR/manifest.tsv}"
export RESID_LAYERS="${RESID_LAYERS:-4,8,12,16,20,24,28,32,36,40,44,48}"
CUDA_VISIBLE_DEVICES="$GPU" exec "$TOOL" -m "$GGUF" -c "${CTX:-32768}" -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
