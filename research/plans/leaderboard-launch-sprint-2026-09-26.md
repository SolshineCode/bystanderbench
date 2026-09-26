# Sprint plan: spend the $500 Rapid Grant and launch the BystanderBench leaderboard (2026-09-26)

Written at the close of the 2026-09-22 → 09-26 session, for the next sprint. Scope, budget and
promises come from the grant as submitted (`research/course-writeup/rapid-grant-application-2026-09-22.md`,
approved 2026-09-24) and the model list agreed with Caleb (`research/plans/leaderboard-model-list-2026-09-22.md`).
**Promise to BlueDot: leaderboard public within ~6 weeks of the money arriving, kept current 12 months.**

## 0. Before any spend (Caleb's steps and decisions)

| # | item | why it gates |
|---|---|---|
| 0.1 | **Claim the $500 grant** in the BlueDot portal (and the $100 one, if still unclaimed). No claim-by date, grant period ~12 months from 2026-09-24. | Money arrives only after a claim; the 6-week clock starts at disbursement. |
| 0.2 | **GPU status.** Caleb put the local GPUs on hold on 2026-09-24. Open-weight rows use the $40 rented-GPU line unless he lifts the hold. | Decides where qwen3.5-27b, gemma-4-31B etc. run. |
| 0.3 | **Two OPEN rules in `docs/SUBMITTING.md`**: errored-episode top-ups, and what to do with his own historical cells above 36. | The fixed-N rule is not final until these are. |
| 0.4 | **B8 long-argument floor**: advisory line (as drafted) or a version bump. | Changes what the board prints. |
| 0.5 | **Visibility.** Repo `SolshineCode/silent-concealment-detection-lab` is PRIVATE, and so are the 49 `DarkStarDeleeuw` datasets. Making them public needs his explicit yes, asked as a yes/no question (standing rule). The HF inventory needs one reconciliation pass first. | The write-up says the release is coming. Nothing public can link to private data. |
| 0.6 | **Per-launch approval for every paid run** (standing rule). Each batch below is proposed with its model list, N and estimated cost, and waits for his go-ahead. | Real money. |

### Status update 2026-09-26 (Caleb's answers)
- 0.1: Caleb will claim. Claiming is also how the (already spent) $100 grant is reimbursed.
  Reminder routine fires 2026-10-03 09:05 PDT.
- 0.3: DECIDED, recorded in `docs/SUBMITTING.md`. Errored episodes: top up exactly the errored count
  once, else provisional. Over-36 historical cells: ranked view at N = 36 (first 36 by run order),
  plus a view toggle showing all episodes ever run per model, unranked, with a note that more
  trials per model is the long-term intention (build this in section 4).
- 0.4: leaning A (advisory long-argument line) but worried about the cost of 6 extra episodes per
  model; a zero-new-run middle ground was proposed 2026-09-26, awaiting his pick.
- 0.5: YES to public (repo + BystanderBench datasets), after the pre-release audit. Datasets from
  other projects stay private unless he says otherwise.
- 0.6: approvals will come per run as they're proposed.
- Compute sponsorship outreach: notes kept outside this repo (Caleb's private notepad), since the repo is going public. Measured basis: ~3-4 A40-min per ~30B episode, so launch open-weight rows ≈ 10-25 A40-h (covered by the $40 line).

## 1. Smoke test the new shape (day 1)

Top up ONE cheap paid model and ONE free model to N = 36 through the current launcher. Measure cost
per episode against the estimate (opus-5 ran at 2.1x its projection), and check `check_submission.py`
passes the result. Only then scale. Record the measured $/episode in `research/canonical/grant_spend.csv`
(new rows, grant-2 tagged).

## 2. Runs (weeks 1-2), in this order

1. **Free-tier top-ups first** (Tier 1a `:free` rows), because free endpoints can vanish. A withdrawn
   endpoint is listed "incomplete, endpoint withdrawn", never dropped.
2. **Cheap paid top-ups** (gpt-5.x, sonnet-5, gemini-3.1-pro, opus-5 at about $22, the largest).
3. **Tier 1c new models** (13 models, about $114 estimated): floor first, then 1-2 episodes, then N.
4. **Open-weight rows** on rented GPU (or local if 0.2 allows): qwen3.5-27b, gemma-4-31B agent arm.

Budget lines: launch runs $180, upkeep $70, submission checks $40, blind human checking $100, rented
GPU $40, margin $70. **Stop and report if any line is 80% used.**

## 3. Blind human checking, round 2 ($100)

Four packets at $25, same raters and protocol as round 1 (`labelling/`). Spot-read rendered items
before sending (CLAUDE.md rule 6). Do not prepare these until Caleb says so (standing instruction).

## 4. Build the leaderboard (week 2-3)

- `visualizations/build_leaderboard.py --fixed-n` over the new cells CSV. Every rated row at N = 36 per
  scenario; refused rows shown as refused.
- Pick the host with Caleb (GitHub Pages from the repo, or an HF Space under the private-until-release
  account). It must rebuild from the same CSV the write-up quotes.
- Submission path: `docs/SUBMITTING.md` + `bystander/leaderboard/check_submission.py` (8 tests), plus a
  12-episode spot re-run per outside submission, paid from the $40 line.
- Consider adding the per-turn label dataset (`research/audits/nla_labels/`, 643 eps / 6,901 turns) as a
  release artifact, with its card's limitations.

## 5. Release (week 3-6)

Repo and datasets public (after 0.5). Update the shared Doc's release sentence to a link. The social
post drafts are in `research/course-writeup/social-drafts-2026-09-22.md`; Caleb posts them himself.
Tell BlueDot it's live (a line to team@bluedot.org).

## 6. After launch

- Upkeep: new frontier models at N = 36 from the $70 line.
- **Grant reports**: a short report within 60 days of wrapping up, for each grant ($100 and $500).
- Apply for Tier 2 funding once the board is up (models priced out at $70-250 each, N = 50-100 for
  everyone; candidate funders in the model list, none applied to yet).

## Research threads NOT in the grant's scope (only if Caleb picks them up)

- Variance-matched ablation control for §F218 (the open confound). Needs GPU time.
- §F216 trace: which published results used the four capture families whose streams omit tool calls.
- Agent-wrongdoer versions of incidents 2 and 3 (built, unrun); a copy-of-self wrongdoer condition.
- `~/autonomy/state/gpu_factors.json` is stale (GPU1 measured about equal to GPU0 in §F211).
