#!/bin/bash
# w45_cvec_causal.sh -- §F208, the causal test of the frozen §F200 probe direction.
#
# Adds +c*v or -c*v to the residual stream at l_out-37, the exact tensor the frozen direction
# is read from, and measures the behavioural alert rate. `v` is either the direction itself
# (treatment) or a magnitude-matched random vector orthogonal to it (control). The design, the
# dose-selection rule, the primary test, the predicted direction and the kill condition are all
# pre-registered in §F208, written before any steered episode ran.
#
# Two instances run, one per GPU:
#   GPU 0, PLAN="probe"  -> alternates A (+c, direction) and B (-c, direction)   <- primary contrast
#   GPU 1, PLAN="random" -> alternates C (+c, random)    and D (-c, random)      <- specificity control
# The primary contrast is deliberately the one on GPU 0 and is started first, so that a run
# truncated by the 07:50 hard deadline still yields a balanced A-vs-B comparison and only the
# control arms are short.
#
# Every steered condition is a NEW (model, mode) cell: it gets its own tool_probe affordance
# floor on its first batch, and report.py refuses it exactly as it refuses any other cell that
# fails the floor or the 75% competence gate. Steered cells are never pooled with the unsteered
# 167/376 baseline.
#
# Env (required): RES_ID (gpusched id for this GPU), GPU, PLAN (probe|random), DOSE (e.g. 0.679)
# Env (optional): EPOCHS (12), PORT, DEADLINE_HHMM (0645), START_N (1)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
cd "$BASE"; source .venv/bin/activate
: "${RES_ID:?}" "${GPU:?}" "${PLAN:?}" "${DOSE:?}"
EPOCHS="${EPOCHS:-12}"; N="${START_N:-1}"
PORT="${PORT:-$((8093 + GPU))}"
DEADLINE=$(date -d "today ${DEADLINE_HHMM:-06:45}" +%s)
[ "$DEADLINE" -lt "$(date +%s)" ] && DEADLINE=$(date -d "tomorrow ${DEADLINE_HHMM:-06:45}" +%s)
STOP=logs/tonight2/STOP
LOG=logs/tonight2/gpu${GPU}_${PLAN}_queue.log
CACHE="$BASE/bystander/.envcache_gpu${GPU}"
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

finish(){ say "releasing $RES_ID"; gpusched release "$RES_ID" >/dev/null 2>&1; say "GPU${GPU} ${PLAN} QUEUE DONE"; }
trap finish EXIT

# Which vector each sign uses. The random control's seed is fixed in §F208 (20260921) and the
# file is built once, here, so every control batch shares one vector rather than a fresh draw
# per batch -- a fresh draw per batch would test "random perturbations in general" instead of
# "this one arbitrary direction", and the pre-registration names the latter.
build_cvec(){ # $1 sign(pos|neg)
    local sign=$1 mag=$DOSE out
    [ "$sign" = "neg" ] && mag="-$DOSE"
    out="bystander/cvec/${PLAN}_${sign}_$(echo $DOSE | tr '.' 'p').gguf"
    if [ ! -f "$out" ]; then
        if [ "$PLAN" = "random" ]; then
            python bystander/scripts/export_probe_cvec.py --scale "$mag" --random 20260921 --out "$out" >> "$LOG" 2>&1
        else
            python bystander/scripts/export_probe_cvec.py --scale "$mag" --out "$out" >> "$LOG" 2>&1
        fi
        # NOTE: this function's stdout is captured by `CV=$(build_cvec ...)`, so NOTHING
        # may print to stdout here except the path on the last line. `say` tees to stdout and
        # would be captured too, which on first launch produced a CV string containing the whole
        # log line and made llama-server reject its own argument. Log to the file directly.
        [ -f "$out" ] || { echo "[$(date '+%F %T')] FAILED to build $out" >> "$LOG"; return 1; }
        echo "[$(date '+%F %T')] built $out (scale $mag)" >> "$LOG"
    fi
    echo "$out"
}

say "GPU${GPU} ${PLAN} QUEUE START res=$RES_ID dose=$DOSE port=$PORT deadline=$(date -d @$DEADLINE '+%F %H:%M')"
bash tools/require_reservation.sh bystander "$GPU" || { say "no reservation, abort"; exit 3; }
export FAIL_ON_ERROR=0.34

run_batch(){ # $1 label  $2 cvec path  $3 tool_arms
    local LAB=$1 CV=$2 TA=$3 try rc
    for try in 1 2 3; do
        [ -e "$STOP" ] && return 2
        say "batch $LAB try $try (tool_arms: $TA)"
        GPU=$GPU PORT=$PORT GGUF="$GGUF" EPOCHS=$EPOCHS LABEL=$LAB \
          ARMS=blatant_wrongdoing_agents TOOL_ARMS="$TA" \
          BYSTANDER_ENVCACHE="$CACHE" \
          EXTRA_ARGS="--control-vector-scaled ${CV}:1.0 --control-vector-layer-range 37 37" \
          bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1; rc=$?
        if [ $rc -eq 6 ]; then say "$LAB REFUSED: control vector did not load. Not retrying."; return 3; fi
        if [ $rc -eq 0 ] && ls "logs/$LAB"/*.eval >/dev/null 2>&1 && grep -q "pilot done" "logs/${LAB}.runlog"; then
            say "batch $LAB OK: $(grep -E 'alerted|discovered' "logs/${LAB}.runlog" | tail -1 | cut -c1-160)"
            return 0
        fi
        say "batch $LAB rc=$rc; tail: $(tail -2 "logs/${LAB}.runlog" | tr '\n' ' ' | cut -c1-200)"
        kill "$(cat bystander/server.pid 2>/dev/null)" 2>/dev/null; sleep 120
    done
    return 1
}

FIRST_pos=1; FIRST_neg=1
while true; do
    [ -e "$STOP" ] && { say "STOP file seen"; break; }
    now=$(date +%s); left=$(( DEADLINE - now ))
    # A 12-episode with_tool batch has run 45-55 min on this model all week. Do not start one
    # without an hour left: a batch cut off mid-flight is episodes spent for nothing.
    if [ "$left" -lt 3600 ]; then say "only ${left}s to deadline, not starting another batch"; break; fi
    for sign in pos neg; do
        [ -e "$STOP" ] && break
        now=$(date +%s); [ $(( DEADLINE - now )) -lt 3600 ] && { say "deadline reached mid-pair"; break; }
        CV=$(build_cvec "$sign") || break
        var="FIRST_$sign"; first=${!var}
        TA="with_tool"; [ "$first" = "1" ] && TA="tool_probe with_tool"
        LAB="bystander-cvec-${PLAN}-${sign}-$(printf %02d $N)"
        run_batch "$LAB" "$CV" "$TA"; rc=$?
        [ $rc -eq 2 ] && break
        [ $rc -eq 3 ] && { say "aborting queue: steering did not apply"; exit 5; }
        [ $rc -eq 0 ] && eval "FIRST_$sign=0"
        N=$((N+1))
    done
done
say "queue loop exited at $(date '+%F %T')"
