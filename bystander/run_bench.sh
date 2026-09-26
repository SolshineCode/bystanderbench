#!/bin/bash
# run_bench.sh — BystanderBench CORE (tier 1): behaviour only, no internals, any model.
#
# The task itself is provider-agnostic; only serving is not. This runner therefore does no
# serving at all and takes any Inspect model string, so the same benchmark runs against a
# hosted API model and a locally-served open-weight one without changing the environment,
# the scorer, or the metrics.
#
#   MODEL=anthropic/claude-sonnet-4-5        bash bystander/run_bench.sh
#   MODEL=openai/gpt-4o                      bash bystander/run_bench.sh
#   MODEL=openrouter/qwen/qwen3.5-27b        bash bystander/run_bench.sh
#   MODEL=openai/local-model OPENAI_BASE_URL=http://127.0.0.1:8099/v1 \
#     OPENAI_API_KEY=sk-local bash bystander/run_bench.sh      # local llama-server
#
# Env: MODEL (required), EPOCHS (12), ARMS, TOOL_ARMS, AFFORDANCE (native|cli),
#      SOLVER_KIND (tools|prompted),
#      LABEL, MAX_CONNECTIONS (1),
#      MAX_TOOL_OUTPUT (16000).
#
# PRECONDITION: the model must sustain a MULTI-TURN tool loop, not merely emit one tool
# call. Screen it first with `bystander/tool_loop_smoke.py` — north-mini-code passes a
# single-turn check and then fails every sample instantly (§F50). For a hosted model,
# point the screen at the provider's OpenAI-compatible endpoint.
#
# Requires Docker for the sandbox. Costs real money against a paid API; this project's
# standing rule is no paid launch without explicit per-launch approval.
set -euo pipefail
# -e matters here specifically: `inspect eval ... | grep ...` hides the eval's exit status
# behind grep's, so without PIPESTATUS a failed run looks like a quiet one and the script
# carries on to the next cell. That is the failure mode that produces an INACCURATE number
# rather than no number, which is worse (§F102 B).
# Repo root is derived from this script's own location, not hardcoded: the previous
# absolute /home/darkstar/... path meant tier 1 could not run for anyone who cloned the
# repo anywhere else, which defeats the point of tier 1 being the portable tier.
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
# Activate a venv only if one is present; a user with inspect_ai already on PATH is fine.
if [[ -f .venv/bin/activate ]]; then source .venv/bin/activate; fi
command -v inspect >/dev/null 2>&1 || {
    echo "ERROR: 'inspect' not on PATH. Install inspect_ai (pip install inspect-ai) or"
    echo "activate the environment that has it, then re-run."; exit 1; }
docker info >/dev/null 2>&1 || {
    echo "ERROR: docker is not available. BystanderBench runs each episode in a docker"
    echo "sandbox; start docker (or grant access) and re-run."; exit 1; }
: "${MODEL:?set MODEL to an Inspect model string, e.g. anthropic/claude-sonnet-4-5}"
EPOCHS="${EPOCHS:-12}"
ARMS="${ARMS:-conspiracy_realistic conspiracy_transposed benign_anomaly blatant_wrongdoing}"
# tool_probe FIRST and BY DEFAULT (2026-09-12). report.py REFUSES every cell that has no
# passing tool_probe floor for its (model, mode), so the previous default of
# "with_tool no_tool" produced a report in which EVERY line said REFUSED — after spending a
# full paid run. The README was corrected on 2026-09-11 and this script was not, which is
# documenting around a defect rather than fixing it: an outsider runs the script.
# no_tool is dropped from the default because report.py refuses it outright (§F107): it
# withholds the escalation channel, so `alerted` there is a structural zero, not a result.
TOOL_ARMS="${TOOL_ARMS:-tool_probe with_tool}"
# AFFORDANCE (2026-09-10): "native" = an alert_oversight tool call, "cli" = an
# ops-escalate executable the model reaches with bash. Use "cli" for any model whose
# chat template lacks a working tool-call grammar -- gemma-3-12b-it, north-mini-code and
# olmo-3-7b-instruct all failed the native screen for template reasons, not behavioural
# ones (§F50/§F51). Never pool results across affordances, and run the tool_probe floor
# under the affordance you intend to measure with.
AFFORDANCE="${AFFORDANCE:-native}"
# SOLVER_KIND (2026-09-10): "tools" = Inspect basic_agent (chat-template tool calls),
# "prompted" = text protocol, for models whose template has no tool support at all
# (gemma-3-12b-it's contains no tools/tool_calls/function -- verified in the GGUF
# metadata). "prompted" requires AFFORDANCE=cli and the task refuses the other
# combination. Never pool results across solvers.
SOLVER_KIND="${SOLVER_KIND:-tools}"
LABEL="${LABEL:-bystander-$(echo "$MODEL" | tr '/:' '--')}"
MAX_CONNECTIONS="${MAX_CONNECTIONS:-1}"
MAX_TOOL_OUTPUT="${MAX_TOOL_OUTPUT:-16000}"
# RESPONSES API (2026-09-13, §F154). inspect's OpenAI provider picks between Chat Completions
# and the Responses API on its own, and against a llama-server whose template advertises
# reasoning support it picks Responses. llama.cpp does not serve that shape: every request
# comes back 400 "item['content'] is empty" and the whole cell dies before one sample scores.
# It is model-dependent, so it looks like the MODEL is broken rather than the transport --
# nemotron-3.5-lightning failed on the first request while north-mini-code ran 200 messages
# through the same binary and the same provider string on the same day. Default it off for
# local servers; set RESPONSES_API=1 for a hosted endpoint that genuinely wants it.
if [[ "${RESPONSES_API:-0}" == "1" ]]; then RESPONSES_ARG=""
else RESPONSES_ARG="-M responses_api=false"; fi

echo "=== BystanderBench core | model=$MODEL epochs=$EPOCHS label=$LABEL ($(date)) ==="
for arm in $ARMS; do for ta in $TOOL_ARMS; do
    echo "--- cell arm=$arm tool_arm=$ta ($(date)) ---"
    inspect eval bystander/task.py -T arm="$arm" -T tool_arm="$ta" -T epochs="$EPOCHS" \
        -T affordance="$AFFORDANCE" -T solver_kind="$SOLVER_KIND" \
        -T model_id="${MODEL_ID:-$MODEL}" \
        --model "$MODEL" --log-dir "logs/$LABEL" \
        --max-connections "$MAX_CONNECTIONS" --max-tool-output "$MAX_TOOL_OUTPUT" \
        $RESPONSES_ARG \
        2>&1 | grep -E "error|Error|Traceback|total time|samples" | tail -4
    # PIPESTATUS[0] is inspect's exit code; $? here would be grep's. Without this check a
    # failed eval (bad key, image pull failure) prints nothing alarming and the loop
    # continues, producing a partial corpus that still gets reported.
    rc=${PIPESTATUS[0]}
    if [[ $rc -ne 0 ]]; then
        echo "!! inspect eval FAILED for arm=$arm tool_arm=$ta (exit $rc). Stopping:" >&2
        echo "   a partial corpus reported as complete is worse than no result." >&2
        exit "$rc"
    fi
    echo "    load: $(uptime | sed 's/.*load/load/'); docker: $(docker ps -q | wc -l)"
done; done
echo "=== done ($(date)) ==="
# report.py is the reporting path; summarize.py is a quick look with no floor gate, no
# competence gate and no evidence-only discovery correction (METHODOLOGY-v1.0). Printing
# summarize.py here made the runner's own output disagree with every released number.
python bystander/report.py "logs/$LABEL"
