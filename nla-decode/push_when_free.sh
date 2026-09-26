#!/bin/bash
# retry-push the decode kernel until a Kaggle slot frees (token injected per push)
set -uo pipefail
cd /home/darkstar/bluedot-unit2-impossiblebench
for i in $(seq 1 60); do
    out=$(bash nla-decode/push_decode.sh 2>&1 | tail -1)
    case "$out" in
        *successfully*) echo "DECODE_V4_PUSHED: $out"; exit 0;;
        *Maximum*) sleep 600;;
        *) echo "DECODE_PUSH_ERROR: $out"; sleep 900;;
    esac
done
echo "DECODE_PUSH_GAVE_UP"
