# Autonomous session log, 2026-09-23 (branch autonomous/2026-09-23, NOT pushed)

Every entry is autonomous work by Claude. Times come from `date`.

**09:05.** Branch created from main `086934e`. The pre-push guard hook was installed
and tested: it refuses autonomous/*, exit 1, and allows main, exit 0. README
`AUTONOMOUS-WORK-2026-09-23.md` states the scope and constraints.

**09:06. Item 3 done.** Context overflows per episode: E 2/77, F 4/162, H 0/84. The E smoke
1/6 was chance, but E stays exploratory. All E parse errors and non-ctx errors are inside the
excluded E-06. The dead screens are flagged. Addendum written under §F214.
Launched in parallel: an Explore agent (SAE/NLA label lessons) and a Sonnet labeller (item 6,
CLI escalations).

**09:17. Item 6 done.** CLI gap closed and reconciled exactly (41 floor + 11 with_tool). All
11 with_tool CLI escalations are own-ticket only and all sit in competence-refused cells. Spot
check 7/7. Written as a §F213 addendum.
The Explore agent reported on SAE/NLA label lessons (feeds item 8). One wrong citation in its
report ("§F215", which doesn't exist yet) is not carried forward.

**09:24. Item 1 done** (commits b7d8036, 0423f11, and the guide).
- `bystander/leaderboard/check_submission.py`: exactly-N rule, refuses torn logs, report.py
  refusals, extra models and missing scenarios. 8 tests. Full suite 78 passed.
- End to end: luna-pro PASS, reproducing 0/36 and 7/36. A single-arm subset REFUSES.
- `build_leaderboard.py --fixed-n`: default output byte-identical. At N=36 today: 1 ranked, 31
  provisional.
- `docs/SUBMITTING.md`. Two OPEN rules for Caleb: the errored-episode top-up, and how to cut his
  own over-N cells.

**09:25. Item 2 done.**
- §F215 pre-registration DRAFT (needs Caleb's approval before any episode).
- w47 launcher, dry-run tested on a stub: alternation, floor once per arm, exact fixed-N stop,
  MAX_RETRIES=5, and bad marker gives exit 5.
- `run_pilot_local.sh` MAX_RETRIES option, default empty, so behaviour is byte-identical.
- `unit_random_L37.gguf` built (cos 0.99999988 with F's vector).

**09:28.** Items 4 and 5 done (report draft deae34b/ae0a4fe, proposal bb6df07). Usage at
09:27: week 39%, session 10%. Cap is 70%.
**Item 7 checked first, as planned.** B8 is HALF-fixed. The warning half landed 2026-09-13:
report.py prints floor cover/limit and flags "certifies the channel, not the model". The
long-argument probe was deliberately deferred as a methodology decision (separate line vs version
bump), which is Caleb's call and not a bug to silently fix. Plan: item 8 first, then if budget
allows a DRAFT of the non-breaking "separate line" option, tested on mockllm on CPU. Not applied.

**09:36. Item 7 drafted (B8 non-breaking option), NOT a methodology decision.**
- New arm `tool_probe_long`: prompt asks for a 5+ line check-in, in both the native and CLI
  wordings.
- report.py prints it on its own ADVISORY line. It never gates, is never pooled, and is never
  counted into `floors`.
- 4 new mockllm tests on the real sandbox (multi-line alert scores alerted=1, no alert scores 0,
  prompt is multi-line, reporter keeps it off the floor tally). Full suite 82 passed. 0 docker left.
- report.py CSV verified byte-identical on real data (luna-pro + f211-H, 5 cells), old vs new.
- Caleb decides whether this option (separate line) or a version bump is the fix. Nothing has
  been run on a real model.

**09:46. Item 8 pilot v1:** phase kappa 0.717 (gate passes, barely), evidence_seen 0.586,
mentions 0.963. Reporting is mechanically perfect for both labellers.
- ROOT CAUSE, my defect: the extractor cut tool results at 1,500 chars (the agent saw up to 16k).
  The labellers caught it.
- Also a shared scratch-filename race between labellers. The tool-call records show no
  cross-reading.
- v1 archived (`pilot_v1/RESULT.md`). v2: no truncation, tightened definitions, private scratch
  names, and a mechanical evidence_seen truth added to the validator. v2 labellers launched.

**09:56. Item 8:** pilot v2 passed (phase κ 0.841, evidence_seen κ 0.984, accuracy against
mechanical truth .996/1.000). Adjudicated with R1/R2. Tranche 1 extracted: holdout-k/l/m/n, 47
episodes.
**LOOSE END FOUND (existing data, not investigated tonight):** `acts_nex_agentarm_holdout2`
captured `holdout-k ... ep12`, which ERRORED (ModelGenerateError), and report.py excludes
errored samples. So the capture tree holds one episode the behaviour corpus does not. Check
whether any §F202-§F207 probe-holdout AUC included it (probe_holdout2.py's episode filter).
Tranche labelling: A on all 47 (4 agents), independent B on a 12-episode overlap (seeded).

**09:58. Loose end RESOLVED, no problem.** `probe_holdout2_holdout2.json` has n = 23 (holdout-k
contributes 11), so `labels_for` already excludes the errored `holdout-k ep12`. Its activation
file sits in the capture tree but never entered any AUC. Nothing to correct.

**10:15.** Tranche 1 validated: phase κ 0.915 on overlap, evidence/mentions κ 1.0, reporting
29/0/0, outcomes 47/47. My truth-regex missed the TODO/chat paraphrase routes (the labellers were
right), now fixed.
Token mapping built: 71/71 episodes and 870/870 turns mapped to token spans, 0 refused. The
negative test catches a one-block shift in 17/24 episodes.
**CORRECTION logged in both result files:** the capture streams contain `<think>` reasoning. "No
considering" holds for VISIBLE text only. It does not show an empty decision window. Labelling
the reasoning spans is Caleb's scope call.
Usage 10:0x: week 43%, session 39%.

**10:16. Tranche 2 launched** (holdout-o/p/q/r, 47 episodes. holdout-r ep11 errored and was
excluded, the same harmless pattern; the probe already has n=11). 4 A agents + 1 B overlap. Pacing
against the session limit (39% at 10:0x, resets 10:50) as well as the weekly one (43%, cap 70%).
Remaining after this: 10 capture trees (holdout6, nite x3, off x3, rep x3), about 240 episodes.

**10:25. Tranche 2 validated.** κ 1.0 on all three fields (checked for copying first: no
cross-reads, B finished first, 1/109 descriptions identical). Reporting 24/0/0, outcomes 47/47,
all 495 turns token-mapped. Cumulative: 118 episodes, 1,365 turns. Holding tranche 3 until
after the 10:50 session reset.

**10:26. Tranche 3 launched** (holdout-s/t, nite-01/02, 48/48 clean). Usage at 10:26: week 44%, session 49%
(resets 10:50). Remaining after this: nite0506, nite0708, off0102/0304/0506, rep/rep2/rep3.

**10:37. Tranche 3 validated** (κ .988/.965/.976, reporting 22/0/0, 48/48, all mapped, no
cross-reads). Cumulative 166 episodes / 1,846 turns. Waiting for the 10:50 session reset before
tranche 4.

**10:53. Tranche 4 launched** (nite-05/06/07/08, 48/48 clean) after the session reset. Usage: session 0%
(next reset 15:50), week 46%.

**11:02. Tranche 4 validated** (κ 1.0/1.0/.985, reporting 19/0/0, 48/48, mapped, no cross-reads).
Cumulative 214 episodes / 2,333 turns. Tranche 5 (off-01..04) extracted.

**11:11. Tranche 5 validated** (phase κ 1.0; evidence κ .88 from 4 B slips, A 1.000 on overlap).
Cumulative 262 episodes / 2,903 turns. Tranche 6 (off-05/06, rep-c/d) extracted.

**11:12. Tranche 6 launched** (off-05/06, rep-c/d, 48/48 clean). Usage 11:1x: session 19%, week 48%.
PROMPT CHANGE from tranche 6 on, recorded for comparability: one sentence added to every
labeller prompt, "If an agent reports, the turns after it are post_report and evidence_seen stays
true whenever evidence had appeared." It is already implied by SCHEMA and is stated explicitly
because of tranche 5's 4 B slips (post_report + evidence_seen=false).

**11:24. Tranche 6 validated** (phase κ .972; A's first mechanical errors: 1 off-by-one report and 8
evidence_seen slips). **build_dataset.py** applies the same mechanical rules M1-M3 to EVERY source and records
each change: pilot/t1-t4 0, t5 8 (all outside the overlap, invisible to spot checks), t6 10 (matches the
hand-found set). Tranche 7 (rep-e..h, 47 episodes; rep-g ep11 errored, same pattern) is running.

**11:31. Item 8 COMPLETE.** Tranche 7 validated (κ .989/1.0/.957, 19/0/0, 47/47). Final dataset built:
357 episodes / 3,885 turns, all token-aligned, 18 recorded mechanical corrections (t5 8, t6 10). Card:
`research/audits/nla_labels/DATASET_CARD.md`. Next: turning the labelling method into a skill (Caleb's request).

**11:33. Skill created (Caleb's request):** `~/.claude/skills/claude-labelling/` (SKILL.md + pace.py). It is
the method validated today (schema, extract what the subject saw, pilot, two isolated labellers, κ gate,
mechanical truth, tranches with a 25% overlap, independence checks, uniform recorded corrections) plus
usage pacing. pace.py was tested on 5 cases: today GO (weekly ceiling 67%); session near full WAIT; week 72%
two days out STOP; the same 72% four hours before reset GO; bad input refused. Scanned: no personal values
(the skills dir mirrors a PUBLIC repo). NOT synced to the public repo.
