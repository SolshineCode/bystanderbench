#!/bin/bash
# w43_nex_control_volume.sh -- last night of local compute (2026-09-20/21).
#
# Grows the nex HUMAN-wrongdoer control cell (blatant_wrongdoing, currently 37/151) toward
# parity with the agent-arm cell (129/285), per Peter Gebauer's relayed scope advice: fill in
# the existing program's volume rather than open new incidents (see bystander/env/content.py
# lines ~1049-1057 for the parked agent-wrongdoer incident-2/3 arms this explicitly excludes).
# Same shape as tools/offline/gpu0_bystander_queue.sh: run_pilot_local.sh in pairs, then
# capture_chain.sh with the pre-decision cut. Open-ended until logs/tonight/STOP.
# Env (required): RES_ID (gpusched id on GPU 0)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
: "${RES_ID:?}"; N="${START_N:-1}"; PORT="${PORT:-8090}"; CAPPORT="${CAPPORT:-8091}"; PDPORT="${PDPORT:-8092}"
STOP=logs/tonight/STOP; LOG=logs/tonight/gpu0_control_queue.log
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
END=$(( $(date +%s) + 7*3600 ))
extend_or_check(){
  if gpusched extend "$RES_ID" 2h >/dev/null 2>&1; then END=$((END + 7200)); say "extended $RES_ID +2h (end $(date -d @$END '+%H:%M'))"; return 0; fi
  local left=$(( END - $(date +%s) ))
  say "extend refused; ${left}s left"
  [ "$left" -gt 5400 ]
}
finish(){ say "releasing $RES_ID"; gpusched release "$RES_ID" >/dev/null 2>&1; say "GPU0 CONTROL QUEUE DONE"; }
trap finish EXIT
export FAIL_ON_ERROR=0.34
say "GPU0 CONTROL QUEUE START res=$RES_ID start_n=$N port=$PORT"
bash tools/require_reservation.sh bystander 0 || { say "no reservation, abort"; exit 3; }
run_batch(){
  local LAB=$1 try rc
  for try in 1 2 3; do
    [ -e "$STOP" ] && return 2
    say "batch $LAB try $try"
    GPU=0 PORT=$PORT GGUF="$GGUF" EPOCHS=12 LABEL=$LAB ARMS=blatant_wrongdoing TOOL_ARMS=with_tool \
      bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1; rc=$?
    if [ $rc -eq 0 ] && ls "logs/$LAB"/*.eval >/dev/null 2>&1 && grep -q "pilot done" "logs/${LAB}.runlog"; then
      say "batch $LAB OK: $(grep -E 'alerted|discovered' "logs/${LAB}.runlog" | tail -1 | cut -c1-160)"; return 0
    fi
    say "batch $LAB rc=$rc; tail: $(tail -2 "logs/${LAB}.runlog" | tr '\n' ' ' | cut -c1-200)"
    kill "$(cat bystander/server.pid 2>/dev/null)" 2>/dev/null; sleep 300
  done
  return 1
}
while true; do
  [ -e "$STOP" ] && { say "STOP file seen"; break; }
  extend_or_check || { say "cannot secure time for another batch; stopping"; break; }
  P=$(printf %02d $N); Q=$(printf %02d $((N+1)))
  LA=bystander-nex-ctrl-nite-$P; LB=bystander-nex-ctrl-nite-$Q; SUF=nite$P$Q
  LOGDIRS=""
  run_batch $LA; rc=$?; [ $rc -eq 2 ] && break; [ $rc -eq 0 ] && LOGDIRS="$LOGDIRS logs/$LA"
  [ -e "$STOP" ] && { say "STOP file seen"; break; }
  run_batch $LB; rc=$?; [ $rc -eq 2 ] && break; [ $rc -eq 0 ] && LOGDIRS="$LOGDIRS logs/$LB"
  if [ -n "$LOGDIRS" ]; then
    say "CHAIN ctrl_$SUF logdirs:$LOGDIRS"
    GGUF="$GGUF" GPU=0 OUT="$BASE/bystander/acts_nex_ctrl_$SUF" LOGDIRS="$LOGDIRS" TAG=bystander \
      CAPPORT=$CAPPORT PDPORT=$PDPORT FULL_EXTRACT=0 bash bystander/capture_chain.sh > "logs/tonight/chain_ctrl_$SUF.log" 2>&1
    say "chain ctrl_$SUF rc=$? verdict: $(tail -1 "$BASE/bystander/acts_nex_ctrl_$SUF.CHAIN_STATUS" 2>/dev/null | cut -c1-160)"
  else
    say "both batches failed; sleeping 15 min"; sleep 900
  fi
  N=$((N+2))
done
