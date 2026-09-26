#!/bin/bash
# run_or_free_sweep.sh — tier-1 sweep across FREE OpenRouter models.
#
# Caleb approved FREE OpenRouter only (2026-09-10). Every model id here MUST end in
# ":free"; the guard below refuses anything else, because this account is spend-capable
# (is_free_tier=false) and a dropped suffix would bill real money.
#
# Tier 1 only: behavioural, no serving, no activation capture. Sequential by design --
# MAX_CONNECTIONS=1 and one model at a time, both to respect upstream free-tier rate
# limits and because the 2026-09-06 incident was caused by concurrent batches, not by any
# individual piece being unsafe.
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS=(
  "${ONLY_MODELS:-nvidia/nemotron-3.5-lightning:free}"
)
# Default set, overridable with ONLY_MODELS for a targeted sweep.
if [[ -z "${ONLY_MODELS:-}" ]]; then
MODELS=(
  "nvidia/nemotron-3.5-lightning:free"
  "nvidia/nemotron-3-super-120b-a12b:free"
  "inclusionai/ling-3.0-flash-vl:free"
  "nex-agi/nex-n2.5-mini:free"
  "nex-agi/nex-n2.5-pro:free"
  "dots-studio/dots-3-note-preview:free"
)
else
  read -r -a MODELS <<< "$ONLY_MODELS"
fi
ARMS_LIST="${ARMS_LIST:-blatant_wrongdoing}"
TA="${TA:-tool_probe}"
EP="${EP:-4}"
for m in "${MODELS[@]}"; do
    case "$m" in
        *:free) ;;
        *) echo "REFUSING non-free model: $m"; exit 2 ;;
    esac
    slug=$(echo "$m" | tr '/:' '--')
    echo "=== $m  arm=$ARMS_LIST tool_arm=$TA epochs=$EP ($(date)) ==="
    MODEL="openrouter/$m" EPOCHS="$EP" ARMS="$ARMS_LIST" TOOL_ARMS="$TA" \
      LABEL="or-${TA}-${slug}" MAX_CONNECTIONS=1 \
      bash bystander/run_bench.sh 2>&1 | grep -E "alerted|cover_task_passed|discovered_content|Error|error" | head -6
    sleep 20
done
echo "SWEEP DONE ($(date))"
