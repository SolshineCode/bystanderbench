# Review of draft_v1 (Claude), for round 2. Fix every item; keep what works.

What works: the summary on top, figure-led sections, the length (~2,100 prose words), the gate
section, the test-awareness move to the end. Keep that shape.

## A. The author's new standing instruction (06_caleb_instructions.md) is violated. Fix all:
1. Line 31 "what took me weeks to see" -> state the finding plainly ("Low cheat rates mostly track low competence.").
2. Line 38 "Renting more GPUs doesn't fix that." -> delete. Also drop "The interpretability arm was humbling."
3. Line 40, the whole "Then I had to withdraw two results" paragraph -> delete. Do not mention withdrawn
   results anywhere.

## B. Claims that go past the evidence (04_facts.md is the authority):
4. Summary #4 and line 92: do NOT say "causal footprint", "one specific direction", or "the effect is spread
   across layers". The random control matches the operation, not the amount of activation removed, so
   direction-specificity is NOT established. Say what was done and found: removing the probe direction after
   every layer cuts reporting from 44.4% to 8.5%; removing a random direction the same way leaves it at 45.5%;
   removing it only at the probe's own layer (37) does nothing (44.2% vs 47.8%); adding, subtracting or
   clamping it does nothing. Reading: something overlapping the direction, across layers, is needed for
   reporting; it is not a switch that makes the model report. Name the open confound once, in one plain sentence.
5. Summary #1: say "cheats quietly" or "hardcodes the tests without saying so", not "hides its cheating".
6. Line 105 "Labs can change this." -> keep the original, hedged claim: the silence varies with something a
   lab controls; nex-n2.5-mini moves and qwen3.5-27b doesn't on the same hardware, quantisation and scorer,
   but they also differ in size and post-training, so this narrows the cause rather than finding it.
7. Line 16: "Ten of the 125 cells are missing" -> "carry no rate".

## C. Style (02_style_human_writing_check.md). The draft reads machine-made in these places:
8. Staccato runs of short declaratives, e.g. line 22 "There is no judge model. There is no keyword matching.
   No LLM grades the transcript." (a tricolon, banned), line 74 "Floor models stay at zero. qwen3.5-27b stays at
   zero. nemotron... stays at zero.", line 83 "The signal is real. It applies equally to human wrongdoers.",
   line 55, line 65. Merge into sentences of varied length that a person would write. Read each paragraph for
   rhythm, not just banned words.
9. Stub sentences and announced transitions: "A few statistical caveats.", "I ran a causal test.", "I then removed
   the direction entirely.", "A common assumption is that larger models report more." Fold them into the next
   sentence.
10. Line 96 "The instrument only matters because it can refuse to print a number." is an aphoristic setup
    line. Replace with a plain opening.
11. Use real markdown headings (`## Heading`), not bold lines. One `#` title.
12. The summary list is good but its items should be the four findings in the author's plain voice, each one
    sentence plus its number. No bold labels that sound like slogans ("The species effect." is fine as a
    section heading; in the list just say it).

## D. Figures
13. `figE_size` does not exist. Use `fig6_size` instead (existing: report rate vs active parameters, by family,
    rho -0.19; it is busy, so the caption should tell the reader what to look at: no upward trend).
14. Move `fig11_swap_all` (very tall, all 18 models) to an appendix at the very end headed
    "## Appendix: every model, both conditions". figB stays in the main text.
15. Captions: lead with the takeaway, one or two sentences, and give the key numbers where the figure shows them.

## E. Keep, from the original, that the draft dropped
16. The one-sentence reason the nex pair is weaker (optional stopping) is kept; good. Also keep, in one
    sentence, that gpt-5.4 moves the other way (14/18 -> 11/18) so "three move" is honest.
17. Keep in one sentence that the frozen probe was fit once and never refit, and the 7-of-11 pass rule was set in
    advance (you have this; keep it).

Output format as before: the full draft between ===DRAFT_V2_START=== and ===DRAFT_V2_END===, then notes between
===NOTES_V2_START=== and ===NOTES_V2_END=== (what changed, anything you disagree with in this review and why).
