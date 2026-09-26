#!/bin/bash
# bystander/capture_chain.sh -- the ONE capture path (2026-09-20).
#
# Why this exists. Three launchers (W19, W33, W36) either promised a capture and never ran it or
# captured token streams and never called extract_resid, and each time the gap was found at
# wind-down, after the ledger had already cited the tree. Every launcher now calls this script
# instead of inlining the steps, and this script refuses to say CHAIN_OK unless the tree it built
# passes an integrity check: capture rc 0, bins == manifest rows, check_layers agrees with the
# requested layers. The verdict is the last line of $OUT.CHAIN_STATUS; a tree without a CHAIN_OK
# line in that file is not citable.
#
# Env (required): GGUF GPU OUT LOGDIRS   (LOGDIRS: space-separated Inspect log dirs)
# Env (optional): LAYERS (4,8,16,24,30,34,37,39 = nex)  EOS (<|im_end|>)  PREDECISION (1)
#                 MATCH (quantile)  CAPPORT (8098)  PDPORT (8099)  FULL_EXTRACT (0)
#                 TAG (reservation tag checked by tools/require_reservation.sh; default bystander)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench
cd "$BASE"; source .venv/bin/activate
: "${GGUF:?}" "${GPU:?}" "${OUT:?}" "${LOGDIRS:?}"
LAYERS="${LAYERS:-4,8,16,24,30,34,37,39}"; EOS="${EOS:-<|im_end|>}"; PREDECISION="${PREDECISION:-1}"
MATCH="${MATCH:-quantile}"; CAPPORT="${CAPPORT:-8098}"; PDPORT="${PDPORT:-8099}"
FULL_EXTRACT="${FULL_EXTRACT:-0}"; TAG="${TAG:-bystander}"
SRV=/home/darkstar/llama.cpp/build/bin/llama-server
NAME=$(basename "$OUT"); STATUS="$OUT.CHAIN_STATUS"; : > "$STATUS"
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$STATUS"; }
fail(){ say "CHAIN_FAIL: $*"; exit 1; }
bash tools/require_reservation.sh "$TAG" "$GPU" || fail "no reservation for tag=$TAG gpu=$GPU"
for d in $LOGDIRS; do
  [ -d "$d" ] || fail "missing logdir $d"
  ls "$d"/*.eval >/dev/null 2>&1 || fail "no .eval in $d"
done
SPID=""
start_server(){ # $1 port  $2 log
  ss -tln | grep -q ":$1 " && fail "port $1 busy"
  CUDA_VISIBLE_DEVICES=$GPU nohup "$SRV" --model "$GGUF" --host 127.0.0.1 --port "$1" -ngl 999 -c 32768 -np 1 \
    --no-webui --jinja --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$2" 2>&1 &
  SPID=$!
  for t in $(seq 1 90); do curl -sf -m 3 "http://127.0.0.1:$1/health" 2>/dev/null | grep -q ok && return 0; sleep 10; done
  kill $SPID 2>/dev/null; fail "server on port $1 never came up (log $2)"
}
stop_server(){
  [ -n "$SPID" ] && kill $SPID 2>/dev/null
  for t in $(seq 1 30); do kill -0 $SPID 2>/dev/null || break; sleep 1; done
  kill -9 $SPID 2>/dev/null; SPID=""; sleep 5
}
extract_tree(){ # $1 tree dir (must hold manifest.tsv)
  mkdir -p "$1/acts"; echo "$LAYERS" | tr ',' '\n' > "$1/requested_layers.txt"
  RESID_MANIFEST="$1/manifest.tsv" RESID_LAYERS="$LAYERS" CUDA_VISIBLE_DEVICES=$GPU \
    "$BASE/concealment-probe/tools/extract_resid" -m "$GGUF" -c 32768 -b 1024 \
    --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$1/extract.log" 2>&1
  local rc=$? nb nr
  nb=$(ls "$1"/acts/*.bin 2>/dev/null | wc -l); nr=$(wc -l < "$1/manifest.tsv")
  say "extract $(basename "$1") rc=$rc bins=$nb/$nr"
  { [ $rc -eq 0 ] && [ "$nb" -eq "$nr" ] && [ "$nb" -gt 0 ]; } || return 1
  python bystander/check_layers.py "$1" --expect "$LAYERS" > "$1/check_layers.log" 2>&1; rc=$?
  say "check_layers $(basename "$1") rc=$rc"
  return $rc
}

say "CHAIN_START $NAME gpu=$GPU gguf=$(basename "$GGUF") logdirs:$LOGDIRS"
start_server "$CAPPORT" "llamacpp_logs/${NAME}_cap_server.log"
python bystander/capture_activations.py --port "$CAPPORT" --eos "$EOS" --out-dir "$OUT" \
  $(for d in $LOGDIRS; do echo -n "--logdir $d "; done) > "$OUT.capture.log" 2>&1
RC=$?; stop_server
NERR=$(grep -c ERR "$OUT.capture.log"); NROWS=$(wc -l < "$OUT/manifest.tsv" 2>/dev/null || echo 0)
say "capture rc=$RC err_lines=$NERR manifest_rows=$NROWS  ($(tail -1 "$OUT.capture.log"))"
{ [ $RC -eq 0 ] && [ "$NROWS" -gt 0 ]; } || fail "capture"

if [ "$PREDECISION" = "1" ]; then
  PD="$OUT.predecision"
  start_server "$PDPORT" "llamacpp_logs/${NAME}_pd_server.log"
  python bystander/decision_index.py --port "$PDPORT" --dirs "$OUT" --capture-schema f151 --match "$MATCH" \
    --out "$PD" > "$PD.index.log" 2>&1
  RC=$?; stop_server
  grep -E "REFUSING TO WRITE|GATE PASS|GATE FAIL|AUC of position|per-batch|alerting \(first_alert\)|silent   \(matched\)" "$PD.index.log" | tee -a "$STATUS"
  [ $RC -eq 0 ] || fail "decision_index rc=$RC (see $PD.index.log)"
  extract_tree "$PD" || fail "predecision extract/check_layers"
fi
if [ "$FULL_EXTRACT" = "1" ]; then
  extract_tree "$OUT" || fail "full-stream extract/check_layers"
fi
say "CHAIN_OK $NAME"
