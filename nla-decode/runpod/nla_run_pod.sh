#!/bin/bash
# Runs ON THE POD after the bystander cell + pod extraction. llama-server must be stopped first
# (AV bf16 ~24 GB + base 4-bit ~8 GB do not fit beside the 18 GB server on a 48 GB A40).
cd /workspace; export HF_HOME=/workspace/hf NLA_WORK=/workspace/nla_out
echo "=== NLA v4 pod run start $(date -Is) ==="; nvidia-smi --query-gpu=memory.used --format=csv,noheader
pgrep -x llama-server >/dev/null && { echo "ABORT: llama-server still running"; exit 2; }
python /workspace/nla_decode_v4_pod.py; echo "nla rc=$?"
ls -la /workspace/nla_out | head; echo "=== NLA v4 pod run done $(date -Is) ==="
