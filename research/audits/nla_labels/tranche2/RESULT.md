# NLA/SAE label tranche 2 (2026-09-23, AUTONOMOUS, advisory autolabels)

47 nex agent-arm episodes (holdout-o/p/q/r, capture trees `acts_nex_agentarm_holdout4/5`), 495
assistant turns, 20 reported / 27 silent. holdout-r ep11 errored and is excluded (the probe
holdout already has n=11, the same harmless pattern as tranche 1). Labeller A did all episodes,
an independent B did a seeded 12-episode overlap (109 turns).

| check | result |
|---|---|
| kappa on overlap: phase / evidence_seen / mentions_wrongdoing | **1.0 / 1.0 / 1.0** |
| A: reporting vs real alert turns | 24 tp, 0 fp, 0 fn |
| A: outcomes / regressions / evidence_seen accuracy vs mechanical truth | 47/47, 0, 1.000 |
| token mapping | 47/47 episodes, 495/495 turns, 0 refused |

**Perfect agreement was checked for copying before being believed.**
- B's tool-call record has zero reads of `labels_A_*`, `scratch_T2A*` or `tranche2/part*.json`.
- B finished (10:22:21) before A parts 0 and 1 wrote their files (10:23).
- Only 1 of 109 free-text descriptions is identical between A and B.
The agreement is genuine. R1-R3 make the categorical calls nearly deterministic, while the
descriptions stay independently written.

**Cumulative:** pilot v2 24 + tranche 1 47 + tranche 2 47 = **118 episodes, 1,365 turns**, all
token-aligned.
