#!/bin/bash
# run_free_screens.sh — sequential behavioral screen of the free-tier small MoE
# coding models (section-14 smallest-cheating-MoE question, cloud/behavioral only).
# One detached process runs all three so a harness-task kill can't strand the batch.
# Slugs verified against the live OpenRouter model list 2026-09-04.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"
source .venv/bin/activate
export OPENROUTER_API_KEY=$(python3 -c "import json; print(json.load(open('/home/darkstar/.claude/settings.json'))['env']['OPENROUTER_API_KEY'])")

# tag|slug
MODELS=(
  "north-mini|cohere/north-mini-code:free"
  "nemotron35-lightning|nvidia/nemotron-3.5-lightning:free"
  "laguna-xs|poolside/laguna-xs-2.1:free"
)

for entry in "${MODELS[@]}"; do
  tag="${entry%%|*}"; slug="${entry##*|}"
  label="moe-free-${tag}-or"
  rm -rf "logs/$label"
  echo "=== SCREEN START $tag ($slug) $(date) ==="
  python3 run_eval_openrouter.py --model "$slug" --label "$label" \
      --splits oneoff,conflicting --limit 25 --max-connections 3 --max-attempts 3
  python3 run_eval_openrouter.py --model "$slug" --label "$label" \
      --splits original --limit 12 --max-connections 3 --max-attempts 3
  echo "=== SCREEN DONE $tag $(date) ==="
done
echo "=== ALL FREE SCREENS DONE $(date) ==="
