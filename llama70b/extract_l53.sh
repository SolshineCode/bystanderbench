#!/bin/bash
# extract_l53.sh — NLA-layer extraction pass for llama3.3-70b samples.
#
# The main extraction sweep (every 4th layer 4..76) does NOT include layer 53,
# the model's published NLA extraction layer (kitft convention: "layer 53" =
# l_out-53 = hidden_states[54] — our llama.cpp extract_resid convention matches
# exactly). This wrapper re-runs extraction with RESID_LAYERS=49,53,57 (NLA
# layer + neighbors) over a SUBSET manifest, writing to acts_nla/ prefixes.
#
# Usage: extract_l53.sh <data/model_tag dir> [sid1 sid2 ...]
#        (no sids = ALL samples in manifest.tsv; expect ~4 min/sample)
set -euo pipefail
DIR="$1"; shift || true
GGUF=/home/darkstar/gguf-downloads/llama-3.3-70b/Llama-3.3-70B-Instruct-Q4_K_M.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" llama70b both || exit 3

mkdir -p "$DIR/acts_nla"
SUB="$DIR/manifest_nla.tsv"
if [ $# -gt 0 ]; then
    : > "$SUB"
    for sid in "$@"; do
        grep -P "/${sid}\t|/${sid}$" "$DIR/manifest.tsv" | head -1 >> "$SUB" || echo "WARN: $sid not in manifest" >&2
    done
else
    cp "$DIR/manifest.tsv" "$SUB"
fi
# redirect output prefixes acts/ -> acts_nla/
sed -i 's|/acts/|/acts_nla/|' "$SUB"
wc -l "$SUB"

export RESID_MANIFEST="$SUB"
export RESID_LAYERS="49,53,57"
CUDA_VISIBLE_DEVICES=0,1 exec "$TOOL" -m "$GGUF" -c 16384 -b 1024 \
  --tensor-split 1,1 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  2>&1
