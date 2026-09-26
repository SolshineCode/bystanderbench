#!/bin/bash
# check_balance.sh — one-shot real OpenRouter balance check. Quick manual "how
# much is actually left right now" command; see spend_watchdog.sh for the
# continuous version that runs automatically alongside any paid batch.
set -uo pipefail
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "OPENROUTER_API_KEY not set." >&2; exit 1
fi
curl -s "https://openrouter.ai/api/v1/credits" -H "Authorization: Bearer $OPENROUTER_API_KEY" | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)['data']
total, used = d['total_credits'], d['total_usage']
remaining = total - used
ts = datetime.datetime.now().isoformat(timespec='seconds')
print(f'[{ts}] total=\${total:.3f} used=\${used:.3f} remaining=\${remaining:.3f}')
if remaining < 1.00:
    print('  ** LOW BALANCE ** -- a paid run_eval_openrouter.py launch will refuse below \$1.00')
"
