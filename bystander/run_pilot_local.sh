#!/bin/bash
# run_pilot_local.sh — small real pilot of the §20 benchmark on ONE local llama-server:
# every (arm × tool_arm) cell, EPOCHS episodes each, sequentially (one docker sandbox at a
# time). Run ONLY after run_smoke_local.sh has passed on the same model (smoke-before-scale).
# Env: GPU (0), PORT (8099), GGUF, CTX (32768), EPOCHS (3), LABEL, ARMS, TOOL_ARMS,
#      REASONING_FORMAT (none). Set to `deepseek-legacy` to expose chain of thought: it
#      keeps <think> blocks inside message.content, which matters because with thoughts in
#      a separate field the assistant turn has EMPTY content and llama.cpp rejects the next
#      request with `item['content'] is empty`, killing the agent loop (same failure shape
#      as §F50). The scorer strips <think> before the visible-prose screen and scores it
#      separately as considered_in_reasoning: reasoning about reporting is NOT reporting.
#      NEVER edit this file while it is executing (§F49): bash reads scripts incrementally
#      and an insertion shifts byte offsets under the running interpreter.
set -uo pipefail
# Repo root from this script's own location, never an absolute path: the GGUFs these
# scripts serve are public Hugging Face downloads, so tier 2 is portable to anyone who
# fetches them -- the only thing that was stopping that was this line (2026-09-12).
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GPU="${GPU:-0}"; PORT="${PORT:-8099}"; CTX="${CTX:-32768}"; EPOCHS="${EPOCHS:-3}"
GGUF="${GGUF:-$BASE/gguf/qwen3.5-27b.gguf}"
# llama-server: honour LLAMA_SERVER, else take it from PATH, else the author's build.
BIN="${LLAMA_SERVER:-$(command -v llama-server || echo "$HOME/llama.cpp/build/bin/llama-server")}"
LABEL="${LABEL:-bystander-pilot-qwen35-27b}"
# Reasoning: default reproduces every prior run (`--reasoning off`) so results stay
# comparable. REASONING_FORMAT=none turns CoT ON -- verified against the live API:
#   none            -> content holds `<think>...`, reasoning_content empty  (loop WORKS)
#   deepseek-legacy -> content EMPTY, reasoning_content set                 (loop DIES,
#                      llama.cpp 400 `item['content'] is empty`, same shape as §F50)
# The flag help reads the other way round, so this was established by calling the API.
if [[ -n "${REASONING_FORMAT:-}" ]]; then
    REASONING_ARGS="--reasoning-format ${REASONING_FORMAT}"
else
    REASONING_ARGS="--reasoning off"
fi
# THINKING BUDGET (2026-09-12, §F123). `--reasoning off` does NOT stop a hybrid model from
# thinking; it only controls whether the tags are parsed out. On the ImpossibleBench coding
# task nex-n2.5-mini ran a single generation to 27,153 tokens under `--reasoning off` and
# would have filled the whole 32K window. `--reasoning-budget 0` ends thinking immediately
# and took the same episode from hours to about three minutes. Left UNSET by default so every
# bystander result before this date reproduces exactly; set REASONING_BUDGET=0 for any new run
# on a hybrid model, and expect a bare `</think>` prefix in the output (which
# screen_behavioral.visible_part's LOOSE_THINK already strips).
[[ -n "${REASONING_BUDGET:-}" ]] && REASONING_ARGS="$REASONING_ARGS --reasoning-budget ${REASONING_BUDGET}"
ARMS="${ARMS:-conspiracy_realistic conspiracy_transposed benign_anomaly}"
# AFFORDANCE / SOLVER_KIND (2026-09-10, §F61/§F62). Defaults reproduce every result
# before that date exactly. "cli" exposes the escalation channel as an ops-escalate
# binary instead of a tool; "prompted" removes tool calls from the loop entirely, for
# models whose chat template has no tool support (gemma-3-12b-it's has none at all).
# prompted REQUIRES cli and the task refuses the other combination. Never pool across
# either dimension -- each needs its own tool_probe floor.
AFFORDANCE="${AFFORDANCE:-native}"
SOLVER_KIND="${SOLVER_KIND:-tools}"
TOOL_ARMS="${TOOL_ARMS:-with_tool no_tool}"
# FAIL_ON_ERROR (2026-09-11, see FINDINGS). Inspect's default aborts the whole task on the
# FIRST sample error, so one episode that walks past the 32768-token window takes every
# completed sibling down with it: 8 episodes lost on `scale-d`, 3 more on the incident-3
# floor, both at exactly n_prompt_tokens=32792. `report.py` then discards the errored log
# whole, so the loss is total rather than partial. A threshold keeps the survivors and still
# fails the run when the errors are systemic rather than incidental.
#
# This changes NOTHING any episode sees -- not the environment, prompt, tools, model or
# scorer -- only whether completed siblings are thrown away. The erroring episode is absent
# either way. Retained episodes are drawn identically to every episode already in the v1.0
# corpus, so the estimand is unaffected and old and new cells stay comparable.
#
# DEFAULT IS EMPTY so every command run before 2026-09-11 reproduces byte-for-byte. New runs
# pass FAIL_ON_ERROR=0.34 explicitly.
FOE_ARG=""
if [[ -n "${FAIL_ON_ERROR:-}" ]]; then FOE_ARG="--fail-on-error ${FAIL_ON_ERROR}"; fi
# MAX_RETRIES (2026-09-23, AUTONOMOUS DRAFT, §F214/§F215). Inspect retries a failing model call
# WITHOUT LIMIT by default, and `--timeout` did not bound it: on 2026-09-22 one E-06 episode
# re-sent a JSON-malformed tool call to a deterministic 500 for 1h50m. With a cap the episode
# errors out and FAIL_ON_ERROR keeps its siblings. DEFAULT EMPTY = byte-identical to every prior run.
if [[ -n "${MAX_RETRIES:-}" ]]; then FOE_ARG="$FOE_ARG --max-retries ${MAX_RETRIES}"; fi
cd "$BASE"; source .venv/bin/activate
bash tools/require_reservation.sh bystander "$GPU" || exit 3
ss -tln | grep -q ":$PORT " && { echo "REFUSING: port $PORT in use"; exit 4; }
LOG="llamacpp_logs/bystander_${LABEL}_server.log"
# --jinja exists to parse TOOL CALLS out of the model's chat template. The prompted
# solver uses no tool schema at all, and demanding a tool-capable template for it
# reintroduces exactly the exclusion that solver was built to remove: olmo-3-7b-instruct's
# template calls `tools | tojson` unconditionally, llama.cpp validates the template at
# STARTUP, and the server refuses to boot -- for a run that would never have sent a tool.
# So prompted mode drops it. Same lesson as the CLI affordance: a fix has to go all the
# way down the stack or it only moves the blocker.
JINJA_ARG="--jinja"
if [[ "$SOLVER_KIND" == "prompted" ]]; then JINJA_ARG=""; fi
# CHAT_TEMPLATE override. Dropping --jinja is not enough on its own: llama.cpp parses the
# GGUF's embedded template at STARTUP either way, so a template whose tool branch it cannot
# evaluate stops the server booting even for a run that will never send a tool.
# olmo-3-7b-instruct is the case -- `tools | tojson` on an Undefined `tools`.
#
# Setting CHAT_TEMPLATE=chatml bypasses the embedded template entirely. Only do this when
# the model's NATIVE format is verified to match: olmo-3's own template uses
# <|im_start|>/<|im_end|>, i.e. it IS chatml, so this serves it correctly rather than
# approximately. Record the override with any result -- a model served under a template
# that is not its own is not the same measurement.
TPL_ARG=""
if [[ -n "${CHAT_TEMPLATE:-}" ]]; then TPL_ARG="--chat-template ${CHAT_TEMPLATE}"; fi
# EXTRA_ARGS (2026-09-21, §F208). Extra llama-server flags, appended verbatim. DEFAULT IS
# EMPTY so every command run before this date reproduces byte-for-byte. It exists for the
# control-vector steering arms (`--control-vector-scaled FILE:SCALE
# --control-vector-layer-range L L`), which are the causal test of the frozen §F200 direction.
# Anything passed here changes the served model, so a run that uses it is a NEW cell with its
# own affordance floor and competence gate -- never pooled with the unsteered cell.
CUDA_VISIBLE_DEVICES="$GPU" nohup "$BIN" --model "$GGUF" --host 127.0.0.1 --port "$PORT" \
    -ngl 999 -c "$CTX" -np 1 --no-webui ${JINJA_ARG} ${TPL_ARG} ${REASONING_ARGS} \
    ${EXTRA_ARGS:-} \
    --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$LOG" 2>&1 &
SPID=$!; echo "$SPID" > bystander/server.pid
for t in $(seq 1 90); do kill -0 $SPID 2>/dev/null || { echo "server died:"; tail -5 "$LOG"; exit 1; }
    curl -sf -m 5 "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break; sleep 10; done
echo "SERVER_READY port=$PORT pid=$SPID gpu=$GPU ctx=$CTX gguf=$(basename "$GGUF") ($(date))"
# A guard must check the thing it claims to check (CLAUDE.md). llama-server has been observed
# to log `failed to load control vector file` and then serve anyway: an unsteered server
# answering as the steered arm would manufacture a clean null. Refuse instead.
if [[ "${EXTRA_ARGS:-}" == *control-vector* ]]; then
    if grep -qiE "failed to load control vector|no valid control vector|control vector n_embd does not match" "$LOG"; then
        echo "REFUSING: control vector did NOT load (see $LOG)"; kill $SPID 2>/dev/null; exit 6
    fi
    echo "CONTROL_VECTOR_OK args=${EXTRA_ARGS}"
fi
export OPENAI_BASE_URL="http://127.0.0.1:$PORT/v1" OPENAI_API_KEY="sk-local-llamacpp"
for arm in $ARMS; do for ta in $TOOL_ARMS; do
    echo "=== cell arm=$arm tool_arm=$ta epochs=$EPOCHS ($(date)) ==="
    # --max-tool-output caps a single tool result (T3, viability review 2026-09-09):
    # an uncapped `cat ci/logs/*.log` can eat the 32k window and end the episode before
    # the decision point, which scores as a zero that never happened.
    inspect eval bystander/task.py -T arm="$arm" -T tool_arm="$ta" -T epochs="$EPOCHS" \
        -T affordance="$AFFORDANCE" -T solver_kind="$SOLVER_KIND" \
        -T model_id="$(basename "$GGUF")" \
        --model openai/local-model --log-dir "logs/$LABEL" --max-connections 1 \
        --max-tool-output "${MAX_TOOL_OUTPUT:-16000}" ${FOE_ARG} \
        -M client_timeout=2400 --timeout 4800 2>&1 | grep -E "error|Error|Traceback|total time|samples" | tail -4
    echo "    load: $(uptime | sed 's/.*load/load/'); docker: $(docker ps -q | wc -l)"
done; done
echo "=== pilot done ($(date)) ==="
python3 bystander/summarize.py "logs/$LABEL"
kill $SPID 2>/dev/null; sleep 5; kill -9 $SPID 2>/dev/null; rm -f bystander/server.pid; echo "server stopped"
