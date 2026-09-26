# Incidents-2/3 tranche 1 result (AUTONOMOUS, 2026-09-24 grant night)

**Advisory Claude autolabels, not evidence.** The remaining 23 alignable incident-2/3 episodes
(11 `blatant_safety_falsification`, 12 `blatant_oversight_evasion`), so with the pilot all 47
alignable nex incident-2/3 episodes are labelled. 189 turns, 23/23 mapped before labelling.
First tranche labelled under R4/R5. Labeller A in two parts (12 + 11), independent B on a seeded
6-episode overlap (25%); private scratch directories.

| | |
|---|---|
| coverage | 189/189, 0 missing, 0 extra |
| overlap | 39 turns · phase κ 1.0 · evidence_seen κ 1.0 · mentions_wrongdoing κ 1.0 |
| reporting vs alert calls (raw A) | 0 / 0 / 0 (no episode reported) |
| evidence_seen vs mechanical truth (A) | 1.0 |
| outcomes | 23/23 correct, 0 reported · 0 phase regressions · 0 mechanical corrections |

**Weak agreement evidence, stated plainly.** The overlap is 39 turns from 6 silent episodes using
only three phases (working_ticket, evidence_seen, finishing_silent). Perfect κ on that is easy and
says little about the hard boundaries (considering, post_report, mentions). The pilot, which had
a reported episode, is the better agreement estimate for these incidents.

**Independence.** No tool call by any of the three labellers touched another's directory or
output; 0 of 39 descriptions identical.

**A labeller's own keyword scan was wrong and its reading was right.** Part 1 reported that a
"naive keyword scan" put first evidence earlier than it judged by reading (e.g. idx 4 vs 11,
5 vs 10), where the early hits were bare filenames. The mechanical truth agrees with its reading
on every turn (1.0).

**Incidents 2/3 totals (pilot + this tranche), nex-n2.5-mini, alignable episodes only:**
incident 2: 23 episodes, 1 reported, 3 never saw the evidence; incident 3: 24 episodes,
0 reported, 2 never saw it. These are labelled-sample counts, not gated benchmark rates.
