#!/bin/bash
# tools/offline/gpu0_bystander_queue.sh -- OFFLINE-MODE worker for GPU 0 (2026-09-20).
#
# Runs BystanderBench nex agent-arm batches (12 episodes each) through the proven W42 shape
# (bystander/run_pilot_local.sh) and, after every pair, bystander/capture_chain.sh with the
# pre-decision cut. Needs NO internet: local llama-server, local docker sandbox image, rule-based
# scorer. Open-ended: keeps going until logs/offline/STOP exists, extending its gpusched
# reservation 2h before every batch. Never edits itself while running (§F49).
#
# Env (required): RES_ID (gpusched reservation id on GPU 0, session name must contain "bystander")
# Env (optional): START_N (first batch number, default 1)  PORT (8090)  CAPPORT (8091)  PDPORT (8092)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
: "${RES_ID:?}"; N="${START_N:-1}"; PORT="${PORT:-8090}"; CAPPORT="${CAPPORT:-8091}"; PDPORT="${PDPORT:-8092}"
STOP=logs/offline/STOP; LOG=logs/offline/gpu0_queue.log
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
END=$(( $(date +%s) + 6*3600 ))          # reservation end as created; updated by extend
extend_or_check(){
  if gpusched extend "$RES_ID" 2h >/dev/null 2>&1; then END=$((END + 7200)); say "extended $RES_ID +2h (end $(date -d @$END '+%H:%M'))"; return 0; fi
  local left=$(( END - $(date +%s) ))
  say "extend refused; ${left}s left on reservation"
  [ "$left" -gt 5400 ]   # a batch+chain needs ~90 min; refuse to start one that cannot finish
}
finish(){ say "releasing $RES_ID"; gpusched release "$RES_ID" >/dev/null 2>&1; say "GPU0 QUEUE DONE"; }
trap finish EXIT
export FAIL_ON_ERROR=0.34
say "GPU0 QUEUE START res=$RES_ID start_n=$N port=$PORT"
bash tools/require_reservation.sh bystander 0 || { say "no reservation, abort"; exit 3; }
run_batch(){ # $1 label -> 0 ok, 1 fail after retries
  local LAB=$1 try rc
  for try in 1 2 3; do
    [ -e "$STOP" ] && return 2
    say "batch $LAB try $try"
    GPU=0 PORT=$PORT GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing_agents TOOL_ARMS=with_tool \
      bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1; rc=$?
    if [ $rc -eq 0 ] && ls "logs/$LAB"/*.eval >/dev/null 2>&1 && grep -q "pilot done" "logs/${LAB}.runlog"; then
      say "batch $LAB OK: $(grep -E 'alerted|discovered' "logs/${LAB}.runlog" | tail -1 | cut -c1-160)"; return 0
    fi
    say "batch $LAB rc=$rc (no .eval or no 'pilot done'); tail: $(tail -2 "logs/${LAB}.runlog" | tr '\n' ' ' | cut -c1-200)"
    kill "$(cat bystander/server.pid 2>/dev/null)" 2>/dev/null; sleep 300
  done
  return 1
}
while true; do
  [ -e "$STOP" ] && { say "STOP file seen"; break; }
  extend_or_check || { say "cannot secure time for another batch; stopping"; break; }
  P=$(printf %02d $N); Q=$(printf %02d $((N+1)))
  LA=bystander-agentarm-nex-off-$P; LB=bystander-agentarm-nex-off-$Q; SUF=off$P$Q
  LOGDIRS=""
  run_batch $LA; rc=$?; [ $rc -eq 2 ] && break; [ $rc -eq 0 ] && LOGDIRS="$LOGDIRS logs/$LA"
  [ -e "$STOP" ] && { say "STOP file seen"; break; }
  run_batch $LB; rc=$?; [ $rc -eq 2 ] && break; [ $rc -eq 0 ] && LOGDIRS="$LOGDIRS logs/$LB"
  if [ -n "$LOGDIRS" ]; then
    say "CHAIN $SUF logdirs:$LOGDIRS"
    GGUF="$GGUF" GPU=0 OUT="$BASE/bystander/acts_nex_agentarm_$SUF" LOGDIRS="$LOGDIRS" TAG=bystander \
      CAPPORT=$CAPPORT PDPORT=$PDPORT FULL_EXTRACT=0 bash bystander/capture_chain.sh > "logs/offline/chain_$SUF.log" 2>&1
    say "chain $SUF rc=$? verdict: $(tail -1 "$BASE/bystander/acts_nex_agentarm_$SUF.CHAIN_STATUS" 2>/dev/null | cut -c1-160)"
  else
    say "both batches failed; sleeping 15 min before next pair"; sleep 900
  fi
  N=$((N+2))
done
