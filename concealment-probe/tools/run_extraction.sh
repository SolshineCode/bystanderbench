#!/bin/bash
# Run residual-stream extraction for a prepared model dataset dir.
# Usage: run_extraction.sh <data/model_tag dir> <gguf path> [extra llama args...]
# Layers: every 4th layer 4..60 (layer sweep discipline; final layer 63 is
# unavailable by construction -- llama.cpp slices the last layer to output rows).
set -euo pipefail
DIR="$1"; GGUF="$2"; shift 2
TOOL="$(dirname "$0")/extract_resid"
mkdir -p "$DIR/acts"
export RESID_MANIFEST="$DIR/manifest.tsv"
export RESID_LAYERS="4,8,12,16,20,24,28,32,36,40,44,48,52,56,60"
exec "$TOOL" -m "$GGUF" -c 16384 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
