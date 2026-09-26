#!/bin/bash
# W5b (2026-09-14 23:00): score qwen3.8:27b conflicting split into Part 1 row 10 and extract
# residuals for the 25 new rows only. Waits for the resumed launcher's DONE marker (the 75-row
# extraction on GPU 1), then: CPU-only prepare_dataset over logs/part1-qwen38-combined (3 evals,
# 100 distinct sids expected), build_rates --write/--check, subset manifest of rows without a
# bin, extract on GPU 1 under the existing reservation. Never edit while running.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; J=/home/darkstar/.claude/jobs/8bfa76b1/tmp
BLOB=/usr/share/ollama/.ollama/models/blobs/sha256-0c93661a3c1c70c7f6529bd6cd50240edd7d01af46afee33fd9594dc450d45a3
PORT=8086; TAG=qwen38-27b; OUT=$BASE/concealment-probe/data/qwen38; D=$OUT/$TAG
cd "$BASE"; source .venv/bin/activate
until grep -q "QWEN38 CONFLICTING+EXTRACT DONE" $J/p1_qwen38_conflicting_extract_v2.log; do sleep 120; done
echo "=== launcher done; bins before: $(ls $D/acts/*.bin 2>/dev/null | wc -l) $(date) ==="
python - <<'PY' || exit 2
from inspect_ai.log import read_eval_log; import glob
for f in glob.glob("logs/part1-qwen38-combined/*.eval"):
    st=read_eval_log(f,header_only=True).status; print(f.split("/")[-1][:40], st); assert st=="success", f
PY
CUDA_VISIBLE_DEVICES="" nohup "$HOME/llama.cpp/build/bin/llama-server" --model "$BLOB" --host 127.0.0.1 --port $PORT \
  -ngl 0 --no-warmup -c 512 -t 6 --jinja --reasoning off --reasoning-budget 0 --no-webui > llamacpp_logs/qwen38_score_cpu_server_b.log 2>&1 < /dev/null &
SPID=$!; for t in $(seq 1 60); do curl -sf -m 3 http://127.0.0.1:$PORT/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:$PORT/health | grep -q ok || { echo "cpu server never came up"; kill $SPID; exit 1; }
cp $D/manifest.tsv $J/qwen38_manifest_75.tsv
echo "=== prepare_dataset $(date) ==="
python concealment-probe/tools/prepare_dataset.py --logdir logs/part1-qwen38-combined --port $PORT --model-tag $TAG --outdir "$OUT" > "$OUT.prepare_b.log" 2>&1; echo "prepare rc=$?"; tail -4 "$OUT.prepare_b.log"
kill $SPID 2>/dev/null; sleep 3; kill -9 $SPID 2>/dev/null
python - "$D/samples.jsonl" <<'PY'
import json,sys,collections
rows=[json.loads(l) for l in open(sys.argv[1])]
print("rows",len(rows),"distinct sids",len({r['sid'] for r in rows}))
for k,v in sorted(collections.Counter((r['split'],r['category']) for r in rows).items()): print("  ",k,v)
PY
python concealment-probe/tools/build_rates.py --write > "$OUT.build_rates_b.log" 2>&1; echo "build_rates rc=$?"; python concealment-probe/tools/build_rates.py --check; echo "check rc=$?"
grep -E "^model|qwen3.8" research/canonical/concealment_rates.csv
echo "=== subset manifest: rows without a bin ==="
awk -F'\t' '{split($2,a,"/"); f=$2".bin"; if (system("test -s "f)!=0) print $0}' $D/manifest.tsv > $J/qwen38_manifest_new.tsv; wc -l < $J/qwen38_manifest_new.tsv
tools/require_reservation.sh claude-qwen38-conflicting 1 || exit 3
RESID_MANIFEST=$J/qwen38_manifest_new.tsv RESID_LAYERS=1,7,12,18,24,30,35,41,47,52,58,64 CUDA_VISIBLE_DEVICES=1 "$BASE/concealment-probe/tools/extract_resid" -m "$BLOB" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$D/extract_b.log" 2>&1; echo "extract_b rc=$?"
echo "bins after: $(ls $D/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < $D/manifest.tsv)"
python bystander/check_layers.py "$D" --expect 1,7,12,18,24,30,35,41,47,52,58,64 2>&1 | head -2; echo "check_layers rc=$?"
echo "=== W5b DONE $(date) ==="
