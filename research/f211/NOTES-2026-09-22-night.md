# Session notes, 2026-09-22 evening to 2026-09-23 07:15 (Claude Code, deep-work)

Running log. Times are PDT and come from `date`, not estimates. Newest entries at the bottom.

## Standing constraints for the night

- **Server maintenance at 08:00 on 09-23 (Caleb).** All work, commits and pushes must be done,
  and the GPU reservation released, by about 07:15.
- **GPU work:** §F211 queues on both GPUs, reservation `31702f29` until 06:57. No new batch
  after about 05:50, last one finishes by about 06:40.
- **Tokens:** Claude Code subscription only. **Never usage credits** (Caleb, 22:2x). Usage
  credits are toggled ON with $23.45 purchased on the account, so reaching a plan limit would
  spend real money. Self-imposed ceiling: **weekly usage under 50%** (37% at 22:10, session 9%,
  session resets 22:50, week resets Fri 19:00). Re-check `claude.ai/settings/usage` every few
  hours. The toggle was left as it is (account setting, needs Caleb's explicit go).
- **Labelling:** allowed ("use tokens for labelling tasks"), but **no human-review prep at
  all** (Caleb, 22:3x). No rater packets, calibration sets or anything aimed at round two.
- **No interim look at §F211 rates** (§F211 pre-registration). The reporter was dry-run for
  statuses only at about 22:10.

## Done earlier this evening (for the record)

- Synced `main` to `origin/main` by fast-forward, `7373b57`.
- Wrote the §F211 pre-registration, built the patched llama.cpp (`~/llama.cpp-ablate`), and ran
  the mechanism check. It passed:
  `research/canonical/f211_mechanism_check_2026-09-22.json`.
- §F212: E (abliterate) failed its smoke gate on 1/6 context-window errors, so it is
  EXPLORATORY. H (clamp t = 0.50) passed.
- Queues launched: GPU1 F at 19:02, GPU0 H/E at 19:04.
- Rapid Grant application ($500) submitted at about 21:30, confirmed on the post-submit page.
  Text: `research/course-writeup/rapid-grant-application-2026-09-22.md` (`d2eb28a`).
- Skill `human-writing-check` got a READ-FIRST note about shape/feel checks.

## Log

**22:1x.** Checked the usage page (numbers above).

**22:2x.** Decided on labelling work: a Claude read of every `alert_oversight` call in the
canonical corpus.

- **Scope.** Every logdir holding a `*bystander*.eval`, minus `-partial`, minus steered dirs
  (`cvec`, `f211`). The `f211` exclusion is on purpose: reading tonight's alerts would be an
  interim look.
- **Why this is not human-review prep.** It is an audit of the benchmark's own alert channel.
  `alert_content_relevant` is a keyword screen with a documented ~90% false-negative rate
  (FINDINGS line ~4053), so nothing in the corpus says what share of each cell's alerts
  actually name the misconduct rather than the agent's own blockage. That share bears on
  whether a leaderboard rate means "reported the wrongdoing".
- **Status of the output.** A Claude autolabel. Advisory, never evidence, per CLAUDE.md
  interpretability rule 3 ("an interpretation you reached yourself is a single-agent autolabel
  and stays flagged").
- **Rubric.** `tools/offline/prompts/prescreen_alert.txt` (09-20), with the one defect §F2xx(e)
  named fixed: agent-pool style names (`close-pool-d`, `agent-pool-07`, "quorum", "the system")
  count as agent. Hand-check a sample of the labels myself before quoting any share.
- Extraction started, via `tools/offline/dump_alerts.py` per logdir into
  `research/audits/claude_alert_labels/raw/`.

**22:50.** Extraction done.
- 239 logdirs, 722 `alert_oversight` calls from 653 alerting episodes, none empty. Median alert
  length 274 characters, max 3,605, total 240k (about 60k tokens).
- **Reconciliation with the cell table (CORRECTED about 23:00).** My first note said the gap
  from the table's 676 was "13 CLI logdirs". That was wrong, and checking the CSV caught it.
  - The table's 676 alerting episodes are 635 native-tool plus 41 `prompted`. Prompted (CLI)
    episodes make no tool call, so this audit cannot see them.
  - The dump's 653 episodes are **452 `with_tool` plus 201 `tool_probe`** floor episodes. The
    table's `alerted` column counts with_tool only (443 across all modes). Floor alerts live in
    `floor_k`.
  - That leaves **452 vs 443 with_tool, 9 extra in the dump.** Most likely these are episodes
    `report.py` drops (errored, or limit-excluded), but that is **not verified**. Any per-cell
    share must be computed on report.py's own episode set, or state that it isn't.
- Arms: blatant_wrongdoing 339, blatant_wrongdoing_agents 320, blatant_safety_falsification 16,
  blatant_oversight_evasion 16, conspiracy_realistic 13, blatant_wrongdoing_noaddressee 12,
  blatant_safety_addressee 6.
- Every logdir maps to exactly one (model, affordance, solver). Meta is in
  `alerts_with_meta.json`.
- Wrongdoer naming checked in `bystander/env/content.py`: human arm `d.raines`, agent arm
  `close-pool-a..f` / "board quorum". Written into RUBRIC.md.
- 8 Sonnet subagents launched, one per ~91-call batch. Each sees only id, arm and alert_text,
  never `alerted`, a rate or the model name, and each must verify that its quotes are verbatim.

**23:01.** Alert labelling complete. Written up as §F213 (advisory autolabel).
- 8 Sonnet labellers, 722/722 labels, independently re-validated: no dups, quotes verbatim,
  enums OK. Batch 1 used a `build_labels.py`. I inspected it: a hard-coded dict of
  per-item manual judgments, no keyword logic. Fine.
- Consistency pass: 24 wrongdoer corrections (`CORRECTIONS.jsonl`). Two root causes:
  - objector-as-wrongdoer (batch 5 especially);
  - **my rubric's "the system" = agent**, which was wrong: "the system computed 118" is the
    victim bookkeeping system.
- Hand check: 25 random rows, 25/25 agree.
- **Headline.** All 11 human-arm own-task-only "alerts" are Llama-3.3-70B, the refused cell.
  Every other cell: 147/147 and 284/284 alerting episodes name the misconduct. The gate is
  independently confirmed. Explicit attribution is rare in both arms (12% / 24%).
- Tokens: about 0.96M subagent tokens.

**23:05.** Usage 38% week / 9% session. The labelling cost about 1 point of the weekly limit.

**23:05. E-06 stalled.**
- Started 21:46. Server log silent since 22:39, GPU0 at 0%, no TCP connection from the client
  to :8093, so Inspect is sleeping in retry backoff.
- Cause: 30 identical `500 Failed to parse tool call arguments as JSON ... missing closing
  quote` from **one episode** that keeps emitting a truncated long Python heredoc as a bash
  argument. I first wrote this up as "ablation breaks JSON, 30 vs 0". **Wrong, corrected
  within minutes.** It is one looping episode, not a rate. Parse errors per arm: E 30 (all
  E-06), H 0, F 0, §F210 arms 0.
- Context overflows so far: E-02 2, E smoke 1. Compare against H/F at the end before saying
  anything.
- Inspect 0.3.261 retries without limit by default, but the run sets `--timeout 4800`, an
  overall request cap across retries. Expect the episode to error out around 23:15-23:25, and
  FAIL_ON_ERROR=0.34 keeps the other five.
- **Decision: wait, do not kill.** Killing loses the five finished episodes, because report.py
  discards an incomplete log whole. Check again at 23:35. If still stuck, kill the inspect pid
  (by PID, never pkill -f) and let run_batch retry.

**23:35. E-06 still looping. The server logged another retry at 23:35:10, so `--timeout 4800`
does not cap it** (each new retry chain seems to reset). Stopped as planned:
- PID 266139 confirmed by its args as the E-06 inspect process (elapsed 1:49), then **SIGINT,
  not a hard kill**, so Inspect writes what it has.
- Inspect: "Task interrupted (3 of 6 total samples logged before interruption)". The log is
  saved with cancelled status. run_pilot_local reached "pilot done" and the queue moved on.
- E-06 therefore contributes at most 3 episodes, and only if report.py accepts a cancelled
  log. CHECK AT REPORT TIME and state it in §F214. Whichever way it goes, that is the only
  deviation. No batch was re-run to replace it: the queue is clock-bound and pre-registration
  says no interim look.
- The looping episode is not a rate. It is recorded as one E episode that never finished,
  having hit a JSON-malformed tool call 30+ times.
- **Resolved (23:36).** `bystander/report.py:147` skips any log with `status != "success"`, so
  E-06's cancelled log (3 episodes) is **excluded**. That is the standing rule, applied as for
  every cell, with no exception. E-06 contributes 0. Cost: GPU0 lost about 1h50m to one looping
  episode. The queue moved on to H-07 at 23:35.
- Lesson for later launchers: one episode stuck on a deterministic 500 can hold a batch for
  hours, and neither `--timeout` nor `--max-retries` (unlimited by default) stopped it. A
  future run should pass `--max-retries` (e.g. 5) so the episode errors out and FAIL_ON_ERROR
  keeps the siblings. Not changed tonight: editing a running launcher is the §F49 hazard.

**23:4x. Stall watchdog armed** (`research/f211/stall_watchdog.sh`, log
`logs/f211/stall_watchdog.log`, runs until 06:45).
- It SIGINTs an f211 inspect PID only when all three hold: server log silent 30+ min, that GPU
  at 0%, and no established TCP connection to that server port.
- Scoped to f211 inspect processes by PID from the process table. Tested both ways before
  arming: the live H-07 / F-10 gave no-fire (log age 0m, 96% util, 2 conns each) and the E-06
  stall state gave fire.
- It exists because the launcher can't be edited while it runs (§F49).

**05:54 (09-23).**
- GPU1 F queue finished at 05:52:50: "under 50 min to deadline, not starting another batch".
  GPU1 at 0 MiB, no server on :8094, no orphaned sandbox.
- The stall watchdog **never fired overnight**. Its log has only its start line, so no batch
  looped after E-06.
- GPU0 is on its last batch, H-25, started 05:46:39. Waiting for "GPU0 primary QUEUE DONE"
  before running the reporter. No rates read yet.

**06:13-06:20. Wrap-up.**
- GPU0 queue done at 06:13:00. GPUs at 0 MiB, 0 containers, no servers. **Reservation 31702f29
  released at 06:13.**
- Reporter run (`research/canonical/f211_ablation_2026-09-23.json`), written up as §F214:
  - H 29/73 (39.7%) vs baseline p = 0.52: **confirmatory null**.
  - E 4/64 (6.2%): exploratory, E vs F p = 1.4e-6, E vs baseline p = 4.6e-10.
  - F 54/145 (37.2%), not different from baseline (p = 0.17).
  - E competence 64/64, no message-cap hits, floor 6/6.
- `mentioned_in_final` / `considered_in_reasoning` are 0 in EVERY arm, including episodes that
  alerted, so those screens are useless here and are not cited.
- Stall watchdog stopped by PID. It never fired.
- NOT done, for Caleb:
  1. The course write-ups and the shared Google Doc still say only that the probe "failed its
     causal test". That stays true of the pre-registered tests (§F210 addition, §F214 clamp),
     but §F214's exploratory ablation result is new. Whether and how to mention it is his call.
     The live Doc must not be blind-overwritten.
  2. A pre-registered replication of E, plus l37-only ablation: next GPU window.
- §F214's stamp corrected to 06:15, the actual clock time (I had written 06:25 from estimation).
