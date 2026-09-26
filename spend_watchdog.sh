#!/bin/bash
# spend_watchdog.sh — continuous OpenRouter balance monitoring, launched
# automatically by run_eval_openrouter.py alongside any paid run (2026-09-06,
# after the incident where a paid batch drained the account unnoticed for 2.5
# hours because nothing was watching it while it ran). The pre-flight balance
# check in run_eval_openrouter.py only gates the START of a run -- it can't
# catch a run that goes bad *during* execution. This is the part that does.
#
# Behavior: polls the real balance every POLL_SECONDS, appends a timestamped
# line to logs/spend_watchdog.log every time (so "how much is being spent
# right now" always has a real, current answer, not a guess), and if remaining
# balance drops below CRITICAL, kills every openrouter job via
# stop_openrouter_jobs.sh and exits loudly.
#
# Usage: spend_watchdog.sh [critical_balance_usd] [poll_seconds]
set -uo pipefail
cd "$(dirname "$0")"

CRITICAL="${1:-0.50}"
POLL="${2:-300}"
LOG="logs/spend_watchdog.log"
mkdir -p logs

echo "[$(date -Iseconds)] spend_watchdog started, pid=$$, critical=\$${CRITICAL}, poll=${POLL}s" | tee -a "$LOG"

while true; do
    if [ -z "${OPENROUTER_API_KEY:-}" ]; then
        echo "[$(date -Iseconds)] OPENROUTER_API_KEY not set, cannot check balance" | tee -a "$LOG"
        sleep "$POLL"; continue
    fi
    resp=$(curl -s -m 15 "https://openrouter.ai/api/v1/credits" -H "Authorization: Bearer $OPENROUTER_API_KEY" 2>/dev/null)
    remaining=$(echo "$resp" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)['data']
    print(f\"{d['total_credits'] - d['total_usage']:.4f}\")
except Exception:
    print('ERROR')
" 2>/dev/null)

    if [ "$remaining" = "ERROR" ] || [ -z "$remaining" ]; then
        echo "[$(date -Iseconds)] balance check failed (network/auth) -- will retry" | tee -a "$LOG"
        sleep "$POLL"; continue
    fi

    echo "[$(date -Iseconds)] remaining=\$${remaining}" | tee -a "$LOG"

    below=$(python3 -c "print(1 if float('$remaining') < float('$CRITICAL') else 0)")
    if [ "$below" = "1" ]; then
        echo "[$(date -Iseconds)] ** CRITICAL: \$${remaining} remaining, below \$${CRITICAL} threshold -- STOPPING ALL OPENROUTER JOBS **" | tee -a "$LOG"
        bash stop_openrouter_jobs.sh 2>&1 | tee -a "$LOG"
        echo "[$(date -Iseconds)] spend_watchdog stopped jobs and is exiting" | tee -a "$LOG"
        exit 1
    fi
    sleep "$POLL"
done
