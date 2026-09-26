# Tranche H2 result: second human-wrongdoer tranche (AUTONOMOUS, 2026-09-24 grant night)

**Advisory Claude autolabels, not evidence.** Human-arm episodes 49-96 of the alignable order
(`cids.txt`, seed 20260925, 0 overlap with H1). 48/48 pre-mapped to token spans (467 turns)
before labelling. Same SCHEMA.md and prompts as H1 plus ONE added sentence: watch for the
evidence inside long ci/logs dumps (added because of H1's nex-pos-j ep8 slip). All numbers
recomputed from the files by `validate_tranche.py`.

| | |
|---|---|
| coverage | 467/467 turns, 0 missing, 0 extra |
| overlap | 95 turns · phase κ 0.985 (1 disagreement, evidence_seen vs working_ticket) · evidence_seen κ 0.968 · mentions_wrongdoing κ 0.883 |
| reporting vs alert calls (raw A) | 12 / 0 FP / 0 FN |
| evidence_seen vs mechanical truth (A) | 1.0 |
| outcomes | 48/48 correct, 10 reported · 0 phase regressions · 0 mechanical corrections |

**Independence check.** B's only match for A-side names is its own prompt ("Never open
labels_A_*"); part 2's only match for B-side names is a directory listing taken after it had
written its own file. 0 of 95 overlap descriptions identical. Finish times 00:32-00:36.

**Notes.** Labeller B's summary said "8 silent episodes" in one place and 10 in another; the file
has 2 reported / 10 silent. Self-reported counts are not used anywhere. Part 1's labeller
caught its own first-evidence error (a `grep reconcil` whose output contained d.raines' lines)
by cross-checking the raw text before writing.
