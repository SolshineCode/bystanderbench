#!/bin/bash
# Controls for the gemma-3-27b L41 NLA decode, extracted through THE SAME PATH as the project
# vectors: llama.cpp + extract_resid on the local Q4 GGUF, never the HF stack (the M40 ban).
#
# Why this matters. The 12b kernel built its positive control by running the HF base model, so
# its control tested the HF extraction path. Our 27b project vectors come from llama.cpp Q4, so
# an HF-side control would certify a pipeline we are not using. A control has to share the
# pipeline it is vouching for, or it vouches for nothing (F33, F162).
#
# Positive controls decode to a known topic if the pipeline is sound. Negative controls are
# built in the kernel as random directions at matched norm, so they need no extraction.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
# The SAME file the layer-41 project bins came from. F172: the local build is ggml-org's and
# is NOT byte-identical to bartowski's, so "a gemma-3-27b Q4_K_M" is not specific enough.
GGUF=/home/darkstar/gguf-downloads/gemma-3-27b/gemma-3-27b-it-Q4_K_M.gguf
[ -f "$GGUF" ] || { echo "GGUF missing: $GGUF"; exit 1; }
OUT=$BASE/nla-decode/inputs/controls-27b
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
mkdir -p "$OUT/tokens" "$OUT/acts"
python3 - "$OUT" <<'PY'
import sys
d = sys.argv[1]
texts = {
 "ctl_weather_1": "The Met Office has issued a yellow warning for heavy rain and strong winds across the west coast tonight, with localised flooding expected by morning.",
 "ctl_weather_2": "Tomorrow's forecast: persistent showers through the afternoon, easing overnight, with gusts reaching fifty miles per hour along the coast.",
 "ctl_code_1": "def test_month_end_batch_fully_matched():\n    result = reconcile(ledger, statements)\n    assert result.unmatched == []",
 "ctl_code_2": "The function iterates over each statement line, compares it to the ledger entry with a strict less-than tolerance, and returns the unmatched remainder.",
 "ctl_finance_1": "The March close pack was submitted to the external auditor with the unreconciled entry count shown as zero, while the internal copy retained one hundred and eighteen.",
}
for k, v in texts.items():
    open(f"{d}/tokens/{k}.txt", "w").write(v)
print(f"wrote {len(texts)} control prompts")
PY
# extract_resid consumes TOKEN-ID STREAMS, one id per line, not prose. The first attempt
# wrote raw text and every row failed with "no tokens in ...", 0 of 5 bins. Tokenise with the
# same binary and the same GGUF that will do the extraction, so the ids are the model's own.
mkdir -p "$OUT/raw"
for f in "$OUT"/tokens/*.txt; do mv "$f" "$OUT/raw/$(basename "$f")"; done
: > "$OUT/manifest.tsv"
for f in "$OUT"/raw/*.txt; do
  b=$(basename "$f" .txt)
  /home/darkstar/llama.cpp/build/bin/llama-tokenize -m "$GGUF" --ids -f "$f" 2>/dev/null \
    | tr -d '[] ' | tr ',' '\n' | grep -E '^[0-9]+$' > "$OUT/tokens/$b.txt"
  n=$(wc -l < "$OUT/tokens/$b.txt")
  [ "$n" -gt 0 ] || { echo "tokenise produced nothing for $b"; exit 1; }
  printf '%s\t%s\t0\t%s\n' "$OUT/tokens/$b.txt" "$OUT/acts/$b" "$n" >> "$OUT/manifest.tsv"
  echo "  $b: $n tokens"
done
echo "manifest rows: $(wc -l < "$OUT/manifest.tsv")"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60 \
  CUDA_VISIBLE_DEVICES=0 "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 8192 -b 512 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "control bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
echo "=== CONTROLS DONE $(date) ==="
