#!/bin/bash
# retry_push.sh <kernel-slug> -- push a moe-floor kernel when a Kaggle slot frees
set -uo pipefail
cd /home/darkstar/bluedot-unit2-impossiblebench
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
SLUG="$1"
for i in $(seq 1 60); do
    out=$(~/.kaggle/cli-venv/bin/kaggle kernels push -p "moe-floor/kernels/$SLUG" --accelerator NvidiaTeslaT4 2>&1 | tail -1)
    case "$out" in
        *successfully*) echo "RETRY_PUSHED $SLUG: $out"; exit 0;;
        *Maximum*) sleep 600;;
        *) echo "RETRY_PUSH_ERROR $SLUG: $out"; sleep 900;;
    esac
done
echo "RETRY_PUSH_GAVE_UP $SLUG"
