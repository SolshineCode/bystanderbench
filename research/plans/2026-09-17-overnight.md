# Overnight plan, 2026-09-17 21:10 PDT -> 07:30

**Budget: $13.83 of the $100 grant. Plan spends about $8 and keeps ~$6 in reserve.**
Framing for the extension request: every dollar tonight buys either a tighter interval on
the one significant result or a decisive answer on the only other model that moved.

## The state this plan starts from

16 testable within-model pairs, one significant: nex-n2.5-mini 26/106 -> 24/47, p = 0.0025.
The shape is a boundary, not a trend (F191): ceiling models cannot move, floor models do not
move, and the one model reporting at an intermediate rate moves a lot. The only hint that the
boundary is soft is GPT-5.6, where both variants go from zero to non-zero without significance.

## Paid, about $8 of $13.83

**P1. GPT-5.6-luna and gpt-5.6-luna-pro to n=36 on BOTH arms.** Currently luna is 0/6 -> 3/6
(p 0.18) and luna-pro 0/18 -> 3/18 (p 0.23). These are the only hosted models that move at all.
At n=36 per arm, a true 0% vs 17% difference is detectable; at n=6 and n=18 it is not. Either
outcome is worth the money: significance means the effect is not unique to one open-weight
model, and a null at n=36 means nex is genuinely the exception and the paper says so.
Guards: balance floor $4, hard cap $8, MAX_CONNECTIONS 4, cheapest model first.

**Not funded tonight, deliberately.** Opus and Sonnet are at ceiling in both conditions and
cannot move; more episodes there buy nothing. Gemini barely discovers. No RunPod: F186 settled
that the NLA-capable models are exhausted, and F189 showed the probe's blocker is a
cut-matching bug, not a shortage of episodes.

## Free, $0

**F1. Free-tier agent-arm top-ups** after the 17:00 cap reset, including a solo retry of
nex-n2.5-pro, whose 12-episode run hung for four hours on 09-15 and was killed by PID.
**F2. More local nex agent-arm episodes** on both M40s: tightens the headline interval and
feeds the probe, which is the thing most limited by n.

## Engineering owed

**E1. The cut-fraction gate (F189).** `decision_index.py` must assert that the matched cut
fraction for silent episodes is within about 0.45-0.55 of the alerting ones BEFORE anything is
fitted. The current failure put alerting cuts at 78.8% of transcript and silent at 5.3%, which
produced an AUC of 0.921 that meant nothing. This is the single highest-value engineering task
because it unblocks a legitimate probe number.
**E2. Re-cut and refit the probe** once E1 passes its own negative test.

## Writing

**W1. Restructure the short write-up** to Peter's brief: the measurement is needed and did not
exist, ImpossibleBench as the narrative of investigating the incident's two factors, the
different situations and human-vs-agent as the spine, visuals carrying the argument, and a long
list of open questions at the end.

## Verification at wind-down

Every landed cell through `report.py` VERSION 1.1; every claim with its k/N and Wilson interval;
spend reconciled against `research/canonical/grant_spend.csv` with any new line marked confirmed
or estimate; findings appended, never edited; push.
