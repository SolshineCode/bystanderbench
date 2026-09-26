#!/bin/bash
# stall_watchdog.sh -- §F211 night only. SIGINTs an f211 `inspect eval` that is stuck in an endless
# retry loop (E-06, 2026-09-22: one episode repeated a JSON-malformed tool call for 1h50m and neither
# --timeout nor the default unlimited --max-retries ended it).
#
# Scope: ONLY inspect processes whose args contain "logs/bystander-f215-", matched by PID from the
# process table (never pkill -f: the CLAUDE.md trap). Fires only when ALL THREE stall signs hold:
#   1. that batch's llama-server log has not been written for >= STALL_MIN minutes
#   2. the batch's GPU is at 0% utilisation
#   3. no ESTABLISHED TCP connection to that batch's server port
# SIGINT (not KILL) so Inspect saves its completed samples. report.py then drops the cancelled log
# under its standing status != success rule; that loss is accepted and logged.
BASE=/home/darkstar/bluedot-unit2-impossiblebench
STALL_MIN=${STALL_MIN:-30}
UNTIL=$(date -d "tomorrow 07:05" +%s)
LOG=$BASE/logs/f215/stall_watchdog.log
say(){ echo "[$(date '+%F %T')] $*" >> "$LOG"; }
say "watchdog start, stall threshold ${STALL_MIN} min, until $(date -d @$UNTIL '+%F %T')"
while [ "$(date +%s)" -lt "$UNTIL" ]; do
  ps -eo pid=,args= | awk '/inspect eval bystander\/task.py/ && /logs\/bystander-f211-/ && !/awk/' | while read -r pid args; do
    lab=$(echo "$args" | grep -oE "logs/bystander-f215-[A-Z]-[0-9]+" | head -1 | cut -d/ -f2)
    [ -z "$lab" ] && continue
    slog="$BASE/llamacpp_logs/bystander_${lab}_server.log"
    [ -f "$slog" ] || continue
    age=$(( ($(date +%s) - $(stat -c %Y "$slog")) / 60 ))
    # which GPU/port: F runs on GPU1/8094, H and E on GPU0/8093
    case $lab in *-[GK]-*) gpu=1; port=8094;; *) gpu=0; port=8093;; esac
    util=$(nvidia-smi -i $gpu --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' ')
    conns=$(ss -tn state established "( dport = :$port or sport = :$port )" 2>/dev/null | tail -n +2 | wc -l)
    if [ "$age" -ge "$STALL_MIN" ] && [ "$util" = "0" ] && [ "$conns" = "0" ]; then
      say "STALL $lab pid=$pid server-log-age=${age}min gpu$gpu=${util}% conns=$conns -> SIGINT"
      kill -INT "$pid"
    fi
  done
  sleep 120
done
say "watchdog end"
