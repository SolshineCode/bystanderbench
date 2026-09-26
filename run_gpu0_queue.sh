#!/bin/bash
# run_gpu0_queue.sh — sequences the GPU0 work queue:
# lightning capture -> north-mini capture -> gemma-12b wave-2 extension.
# Each step gets its own fresh gpusched reservation (not reusing a stale one),
# and the queue waits for real GPU0 memory to clear between steps, not just a
# process-exit signal, matching the established backoff pattern elsewhere.
#
# ## Rewritten 2026-09-07 after reviewing what this script actually did
#
# The 2026-09-06 run printed "=== GPU0 QUEUE COMPLETE ===" while **two of its
# three steps never ran**. `gpusched reserve` returned exit 3 (CONFLICT with the
# still-active claude-olmo3-saes window) for steps 1 and 2, the script never
# checked that exit status, the step scripts then correctly refused, and the
# queue moved on and declared success. The lightning and north-mini local
# activation captures were silently lost; nobody noticed until 2026-09-07.
#
# Three defects, all fixed below:
#   1. `gpusched reserve`'s exit status was ignored -- a refused reservation read
#      exactly like a granted one.
#   2. Step 3 never released its reservation.
#   3. The final banner was unconditional, so a queue that accomplished nothing
#      reported the same as a queue that did everything.
# Same family as the OpenRouter incident: a success message that isn't tied to a
# verified outcome. The banner now reports per-step status and the script exits
# non-zero if anything was skipped or failed.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"

declare -a RESULTS=()

wait_for_gpu0_clear() {
    local used=""
    for _ in $(seq 1 12); do
        used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0)
        [ "$used" -lt 1500 ] && break
        sleep 15
    done
    echo "GPU0 used=${used}MiB"
}

# run_step <label> <session> <duration> <purpose> <command...>
run_step() {
    local label="$1" session="$2" dur="$3" purpose="$4"; shift 4
    echo "=== $label ==="
    wait_for_gpu0_clear

    local res_out res_rc
    res_out=$(~/bin/gpusched reserve --gpu 0 --duration "$dur" --session "$session" \
                  --harness claude-code --purpose "$purpose" 2>&1)
    res_rc=$?
    echo "$res_out"
    if [ "$res_rc" -ne 0 ]; then
        echo "!! SKIPPED $label: gpusched reserve failed (exit $res_rc). NOT running this step."
        echo "!! Re-queue it against a free window (gpusched next-free --gpu 0) -- do not --force."
        RESULTS+=("SKIPPED  $label (reservation refused, exit $res_rc)")
        return 1
    fi

    local id
    # Real gpusched output is: "reserved: id <hex> gpu=N <start> -> <end>".
    # The pre-2026-09-07 version of this script parsed "(id <hex>)", a format
    # gpusched never emits -- so every `release` in the old queue silently
    # matched nothing and reservations were left to lapse instead of being
    # released. Verified against live gpusched output before committing.
    id=$(sed -nE 's/^reserved: id ([a-f0-9]+).*/\1/p' <<<"$res_out" | head -1)
    [ -n "$id" ] && echo "reserved id=$id"

    "$@"
    local rc=$?
    echo "$label finished, exit=$rc ($(date))"

    if [ -n "$id" ]; then
        ~/bin/gpusched release "$id" 2>&1 && echo "released $id"
    else
        echo "!! WARNING: could not parse a reservation id from reserve output; release by hand."
    fi

    if [ "$rc" -eq 0 ]; then
        RESULTS+=("OK       $label")
    else
        RESULTS+=("FAILED   $label (exit $rc)")
    fi
    return "$rc"
}

run_step "[1/3] lightning capture" claude-lightning-capture 2h \
    "lever-1 capture: nemotron-3.5-lightning teacher-forced through prepare_dataset.py, standard layer sweep" \
    bash -c 'bash lightning/run_capture.sh > run_lightning_capture.log 2>&1'

run_step "[2/3] north-mini-code capture" claude-northmini-capture 2h \
    "lever-1 capture: north-mini-code teacher-forced through prepare_dataset.py (llama.cpp cohere2moe build)" \
    bash -c 'bash north-mini/run_capture.sh > run_northmini_capture.log 2>&1'

run_step "[3/3] gemma-12b wave-2 extension" claude-gemma12b-ext 8h \
    "lever-2 N extension: gemma-3-12b-it wave-2" \
    bash -c 'LIMIT_IMP=75 LIMIT_ORIG=25 PORT=8093 GPU=0 UPLOAD=0 bash gemma12b/run_full_pipeline.sh > run_gemma12b_wave2.log 2>&1'

echo
echo "=== GPU0 QUEUE FINISHED ($(date)) ==="
for r in "${RESULTS[@]}"; do echo "  $r"; done
if printf '%s\n' "${RESULTS[@]}" | grep -qE '^(SKIPPED|FAILED)'; then
    echo "!! Queue did NOT complete cleanly -- see the lines above. Exiting non-zero."
    exit 1
fi
echo "All steps completed."
