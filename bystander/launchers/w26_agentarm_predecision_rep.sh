#!/bin/bash
# W26 (2026-09-16): extend the agent-arm probe from n=26 to n=50 by putting the replication
# episodes through the same pre-decision pipeline. F183's weakest point is n=26 with the best of
# 24 cells reported; doubling n is the cheapest thing that can falsify or firm it up.
# --capture-schema f151 because these trees were captured after the 2026-09-13 capture change.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm_rep.predecision
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8099 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/agentarm_rep_predecision_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8099/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8099/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
python bystander/decision_index.py --port 8099 --dirs bystander/acts_nex_agentarm_rep \
  --capture-schema f151 --out "$OUT" > "$OUT.index.log" 2>&1
echo "decision_index rc=$?  rows: $(wc -l < "$OUT/manifest.tsv" 2>/dev/null || echo 0)"
kill $SPID 2>/dev/null; sleep 8
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"
echo "=== REFIT AT HIGHER N ==="
python bystander/probe_alert.py --arm blatant_wrongdoing_agents --transfer-arm blatant_wrongdoing \
  --perms 2000 --predecision \
  --extra-logdir logs/bystander-agentarm-nex-a --extra-logdir logs/bystander-agentarm-nex-b \
  --extra-logdir logs/bystander-agentarm-nex-rep-c --extra-logdir logs/bystander-agentarm-nex-rep-d \
  --extra-logdir logs/bystander-agentarm-smoke \
  --extra-actdir bystander/acts_nex_agentarm.predecision \
  --extra-actdir "$OUT" \
  --out research/canonical/probe_alert_agentarm_predecision_n50.json 2>&1 | tail -16
echo "=== W26 DONE $(date) ==="
