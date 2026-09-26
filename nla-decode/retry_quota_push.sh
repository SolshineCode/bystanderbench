#!/bin/bash
# retry_quota_push.sh — retry-push both new NLA kernels (corrected local decode +
# steering calibration) until Kaggle's weekly GPU quota frees up. Checks every
# 10 min; no hard cutoff since we don't know the exact weekly reset time from
# here and each check is a cheap API call -- kill manually (pkill -f
# retry_quota_push.sh) if it's no longer needed.
set -uo pipefail
cd /home/darkstar/bluedot-unit2-impossiblebench
K=~/.kaggle/cli-venv/bin/kaggle
KERNELS=(
  "nla-decode/kernels/nla-decode-gemma12b-local-20260906"
  "nla-decode/kernels/nla-steer-gemma12b-20260906"
)
DONE=()
while true; do
    for kdir in "${KERNELS[@]}"; do
        if [[ " ${DONE[*]} " == *" $kdir "* ]]; then continue; fi
        out=$("$K" kernels push -p "$kdir" --accelerator NvidiaTeslaT4 2>&1 | tail -1)
        echo "[$(date +%T)] $kdir -> $out"
        case "$out" in
            *successfully*) DONE+=("$kdir");;
        esac
    done
    if [ "${#DONE[@]}" -eq "${#KERNELS[@]}" ]; then
        echo "ALL_KERNELS_PUSHED"
        exit 0
    fi
    sleep 600
done
