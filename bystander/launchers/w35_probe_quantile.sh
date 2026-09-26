#!/bin/bash
# W35 (2026-09-19): probe re-cut with the quantile matcher (checkpoint 1 relaunch). Prior
# attempts: turnrank -> position-AUC 0.705 (refused), turnfrac -> 0.388 (refused). Both draw a
# random value per episode so the silent distribution only matches alerting IN EXPECTATION;
# quantile matching fixes the distribution by construction. Pools all three nex agent-arm trees.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=$BASE/bystander/acts_nex_agentarm.predecision3
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8099 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w35_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8099/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8099/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }
echo "=== RE-CUT with quantile matching, gate must PASS ==="
python bystander/decision_index.py --port 8099 \
  --dirs bystander/acts_nex_agentarm bystander/acts_nex_agentarm_rep bystander/acts_nex_agentarm_rep2 \
  --capture-schema f151 --match quantile --out "$OUT" > "$OUT.index.log" 2>&1
RC=$?
grep -E "REFUSING TO WRITE|GATE PASS|AUC of position|decision_index" "$OUT.index.log" | tail -6
kill $SPID 2>/dev/null; sleep 8
if [ $RC -ne 0 ]; then echo "re-cut failed rc=$RC, stopping here"; exit 1; fi
echo "=== EXTRACT ==="
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"
echo "=== REFIT ==="
python bystander/probe_alert.py --arm blatant_wrongdoing_agents --transfer-arm blatant_wrongdoing \
  --perms 2000 --predecision \
  --extra-logdir logs/bystander-agentarm-nex-a --extra-logdir logs/bystander-agentarm-nex-b \
  --extra-logdir logs/bystander-agentarm-nex-rep-c --extra-logdir logs/bystander-agentarm-nex-rep-d \
  --extra-logdir logs/bystander-agentarm-nex-rep-e --extra-logdir logs/bystander-agentarm-nex-rep-f \
  --extra-logdir logs/bystander-agentarm-smoke --extra-actdir "$OUT" \
  --out research/canonical/probe_alert_agentarm_quantile.json 2>&1 | tail -16
echo "=== W35 DONE $(date) ==="
