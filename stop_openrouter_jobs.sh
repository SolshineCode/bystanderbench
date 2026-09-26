#!/bin/bash
# stop_openrouter_jobs.sh — reliably stop every run_eval_openrouter.py instance
# and its descendants, and PROVE it (never just report success on a kill exit
# code, which is exactly what went wrong on 2026-09-06: a parent-process kill
# didn't propagate to the actual Python worker, which kept running and
# spending for 2.5 unnoticed hours).
#
# Mechanism: run_eval_openrouter.py calls os.setpgrp() at startup, making it
# (and everything it spawns -- docker-compose, sandboxes) the leader of its own
# process group regardless of how it was launched. `kill -- -PGID` (negative
# PGID) signals the whole group at once, not just one PID.
set -uo pipefail

echo "=== finding live run_eval_openrouter.py processes ==="
PIDS=$(pgrep -f "run_eval_openrouter.py" 2>/dev/null)
if [ -z "$PIDS" ]; then
    echo "none found via pgrep."
else
    for pid in $PIDS; do
        pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')
        if [ -n "$pgid" ]; then
            echo "killing process group $pgid (pid $pid was a member)"
            kill -- -"$pgid" 2>&1
            sleep 1
            kill -9 -- -"$pgid" 2>&1
        fi
    done
fi

echo "=== also sweeping any docker-compose/inspect stragglers by name ==="
pkill -9 -f "run_eval_openrouter\|run_eval_gpu\|docker-compose.*inspect-lcb" 2>&1

echo "=== clearing inspect-tool-support sandbox containers ==="
N=$(docker ps -q --filter "ancestor=aisiuk/inspect-tool-support" 2>/dev/null | wc -l)
docker ps -q --filter "ancestor=aisiuk/inspect-tool-support" 2>/dev/null | xargs -r docker kill 2>&1
echo "killed $N container(s)"

sleep 2
echo "=== VERIFICATION (this is the part that was skipped on 2026-09-06) ==="
REMAINING_PROC=$(pgrep -af "run_eval_openrouter.py|run_eval_gpu.py" 2>/dev/null)
REMAINING_DOCKER=$(docker ps -q 2>/dev/null | wc -l)
if [ -n "$REMAINING_PROC" ]; then
    echo "FAILED — still alive:"
    echo "$REMAINING_PROC"
    exit 1
fi
if [ "$REMAINING_DOCKER" -gt 0 ]; then
    echo "FAILED — $REMAINING_DOCKER docker container(s) still running:"
    docker ps
    exit 1
fi
echo "VERIFIED CLEAN: no run_eval_openrouter.py/run_eval_gpu.py process, 0 docker containers."
rm -f /tmp/.run_eval_openrouter_paid.lock
echo "paid-instance lock cleared."
