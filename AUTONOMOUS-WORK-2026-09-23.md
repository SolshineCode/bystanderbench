# AUTONOMOUS WORK: branch `autonomous/2026-09-23`

**Everything on this branch was done by Claude (Opus 5.5, Claude Code) working autonomously on
2026-09-23, without Caleb reviewing each step.** Caleb set the scope and constraints in chat. He
did not review the contents. Treat all of it as a draft for his review, not as settled project
work.

- **Merged to `main` and pushed on 2026-09-23 at about 14:00, on Caleb's explicit instruction**
  ("Push and merge it all to main"). That publishes the work. It does NOT mean each item was
  reviewed: §F215 is still a pre-registration DRAFT needing his approval before any run, and
  the OPEN rules and decisions below are still his.
- (Before merging:) local only until Caleb said otherwise. A local `.git/hooks/pre-push` hook
  refuses to push `autonomous/*` branches (tested both ways). The branch has no upstream.
- **No local GPU use, no paid API calls, no messages sent, no shared Doc edits.**
- **Claude autolabels are advisory.** Any label here is a single-agent autolabel (CLAUDE.md
  interpretability rule 3), not evidence, until checked independently.
- **No human-review prep** (Caleb, 2026-09-22).
- Token budget: Claude Code subscription only, never usage credits. Self-cap at 70% of the
  weekly limit.

## Scope Caleb approved (2026-09-23 ~09:00)

1. Leaderboard release tooling: submission checker, submitter docs, fixed-N leaderboard page,
   tests.
2. Pre-registration §F215: E replication + l37-only ablation, with launchers hardened by
   `--max-retries`.
3. §F214 loose ends: context overflows per arm, flag the dead `mentioned_in_final` /
   `considered_in_reasoning` screens.
4. Draft of the 60-day report on the first $100 Rapid Grant.
5. Proposed write-up wording for §F214 (a proposal file only, the live Doc untouched).
6. §F213 gap: the 41 CLI/prompted escalations.
7. Verify, and if still real fix, the B8 floor bug (`tool_probe` over-certifies).
8. Labelling that would let someone train a behaviour-specialised SAE or NLA, based on what the
   related projects learned.

## Log

See `research/f211/NOTES-2026-09-23-autonomous.md` for the running log, with times from `date`.
