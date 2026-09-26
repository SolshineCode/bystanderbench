# NLA/SAE label pilot v2 (2026-09-23, AUTONOMOUS, advisory autolabels)

Same 24 episodes as v1 (nex holdout-i/j, 278 assistant turns, 12 reported / 12 silent). Two
independent Sonnet labellers, full tool results, tightened definitions, private scratch names.

| field | kappa v1 | kappa v2 | v2 raw agreement |
|---|---|---|---|
| phase | 0.717 | **0.841** | 0.881 |
| evidence_seen | 0.586 | **0.984** | 0.996 |
| mentions_wrongdoing | 0.963 | **0.973** | 0.989 |

- `evidence_seen` accuracy against the mechanical truth (the environment's own evidence strings
  in the full tool text): **A 0.996, B 1.000**.
- Both labellers: `reporting` on exactly the 15 alert turns (0 fp / 0 fn), 24/24 outcomes, 0
  phase regressions.
- All 33 phase disagreements were definitional (20 considering vs post_report, 13 orienting vs
  working_ticket). Adjudicated by rules R1/R2, now in SCHEMA.md. Final set:
  `pilot_v2_final_labels.jsonl` (both labellers' descriptions kept, `adjudicated` and `rule`
  flagged per row, 3 `mentions_wrongdoing` splits left null rather than guessed).

**CORRECTION (2026-09-23 ~10:20, found while building the token mapping).** The observation
below overstates what the labels show. The captured token streams CONTAIN the model's `<think>`
reasoning ("We need modify repo. Need inspect. …"), and the labels deliberately cover the
VISIBLE transcript only (the §F38 scope decision in SCHEMA.md). So "no `considering`" means no
deliberation in visible text. It does NOT mean the decision window is empty. Deliberation may
well be in the reasoning tokens, which are captured and unlabelled. Whether to label reasoning
spans too is a scope decision for Caleb. It would be the most direct target for an NLA.

**Observation:** `considering` occurs once in 278 turns. With reasoning off, nex never visibly
deliberates. It sees the evidence and then reports or finishes. Text labels can mark the
decision WINDOW (first evidence to the report or finish) but cannot describe what happens
inside it, because nothing visible does. That is the gap an NLA on the stored pre-decision
activations would target, and §F214's direction is the obvious first probe of it.

**Limits:** same model family for both labellers (correlated errors possible). One model, one
scenario. Autolabels are advisory until independently checked. No token-position mapping yet.
