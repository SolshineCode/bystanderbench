# NLA/SAE label tranche 5 (2026-09-23, AUTONOMOUS, advisory autolabels)

48 nex agent-arm episodes (off-01/02/03/04, capture trees `acts_nex_agentarm_off0102`,
`acts_nex_agentarm_off0304`), 570 assistant turns, 23 reported / 25 silent. 48/48 clean.
Labeller A did all episodes, an independent B did a seeded 12-episode overlap (156 turns). B's
tool-call record has zero reads of A's files or parts.

| check | result |
|---|---|
| kappa on overlap: phase / evidence_seen / mentions_wrongdoing | 1.0 / 0.88 / 1.0 |
| A: reporting vs real alert turns | 31 tp, 0 fp, 0 fn |
| A: outcomes / regressions / evidence_seen accuracy vs mechanical truth | 48/48, 0, 0.986 |
| token mapping | 48/48 episodes, 570/570 turns |

**evidence_seen κ 0.88 despite phase κ 1.0 was traced.** It comes from 4 overlap turns where B
labelled `post_report` but set `evidence_seen=false`, contradicting both its own phase and the
mechanical truth. On the overlap, A scores 1.000 against the truth and B 0.974. The final set is
A's, so B's slips do not reach it.

**The corpus's 2nd `considering` turn:** off-01 ep9 idx28, where the agent added a new
interpretation ("possible false external audit submission") and a self-imposed policy after
reporting.

**Cumulative:** 24 + 47 + 47 + 48 + 48 + 48 = **262 episodes, 2,903 turns**, all token-aligned.
