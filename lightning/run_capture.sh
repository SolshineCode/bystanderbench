#!/bin/bash
# run_capture.sh (lightning) — teacher-force nemotron-3.5-lightning's own existing
# real OpenRouter transcripts (logs/moe-free-nemotron35-lightning-or/*.eval,
# already hand-audited: mechanism_audit.json, screen_summary_v2.jsonl) through the
# LOCAL GGUF for its own residual-stream activations. No fresh generation --
# prepare_dataset.py only ever tokenizes+prefills existing history/target text,
# it never asks the model to produce new content, so this is a straight reuse of
# the standard local-capture tool against a cloud-sourced logdir. Feeds the
# pooled cross-model probe (positioning doc section 18); no published SAE/NLA
# checkpoint exists for this model.
#
# Requires an ACTIVE gpusched reservation mentioning "lightning".
set -uo pipefail

BASE=/home/darkstar/bluedot-unit2-impossiblebench
HERE="$BASE/lightning"
VENV="$BASE/.venv/bin/activate"
PORT="${PORT:-8096}"
GPU="${GPU:-0}"
TAG=nemotron35-lightning
SRCLOGS="$BASE/logs/moe-free-nemotron35-lightning-or"
DATA="$BASE/concealment-probe/data/lightning"

cd "$BASE"
source "$VENV"

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" lightning "$GPU" || exit 3

echo "=== [1/4] launching server (single GPU $GPU) ==="
"$HERE/serve_lightning.sh" "$PORT" "$GPU" || exit 1

echo "=== smoke test ==="
SMOKE=$(curl -sf -m 600 "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Say OK and nothing else."}],"max_tokens":8}')
echo "$SMOKE" | python3 -c "import json,sys; r=json.load(sys.stdin); print('smoke reply:', r['choices'][0]['message']['content'][:80])" || {
    echo "smoke test failed: $SMOKE" >&2; exit 1; }

echo "=== [2/4] teacher-force existing transcripts through prepare_dataset.py ==="
mkdir -p "$DATA"
# eos-suffix left at prepare_dataset.py's default (<|im_end|>\n) -- confirmed
# correct for this model directly from the GGUF's own embedded chat_template
# (token 11 = <|im_end|>, assistant turns close with '<|im_end|>\n') before
# writing this script, not assumed.
python3 concealment-probe/tools/prepare_dataset.py \
    --logdir "$SRCLOGS" --port "$PORT" --model-tag "$TAG" --outdir "$DATA" \
    2>&1 | tee "$HERE/prepare_dataset.log"

echo "=== [3/4] stop server, extract activations ==="
if [ -f "$HERE/server.pid" ]; then
    kill "$(cat "$HERE/server.pid")" 2>/dev/null; sleep 15
    kill -9 "$(cat "$HERE/server.pid")" 2>/dev/null
    rm -f "$HERE/server.pid"
fi
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")
    [ "$used" -lt 1500 ] && break; sleep 10
done
"$HERE/extract_lightning.sh" "$DATA/$TAG" "$GPU" 2>&1 | tee "$BASE/llamacpp_logs/lightning_extraction.log"

echo "=== [4/4] done ($(date)) ==="
echo "Activations at $DATA/$TAG/acts, manifest at $DATA/$TAG/manifest.tsv"
echo "NOTE: samples.jsonl here is prepare_dataset.py's OWN fresh keyword-based labeling of"
echo "the same source transcripts -- it does NOT automatically inherit the OpenRouter screen's"
echo "hand-audited labels ($SRCLOGS/mechanism_audit.json, screen_summary_v2.jsonl)."
echo "Before citing any count from this samples.jsonl, spot-check it against those existing"
echo "audited labels -- same source text so it should mostly agree, but standing discipline"
echo "says verify, don't assume."
