#!/bin/bash
# run_smoke_local.sh — first REAL run of the §20 bystander benchmark on a local model.
# Smoke-test-before-scaling (CLAUDE.md): launches one llama-server, verifies (a) a plain
# reply and (b) that the model can actually emit a tool call through llama.cpp's jinja
# handler, then runs ONE sample; scaling is a separate, explicit decision.
# Requires an active gpusched reservation whose session/purpose mentions "bystander" on $GPU.
# Env: GPU (0), PORT (8099), GGUF (gemma-3-12b-it Q4_K_M), CTX (32768), ARM, TOOL_ARM,
#      EPOCHS (1), LABEL (bystander-smoke-<model>)
set -uo pipefail
# Repo root from this script's own location, never an absolute path: the GGUFs these
# scripts serve are public Hugging Face downloads, so tier 2 is portable to anyone who
# fetches them -- the only thing that was stopping that was this line (2026-09-12).
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Where the public GGUFs live; override for any other layout.
GGUF_DIR="${GGUF_DIR:-$HOME/gguf-downloads}"
GPU="${GPU:-0}"; PORT="${PORT:-8099}"; CTX="${CTX:-32768}"
GGUF="${GGUF:-$GGUF_DIR/gemma-3-12b/gemma-3-12b-it-Q4_K_M.gguf}"
# llama-server: honour LLAMA_SERVER, else take it from PATH, else the author's build.
BIN="${LLAMA_SERVER:-$(command -v llama-server || echo "$HOME/llama.cpp/build/bin/llama-server")}"
ARM="${ARM:-conspiracy_realistic}"; TOOL_ARM="${TOOL_ARM:-with_tool}"; EPOCHS="${EPOCHS:-1}"
LABEL="${LABEL:-bystander-smoke-gemma12b}"
cd "$BASE"; source .venv/bin/activate
bash tools/require_reservation.sh bystander "$GPU" || exit 3
ss -tln | grep -q ":$PORT " && { echo "REFUSING: port $PORT in use"; exit 4; }
LOG="llamacpp_logs/bystander_${LABEL}_server.log"
CUDA_VISIBLE_DEVICES="$GPU" nohup "$BIN" --model "$GGUF" --host 127.0.0.1 --port "$PORT" \
    -ngl 999 -c "$CTX" -np 1 --no-webui --jinja --reasoning off \
    ${REASONING_BUDGET:+--reasoning-budget "$REASONING_BUDGET"} \
    --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$LOG" 2>&1 &
SPID=$!; echo "$SPID" > bystander/server.pid
for t in $(seq 1 90); do kill -0 $SPID 2>/dev/null || { echo "server died:"; tail -5 "$LOG"; exit 1; }
    curl -sf -m 5 "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break; sleep 10; done
echo "SERVER_READY port=$PORT pid=$SPID gpu=$GPU ctx=$CTX gguf=$(basename "$GGUF")"
echo "=== smoke 1: plain reply ==="
curl -sf -m 600 "http://127.0.0.1:$PORT/v1/chat/completions" -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Say OK and nothing else."}],"max_tokens":8}' \
  | python3 -c "import json,sys; print('reply:', json.load(sys.stdin)['choices'][0]['message']['content'][:60])" || { echo "plain smoke failed"; kill $SPID; exit 1; }
echo "=== smoke 2: tool call through jinja handler ==="
curl -sf -m 600 "http://127.0.0.1:$PORT/v1/chat/completions" -H 'Content-Type: application/json' -d '{
 "model":"local","max_tokens":200,
 "messages":[{"role":"user","content":"List the files in the current directory using the bash tool."}],
 "tools":[{"type":"function","function":{"name":"bash","description":"Run a bash command","parameters":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}}]
}' | python3 -c "
import json,sys; r=json.load(sys.stdin)['choices'][0]['message']; tc=r.get('tool_calls') or []
print('tool_calls:', [(t['function']['name'], t['function']['arguments'][:60]) for t in tc]); print('content:', (r.get('content') or '')[:120])
sys.exit(0 if tc else 2)" || { echo "TOOL-CALL SMOKE FAILED: model did not emit a tool call; do not run the benchmark on this server"; kill $SPID; exit 2; }
echo "=== inspect eval: arm=$ARM tool_arm=$TOOL_ARM epochs=$EPOCHS ($(date)) ==="
export OPENAI_BASE_URL="http://127.0.0.1:$PORT/v1" OPENAI_API_KEY="sk-local-llamacpp"
inspect eval bystander/task.py -T arm="$ARM" -T tool_arm="$TOOL_ARM" -T epochs="$EPOCHS" \
    --model openai/local-model --log-dir "logs/$LABEL" --max-connections 1 \
    -M client_timeout=2400 --timeout 4800 2>&1 | tail -15
echo "=== done ($(date)); uptime: $(uptime | sed 's/.*load/load/'); docker: $(docker ps -q | wc -l) containers ==="
python3 bystander/summarize.py "logs/$LABEL"
if [ "${KEEP_SERVER:-0}" != "1" ]; then kill $SPID 2>/dev/null; sleep 5; kill -9 $SPID 2>/dev/null; rm -f bystander/server.pid; echo "server stopped"; fi
