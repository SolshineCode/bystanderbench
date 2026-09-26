#!/bin/bash
# W22 (2026-09-15): the pre-decision re-extraction for the agent-perpetrator arm. The pooled
# fit on this arm returned AUC 0.950, which probe_alert.py itself refuses to let anyone quote,
# because the pooled window can contain the escalation call: that measures the presence of a
# decision, not a prediction of it. F134 caught the same leak at AUC 0.996 and F167 is the
# honest control-arm number (0.675) that survived the fix. Same treatment here.
#
# decision_index.py truncates each transcript at the moment the agent commits to escalating and
# picks matched cut positions for the silent episodes, then the tree is re-extracted and refit.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm.predecision
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8098 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/agentarm_predecision_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8098/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8098/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
python bystander/decision_index.py --port 8098 \
  --dirs bystander/acts_nex_agentarm --capture-schema f151 \
  --out "$OUT" > "$OUT.index.log" 2>&1
echo "decision_index rc=$?  lines: $(wc -l < "$OUT/manifest.tsv" 2>/dev/null || echo 0)"
kill $SPID 2>/dev/null; sleep 8
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"
echo "=== W22 DONE $(date) ==="
