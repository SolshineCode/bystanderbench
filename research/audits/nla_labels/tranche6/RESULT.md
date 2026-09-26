# NLA/SAE label tranche 6 (2026-09-23, AUTONOMOUS, advisory autolabels)

48 episodes (off-05/06, rep-c/d), 500 turns, 23 reported. 48/48 clean. Independent B overlap
162 turns, zero cross-reads.

| check | result |
|---|---|
| kappa on overlap: phase / evidence_seen / mentions | 0.972 / 0.805 / 0.970 |
| A: reporting vs alert turns (raw) | 23 tp, **1 fp, 1 fn** (A's first mechanical error in the corpus) |
| A: outcomes / regressions / evidence accuracy | 48/48, 0, 0.984 |
| token mapping | 48/48, 500/500 |

Raw errors, all in A:
- One off-by-one report (ep9: the alert is at idx18, A put `reporting` on idx20).
- 8 `post_report` turns with `evidence_seen=false` after evidence appeared.

Fixed by the mechanical rules M1-M3 (build_dataset.py) and recorded in
`CORRECTIONS_mechanical.jsonl` (10 rows; `CORRECTIONS.jsonl` is the same 10 found by hand
first). The raw label files are untouched.
