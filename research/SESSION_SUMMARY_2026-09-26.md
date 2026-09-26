# Session summary, 2026-09-22 → 2026-09-26

One long session (with several GPU grants and autonomous stretches). Everything below is committed and
pushed to `main`. Pointers go to the primary record; numbers come from the ledger, not from here.

## Outcomes

- **Final BlueDot course project SUBMITTED** 2026-09-26 ~00:05 PDT. Confirmation email received; editable
  until 4 October; feedback about a week after that. Course shows 100% complete.
  → `research/course-writeup/final-submission-answers-2026-09-25.md`
- **Second Rapid Grant ($500) APPROVED** 2026-09-24 to release BystanderBench as a public leaderboard.
  Application: `research/course-writeup/rapid-grant-application-2026-09-22.md`. Claim terms (no claim-by
  date; 12-month grant period; report within 60 days of wrap-up) are in project memory.
- **§F218: the ablation result replicated, confirmatory.** Removing the frozen probe direction after every
  layer: reporting 4/47 vs 20/44 for a random direction (Holm p = 1.8e-4). Removing it at the probe's own
  layer only: no effect (kill condition met). Open confound: the control matches the operation, not the
  removed variance. → `research/FINDINGS.md` §F211-§F218, `research/canonical/f215_replication_2026-09-24_final.json`
- **Write-up overhauled** (about 4,600 → 1,680 words, 9 figures). The shared Doc (same link, "anyone with the
  link can comment") is at Drive version 7. → `research/course-writeup/overhaul-2026-09-24/final_draft_v3.md`,
  `BlueDot-BystanderBench-2026-09-25.docx`, read-aloud MP3 (local only, not in git)
- **Per-turn label dataset v1**: 643 episodes / 6,901 turns, all token-aligned, across the agent arm, the
  human arm and incidents 2/3, with schema rules R1-R5 and a documented pre-R4 limitation.
  → `research/audits/nla_labels/DATASET_CARD.md`
- **§F216 (+ addendum)**: four nex capture families have token streams that omit tool calls. Not yet traced
  to published numbers.
- **Research log** entry for 2026-09-25 added to the Google Doc log (the 09-22 null line was never pasted).
- **Skills**: `claude-labelling` (PR #12) and the human-writing-check shape-tells update (PR #13) are merged
  into the public `SolshineCode/claude-code-skills`.

## Process lessons written down this session

- The night-1 stall watchdog could never fire (it filtered on an f211 pattern). Text-match process filters
  SIGINT the caller's own shell, and `setsid nohup` can leave SIGINT ignored. Fixed in
  `research/f211/stall_watchdog_f215b.sh`, recorded in the §F217 addendum.
- With `setsid nohup cmd &`, `$!` is not the script's PID. Find it by scanning `/proc` cmdlines.
- Drive "Manage versions → Upload new version" can be done in Chrome by intercepting the file-input
  `click()`. Method in `research/course-writeup/HOW-TO-SWAP-THE-DOC.md`.
- New human-writing tells: stub subtitles, echoed frames, trailing kicker tags (in the skill).

## State at close

- GPUs: no reservation and nothing running. Caleb put the local GPUs **on hold** on 2026-09-24 until he
  says otherwise.
- Repo and datasets are still PRIVATE.
- Next sprint: `research/plans/leaderboard-launch-sprint-2026-09-26.md`.
