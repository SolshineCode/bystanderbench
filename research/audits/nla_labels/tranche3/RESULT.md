# NLA/SAE label tranche 3 (2026-09-23, AUTONOMOUS, advisory autolabels)

48 nex agent-arm episodes (holdout-s/t, nite-01/02, capture trees `acts_nex_agentarm_holdout6`,
`acts_nex_agentarm_nite0102`), 481 assistant turns, 21 reported / 27 silent. 48/48 clean, no
errored episodes. Labeller A did all episodes, an independent B did a seeded 12-episode overlap
(124 turns). B's tool-call record has zero reads of A's files or parts.

| check | result |
|---|---|
| kappa on overlap: phase / evidence_seen / mentions_wrongdoing | 0.988 / 0.965 / 0.976 |
| phase disagreements | 1 (working_ticket vs evidence_seen) |
| A: reporting vs real alert turns | 22 tp, 0 fp, 0 fn |
| A: outcomes / regressions / evidence_seen accuracy vs mechanical truth | 48/48, 0, 0.992 |
| token mapping | 48/48 episodes, 481/481 turns, 0 refused |

**Cumulative:** pilot v2 24 + t1 47 + t2 47 + t3 48 = **166 episodes, 1,846 turns**, all
token-aligned.
