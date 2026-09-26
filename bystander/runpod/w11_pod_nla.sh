#!/bin/bash
# W11 stage 3 (2026-09-15): NLA v4 (bf16 AV) on the pod after POD EXTRACT DONE; results back to
# nla-decode/results/runpod-2026-09-15/. Pod is NOT terminated here (I verify artifacts first).
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; J=/home/darkstar/.claude/jobs/8bfa76b1/tmp
SSH="ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95"
until grep -q "POD EXTRACT DONE" $J/w11_pod_extract.log; do sleep 60; done
echo "=== NLA stage start $(date) ==="
$SSH 'nohup /workspace/nla_run_pod.sh > /workspace/nla_run.log 2>&1 < /dev/null & echo "nla pid $!"'
until $SSH 'grep -qE "NLA v4 pod run done|nla rc=" /workspace/nla_run.log' 2>/dev/null; do sleep 90; done
$SSH 'grep -E "rc=|ABORT|Traceback|DONE|control|VRAM|AV_QUANT" /workspace/nla_run.log | tail -12'
R=$BASE/nla-decode/results/runpod-2026-09-15; mkdir -p "$R"
scp -q -i $HOME/.ssh/id_ed25519 -P 22083 -o StrictHostKeyChecking=no -o BatchMode=yes "root@69.30.85.95:/workspace/nla_out/*" "$R/" ; scp -q -i $HOME/.ssh/id_ed25519 -P 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95:/workspace/nla_run.log "$R/nla_run.log"
ls -la "$R"; echo "=== NLA STAGE DONE $(date) ==="
