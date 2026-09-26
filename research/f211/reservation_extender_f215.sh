#!/bin/bash
# Extend §F215's gpusched reservation 1h at a time, ONLY while a §F215 queue log shows the queue
# still running (started and not "QUEUE DONE"), and never past the grant deadline in
# ~/autonomy/state/GRANT_DEADLINE. Liveness comes from the queue's own log, never a process-name
# match. Exits when both queues are done or the deadline passes.
RES=${1:?reservation id}; L=/home/darkstar/bluedot-unit2-impossiblebench/logs/f215
DL=$(date -d "$(cut -d' ' -f1 ~/autonomy/state/GRANT_DEADLINE)" +%s)
log(){ echo "[$(date '+%F %T')] $*" >> $L/extender.log; }
log "extender start res=$RES deadline=$(date -d @$DL '+%F %T')"
while [ "$(date +%s)" -lt "$DL" ]; do
  live=0
  for q in $L/gpu0_allayers_queue.log $L/gpu1_l37_queue.log; do
    [ -f "$q" ] && ! grep -q "QUEUE DONE" "$q" && live=1
  done
  started=$(ls $L/gpu*_queue.log 2>/dev/null | wc -l)
  if [ "$started" -gt 0 ] && [ "$live" = 0 ]; then log "both queues done, extender exits"; break; fi
  # gpusched list prints "<start> -> <end>" as 2026-09-24T01:53 (no seconds, no tz; local time)
  endt=$(~/bin/gpusched list 2>/dev/null | grep "$RES" | sed -nE 's/.*-> ([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}).*/\1/p' | head -1)
  [ -n "$endt" ] && left=$(( $(date -d "$endt" +%s) - $(date +%s) )) || left=99999
  if [ "$left" -lt 2400 ]; then
    if [ $(( $(date +%s) + left + 3600 )) -le $(( DL + 600 )) ]; then
      ~/bin/gpusched extend "$RES" 1h >> $L/extender.log 2>&1 && log "extended by 1h (was ${left}s left)"
    else
      ~/bin/gpusched extend "$RES" 30m >> $L/extender.log 2>&1 && log "extended by 30m, near deadline (was ${left}s left)"
    fi
  fi
  sleep 300
done
log "extender end"
