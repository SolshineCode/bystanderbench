#!/bin/bash
# run_or_paid.sh — PAID OpenRouter runs. Separate from run_or_free_sweep.sh on purpose:
# that script asserts every model id ends in ":free" and that assertion must never be
# weakened to let paid work through.
#
# Approved by Caleb 2026-09-10 for a specific four-model set. Standing rule otherwise:
# no paid launch without an explicit per-launch go-ahead in that session.
#
# Safety here is the 2026-09-06 incident written down: five concurrent batches at
# --max-connections 20, no smoke test, ~82 docker sandboxes, load average 27, and $5.67
# burned on timeout-corrupted attempts rather than model behaviour. Then a kill on the
# parent was reported as "stopped" while a child kept spending for 2.5 more hours.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL="${MODEL:?set MODEL to a paid OpenRouter id}"
EPOCHS="${EPOCHS:?set EPOCHS}"
ARM="${ARM:-blatant_wrongdoing}"
TA="${TA:?set TA (tool_probe first, then with_tool)}"
MIN_BALANCE="${MIN_BALANCE:-1.00}"

case "$MODEL" in
  *:free) echo "REFUSING: $MODEL is a free model; use run_or_free_sweep.sh"; exit 2 ;;
esac

# Pre-flight balance. The pre-run check is what caught an empty account earlier today
# before any setup was wasted; it refuses rather than warns.
BAL=$(CRASH_RISK_ACK=1 ~/research-pt113/bin/python - <<'PY'
import os, json, urllib.request
k=os.environ["OPENROUTER_API_KEY"]
d=json.load(urllib.request.urlopen(urllib.request.Request(
    "https://openrouter.ai/api/v1/credits", headers={"Authorization":f"Bearer {k}"}), timeout=30))["data"]
print("%.4f" % (d.get("total_credits",0)-d.get("total_usage",0)))
PY
)
echo "[balance] \$$BAL remaining (floor \$$MIN_BALANCE)"
awk -v b="$BAL" -v m="$MIN_BALANCE" 'BEGIN{exit !(b+0 < m+0)}' && {
    echo "REFUSING: balance \$$BAL is below the \$$MIN_BALANCE floor."; exit 3; }

SLUG=$(echo "$MODEL" | tr '/:.' '---')
LABEL="orpaid-${TA}-${SLUG}"
echo "=== PAID $MODEL | arm=$ARM tool_arm=$TA epochs=$EPOCHS ($(date)) ==="
echo "    load before: $(uptime | sed 's/.*load/load/')  docker: $(docker ps -q | wc -l)"

MODEL="openrouter/$MODEL" EPOCHS="$EPOCHS" ARMS="$ARM" TOOL_ARMS="$TA" \
  LABEL="$LABEL" MAX_CONNECTIONS=1 \
  bash bystander/run_bench.sh 2>&1 | grep -E "alerted|cover_task_passed|discovered_content|Error|error" | head -8

AFTER=$(CRASH_RISK_ACK=1 ~/research-pt113/bin/python - <<'PY'
import os, json, urllib.request
k=os.environ["OPENROUTER_API_KEY"]
d=json.load(urllib.request.urlopen(urllib.request.Request(
    "https://openrouter.ai/api/v1/credits", headers={"Authorization":f"Bearer {k}"}), timeout=30))["data"]
print("%.4f" % (d.get("total_credits",0)-d.get("total_usage",0)))
PY
)
echo "    load after:  $(uptime | sed 's/.*load/load/')  docker: $(docker ps -q | wc -l)"
awk -v a="$BAL" -v b="$AFTER" -v n="$EPOCHS" 'BEGIN{
    printf "[spend] before $%.4f  after $%.4f  used $%.4f  = $%.4f/episode\n", a, b, a-b, (a-b)/n }'
