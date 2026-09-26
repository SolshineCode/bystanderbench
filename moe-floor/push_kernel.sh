#!/bin/bash
# push_kernel.sh <slug> — push one rendered kernel to Kaggle with a T4 request.
set -euo pipefail
SLUG="$1"
HERE=/home/darkstar/bluedot-unit2-impossiblebench/moe-floor
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
~/.kaggle/cli-venv/bin/kaggle kernels push -p "$HERE/kernels/$SLUG" --accelerator NvidiaTeslaT4
echo "pushed $SLUG; poll with: KAGGLE_API_TOKEN=... ~/.kaggle/cli-venv/bin/kaggle kernels status calebdeleeuw/$SLUG"
