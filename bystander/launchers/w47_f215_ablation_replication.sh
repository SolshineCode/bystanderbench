#!/bin/bash
# w47_f215_ablation_replication.sh -- §F215 (approved for running by Caleb's GPU grant, 2026-09-23 ~23:45):
# pre-registered replication of §F214's exploratory ablation, plus the layer-37-only pair.
# Derived from w46_f211_ablation.sh (same verified machinery: marker guard, per-GPU envcache).
# Differences: FIXED N (BATCHES_PER_ARM x EPOCHS) instead of a clock, and MAX_RETRIES=5.
#
# (w46 header follows for the shared machinery)
# w46_f211_ablation.sh -- §F211: ablation ("abliteration") and clamp-amplification of the frozen
# §F200 direction, on the patched llama.cpp build at ~/llama.cpp-ablate. Design, predictions and
# kill conditions are pre-registered in §F211, written before any episode ran.
#
#   §F215: GPU 0, PLAN="allayers" -> alternates E (ablate d, l1-39) and F (ablate random, l1-39)
#          GPU 1, PLAN="l37"      -> alternates G (ablate d, l37 only) and K (ablate random, l37 only)
#
# Every condition is its own (model, mode) cell with its own tool_probe floor on its first batch.
# Never pooled with the unsteered cell or with each other (report.py keys by GGUF basename, so
# run the reporter per arm -- see research/f211/report.py).
#
# Env (required): RES_ID, GPU, PLAN (allayers|l37). Resumes from completed batches (fixed N).
# Env (optional): EPOCHS (6), PORT, DEADLINE_HHMM (05:57), START_N (1)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
export LLAMA_SERVER=/home/darkstar/llama.cpp-ablate/build/bin/llama-server
cd "$BASE"; source .venv/bin/activate
: "${RES_ID:?}" "${GPU:?}" "${PLAN:?}"
CLAMP_T="${CLAMP_T:-0}"
BATCHES_PER_ARM="${BATCHES_PER_ARM:-8}"
export MAX_RETRIES="${MAX_RETRIES:-5}"
EPOCHS="${EPOCHS:-6}"; N="${START_N:-1}"
PORT="${PORT:-$((8093 + GPU))}"
DEADLINE=$(date -d "today ${DEADLINE_HHMM:-05:57}" +%s)
[ "$DEADLINE" -lt "$(date +%s)" ] && DEADLINE=$(date -d "tomorrow ${DEADLINE_HHMM:-05:57}" +%s)
mkdir -p logs/f215
STOP=logs/f215/STOP
LOG=logs/f215/gpu${GPU}_${PLAN}_queue.log
CACHE="$BASE/bystander/.envcache_gpu${GPU}"
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
finish(){ say "GPU${GPU} ${PLAN} QUEUE DONE (reservation $RES_ID left to the session to release)"; }
trap finish EXIT

# arm -> "cvec_file layer_lo layer_hi mode clamp"
arm_cfg(){ case $1 in
  H) echo "bystander/cvec/unit_probe_L37.gguf 37 37 clamp $CLAMP_T";;
  E) echo "bystander/cvec/abl_probe_L1-39.gguf 1 39 ablate 0";;
  F) echo "bystander/cvec/abl_random_L1-39.gguf 1 39 ablate 0";;
  G) echo "bystander/cvec/unit_probe_L37.gguf 37 37 ablate 0";;
  K) echo "bystander/cvec/unit_random_L37.gguf 37 37 ablate 0";;
esac; }

say "GPU${GPU} ${PLAN} QUEUE START res=$RES_ID clamp_t=$CLAMP_T port=$PORT deadline=$(date -d @$DEADLINE '+%F %H:%M') server=$LLAMA_SERVER"
bash tools/require_reservation.sh bystander "$GPU" || { say "no reservation, abort"; exit 3; }
export FAIL_ON_ERROR=0.34

run_batch(){ # $1 arm  $2 label  $3 tool_arms
    local ARM=$1 LAB=$2 TA=$3 try rc cv lo hi mode t slog
    read -r cv lo hi mode t <<< "$(arm_cfg "$ARM")"
    slog="llamacpp_logs/bystander_${LAB}_server.log"
    for try in 1 2 3; do
        [ -e "$STOP" ] && return 2
        say "batch $LAB arm=$ARM mode=$mode t=$t layers=$lo-$hi try $try (tool_arms: $TA)"
        mk="$BASE/logs/f215/markers/${LAB}.try${try}"; mkdir -p "$(dirname "$mk")"; rm -f "$mk"
        LLAMA_CVEC_MODE=$mode LLAMA_CVEC_CLAMP=$t LLAMA_CVEC_MARKER="$mk" \
        GPU=$GPU PORT=$PORT GGUF="$GGUF" EPOCHS=$EPOCHS LABEL=$LAB \
          ARMS=blatant_wrongdoing_agents TOOL_ARMS="$TA" \
          BYSTANDER_ENVCACHE="$CACHE" \
          EXTRA_ARGS="--control-vector-scaled ${cv}:1.0 --control-vector-layer-range $lo $hi" \
          bash bystander/run_pilot_local.sh > "logs/${LAB}.runlog" 2>&1; rc=$?
        # The patched op writes a marker from inside apply_to the first time it builds a graph
        # (llama-server drops libllama INFO lines, so the server log cannot carry this proof).
        # No marker, or the wrong mode/target, means the stock add ran: INVALID, not a null.
        if ! grep -qE "^CVEC_MODE=${mode} CVEC_CLAMP=$(printf '%.6f' "$t") " "$mk" 2>/dev/null; then
            say "$LAB INVALID: marker $mk lacks CVEC_MODE=${mode} t=${t} ($(cat "$mk" 2>/dev/null | head -1)). Aborting queue."
            mv "logs/$LAB" "logs/f215/INVALID_$LAB" 2>/dev/null; return 3
        fi
        if [ $rc -eq 6 ]; then say "$LAB REFUSED: control vector did not load."; return 3; fi
        if [ $rc -eq 0 ] && ls "logs/$LAB"/*.eval >/dev/null 2>&1 && grep -q "pilot done" "logs/${LAB}.runlog"; then
            say "batch $LAB OK: $(grep -E 'alerted|discovered' "logs/${LAB}.runlog" | tail -1 | cut -c1-160)"
            return 0
        fi
        say "batch $LAB rc=$rc; tail: $(tail -2 "logs/${LAB}.runlog" | tr '\n' ' ' | cut -c1-200)"
        kill "$(cat bystander/server.pid 2>/dev/null)" 2>/dev/null; sleep 120
    done
    return 1
}

case $PLAN in allayers) ARMS_SEQ="E F";; l37) ARMS_SEQ="G K";; *) say "bad PLAN"; exit 2;; esac
declare -A FIRST; for a in $ARMS_SEQ; do FIRST[$a]=${SKIP_FLOOR:-1}; done
declare -A DONE; for a in $ARMS_SEQ; do DONE[$a]=0; done
# RESUME (2026-09-23 23:5x): N is fixed, not the clock (§F215), so a window that ends early must be
# resumable without re-running floors or over-shooting N. Count completed batches from the files
# they produced: a run log that reached "pilot done" and whose marker matches the arm's mode.
for a in $ARMS_SEQ; do
    read -r _cv _lo _hi amode _t <<< "$(arm_cfg "$a")"
    for rl in logs/bystander-f215-${a}-*.runlog; do
        [ -e "$rl" ] || continue
        lab=$(basename "$rl" .runlog)
        grep -q "pilot done" "$rl" && ls "logs/$lab"/*.eval >/dev/null 2>&1 \
          && grep -qs "^CVEC_MODE=${amode} " logs/f215/markers/${lab}.try* && DONE[$a]=$((DONE[$a]+1))
        n=$(echo "$lab" | grep -oE '[0-9]+$' | sed 's/^0*//'); [ -n "$n" ] && [ "$n" -ge "$N" ] && N=$((n+1))
    done
    [ "${DONE[$a]}" -gt 0 ] && FIRST[$a]=0
done
say "resume state: $(for a in $ARMS_SEQ; do echo -n "$a=${DONE[$a]} "; done)next N=$N"
[ "${SKIP_FLOOR:-1}" = "0" ] && say "floors already run in the smoke; no tool_probe batches"
while true; do
    [ -e "$STOP" ] && { say "STOP file seen"; break; }
    alldone=1; for a in $ARMS_SEQ; do [ "${DONE[$a]}" -lt "$BATCHES_PER_ARM" ] && alldone=0; done
    [ $alldone = 1 ] && { say "fixed N reached: $BATCHES_PER_ARM batches per arm"; break; }
    [ $(( DEADLINE - $(date +%s) )) -lt 3000 ] && { say "under 50 min to deadline, not starting another batch"; break; }
    for arm in $ARMS_SEQ; do
        [ -e "$STOP" ] && break
        [ $(( DEADLINE - $(date +%s) )) -lt 3000 ] && { say "deadline reached mid-pair"; break; }
        TA="with_tool"; [ "${FIRST[$arm]}" = "1" ] && TA="tool_probe with_tool"
        [ "${DONE[$arm]}" -ge "$BATCHES_PER_ARM" ] && continue
        LAB="bystander-f215-${arm}-$(printf %02d $N)"
        run_batch "$arm" "$LAB" "$TA"; rc=$?
        [ $rc -eq 2 ] && break
        [ $rc -eq 3 ] && { say "aborting queue: intervention not verified"; exit 5; }
        [ $rc -eq 0 ] && { FIRST[$arm]=0; DONE[$arm]=$((DONE[$arm]+1)); }
        N=$((N+1))
    done
done
say "queue loop exited"
