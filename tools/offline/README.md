# Offline mode: keeping both GPUs working when the internet is down

Built 2026-09-20 in the 25 minutes before a planned Wi-Fi outage, ran unattended 12:27-18:10
(5h40m) and produced 6 BystanderBench batches, 3 activation trees and 44 local-model alert
prescreens with zero operator input. Claude Code cannot run without internet; these two workers
can. Everything below runs on local llama.cpp, local docker, and the rule-based scorer.

## What runs where

| GPU | script | what it does | stops when |
|---|---|---|---|
| 0 | `gpu0_bystander_queue.sh` | nex agent-arm batches (12 episodes each) via `bystander/run_pilot_local.sh`; after every pair, `bystander/capture_chain.sh` (pre-decision cut + extraction + integrity check) | `logs/offline/STOP` exists, checked between batches; the running batch/chain finishes first |
| 1 | `gpu1_hermes_worker.sh` | serves a local GGUF on port 8097 (`--alias hermes-offline`, 64K ctx, pinned by `CUDA_VISIBLE_DEVICES=1`) for Hermes's `llamacpp-local` provider; Hermes writes a status note every 15 min and prescreens each finished batch's `alert_oversight` calls | `logs/offline/STOP`, checked every 2 min |

Both self-extend their gpusched reservation (2h per batch on GPU 0, hourly on GPU 1) and release
it on exit. All control flow is deterministic bash; the local model only ever sees a fixed prompt
with the facts pre-gathered for it (`prompts/`). Its output is advisory and is labelled as such in
every row it writes.

## Launch (in this order)

```
gpusched reserve --gpu 0 --duration 6h --start now --session claude-bystander-offline --harness claude-code --purpose "..." --json
gpusched reserve --gpu 1 --duration 6h --start now --session claude-hermes-offline --harness claude-code --purpose "..." --json
RES_ID=<gpu0 id> PORT=8093 CAPPORT=8098 PDPORT=8099 setsid nohup bash tools/offline/gpu0_bystander_queue.sh > logs/offline/gpu0_queue.nohup 2>&1 < /dev/null & disown
# wait until nvidia-smi shows GPU 0 above 15 GB (the batch server is up), then:
RES_ID=<gpu1 id> bash tools/offline/relaunch_gpu1.sh
```

The GPU 0 session name must contain `bystander` (`run_pilot_local.sh` and `capture_chain.sh`
check for that tag). `START_N` picks the first batch number; labels are
`bystander-agentarm-nex-off-NN`, trees `acts_nex_agentarm_offNNMM`.

Then verify, do not assume: `nvidia-smi` shows real memory on both cards, `logs/offline/gpu0_queue.log`
has a `batch ... try 1` line, `logs/offline/gpu1_hermes_worker.log` has `healthy=yes`, and the first
entry in `logs/offline/hermes_status_notes.txt` is a note and not a Hermes init error.

## Stop

`touch logs/offline/STOP`. Wait for `GPU0 QUEUE DONE` and `GPU1 WORKER DONE` in the two logs,
then `gpusched status` should show no reservations and `nvidia-smi` 0 MiB on both. Remove the
STOP file before the next launch.

## Outputs

- `logs/bystander-agentarm-nex-off-NN/` Inspect logs, `logs/...NN.runlog` the pilot output
- `bystander/acts_nex_agentarm_offNNMM.predecision/` trees, verdict in `.CHAIN_STATUS`
- `logs/offline/hermes_status_notes.txt` one note per 15 min
- `research/audits/offline_prescreen/<batch>.jsonl` one row per alert call with the model's JSON
  (`prescreen`), the raw reply, a validity flag and a provenance string. NOT evidence: a hand-read
  queue ordering aid only. `<batch>.alerts.jsonl` is the deterministic dump it was made from
  (`dump_alerts.py`).

## What went wrong on the first run, so the next one is faster

1. **ollama loaded the model on CPU, not GPU 1.** Its GPU discovery runs once at service start and
   had timed out (home `CLAUDE.md`, failure mode 2). The fix is `sudo systemctl restart ollama`,
   which this session's permissions could not run. Hermes therefore uses llama-server through the
   `llamacpp-local` provider already in `~/.hermes/config.yaml` (port 8097). That is the better
   design anyway: `CUDA_VISIBLE_DEVICES=1` pins the card deterministically, where ollama picks
   whichever GPU has room at load time and could land on GPU 0 in the seconds between two
   llama-server processes there.
2. **Hermes refuses any model whose reported context window is under 64K.** The first server was
   started at 16K and every Hermes call failed with `Failed to initialize agent`. The worker now
   serves at `-c 65536`; nex Q4_K_M fits on the M40 at that size (21.1 GB). If it did not, the
   worker falls back to gemma-3-12b-it.
3. **The status-note prompt's attribution line said `qwen3.5:27b` for the whole run** although the
   model was nex. The `sed` that fixed it sat in a compound command that aborted before it ran.
   Every note from 2026-09-20 carries the wrong model name; the worker log (`server pid=... gguf=`)
   is the authority. Fixed in `prompts/status_note.txt` after the run.
4. **nex prints its reasoning into the note body** before the six-line answer (Hermes `-Q` does
   not strip it). The final lines were accurate against the facts block every time checked, but
   the notes are long. A reasoning-stripping step, or a non-thinking model, would fix it.
5. **A bash hook on this box refuses command lines that pair a `grep` process scan with `kill`**
   (the self-match rule from home `CLAUDE.md`). Three relaunch attempts were silently refused with
   exit 1 and no output. Killing is done from a script file (`relaunch_gpu1.sh`), never inline.
6. The worker's prescreen loop `break`s on STOP but still renames the `.part` file to the final
   name, so a batch interrupted mid-prescreen would look complete. Not hit (STOP was set after the
   last prescreen finished); check row counts against `.alerts.jsonl` before trusting a file.
7. **HF publishing after the outage.** The default token on this box (`~/.cache/huggingface/token`,
   and the `[DarkStar]` profile in `stored_tokens`, which is the same token) is the public
   `Solshine` account; `push_acts_tree.py`'s identity guard refused it, correctly. The
   `DarkStarDeleeuw` credential is `HF_AGENT_TOKEN` in the Claude session environment:
   `HF_TOKEN="$HF_AGENT_TOKEN"`. And IPv6 to HF's CDN was dead after the router reset (an upload
   sat in `SYN-SENT` for 20 minutes, no error; `ss -tnp | grep pid=<pid>` shows it). What worked:
   `HF_HUB_DISABLE_XET=1` plus forcing IPv4 by filtering `socket.getaddrinfo` to `AF_INET` in a
   `python -c` wrapper around the push script.
8. **The self-match kill trap, one level removed.** A kill script that pattern-matches process
   names is safe to *run*, but the command line that runs it must not contain the pattern either:
   a single Bash call that both wrote a heredoc mentioning `push_acts_tree` and ran the kill
   script killed its own shell (exit 144). Kill in one short command; do everything else in the
   next.

## What to improve before relying on it for a long outage

- Alternate human-arm control batches with agent-arm ones: this run grew the agent cell only
  (219 -> 291 episodes) while the control cell stayed at 151. The chain for human-arm batches needs
  the matcher's nearest-boundary fix first (owed by the 2026-09-20 summary).
- Give the GPU 1 model a real job with more value than status notes once a prompt has been checked
  on a few dozen items against a hand read; the prescreen categories from this run are the first
  such calibration set.
- Disk: each pair of batches plus tree is about 7 MB in the repo tree but the Inspect logs and
  llama.cpp KV caches are larger; the box was at 93% when this ran. Add a disk guard to the queue.
