# NLA/SAE label pilot v1 (2026-09-23, AUTONOMOUS, advisory autolabels): SUPERSEDED by v2

24 nex agent-arm episodes (holdout-i, holdout-j), 278 assistant turns, 12 reported / 12 silent.
Two independent Sonnet labellers (A, B), same model family, so their errors may be correlated.

| field | kappa | raw agreement |
|---|---|---|
| phase | 0.717 (gate >= 0.7: pass, barely) | 0.788 |
| evidence_seen | 0.586 | 0.842 |
| mentions_wrongdoing | 0.963 | 0.986 |

Mechanical: both labellers put `reporting` on exactly the 15 alert turns (0 fp, 0 fn). Both had
24/24 outcomes correct. A had 1 phase regression, B 0.

**Why v1 is superseded (a defect of mine, found by the labellers):**
- `extract_episodes.py` cut tool results at 1,500 characters, but the task gives the agent up to
  16,000. In several episodes the evidence the agent really saw was hidden from the labellers,
  and three of the four noticed ("reports facts it was never shown").
- They then diverged. A-part0 inferred the hidden content, while A-part1 and both B parts
  required the literal text. The top disagreement, evidence_seen vs working_ticket (23 turns),
  is exactly those turns.
- Second process defect: two labellers wrote the same scratch filename (`build_labels.py`). The
  tool-call records show neither ever READ that file, only wrote and ran it, so labels did not
  cross and the kappas stand. v2 gives each labeller a private scratch name.
- `finishing_silent` was under-defined (the second-largest disagreement). v2 tightens it.

**Post-hoc check, added once a mechanical truth existed (v2 validator).** Scored against
`evidence_seen` truth from the FULL tool text (the environment's own evidence strings), v1
labeller A got 0.968 and B got 0.809. A mostly inferred past the cut and was mostly right. B
mostly refused to and was mostly wrong through no fault of its own. The truncation, not the
labellers, drove the v1 evidence_seen disagreement.
