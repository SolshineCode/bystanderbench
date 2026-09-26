#!/bin/bash
# collect_results.sh <slug> — download a finished recruiter-trial kernel's outputs
# and run the pilot first-look analysis.
set -euo pipefail
SLUG="$1"
HERE=/home/darkstar/bluedot-unit2-impossiblebench/recruiter-trial
OUT="$HERE/results/$SLUG"
mkdir -p "$OUT"
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
~/.kaggle/cli-venv/bin/kaggle kernels output "calebdeleeuw/$SLUG" -p "$OUT"
echo "=== first-look analysis: $SLUG ==="
python3 "$HERE/analyze_pilot.py" "$OUT"
