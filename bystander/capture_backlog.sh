#!/bin/bash
# Retroactively capture activations for every completed BystanderBench run that predates
# capture_activations.py, per the standing rule in CLAUDE.md (capture on every inference
# run). Waits for any in-flight extraction to finish, then does the qwen runs in one
# server session and the nemotron run in another, since capture must replay through the
# SAME model that produced the episodes.
set -uo pipefail
# Repo root from this script's own location, never an absolute path: the GGUFs these
# scripts serve are public Hugging Face downloads, so tier 2 is portable to anyone who
# fetches them -- the only thing that was stopping that was this line (2026-09-12).
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Where the public GGUFs live; override for any other layout.
GGUF_DIR="${GGUF_DIR:-$HOME/gguf-downloads}"
cd "$BASE"
# llama-server: honour LLAMA_SERVER, else take it from PATH, else the author's build.
BIN="${LLAMA_SERVER:-$(command -v llama-server || echo "$HOME/llama.cpp/build/bin/llama-server")}"
EXTRACT="$BASE/concealment-probe/tools/extract_resid"

# wait for the in-flight extraction to release the card
while pgrep -x extract_resid >/dev/null 2>&1; do sleep 30; done

run_model () {
    local tag="$1" gguf="$2" layers="$3" eos="$4"; shift 4
    local out="bystander/acts_$tag"
    echo "=== $tag: $* ==="
    CUDA_VISIBLE_DEVICES=0 nohup "$BIN" --model "$gguf" --host 127.0.0.1 --port 8089 \
        -ngl 999 -c 32768 -np 1 --no-webui --jinja --cache-type-k q8_0 --cache-type-v q8_0 \
        --flash-attn on > "llamacpp_logs/capture_${tag}.log" 2>&1 &
    local SPID=$!
    for t in $(seq 1 60); do
        curl -sf -m 3 http://127.0.0.1:8089/health 2>/dev/null | grep -q ok && break; sleep 10
    done
    if ! curl -sf -m 3 http://127.0.0.1:8089/health 2>/dev/null | grep -q ok; then
        echo "$tag: server never came up"; kill $SPID 2>/dev/null; return 1
    fi
    local args=(); for d in "$@"; do args+=(--logdir "$d"); done
    "$BASE/.venv/bin/python" bystander/capture_activations.py --port 8089 \
        --eos "$eos" --out-dir "$out" "${args[@]}" 2>&1 | tail -3
    kill $SPID 2>/dev/null; sleep 8
    if [[ -s "$out/manifest.tsv" ]]; then
        mkdir -p "$out/acts"
        # §F156: record what we ASKED for, from the same variable we pass, so
        # check_layers.py can refuse a silently-shortened layer list. extract_resid drops
        # layers whose tensor names it does not see and reports only what it wrote.
        printf '%s\n' "$layers" > "$out/requested_layers.txt"
        RESID_MANIFEST="$out/manifest.tsv" RESID_LAYERS="$layers" CUDA_VISIBLE_DEVICES=0 \
            "$EXTRACT" -m "$gguf" -c 32768 -b 1024 --cache-type-k q8_0 --cache-type-v q8_0 \
            --flash-attn on > "$out/extract.log" 2>&1
        echo "$tag: $(ls "$out"/acts/*.bin 2>/dev/null | wc -l) bins"
        "$BASE/.venv/bin/python" "$BASE/bystander/check_layers.py" "$out" \
            || echo "$tag: CHECK_LAYERS REFUSED -- see above" >&2
    fi
}

run_model qwen_backlog "$BASE/gguf/qwen3.5-27b.gguf" 4,8,16,24,32,40,48,56 "<|im_end|>" \
    logs/bystander-pilot-qwen35-27b logs/bystander-toolprobe-qwen35-27b \
    logs/bystander-blatant-qwen35-27b logs/bystander-smoke-qwen35-27b

run_model nemotron_floor \
    "${NEMOTRON_GGUF:-$GGUF_DIR/nemotron-35-lightning/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf}" \
    4,8,16,24,32,40,48 "<|im_end|>" logs/bystander-floor-nemotron

echo "=== backlog capture complete ($(date)) ==="
