#!/bin/bash
# run_capture.sh (north-mini) — teacher-force north-mini-code's own existing real
# OpenRouter transcripts (logs/moe-free-north-mini-or/*.eval, already hand-audited)
# through the LOCAL GGUF for its own residual-stream activations. Same
# teacher-forcing reuse of prepare_dataset.py as lightning/run_capture.sh.
#
# North-mini's chat template (cohere2moe / Command-family convention) is NOT
# ChatML -- turns close with <|END_OF_TURN_TOKEN|>, possibly preceded by other
# markers depending on turn type, and the exact closing sequence for a PLAIN
# assistant text response wasn't confirmed by static template reading alone
# (the template is large and branchy). Rather than guess and silently bake in
# a wrong token-boundary assumption, this script empirically derives the
# eos-suffix from the live server's own /apply-template output before running
# the real capture, and refuses to proceed if the result looks wrong.
#
# Requires an ACTIVE gpusched reservation mentioning "north-mini"/"northmini".
set -uo pipefail

BASE=/home/darkstar/bluedot-unit2-impossiblebench
HERE="$BASE/north-mini"
VENV="$BASE/.venv/bin/activate"
PORT="${PORT:-8097}"
GPU="${GPU:-0}"
TAG=north-mini-code
SRCLOGS="${SRCLOGS:-$BASE/logs/moe-free-north-mini-or}"
DATA="${DATA:-$BASE/concealment-probe/data/north-mini}"

cd "$BASE"
source "$VENV"

# Reservation guard (2026-09-07): checks the reservation actually covers the GPU
# this job will use. The old `gpusched status | grep -qi "<tag>"` matched a
# reservation on ANY gpu -- on 2026-09-06 a GPU-1 reservation authorised a run
# that then used GPU 0. See tools/require_reservation.sh.
bash "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/tools/require_reservation.sh" north-mini "$GPU" || exit 3

echo "=== [1/5] launching server (single GPU $GPU) ==="
"$HERE/serve_northmini.sh" "$PORT" "$GPU" || exit 1

echo "=== smoke test ==="
SMOKE=$(curl -sf -m 600 "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Say OK and nothing else."}],"max_tokens":8}')
echo "$SMOKE" | python3 -c "import json,sys; r=json.load(sys.stdin); print('smoke reply:', r['choices'][0]['message']['content'][:80])" || {
    echo "smoke test failed: $SMOKE" >&2; exit 1; }

echo "=== [2/5] empirically derive the eos-suffix from the live template ==="
# 2026-09-08: the derivation below is correct for templates that CLOSE a final assistant
# turn, but cohere2moe leaves the last assistant turn open (no closing markers -- it
# prefills `<|START_THINKING|><|END_THINKING|><|START_TEXT|>` and stops), so it refused
# with "empty suffix". Probing with the assistant turn in the MIDDLE of a history shows
# the real close is `<|END_TEXT|><|END_OF_TURN_TOKEN|>`. EOS_SUFFIX may therefore be
# supplied in the environment (with PREP_EXTRA for the native-reasoning flags, see
# prepare_dataset.py --strip-prompt-tail/--think-open/--think-close); the derivation
# still runs as the default path when it is not.
if [ -n "${EOS_SUFFIX:-}" ]; then
    echo "EOS_SUFFIX supplied by environment: $(python3 -c "import sys; print(repr(sys.argv[1]))" "$EOS_SUFFIX")"
else
EOS_SUFFIX=$(python3 - "$PORT" <<'PYEOF'
import sys, json, urllib.request

port = sys.argv[1]
MARKER = "ZZZ_NORTHMINI_PROBE_MARKER_ZZZ"

def apply_template(messages):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/apply-template",
        data=json.dumps({"messages": messages}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["prompt"]

history = [{"role": "user", "content": "Say the marker word."}]
with_asst = history + [{"role": "assistant", "content": MARKER}]

rendered = apply_template(with_asst)
idx = rendered.find(MARKER)
if idx == -1:
    print("ERROR: marker not found in rendered template", file=sys.stderr)
    sys.exit(1)
suffix = rendered[idx + len(MARKER):]
# sanity bounds: shouldn't be empty, shouldn't be enormous (would mean we
# accidentally captured a whole next-turn's content, not just closing markers)
if len(suffix) == 0:
    print("ERROR: empty suffix detected -- template renders nothing after assistant content", file=sys.stderr)
    sys.exit(1)
if len(suffix) > 200:
    print(f"ERROR: suspiciously long suffix ({len(suffix)} chars) -- likely captured more than just closing markers: {suffix!r}", file=sys.stderr)
    sys.exit(1)
print(suffix, end="")
PYEOF
)
RC=$?
if [ $RC -ne 0 ] || [ -z "$EOS_SUFFIX" ]; then
    echo "REFUSING: could not safely derive eos-suffix from the live template (see stderr above)." >&2
    echo "Do not guess -- inspect the template/render manually before proceeding." >&2
    exit 5
fi
echo "derived eos-suffix (repr): $(python3 -c "import sys; print(repr(sys.argv[1]))" "$EOS_SUFFIX")"
fi

echo "=== [3/5] teacher-force existing transcripts through prepare_dataset.py ==="
mkdir -p "$DATA"
python3 concealment-probe/tools/prepare_dataset.py \
    --logdir "$SRCLOGS" --port "$PORT" --model-tag "$TAG" --outdir "$DATA" \
    --eos-suffix "$EOS_SUFFIX" ${PREP_EXTRA:-} \
    2>&1 | tee "$HERE/prepare_dataset${LOGTAG:-}.log"

echo "=== [4/5] stop server, extract activations ==="
if [ -f "$HERE/server.pid" ]; then
    kill "$(cat "$HERE/server.pid")" 2>/dev/null; sleep 15
    kill -9 "$(cat "$HERE/server.pid")" 2>/dev/null
    rm -f "$HERE/server.pid"
fi
for i in $(seq 1 12); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")
    [ "$used" -lt 1500 ] && break; sleep 10
done
if [ "${SKIP_EXTRACT:-0}" = "1" ]; then
    echo "SKIP_EXTRACT=1: server stopped, tokens+manifest written; run extract_northmini.sh separately (e.g. with RESID_MANIFEST=<prioritised manifest> CTX=184320)."
else
"$HERE/extract_northmini.sh" "$DATA/$TAG" "$GPU" 2>&1 | tee "$BASE/llamacpp_logs/northmini_extraction${LOGTAG:-}.log"
fi

echo "=== [5/5] done ($(date)) ==="
echo "Activations at $DATA/$TAG/acts, manifest at $DATA/$TAG/manifest.tsv"
echo "NOTE: samples.jsonl here is prepare_dataset.py's OWN fresh keyword-based labeling of"
echo "the same source transcripts -- it does NOT automatically inherit the OpenRouter screen's"
echo "hand-audited labels ($SRCLOGS/mechanism_audit.json if present)."
echo "Before citing any count from this samples.jsonl, spot-check it against those existing"
echo "audited labels -- same source text so it should mostly agree, but standing discipline"
echo "says verify, don't assume."
