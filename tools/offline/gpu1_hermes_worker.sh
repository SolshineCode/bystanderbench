#!/bin/bash
# tools/offline/gpu1_hermes_worker.sh -- OFFLINE-MODE worker for GPU 1 (2026-09-20).
# Keeps ollama qwen3.5:27b resident on GPU 1 (keep_alive -1 ping every 2 min; if it ever lands on
# GPU 0 it is unloaded and reloaded once GPU 0 is full again), and drives Hermes (local model only,
# no tools, fixed prompts) to: (a) write a status note every 15 min, (b) prescreen alert_oversight
# calls of every finished offline batch (advisory, NOT evidence). Open-ended until logs/offline/STOP.
# Env (required): RES_ID (gpusched id on GPU 1)
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; cd "$BASE"; source .venv/bin/activate
: "${RES_ID:?}"; STOP=logs/offline/STOP; LOG=logs/offline/gpu1_hermes_worker.log
NOTES=logs/offline/hermes_status_notes.txt; PRE=research/audits/offline_prescreen
MODEL=hermes-offline; PORT=8097; GGUFS="/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf /home/darkstar/gguf-downloads/gemma-3-12b/gemma-3-12b-it-Q4_K_M.gguf"; GGUF=""
SRV=/home/darkstar/llama.cpp/build/bin/llama-server; SLOG=llamacpp_logs/hermes_offline_server.log; SPID=""
say(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
trap 'say "stopping server $SPID"; kill $SPID 2>/dev/null; say "releasing $RES_ID"; gpusched release "$RES_ID" >/dev/null 2>&1; say "GPU1 WORKER DONE"' EXIT
gpu_mem(){ nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$1" | tr -d ' '; }
healthy(){ curl -sf -m 5 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q ok; }
ping_model(){ :; }
ensure_on_gpu1(){ # llama-server pinned to GPU 1 by CUDA_VISIBLE_DEVICES; restart if dead
  healthy && [ "$(gpu_mem 1)" -ge 6000 ] && return 0
  [ -n "$SPID" ] && { kill $SPID 2>/dev/null; sleep 5; kill -KILL $SPID 2>/dev/null; }
  local g t; for g in $GGUFS; do   # Hermes needs >=64K context; nex first, gemma-3-12b if nex will not fit at 64K
    say "starting llama-server on GPU1 port $PORT ($(basename $g)) ctx=65536"
    CUDA_VISIBLE_DEVICES=1 nohup "$SRV" --model "$g" --alias "$MODEL" --host 127.0.0.1 --port "$PORT" -ngl 999 -c 65536 -np 1 \
      --no-webui --jinja --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on > "$SLOG" 2>&1 &
    SPID=$!; for t in $(seq 1 60); do healthy && break; kill -0 $SPID 2>/dev/null || break; sleep 10; done
    say "server pid=$SPID gguf=$(basename $g) healthy=$(healthy && echo yes || echo no) g0=$(gpu_mem 0) g1=$(gpu_mem 1)"
    if healthy && [ "$(gpu_mem 1)" -ge 6000 ]; then GGUF=$g; return 0; fi
    kill $SPID 2>/dev/null; sleep 5; kill -KILL $SPID 2>/dev/null; SPID=""
  done; return 1
}
hermes_ask(){ # $1 prompt file with placeholders substituted -> stdout
  timeout 1200 hermes chat -Q --provider llamacpp-local -m "$MODEL" --max-turns 2 -q "$(cat "$1")" 2>>"$LOG"
}
status_note(){
  local F=logs/offline/_facts.txt
  { echo "now: $(date)"; echo "gpu0_mem_MiB: $(gpu_mem 0)  gpu1_mem_MiB: $(gpu_mem 1)"
    echo "disk_free_GB: $(df -BG --output=avail "$BASE" | tail -1 | tr -d ' G')"
    echo "queue_log_lines: $(wc -l < logs/offline/gpu0_queue.log 2>/dev/null)  last_modified: $(stat -c %y logs/offline/gpu0_queue.log 2>/dev/null | cut -c1-19)"
    echo "batches_ok: $(grep -c 'batch .* OK' logs/offline/gpu0_queue.log 2>/dev/null)  chain_ok: $(grep -l CHAIN_OK bystander/acts_nex_agentarm_off*.CHAIN_STATUS 2>/dev/null | wc -l)  chain_fail: $(grep -l CHAIN_FAIL bystander/acts_nex_agentarm_off*.CHAIN_STATUS 2>/dev/null | wc -l)"
    echo "stop_file_present: $([ -e $STOP ] && echo yes || echo no)"
    echo "--- last 12 queue log lines ---"; tail -12 logs/offline/gpu0_queue.log 2>/dev/null; } > "$F"
  python3 - "$F" tools/offline/prompts/status_note.txt logs/offline/_status_prompt.txt <<'PY'
import sys; f,t,o=sys.argv[1:4]; open(o,'w').write(open(t).read().replace('__FACTS__',open(f).read()))
PY
  { echo "===== $(date '+%F %T') ====="; hermes_ask logs/offline/_status_prompt.txt; echo; } >> "$NOTES"
  say "status note written ($(wc -l < "$NOTES") lines total)"
}
prescreen_batch(){ # $1 logdir
  local B; B=$(basename "$1"); local OUT="$PRE/$B.jsonl" RAW="$PRE/$B.alerts.jsonl"
  [ -e "$OUT" ] && return 0
  python tools/offline/dump_alerts.py "$1" "$RAW" >>"$LOG" 2>&1 || { say "dump failed for $B"; return 1; }
  : > "$OUT.part"
  while IFS= read -r line; do
    [ -e "$STOP" ] && break
    python3 - "$line" tools/offline/prompts/prescreen_alert.txt logs/offline/_prescreen_prompt.txt <<'PY'
import sys,json; d=json.loads(sys.argv[1]); t=open(sys.argv[2]).read()
open(sys.argv[3],'w').write(t.replace('__ALERT_TEXT__', d['alert_text'][:6000]))
PY
    local ans; ans=$(hermes_ask logs/offline/_prescreen_prompt.txt | tr -d '\r')
    python3 - "$line" "$ans" >> "$OUT.part" <<'PY'
import sys,json,re
d=json.loads(sys.argv[1]); raw=sys.argv[2]; m=re.search(r'\{.*\}', raw, re.S); parsed=None
try: parsed=json.loads(m.group(0)) if m else None
except Exception: parsed=None
ok = isinstance(parsed,dict) and parsed.get('category') in ('names_misconduct','task_blockage','other')
d.update({'prescreen': parsed if ok else None, 'prescreen_raw': raw[-800:], 'prescreen_valid': bool(ok),
          'provenance': 'local nex-n2.5-mini (llama-server GPU1) via hermes, offline mode 2026-09-20, ADVISORY ONLY, not evidence, must be hand-read'})
print(json.dumps(d))
PY
    ping_model
  done < "$RAW"
  mv "$OUT.part" "$OUT"; say "prescreen $B: $(wc -l < "$OUT") alerts, valid=$(grep -c '"prescreen_valid": true' "$OUT")"
}
say "GPU1 WORKER START res=$RES_ID model=$MODEL"
ensure_on_gpu1 || say "WARNING: model not confirmed on GPU1 (g0=$(gpu_mem 0) g1=$(gpu_mem 1)); continuing, will retry each cycle"
last_note=0; last_ext=$(date +%s); tick=0
while true; do
  [ -e "$STOP" ] && { say "STOP file seen"; break; }
  ensure_on_gpu1 || say "model placement still unconfirmed"
  ping_model
  now=$(date +%s)
  if [ $((now - last_ext)) -ge 3600 ]; then gpusched extend "$RES_ID" 2h >/dev/null 2>&1 && say "extended $RES_ID +2h" || say "extend refused"; last_ext=$now; fi
  for d in logs/bystander-agentarm-nex-off-*/; do
    [ -d "$d" ] || continue; L="logs/$(basename "$d").runlog"
    grep -q "pilot done" "$L" 2>/dev/null && ls "$d"/*.eval >/dev/null 2>&1 && prescreen_batch "${d%/}"
  done
  if [ $((now - last_note)) -ge 900 ]; then status_note; last_note=$(date +%s); fi
  tick=$((tick+1)); sleep 120
done
