# Tranche 8 result (AUTONOMOUS, 2026-09-23/24 grant night)

**Advisory Claude autolabels, not evidence.** The last 48 captured nex-n2.5-mini agent-arm
episodes. Labeller A: 4 Sonnet parts; labeller B: independent Sonnet on a seeded 12-episode
overlap. Numbers recomputed from the files by `validate_tranche.py` (not the labellers' own
counts), re-run 2026-09-24 00:2x when this file was written (it had been missed on the night).

| | |
|---|---|
| coverage | 541/541 turns, 0 missing, 0 extra |
| overlap | 169 turns · phase κ 1.0 · evidence_seen κ 0.978 · mentions_wrongdoing κ 0.987 |
| reporting vs alert calls (raw A) | 31 / 0 FP / 0 FN |
| evidence_seen vs mechanical truth (A) | 1.0 |
| outcomes | 48/48 correct, 29 reported · 0 phase regressions · 0 mechanical corrections |
