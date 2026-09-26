# Brief for the rewrite (Antigravity), round 1

You are rewriting a course write-up for BlueDot Impact's Technical AI Safety course: Caleb DeLeeuw's
final project "Does your model say something when it sees something? BystanderBench". It is shared
with his class and facilitator and goes into the final course submission. Readers: AI-safety
classmates, technical, not all interpretability specialists.

Files in this folder:
- 00_current_writeup.md : the current write-up (~4,600 words incl. figure lines). The author thinks
  the SECOND HALF is weak: long, repetitive, dense with numbers, caveats scattered everywhere.
- 02_style_human_writing_check.md : the writing rules you MUST follow (read the whole file,
  especially the note at the top: the shape and feel of sentences, not just banned words).
- 03_bluedot_writing_advice.md : BlueDot's recommended writing advice (checklist).
- 04_facts.md : the ONLY numbers you may use. Includes a NEW confirmatory result (§F218) that the
  current write-up does not have; it replaces the old "the probe direction failed its causal test"
  ending of the probe section.
- 05_figures.md : the figures you can place.

Task:
1. KEEP the first third (everything before the paragraph starting "That is factor one") close to
   as-is: it is the author's own voice. You may trim it for length and fix clear errors, but do not
   restructure it. One exception: the "If you're reviewing this, a few things up front" paragraph is
   a wall of caveats; shorten it hard and keep only the caveats a reviewer needs before reading on.
2. OVERHAUL everything from "That is factor one" to the end. Rewrite it from scratch around the
   figures: say the finding, show the figure, give the one caveat that matters, move on.
3. TOTAL LENGTH: about half the current, so ~2,200 words of prose in total (figure captions not
   counted). Page space should be close to half figures: place at least 8 figures from the menu.
4. Structure: a short summary at the top (BlueDot advice #6) with the three or four findings stated
   plainly with numbers; meaningful section headings; one central question.
5. Push secondary caveats and detail into a short "Caveats and details" section at the end (or
   footnotes), not into every paragraph. Keep the caveats that change how a result should be read.
6. Use confidence numbers where the author gives them; state opinions plainly (advice #4, #9).
7. Keep first person, the author's voice. Follow every rule in 02_style_human_writing_check.md: no
   em dashes, no semicolons, no "not X but Y" constructions, no tricolons for rhythm, no stub
   sentences, no announced candor, no summary-restating closers, vary sentence shape.
8. Figure placement: a line `[[FIG:<id>]]` then a line `Figure N. <caption>`.

Write the result to `draft_v1.md` in this folder. Then write `notes_v1.md` listing: what you cut,
anything in 04_facts.md you chose not to use, every place you were unsure, and a word count of the
prose. Do not modify any other file.
