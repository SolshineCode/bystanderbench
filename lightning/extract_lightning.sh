#!/bin/bash
# extract_lightning.sh — residual-stream extraction for nemotron-3.5-lightning
# (d_model 2688, 52 blocks), single M40, standard every-4th-layer probe sweep.
# No published SAE/NLA checkpoint for this model -- this data feeds the pooled
# cross-model probe (positioning doc section 18), not an SAE decode.
#
# Usage: extract_lightning.sh <data/model_tag dir> [gpu] [extra llama args...]
set -euo pipefail
DIR="$1"; GPU="${2:-0}"; shift 2 || true
GGUF=/home/darkstar/gguf-downloads/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf
TOOL=/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe/tools/extract_resid

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" lightning "$GPU" || exit 3

mkdir -p "$DIR/acts"
export RESID_MANIFEST="$DIR/manifest.tsv"
# Layer sweep corrected 2026-09-07 by enumeration, not assumption.
#
# This model is a hybrid (Mamba/attention) MoE: of its 52 blocks only 23 emit an
# `l_out-<n>` tensor, at irregular indices
#   1,3,6,8,10,13,15,17,20,22,24,27,29,31,34,36,38,40,43,45,47,49,51
# (measured with RESID_LAYERS=all on one sample). The previous every-4th-layer
# default (4,8,...,48) matched only 5 of them -- 4,12,16,28,32,44,48 simply do
# not exist here, and extract_resid silently captures whatever intersects rather
# than warning. The sweep below is every other AVAILABLE layer: 12 layers spanning
# the full depth 1..51. CLAUDE.md's standing rule is to check the layer convention
# before any new capture; for a hybrid arch that check has to include *which layer
# indices exist*, not just the l_out-L/hidden_states[L+1] offset.
export RESID_LAYERS="${RESID_LAYERS:-1,6,10,15,20,24,29,34,38,43,47,51}"
# -c 102400: transcripts here run 3k-100k tokens (median 27k, max 100717). The
# previous -c 8192 silently skipped 60 of 62 samples ("exceeds n_ctx") while the
# pipeline still printed its normal done banner. Measured VRAM at 102400 ctx with
# q8_0 KV + flash-attn: 18.5 GiB of 22.5 GiB, so this fits one M40.
CUDA_VISIBLE_DEVICES="$GPU" exec "$TOOL" -m "$GGUF" -c 102400 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  "$@" 2>&1
