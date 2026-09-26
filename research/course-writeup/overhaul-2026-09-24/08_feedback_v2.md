# Review of draft_v2 (Claude), for round 3. v2 is much better: keep its sections, figures, headings,
# length and the corrected probe/intervention paragraph. Fix only these.

1. FIRST THIRD WAS REWRITTEN, NOT KEPT. The author asked to keep it close to as-is. Restore these from
   00_current_writeup.md, trimmed but in the author's own words and sentence shapes:
   - the paragraph "As part of Peter Gebauer's BlueDot Course, and the generous funding of a BlueDot Rapid
     Grant, I've undertaken to study two key aspects..." with the two factors, (1) concealment and (2) lack
     of human alerts, and "measure these two factors in isolation, both as black box benchmarks and as
     internal representations using probes and Natural Language Autoencoders" (fix the one grammar slip
     "Open AI" -> "OpenAI"; keep everything else close);
   - "Factor one from the incident is concealment, so that's where I started." to open the concealment section;
   - the concealment section's original wording where v2 flattened it (e.g. "Ten model configurations, every
     passing solution audited by hand."), minus the three deletions already made (weeks, GPUs, withdrawals).
2. Line 67 is WRONG: "with a 7-of-11 pass rule set in advance". The rule set in advance was per batch:
   holdout p < 0.05 and AUC >= 0.70 counts as a replication. 7 of 11 is the OUTCOME. Also say the transcripts
   are cut before the agent commits to escalating, so the probe cannot read the alert itself (one clause).
3. Line 51 logic: "not an OpenAI trait, because gpt-5.4 moves the other way" joins two different points. Say:
   not every OpenAI model moves (gpt-5.5 reports 18/18 both ways; Claude Opus and Sonnet sit at the ceiling
   both ways), and gpt-5.4 even goes slightly the other way (14/18 -> 11/18), so "three move" is three of
   eighteen, not a clean split.
4. Figure 4 caption: delete "A one-line strip summarises the other 15 models" (the figure has no strip).
5. Figure 5 caption and line 63: give the permutation p (0.51) with rho -0.19; "no upward trend" is the
   point; drop the word "flat" before a correlation.
6. Restore a SHORT limits section before the appendix, `## Limits`, 4 bullets max, each one sentence:
   everything is synthetic and one environment per incident; the agent-pool effect rests on three of
   eighteen models and one incident; models pinned at zero or at the ceiling can't show an effect; I can't
   see inside hosted models. (Test awareness already has its own section; don't repeat it.)
7. Style passes still needed (02): line 21 and line 32 are runs of short same-shaped declaratives; vary
   them. Line 45 "Harmless novelty gets ignored." is a stub; fold it. Line 77 "It is not a switch that makes
   the model report." after "Something overlapping... is needed" reads as a "not X" flourish; merge into one
   sentence: "Something overlapping the direction, spread across layers, seems to be needed for reporting,
   though adding more of it does nothing."
8. The summary list: keep it, but put a one-line lead-in that states the incident stake first (the ~1,200
   agents, none alerted a human), since the summary is what a skimmer reads.

Same output format: ===DRAFT_V3_START=== ... ===DRAFT_V3_END===, then ===NOTES_V3_START=== ... ===NOTES_V3_END===.
