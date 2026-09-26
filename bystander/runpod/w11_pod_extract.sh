#!/bin/bash
# W11 follow-up (2026-09-15): residual extraction for the gemma-3-27b pod cell ON THE POD, against the
# exact bartowski GGUF that generated the text (local file is ggml-org, different build: see
# w11_gguf_provenance.txt). Sequence: W11 CELL DONE -> stop llama-server -> rsync token tree up ->
# extract_resid (relinked 01:12) -> rsync bins back -> check_layers --expect. Never edit while running.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; J=/home/darkstar/.claude/jobs/8bfa76b1/tmp
SSH="ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95"
LAYERS=4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60
D=bystander/acts_gemma3_27b_pod; cd "$BASE"
until grep -q "W11 CELL DONE" $J/w11_pod_gemma3_27b_cell.log; do sleep 60; done
echo "=== pod extract start $(date) === manifest rows: $(wc -l < $D/manifest.tsv)"
$SSH 'pkill -x llama-server; sleep 5; pgrep -x llama-server >/dev/null && { echo "server still up"; exit 2; }; echo "server stopped"; nvidia-smi --query-gpu=memory.used --format=csv,noheader' || exit 2
$SSH "mkdir -p /workspace/bluedot/$D/acts"
rsync -a -e "ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes" --include='*.txt' --include='manifest.tsv' --include='*.meta.json' --exclude='acts/*' "$D/" root@69.30.85.95:/workspace/bluedot/$D/ && echo "tree up: $($SSH "ls /workspace/bluedot/$D/*.txt | wc -l") txt"
echo "$LAYERS" | tr ',' '\n' > $D/requested_layers.txt
$SSH "cd /workspace/bluedot && RESID_MANIFEST=$D/manifest.tsv RESID_LAYERS=$LAYERS /workspace/extract_resid -m /workspace/google_gemma-3-27b-it-Q4_K_M.gguf -c 32768 -b 1024 --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > /workspace/extract_gemma3_27b.log 2>&1; echo extract rc=\$?; grep -c ' wrote ' /workspace/extract_gemma3_27b.log; ls /workspace/bluedot/$D/acts/*.bin | wc -l"
rsync -a -e "ssh -i $HOME/.ssh/id_ed25519 -p 22083 -o StrictHostKeyChecking=no -o BatchMode=yes" root@69.30.85.95:/workspace/bluedot/$D/acts/ "$D/acts/" && echo "bins back: $(ls $D/acts/*.bin | wc -l)"
scp -q -i $HOME/.ssh/id_ed25519 -P 22083 -o StrictHostKeyChecking=no -o BatchMode=yes root@69.30.85.95:/workspace/extract_gemma3_27b.log "$D.extract.log"
source .venv/bin/activate; python bystander/check_layers.py "$D" --expect $LAYERS 2>&1 | head -2; echo "check_layers rc=$?"
echo "=== POD EXTRACT DONE $(date) ==="
