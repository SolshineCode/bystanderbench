#!/bin/bash
# capture_run.sh TAG GGUF GPU PORT LAYERS LOGDIR [LOGDIR...]
# Capture + extract activations for finished BystanderBench runs of ONE model.
# Generalises capture_backlog.sh so two models can capture on two cards at once.
# Capture must replay through the SAME model that produced the episodes, hence per-model.
set -uo pipefail
# Repo root from this script's own location, never an absolute path: the GGUFs these
# scripts serve are public Hugging Face downloads, so tier 2 is portable to anyone who
# fetches them -- the only thing that was stopping that was this line (2026-09-12).
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
TAG="$1"; GGUF="$2"; GPU="$3"; PORT="$4"; LAYERS="$5"; shift 5
OUT="bystander/acts_$TAG"
# CTX / TENSOR_SPLIT (2026-09-12). Both -c values below were hardcoded at 32768, which is
# fine for every model captured so far and impossible for a 70B: Llama-3.3-70B-Instruct
# Q4_K_M is 39.6 GiB against 45.0 GiB of VRAM across both cards, and a q8_0 KV at 32k needs
# ~5.0 GiB more than that leaves. llama.cpp refuses outright. The proven llama-70b config in
# this repo (llama70b/extract_l53.sh) is -c 16384 with --tensor-split 1,1.
# DEFAULTS REPRODUCE EVERY PRIOR CAPTURE EXACTLY: CTX 32768, no tensor-split flag.
CTX="${CTX:-32768}"
TS_ARG=""; [[ -n "${TENSOR_SPLIT:-}" ]] && TS_ARG="--tensor-split ${TENSOR_SPLIT}"
# llama-server: honour LLAMA_SERVER, else take it from PATH, else the author's build.
BIN="${LLAMA_SERVER:-$(command -v llama-server || echo "$HOME/llama.cpp/build/bin/llama-server")}"
# The reservation guard speaks gpusched's vocabulary ("0", "1", "both") while
# CUDA_VISIBLE_DEVICES speaks CUDA's ("0", "1", "0,1"). Passing the CUDA form to the guard
# makes it refuse a perfectly valid `--gpu both` reservation, which is what happened to the
# first llama-70b capture. Translate rather than weaken the guard: it was right to refuse an
# index it did not recognise.
RES_GPU="$GPU"; [[ "$GPU" == *,* ]] && RES_GPU=both
# CHAT_TEMPLATE (2026-09-13, §F139). Optional override for a model whose EMBEDDED template
# llama-server cannot parse. Olmo-3-7B-Instruct's calls `tools | tojson`; minja has no
# `tojson`, so the server aborts at startup and 4 episodes were uncapturable for a day.
# ONLY safe when the override renders identically for the episodes being replayed. The Olmo
# file differs at exactly the three `| tojson` sites, all inside tools-only branches, and
# those are prompted CLI episodes that pass no tools. Verified by reversing the edit and
# getting the embedded template back byte for byte.
TPL_ARG=""
[[ -n "${CHAT_TEMPLATE:-}" ]] && TPL_ARG="--chat-template-file ${CHAT_TEMPLATE}"
bash tools/require_reservation.sh bystander "$RES_GPU" || exit 3
CUDA_VISIBLE_DEVICES="$GPU" nohup "$BIN" --model "$GGUF" --host 127.0.0.1 --port "$PORT" \
  -ngl 999 -c "$CTX" ${TS_ARG} -np 1 --no-webui --jinja ${TPL_ARG} --cache-type-k q8_0 --cache-type-v q8_0 \
  --flash-attn on > "llamacpp_logs/capture_${TAG}.log" 2>&1 &
SPID=$!
for t in $(seq 1 60); do curl -sf -m 3 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q ok || { echo "$TAG: server never came up"; tail -3 "llamacpp_logs/capture_${TAG}.log"; kill $SPID 2>/dev/null; exit 1; }
args=(); for d in "$@"; do args+=(--logdir "$d"); done
"$BASE/.venv/bin/python" bystander/capture_activations.py --port "$PORT" --out-dir "$OUT" "${args[@]}" 2>&1 | tail -2
kill $SPID 2>/dev/null; sleep 8
mkdir -p "$OUT/acts"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS="$LAYERS" CUDA_VISIBLE_DEVICES="$GPU" \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c "$CTX" ${TS_ARG} -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "$TAG: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) bins"
# PER-LAYER ZERO CHECK (2026-09-13, §F139). A requested layer the model never emits is
# written as zeros, not refused, and the bin still has the exact expected size, the right
# d_model and no NaN. Nothing short of looking inside each layer catches it. Runs here so a
# refusal costs one re-run rather than a silent hole in the corpus.
"$BASE/.venv/bin/python" bystander/check_layers.py "$OUT" || {
  echo "$TAG: CAPTURE REFUSED by check_layers.py, see above"; exit 4; }
