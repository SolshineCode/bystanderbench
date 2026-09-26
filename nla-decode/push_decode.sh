#!/bin/bash
# push_decode.sh — inject HF token into a temp copy of the decode kernel and push.
set -euo pipefail
SRC=/home/darkstar/bluedot-unit2-impossiblebench/nla-decode/kernels/nla-decode-gemma12b-20260905
TMP=$(mktemp -d)
cp "$SRC/kernel-metadata.json" "$TMP/"
TOKEN=$(grep -oP '^HF_AGENT_TOKEN=\K.*' ~/.hermes/.env)
sed "s|INJECT_HF_TOKEN|$TOKEN|" "$SRC/script.py" > "$TMP/script.py"
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
~/.kaggle/cli-venv/bin/kaggle kernels push -p "$TMP" --accelerator NvidiaTeslaT4
rm -rf "$TMP"
