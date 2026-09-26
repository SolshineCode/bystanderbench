#!/bin/bash
# W29 (2026-09-18): the F189 owed work, in the order a guard has to be proven.
#   1. NEGATIVE TEST: re-run the OLD --match turnrank config and require the gate to REFUSE.
#      A guard never seen to say no is not evidence of anything (standing project rule).
#   2. Re-cut with --match turnfrac, which matches relative turn position instead of rank
#      counted from the end, and require the gate to PASS.
#   3. Extract, then refit the probe on a tree whose cut positions are actually matched.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
tools/require_reservation.sh claude-bystander-agentarm 0 || exit 3
CUDA_VISIBLE_DEVICES=0 nohup /home/darkstar/llama.cpp/build/bin/llama-server \
  --model "$GGUF" --host 127.0.0.1 --port 8097 -ngl 999 -c 32768 -np 1 --no-webui --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > llamacpp_logs/w29_server.log 2>&1 &
SPID=$!
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8097/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8097/health | grep -q ok || { echo "server never came up"; kill $SPID; exit 1; }

echo "=== 1. NEGATIVE TEST: the gate must REFUSE the old turnrank config ==="
python bystander/decision_index.py --port 8097 --dirs bystander/acts_nex_agentarm \
  --capture-schema f151 --match turnrank --out /tmp/w29_negative_test > /tmp/w29_neg.log 2>&1
RC=$?
grep -E "REFUSING TO WRITE|GATE PASS|AUC of position" /tmp/w29_neg.log | tail -3
if [ $RC -ne 2 ]; then
  echo "!! GATE DID NOT FIRE on the known-bad config (rc=$RC). The gate is not trustworthy."
  kill $SPID; exit 1
fi
echo "GATE NEGATIVE TEST PASSED: refused with rc=2"

echo "=== 2. RE-CUT with turnfrac, gate must PASS ==="
OUT=$BASE/bystander/acts_nex_agentarm.predecision2
python bystander/decision_index.py --port 8097 --dirs bystander/acts_nex_agentarm bystander/acts_nex_agentarm_rep \
  --capture-schema f151 --match turnfrac --out "$OUT" > "$OUT.index.log" 2>&1
RC=$?
grep -E "REFUSING TO WRITE|GATE PASS|AUC of position|decision_index" "$OUT.index.log" | tail -4
[ $RC -eq 0 ] || { echo "re-cut failed rc=$RC"; kill $SPID; exit 1; }
kill $SPID 2>/dev/null; sleep 8

echo "=== 3. EXTRACT ==="
mkdir -p "$OUT/acts"; echo "4,8,16,24,30,34,37,39" | tr ',' '\n' > "$OUT/requested_layers.txt"
RESID_MANIFEST="$OUT/manifest.tsv" RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
  "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
  --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$OUT/extract.log" 2>&1
echo "bins: $(ls "$OUT"/acts/*.bin 2>/dev/null | wc -l) / $(wc -l < "$OUT/manifest.tsv")"
python bystander/check_layers.py "$OUT" --expect 4,8,16,24,30,34,37,39; echo "check_layers rc=$?"

echo "=== 4. REFIT on a tree whose cuts are matched ==="
python bystander/probe_alert.py --arm blatant_wrongdoing_agents --transfer-arm blatant_wrongdoing \
  --perms 2000 --predecision \
  --extra-logdir logs/bystander-agentarm-nex-a --extra-logdir logs/bystander-agentarm-nex-b \
  --extra-logdir logs/bystander-agentarm-nex-rep-c --extra-logdir logs/bystander-agentarm-nex-rep-d \
  --extra-logdir logs/bystander-agentarm-smoke --extra-actdir "$OUT" \
  --out research/canonical/probe_alert_agentarm_gated.json 2>&1 | tail -14
echo "=== W29 DONE $(date) ==="
