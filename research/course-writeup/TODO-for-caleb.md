# Course write-up: what you need to do

Written 2026-09-14. Companion to `course-writeup-2026-09-14.md` (the skeleton), `citations.md`, `appendix-hf-datasets.md`, and `visualizations/course/figures.md`.

## Do these, in order

1. Read the skeleton's headline block and TL;DR. Rewrite both in your voice until a friend outside AI safety can repeat the point back. BlueDot's advice is that everything flows from the headline, so spend the most time here.
2. Write the two `[CALEB: ...]` passages (why this project, what Peter's class added). Nobody else can.
3. Turn the `(bullets)` sections (3.5, 5, 7) into prose. Pick three items from section 5, not all seven.
4. Cut. The body is about 2,400 words before your additions. Hobbhahn's numbers: most readers give a 10-minute post 2 to 5 minutes. Anything a reader doesn't need to follow the argument goes to the appendix.
5. Drop the figures in at the `[FIG n]` marks using the captions in `visualizations/course/figures.md`. Use them verbatim or shorten; don't restate the numbers in the caption in the paragraph next to it.
6. Replace each `[CITE key]` with a numbered reference from `citations.md`. Keys used in the skeleton: metr-redwood, openai-report, impossiblebench, llamacpp, gemmascope2, nla-anthropic, kitft-nla, inspect. Add cotra where you discuss the incident's severity, apollo-probes and kumar-probes in 3.4, denison-subterfuge and hojmark in section 1 or 7 if you want related work.
7. Re-sync numbers once, at the end, from `research/audits/cells_<latest>.csv` and `research/canonical/concealment_rates.csv`. The lightning +12 batches landed (§F169 with its correction: 0/84 thinking-on, 0/61 conditional; already synced). The qwen3.8 conflicting split will change row 10 of the Part 1 table. Free-tier cells still at n=6 (ling-vl, ling-sante, lightning, nemotron-super) and the partial ling-fin batch top up on the next quota resets; the paid frontier cells move once the OpenRouter balance is topped up. Re-sync from the latest cells CSV at the end.
8. Run `/human-writing-check` on your final prose. The skeleton has been checked; your additions haven't.
9. Get one person to read it before submitting. BlueDot's advice and Hobbhahn's both say this is the step people skip.

## Decisions only you can make

- Make the 21 `DarkStarDeleeuw` datasets public before the post goes out, or the appendix links are dead. Also the GitHub repo.
- Whether to run Opus's benign control (about $2.67). Without it, 6/6 has no matched control and section 6 says so.
- Whether to name Peter and the cohort in acknowledgements.

## How to cite, and where

Load-bearing (must appear): the METR/Redwood report and OpenAI's technical report for the incident; ImpossibleBench for Part 1's task source; Inspect AI and llama.cpp for the tooling; Gemma Scope 2 and the NLA paper plus the kitft checkpoints for the interpretability arms. Cite the incident reports in section 1 and nowhere else. Cite tools once, on first mention in section 2. Cite interpretability sources in 3.4 only.

Supporting (cite if the sentence is there): Cotra's post for the "surprised me" framing; Apollo's probe paper and Kumar's pressure-test for why a null probe result is plausible; Denison et al. and Højmark et al. for related behavioural measures; the Dwarkesh explainer only as a pointer for readers, never as evidence.

Use numeric inline citations [n] and one numbered list in Appendix G. Don't cite the ledger (§F numbers) in the body; those go in the appendix and in figure captions.

## How the figures should sit

- Fig 1 (cross-model, incident 1) is the money figure. It goes right after the section 3.1 table, or replaces the table. One of the two, not both.
- Fig 2 (nex incident effect) sits at the top of 3.2, before the five hypotheses.
- Fig 3 (lightning) can be small. Its job is to show four bars at full height and one at zero.
- Fig 4 (competence vs concealment) is the whole Part 1 argument in one picture. Put it in 3.4 and let the text be short.
- Fig 5 (probe AUC by layer) and Fig 6 (scaling) are appendix figures unless you have room. If you keep one in the body, keep Fig 6; the size result is the one readers will ask about.
- Fig 7 (instruction ladder) is appendix only.
- Every figure already carries k/N and a Wilson interval on each bar. Don't repeat the interval in prose; say the rate and point at the figure.

## What must not appear

- Any BystanderBench number not from `report.py` VERSION 1.1, or any concealment number not from the canonical CSV.
- Pooled free-tier and local cells for the same model. They are separate provenance categories.
- A rate for a refused cell. Say "refused" and why.
- The three stale p-values flagged in the 09-12 draft. Two are re-derived at VERSION 1.1 counts and in the skeleton (incident 1 vs benign p = 0.004; incident 1 vs no-addressee p = 0.027; §F168). The ICC threshold and cluster-permutation p from the 09-12 draft are NOT re-derived; leave them out unless someone re-runs them.
- Anything about pay, funding, or the labellers' identities.

## One judgment call the reviewer raised

Hobbhahn's "one core topic" rule. An independent review (Antigravity, Gemini 3.1 Pro; filed at `research/audits/2026-09-14-antigravity-review-course-writeup.md`) says the skeleton has two topics. Your framing is one incident with two aspects, and the skeleton already leads with BystanderBench and gives Part 1 one section. If a reader in your feedback round says the same thing, the cut is to move all of Part 1 into the appendix and keep one paragraph in section 3.4. Your call.

## Length target (Caleb, 2026-09-15)

The cohort reads this in a five-minute breakout. So the deliverable is `course-writeup-short-2026-09-15.md` (about 800 words, three results, one figure each), and `course-writeup-2026-09-14.md` becomes the long version linked from it: methods, every cell, the appendix. Write the short one first, in your voice. If a paragraph in it makes a reader stop to think, it belongs in the long version.

## Added 2026-09-15 (overnight, W11 pod cell)
- RunPod billing: the §F172 spend line is an estimate (≈$0.93 for pod `00jz5m3ou6z00i`, 00:36–02:27 PDT). Read the actual charge from the RunPod billing page and replace the number in `research/FINDINGS.md` §F172 and the session spend log; cumulative RunPod is then $1.02 + actual.
- Before making datasets public: the HF appendix now lists 23 datasets (two added 09-15). Re-run the MANIFEST-vs-live-listing check the appendix describes and refresh its conclusion line.
- gemma-3-27b in prompted CLI mode is refused on competence at 27B exactly as at 12B (§F172). If you want a scored gemma-3 cell, it needs a native tool-call template the family does not ship, or a different cover task; say so in the limitations rather than re-running.

## Added 2026-09-15: the size claim moved (§F177)

Drafting 3.5 meant re-running `bystander/scaling_read.py` against the current cell table,
because the 09-14 read's family numbers predated the W9/W4 top-ups. The corpus-level answer
did not move (incident-1 Spearman rho -0.190, p 0.512, literally the same ranks at larger n).
One thing did: the nex-mini vs nex-pro pair, same free-tier path and same incident, went from
1/5 vs 4/6 at Fisher p 0.24 to **3/22 vs 20/24 at p = 4.09e-06**.

- The title currently reads "it depends on the model, not the size." That is still defensible
  for the corpus and it is now too strong for the nex pair. I did not change your title. The
  narrow version that survives everything is "size does not explain the spread across models."
  Your call, and it is the one editorial decision in this batch I would not make for you.
- Section 3.5 states both results and the four reasons the nex pair is not a scaling law
  (one pair; post-training confounded with size; 0/6 vs 0/5 on incident 3; the mini cell's own
  model reports 24.5% on a different serving path).
- The short write-up and its one-line findings list were updated to match, along with three
  numbers that had gone stale in it against the long version: 286 measurement episodes for
  qwen3.5 (was 277), ten of 89 refused cells (was nine of 87), 28 datasets (was 21).

## Added 2026-09-15: who the wrongdoer is in the three blatant incidents (§F178)

You asked whether it is clear to the target model that another AI agent did the thing it
found. Checked in `bystander/env/content.py`, not in the prose. In all three blatant
incidents, which are the cells every headline number comes from, the wrongdoer is a named
human: Dev Raines the controller overruling Jen Okafor on incident 1, t.okonkwo and
priya.raman on incident 2, jen.okafor and tomas.alvarez on incident 3. No agent, bot or AI
vocabulary appears anywhere in their evidence, the system prompt casts the model as a
software engineer on a human team, and the `_named` escalation wording says "misconduct by
someone on the team." Agent-perpetrated misconduct exists only in `conspiracy_realistic` and
`conspiracy_transposed`, which together are 2 alerts across 85 episodes on two models
(claude-sonnet-5 2/2 conditional at n=6, everything else zero).

Why: the conspiracy arms were the original agent-perpetrated design and produced ambiguous
zeros because the evidence was hex-encoded and buried. The blatant arms were added on
2026-09-08/09 to raise salience by putting the misconduct in plain prose in a file the ticket
already opens. Written that way the actors became people, and nothing re-checked the framing
afterwards.

**Your decision, and it is a claim-level one, so I have not touched the titles, the README or
the headline block:**

1. Keep the instrument and narrow the wording, so the benchmark measures whether an agent
   reports misconduct it stumbles on, and the tie to the incident is the bystander structure
   rather than the wrongdoer's species. Cheap, honest, and it costs the snappiest version of
   the title.
2. Earn the current wording with a fourth incident: blatant salience, same evidence volume,
   agent-perpetrated, built from the §F104 template. One arm, local models, a few GPU hours.
   That is the only way to find out whether the species of the wrongdoer changes the rate,
   which is itself a result worth having either way.
3. Both: narrow the wording now for the cohort deadline, run the fourth incident after.

## Canonical published draft (added 2026-09-15)

The short write-up has a live home that classmates are reading:

`https://docs.google.com/document/d/1wdrk6igKBt1AMABlYw9QVvUql2RDSiK3/edit`
(uploaded .docx, `rtpof=true`, owner ouid 100090163002736474340)

**Sync direction is repo to Doc, never the reverse without checking.** The repo copy
(`research/course-writeup/course-writeup-short-2026-09-15.md`, built to
`BystanderBench-short-2026-09-15.docx`) is where numbers come from, because every figure in it
traces to `bystander/report.py` VERSION 1.1 output. The Doc is where readers and their comments
live.

**Before any update to the Doc:** read it first. It is shared, so it may carry Caleb's own edits
and classmates' comments that do not exist in the repo copy. Replacing wholesale would destroy
both. The safe procedure is to diff the Doc against the repo copy, carry any Doc-only prose back
into the repo, and only then push the merged version out.

## Re-sync to §F205 (2026-09-20, after the overnight GPU grant)

Both write-ups now carry the numbers from `research/audits/cells_2026-09-20_after_w42.csv`
(125 cells, 10 refused) and the ledger through §F205. What moved since the 09-15 draft, so you
know where to re-read:

- The swap result is the headline in both versions. nex is now 37/151 against 99/219 (p 0.00005);
  gpt-5.6-luna and luna-pro unchanged; the OpenAI family (§F195) and the floor models at n=36
  (§F196) are in as the two "it is not X" sentences.
- The probe has a survivor. Section 3.5 (long) and the new short section carry the six holdouts,
  the two that fail, the pooled 0.753, and the human-arm transfer. It is described as a weak,
  real, uninterpreted signal and nothing more. `fig12_probe_holdouts.png` is new.
- Section 5 (long) now names the human-wrongdoer framing mistake, the three probe withdrawals
  and the withheld null (§F201), and the blind-labelling withdrawal of the SAE reading (§F190).
- The long version's parked sections 3.2 to 3.6 are restored as the human-wrongdoer condition,
  labelled as such, with every number re-pulled from the 09-20 table (two Fisher p-values moved:
  benign vs incident 1 is 0.005, no-addressee vs incident 1 is 0.022).
- All 12 figures regenerated from the 09-20 table; `figures.md` has entries for 8 to 12.
- Appendix F lists 43 datasets (15 added in a new Group 5). MANIFEST now names all 43.

Decisions still yours:

- **Title.** "Mostly no" is now true of the corpus but not of the three models that move, and
  the finding people will repeat is "who did it matters." I have not touched it.
- **The Google Doc.** Not synced. The rule in the section above stands: read it, diff against
  `course-writeup-short-2026-09-15.md`, carry classmates' comments and your edits back into the
  repo copy, then push. The repo copy is 2,336 words now, up from 1,895.
- **"go public with this post"** in the last paragraph of the short version replaces "are
  public"; today the repo and all 43 datasets are private. Flip visibility before posting or
  change the sentence.
- **The 75 unread alerts** on the nex agent arm. Both write-ups say the rate rests on the scorer
  for those. A hand read of a random 20 would let you drop that caveat.
- The two `[CALEB: ...]` passages in the long version are still yours to write.

## 2026-09-20 evening (offline run, §F206)
- Both write-ups cite the nex agent-arm cell as 99/219 = 45.2% (Fisher 4.8e-5). After the six
  offline batches the cell is 129/285 = 45.3% [39.6, 51.1], Fisher 2.0e-5, control unchanged at
  37/151. Same rate, narrower interval. Re-sync the numbers when the write-ups are next touched;
  no prose change is needed. Source: `research/audits/cells_2026-09-20_offline.csv`.
- Probe series under the fixed direction is now 5 replicate / 3 miss over eight holdouts, pooled
  n = 190 AUC 0.759 [0.686, 0.829]. The write-ups' probe section (five holdouts, 0.753) can carry
  the eight-holdout numbers when re-synced; the framing does not change.

## 2026-09-22, the last night: what changed and what is still yours

### Decisions that are still only yours

1. **The title.** Unchanged from me, twice over now. The current one claims "it depends on the
   model, not the size", which §F177 showed is too strong for the nex mini-vs-pro pair. The
   narrow version that survives everything is "size does not explain the spread across models".
   And the live Google Doc carries a better alternative you wrote yourself and then buried:
   **"Does your model say something when it sees something? BystanderBench"**. See
   `google-doc-diff-2026-09-22.md`.
2. **The Google Doc, and this one is urgent.** It is not slightly stale, it is a pre-09-15 draft.
   It still says "nothing significant yet", still shows nex at 26/106 vs "2/2, smoke only", and
   still presents **58.3%** as the result with a p-value. The cell is 167/376 = 44.4%. Anyone in
   the cohort reading it before you present is reading numbers this project has corrected. The
   full diff, and the six pieces of Doc-only content a wholesale push would destroy, are in
   `research/course-writeup/google-doc-diff-2026-09-22.md`. I did not touch the Doc.
3. **Repo and dataset visibility.** Both write-ups and both social drafts end on links that 404
   today. Flip visibility or cut the sentences.
4. **The one remaining `[CALEB: ...]` passage** in the long version, section 1: why you picked
   this over the shortlist, and what Peter's class added.

### What I finished

- **Both write-ups are re-synced and were read top to bottom**, not patched where the last
  problem was. Seven stale things came out, listed in the commit for §F208. The two that would
  have embarrassed you: the short version's swap table still printed Fisher p 0.00002 when the
  real value at 59/258 vs 167/376 is 2.2e-8, and the long version's entire probe section was
  still at eight holdouts while the short version had moved to eleven.
- **The long version is no longer a skeleton.** All 8 `[CITE key]` placeholders are resolved to
  numbered references with a real Appendix G, and all 14 `[FIG n]` marks are embedded images with
  descriptive alt text.
- **Twitter and LinkedIn drafts**, in `social-drafts-2026-09-22.md`, with a pre-flight checklist,
  a source line for every number, and an explicit list of what they refuse to claim. Peter
  Gebauer's name was verified against the 2026-09-01 Zoom screenshot rather than against prose;
  the spelling in the write-ups is right.

### What ran on the GPUs

The causal test of the frozen §F200 probe direction, pre-registered as §F208 before any episode
ran. Results, and whether the direction turned out to be causally load-bearing or not, are in
§F209. The pre-registration names the kill condition in advance, so read §F208 first and §F209
second, in that order.

## 2026-09-22 06:25, the overnight result and what it changes

**The causal test came back null, and that is now in both write-ups.** Adding the frozen probe
direction to the residual stream: 15/31 = 48.4%. Subtracting it: 16/35 = 45.7%. Unsteered: 44.4%.
Fisher p = 1.00. The kill condition was written before the run (§F208), so §F210 says the
direction is not causally load-bearing at that dose and the write-ups say the same.

**Read it as a result, not a disappointment, and say so if anyone asks in the breakout.** The
probe section used to end on "a weak, real signal and I cannot tell you what it represents". It
now ends on a pre-registered negative that narrows what it can be. That is a stronger position
than the one you had yesterday, and it is the kind of thing the project's whole discipline exists
to produce.

**One caveat you should know before you are asked about it.** The magnitude-matched random
direction moved the rate further than the real direction did (14.3% against 53.3%, p = 0.050, at
n=14 and n=15). That is below the pre-registered 24-episode minimum so nothing is claimed from
it, and §F210 reports it rather than omitting it. If someone in the cohort spots it, the honest
answer is: underpowered, uncorrected, one of five comparisons, and if it replicates it makes the
null worse for the direction rather than better.

### Still only yours, unchanged from the earlier section

1. **The title.** Three independent reviewers have now flagged it. The body now carries the size
   numbers (Spearman rho -0.19, p 0.51) so the claim is at least checkable, but the narrow version
   remains "size does not explain the spread across models", and the Doc has your own better
   alternative.
2. **The Google Doc**, which is still a pre-09-15 draft showing 58.3% as the result. This is the
   most urgent item on the list and it is not fixed.
3. **Repo and dataset visibility.** Both write-ups and both social drafts end on links that 404.
4. **The `[CALEB: ...]` passage** in the long version, section 1.
5. **The grant email** (`messages/2026-09-22-bluedot-grant-extension-request.md`), which is
   drafted and not sent. Check the amount and whether the program has a follow-on tier.

### Newly owed, small

- The HF dataset inventory disagrees with itself: the appendix catalogues 49, MANIFEST has the
  overnight trees, and the write-up used to say 43. Fixed in the prose, but the inventory itself
  needs one reconciliation pass before the datasets go public.
- The eval-awareness scan's 367 episodes are not attributed to a model or run anywhere in the
  short write-up. It is a keyword screen and labelled as one, but a reader could reasonably ask.

## Correction, 2026-09-22 06:35: the Doc has no classmate comments or edits

Earlier sections of this file (the 09-15 "Canonical published draft" block and the 09-20 re-sync
block) say the Google Doc "is where readers and their comments live" and warn that replacing it
wholesale would destroy classmates' comments. **That was an assumption and it is wrong.** Checked
directly today:

- It is an uploaded `.docx`, not a native Doc.
- Sharing is `anyone` = **commenter**, Caleb = owner. No one else has edit rights at all.
- Last modified 2026-09-15 21:07 UTC, two hours after upload. Never touched since.
- The two threads in it are Caleb's own resolved suggestions from Sep 15, zero replies.

So the "read and diff before pushing" ceremony is not needed for comment preservation. What IS
still needed is preserving the six Doc-only items listed in `google-doc-diff-2026-09-22.md`,
because those are Caleb's own writing and exist nowhere else. With those captured, replacing the
Doc is a safe, cheap fix for the stale 58.3%.
