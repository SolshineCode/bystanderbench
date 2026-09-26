#!/bin/bash
# run_full_pipeline.sh (olmo3) — ImpossibleBench concealment run + SAE-aligned
# activation capture for the decoderesearch/olmo-3-saes workstream.
# TWO-MODEL DESIGN: evals/generation use Olmo-3-7B-Instruct (llama-server);
# extraction re-runs the transcripts through BASE Olmo-3-1025-7B Q8_0 at layers
# 4/16/28 to match the SAE training checkpoint exactly (see extract_olmo3.sh
# header for the full rationale). Requires an ACTIVE gpusched reservation
# mentioning olmo3.
#
# Env knobs: PORT (8095), GPU (0), LIMIT_IMP (25), LIMIT_ORIG (12), ATT_IMP (3),
#            ATT_ORIG (2), UPLOAD (0)
set -uo pipefail

BASE=/home/darkstar/bluedot-unit2-impossiblebench
HERE="$BASE/olmo3"
VENV="$BASE/.venv/bin/activate"
PORT="${PORT:-8095}"
GPU="${GPU:-0}"
LIMIT_IMP="${LIMIT_IMP:-25}"
LIMIT_ORIG="${LIMIT_ORIG:-12}"
ATT_IMP="${ATT_IMP:-3}"
ATT_ORIG="${ATT_ORIG:-2}"
TAG=olmo3-7b
DATA="$BASE/concealment-probe/data/olmo3"
COMBINED="$BASE/logs/${TAG}-all"

cd "$BASE"
source "$VENV"

# Reservation guard (2026-09-07): verifies the reservation actually covers the
# GPU(s) this job uses. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" olmo3 "$GPU" || exit 3

echo "=== [1/6] launching server (single GPU $GPU) ==="
"$HERE/serve_olmo3.sh" "$PORT" "$GPU" || exit 1

echo "=== smoke test ==="
SMOKE=$(curl -sf -m 600 "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Say OK and nothing else."}],"max_tokens":8}')
echo "$SMOKE" | python3 -c "import json,sys; r=json.load(sys.stdin); print('smoke reply:', r['choices'][0]['message']['content'][:80])" || {
    echo "smoke test failed: $SMOKE" >&2; exit 1; }

run_split () {  # split limit attempts
    local sp="$1" lim="$2" att="$3"
    echo "=== eval split=$sp limit=$lim attempts=$att ($(date)) ==="
    python3 run_eval_gpu.py --label "${TAG}-${sp}" --port "$PORT" \
        --splits "$sp" --limit "$lim" --max-connections 1 --max-attempts "$att" \
        2>&1 | tee -a "run_${TAG}-${sp}.log"
}

echo "=== [2/6] evals (positives-first order) ==="
run_split oneoff      "$LIMIT_IMP"  "$ATT_IMP"
run_split conflicting "$LIMIT_IMP"  "$ATT_IMP"
run_split original    "$LIMIT_ORIG" "$ATT_ORIG"

echo "=== [3/6] prepare dataset (server still up for /apply-template) ==="
mkdir -p "$COMBINED"
cp -f logs/${TAG}-oneoff/*.eval logs/${TAG}-conflicting/*.eval logs/${TAG}-original/*.eval "$COMBINED/" 2>/dev/null
[ -f "$HERE/label_overrides.json" ] || echo '{}' > "$HERE/label_overrides.json"
python3 concealment-probe/tools/prepare_dataset.py \
    --logdir "$COMBINED" --port "$PORT" --model-tag "$TAG" --outdir "$DATA" \
    --eos-suffix $'<|im_end|>\n' --overrides "$HERE/label_overrides.json" \
    2>&1 | tee "$HERE/prepare_dataset.log"

echo "=== [4/6] stop server, extract activations ==="
if [ -f "$HERE/server.pid" ]; then
    kill "$(cat "$HERE/server.pid")" 2>/dev/null; sleep 15
    kill -9 "$(cat "$HERE/server.pid")" 2>/dev/null
    rm -f "$HERE/server.pid"
fi
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")
    [ "$used" -lt 1500 ] && break; sleep 10
done
"$HERE/extract_olmo3.sh" "$DATA/$TAG" "$GPU" 2>&1 | tee "$BASE/llamacpp_logs/olmo3_extraction.log"

echo "=== [5/6] export transcripts + stage HF folder ==="
python3 concealment-probe/tools/export_transcripts.py \
    --logdir "$COMBINED" --out "$DATA/$TAG/transcripts.jsonl" \
    2>&1 | tail -5
cp -f "$HERE/label_overrides.json" "$DATA/$TAG/label_overrides.json"
SRVCFG=$(grep -hoE "SERVER_READY.*" "$HERE/server_ready.log" 2>/dev/null | tail -1)
PKG_ARGS=(
    --data-dir "$DATA/$TAG"
    --logdir "logs/${TAG}-oneoff" --logdir "logs/${TAG}-conflicting" --logdir "logs/${TAG}-original"
    --staging "$BASE/hf_upload_olmo3"
    --repo-id "DarkStarDeleeuw/bluedot-unit2-concealment-probe-olmo3-7b"
    --pipeline-dir "$HERE" --server-log-glob "olmo3_*.log"
    --limits "oneoff $LIMIT_IMP, conflicting $LIMIT_IMP, original $LIMIT_ORIG"
    --max-attempts "$ATT_IMP (impossible splits), $ATT_ORIG (original)"
    --client-timeout 2400 --retry-budget 4800
    --run-dates "$(date +%Y-%m-%d)"
)
[ -n "$SRVCFG" ] && PKG_ARGS+=(--server-config "$SRVCFG")
python3 "$BASE/llama70b/package_and_upload.py" "${PKG_ARGS[@]}" --no-upload

echo "=== [6/6] label-audit reminder ==="
python3 - "$DATA/$TAG/samples.jsonl" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
flagged = [r for r in rows if r["flagged"]]
cheats  = [r for r in rows if r["category"] == "concealed_cheat"]
print(f"{len(flagged)} keyword-flag hits ('disclosed' candidates) — EVERY one needs hand audit")
print(f"{len(cheats)} concealed_cheat — verify each + assign cheat_mechanism (check_override vs hardcode)")
for r in flagged + cheats:
    print(f"  AUDIT {r['sid']}: cat={r['category']} ver={r['verification_result']} toks={r['n_total_tokens']}")
EOF
if [ "${UPLOAD:-0}" = "1" ]; then
    echo "=== uploading to HF ==="
    python3 "$BASE/llama70b/package_and_upload.py" "${PKG_ARGS[@]}"
else
    echo "staged only (UPLOAD!=1). Audit labels, then re-run package step with upload."
fi
echo "=== pipeline done ($(date)) ==="
