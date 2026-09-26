#!/bin/bash
# stall_watchdog_f215b.sh -- for the w48 finish run (2026-09-24 day). Replaces stall_watchdog_f215.sh,
# which could NEVER fire: its process filter matched "logs/bystander-f211-" (copied from §F211), so no
# §F215 inspect process ever passed it (found 2026-09-24 07:4x while re-arming it; see §F217 addendum).
#
# SIGINTs ONLY an `inspect eval` whose --log-dir is logs/bystander-f215-<ARM>-<N>, matched by PID from
# the process table (never pkill -f). Fires only when ALL THREE stall signs hold for that batch:
#   1. its llama-server log unwritten for >= STALL_MIN minutes
#   2. its GPU at 0% utilisation
#   3. no ESTABLISHED TCP connection on its server port
# The batch's GPU is read from the w48 queue log that launched it (K runs on both cards now), never
# guessed from the arm letter. Runs until UNTIL_EPOCH (required, absolute), so no "tomorrow" slip.
BASE=${F215_TEST_BASE:-/home/darkstar/bluedot-unit2-impossiblebench}
STALL_MIN=${STALL_MIN:-30}; UNTIL=${UNTIL_EPOCH:?absolute epoch seconds}; ONCE=${ONCE:-0}
LOG=$BASE/logs/f215/stall_watchdog_b.log
say(){ echo "[$(date '+%F %T')] $*" >> "$LOG"; }
say "watchdog-b start, stall threshold ${STALL_MIN} min, until $(date -d @$UNTIL '+%F %T')"
while [ "$(date +%s)" -lt "$UNTIL" ]; do
  # Match on the EXECUTABLE, not on text anywhere in the command line: a shell whose command line
  # merely mentions a batch label (an agent checking on the queue, this script's own tester) matched
  # the text-only filter and was SIGINTed in the 2026-09-24 test. Qualifies only if argv[0] is
  # .../inspect, or argv[0] is python* and argv[1] is .../inspect; and argv continues "eval".
  ps -eo pid=,args= | awk '{ n=split($2,a,"/"); b=a[n]; m=split($3,c,"/"); d=c[m]
      if ((b=="inspect" && $3=="eval") || (b ~ /^python/ && d=="inspect" && $4=="eval")) print }' \
    | awk '$0 ~ /logs\/bystander-f215-[A-Z]-[0-9]+/' | while read -r pid args; do
    lab=$(echo "$args" | grep -oE "logs/bystander-f215-[A-Z]-[0-9]+" | head -1 | cut -d/ -f2)
    [ -z "$lab" ] && continue
    q=$(grep -l "batch $lab " $BASE/logs/f215/gpu*_finish_queue.log 2>/dev/null | head -1)
    [ -z "$q" ] && { say "SEEN $lab pid=$pid but no w48 queue log names it; not touching"; continue; }
    gpu=$(basename "$q" | sed -E 's/^gpu([01])_.*/\1/'); port=$((8093 + gpu))
    slog="$BASE/llamacpp_logs/bystander_${lab}_server.log"
    [ -f "$slog" ] || { say "SEEN $lab pid=$pid gpu$gpu but no server log yet"; continue; }
    age=$(( ($(date +%s) - $(stat -c %Y "$slog")) / 60 ))
    util=$(nvidia-smi -i $gpu --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' ')
    conns=$(ss -tn state established "( dport = :$port or sport = :$port )" 2>/dev/null | tail -n +2 | wc -l)
    [ "$ONCE" = 1 ] && say "CHECK $lab pid=$pid gpu$gpu port=$port age=${age}min util=${util}% conns=$conns"
    if [ "$age" -ge "$STALL_MIN" ] && [ "$util" = "0" ] && [ "$conns" = "0" ]; then
      # SIGINT lets Inspect save completed samples, but a process launched with `&`/setsid nohup from a
      # non-interactive shell inherits SIGINT as IGNORED (seen in the 2026-09-24 test), so read the
      # mask: ignored -> SIGTERM now; otherwise SIGINT, then SIGTERM if still alive after 60 s.
      ign=$(awk '/^SigIgn/{print $2}' /proc/$pid/status 2>/dev/null)
      if [ -n "$ign" ] && (( 16#$ign & 2 )); then
        say "STALL $lab pid=$pid age=${age}min gpu$gpu=${util}% conns=$conns; SIGINT ignored -> SIGTERM"; kill -TERM "$pid"
      else
        say "STALL $lab pid=$pid age=${age}min gpu$gpu=${util}% conns=$conns -> SIGINT"; kill -INT "$pid"
        sleep 60; kill -0 "$pid" 2>/dev/null && { say "$lab pid=$pid survived SIGINT -> SIGTERM"; kill -TERM "$pid"; }
      fi
    fi
  done
  [ "$ONCE" = 1 ] && break
  sleep 120
done
say "watchdog-b end"
