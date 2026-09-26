#!/bin/bash
# Runs ON THE POD (00jz5m3ou6z00i, A40). Builds llama.cpp (CUDA) + libcommon + extract_resid,
# downloads bartowski's gemma-3-27b-it Q4_K_M, serves on 0.0.0.0:8080 with --no-prefill-assistant
# (fresh builds default prefill ON and 400 the capture prefixes, F: 2026-09-14 S10).
set -uo pipefail
exec > >(tee -a /workspace/setup.log) 2>&1
echo "=== setup start $(date -Is) ==="; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
export DEBIAN_FRONTEND=noninteractive PATH=/usr/local/cuda/bin:$PATH
command -v cmake >/dev/null || { apt-get update -qq && apt-get install -y -qq cmake git curl >/dev/null; }
cd /workspace
[ -d llama.cpp ] || git clone -q --depth 1 https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
if [ ! -x build/bin/llama-server ]; then
  cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_CURL=ON -DBUILD_SHARED_LIBS=ON >/dev/null 2>&1 || cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DBUILD_SHARED_LIBS=ON
  cmake --build build --config Release -j "$(nproc)" --target llama-server llama-tokenize common 2>&1 | tail -3
fi
echo "llama-server: $(./build/bin/llama-server --version 2>&1 | head -1)"
if [ -f /workspace/extract_resid.cpp ] && [ ! -x /workspace/extract_resid ]; then
  LC=$(find build -name "libcommon*" | head -1); echo "libcommon: ${LC:-none}"
  g++ -O2 -std=c++17 /workspace/extract_resid.cpp -I include -I ggml/include -I common -I build -L build/bin -L build/src -L build/ggml/src -L build/common \
      -lllama -lggml -lggml-base -lcommon -o /workspace/extract_resid -Wl,-rpath,/workspace/llama.cpp/build/bin 2>&1 | tail -5
  [ -x /workspace/extract_resid ] && echo "extract_resid built OK" || echo "extract_resid build FAILED (extraction falls back to local)"
fi
cd /workspace
G=google_gemma-3-27b-it-Q4_K_M.gguf
if [ ! -f "$G" ]; then
  curl -L -C - --retry 8 --retry-delay 15 --retry-all-errors -o "$G.part" \
    "https://huggingface.co/bartowski/google_gemma-3-27b-it-GGUF/resolve/main/$G" && mv "$G.part" "$G"
fi
ls -la --block-size=M "$G"; sha256sum "$G" > "$G.sha256" &
nohup /workspace/llama.cpp/build/bin/llama-server --model "/workspace/$G" --host 0.0.0.0 --port 8080 \
  -ngl 999 -c 32768 -np 1 --no-webui --no-prefill-assistant --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on \
  > /workspace/server.log 2>&1 &
echo "server pid $!"
for t in $(seq 1 90); do curl -sf -m 3 http://127.0.0.1:8080/health 2>/dev/null | grep -q ok && break; sleep 10; done
curl -sf -m 3 http://127.0.0.1:8080/health; echo; grep -o "n_ctx_slot *= *[0-9]*" /workspace/server.log | tail -1
echo "=== setup done $(date -Is) ==="
