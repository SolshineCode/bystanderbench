#!/bin/bash
# W18 (2026-09-15): agent-perpetrator arm, n=12, on gemma-4-31B-it Q4_K_M served on RunPod pod
# 65xajxyofirejq (A40, EU-SE-1, $0.49/h) over an SSH tunnel, with token capture over the same
# tunnel and residual extraction ON THE POD. gemma-4-31b passes competence 12/12 on its
# human-wrongdoer control and has a passing floor, and the M40s cannot serve it, so this is an
# activation-backed pair the local box cannot produce. Floors are keyed by (model, mode) and
# carry over from the control, so no floor episodes are spent here.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
POD=root@194.68.245.47; PP=22046
MID=gemma-4-31B-it-Q4_K_M.gguf
LPORT=8093
cd "$BASE"; source .venv/bin/activate
ssh -p $PP -o StrictHostKeyChecking=no -o BatchMode=yes -o ServerAliveInterval=30 -N -L $LPORT:127.0.0.1:8080 $POD &
TPID=$!
for t in $(seq 1 40); do curl -sf -m 5 http://127.0.0.1:$LPORT/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 5 http://127.0.0.1:$LPORT/health | grep -q ok || { echo "pod server not reachable through tunnel"; kill $TPID; exit 1; }
export OPENAI_BASE_URL=http://127.0.0.1:$LPORT/v1 OPENAI_API_KEY=sk-local
C="-T affordance=native -T solver_kind=tools -T model_id=$MID --model openai/local-model
   --max-connections 1 --max-tool-output 16000 -M responses_api=false"
echo "=== SMOKE agent arm epochs=1 $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing_agents -T tool_arm=with_tool -T epochs=1 $C \
  --log-dir logs/bystander-agentarm-gemma4-pod-smoke > logs/gemma4_agentarm_smoke.runlog 2>&1
RC=$?; echo "SMOKE rc=$RC"; [ $RC -ne 0 ] && { tail -15 logs/gemma4_agentarm_smoke.runlog; kill $TPID; exit 1; }
echo "=== CEILING agent arm n=12 $(date) ==="
inspect eval bystander/task.py -T arm=blatant_wrongdoing_agents -T tool_arm=with_tool -T epochs=12 $C \
  --log-dir logs/bystander-agentarm-gemma4-pod > logs/gemma4_agentarm_cell.runlog 2>&1; echo "CEILING rc=$?"
python -m bystander.report logs/bystander-agentarm-gemma4-pod logs/bystander-gemma4-31b-pod 2>&1 | tail -12
echo "=== CAPTURE tokens over tunnel $(date) ==="
OUT=$BASE/bystander/acts_gemma4_agentarm_pod
python bystander/capture_activations.py --port $LPORT --out-dir "$OUT" \
  --logdir logs/bystander-agentarm-gemma4-pod --logdir logs/bystander-agentarm-gemma4-pod-smoke > "$OUT.capture.log" 2>&1
echo "capture rc=$?  $(grep -c ERR "$OUT.capture.log") ERR lines"
kill $TPID 2>/dev/null
echo "=== W18 DONE $(date) ==="
