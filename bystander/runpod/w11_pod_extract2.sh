#!/bin/bash
# W11 extraction re-run (2026-09-15 02:15): first run failed 0/18 because manifest paths are absolute local
# paths; fixed with a symlink on the pod (/home/darkstar/bluedot-unit2-impossiblebench -> /workspace/bluedot).
# Waits for the NLA stage to finish (VRAM), then extracts, rsyncs bins back, check_layers --expect.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; J=/home/darkstar/.claude/jobs/8bfa76b1/tmp
SSH="ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95"
LAYERS=4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60; D=bystander/acts_gemma3_27b_pod; cd "$BASE"
until $SSH 'grep -qE "NLA v4 pod run done|nla rc=" /workspace/nla_run.log' 2>/dev/null; do sleep 60; done
echo "=== extract2 start $(date) === $($SSH 'nvidia-smi --query-gpu=memory.used --format=csv,noheader')"
$SSH "cd /workspace/bluedot && RESID_MANIFEST=$D/manifest.tsv RESID_LAYERS=$LAYERS /workspace/extract_resid -m /workspace/google_gemma-3-27b-it-Q4_K_M.gguf -c 32768 -b 1024 --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > /workspace/extract_gemma3_27b_2.log 2>&1; echo extract rc=\$?; grep -E ' done: ' /workspace/extract_gemma3_27b_2.log; ls /workspace/bluedot/$D/acts/*.bin 2>/dev/null | wc -l"
rsync -a -e "ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes" root@69.30.85.95:/workspace/bluedot/$D/acts/ "$D/acts/" && echo "bins back: $(ls $D/acts/*.bin 2>/dev/null | wc -l)"
scp -q -i $HOME/.ssh/id_ed25519 -P 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95:/workspace/extract_gemma3_27b_2.log "$D.extract.log"
source .venv/bin/activate; python bystander/check_layers.py "$D" --expect $LAYERS 2>&1 | head -3; echo "check_layers rc=${PIPESTATUS[0]}"
echo "=== POD EXTRACT2 DONE $(date) ==="
