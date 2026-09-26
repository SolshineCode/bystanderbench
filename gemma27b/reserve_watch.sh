#!/bin/bash
# reserve_watch.sh <reservation-id> <pid> -- keep a gpusched reservation alive
# while <pid> runs; release the moment it exits. Extends 1h when <45min remain.
set -uo pipefail
RESID="$1"; PID="$2"
while kill -0 "$PID" 2>/dev/null; do
    line=$(~/bin/gpusched status 2>/dev/null | grep "$RESID" || true)
    end=$(grep -oE "until [0-9T:-]+" <<<"$line" | awk '{print $2}')
    if [ -n "$end" ]; then
        rem=$(( $(date -d "$end" +%s) - $(date +%s) ))
        if [ "$rem" -lt 2700 ]; then
            ~/bin/gpusched extend "$RESID" 1h && echo "EXTENDED $RESID (+1h, was ${rem}s left)" \
                || echo "EXTEND_REFUSED $RESID (${rem}s left) -- someone queued behind; finishing in window"
        fi
    else
        echo "RESERVATION_GONE $RESID while pid $PID still alive"
    fi
    sleep 600
done
~/bin/gpusched release "$RESID" && echo "RELEASED $RESID (pid $PID exited)"
