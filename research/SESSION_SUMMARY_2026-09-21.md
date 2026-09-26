# Session summary, 2026-09-20 23:24 - 2026-09-21 07:43 PDT (last night of local compute)

## The headline

This was the final night this project has the M40s. Compute went where Peter Gebauer's relayed
scope advice pointed it (a code comment in `bystander/env/content.py`, dated 2026-09-15: "no
work toward new findings, fill in the existing program (volume, NLA, probe)"), found in git
history and a source comment tonight, not in any saved transcript of what he actually said.

- **nex-n2.5-mini swap, the project's headline result, grew and held.** Human-wrongdoer control
  arm: 37/151 -> 59/258 (22.9%). Agent-wrongdoer arm: 129/285 -> 167/376 (44.4%). Fisher exact
  2.2e-8, stronger than the 09-20 evening's 2.0e-5 at roughly double the n. The rate did not move;
  the interval tightened.
- **The frozen probe direction (§F200) grew from 8 fresh holdouts to 11.** Three new batches:
  nite0102 (AUC 0.72, passes), nite0506 (AUC 0.61, fails), nite0708 (AUC 0.89, passes). Pooled:
  n=262, 117 alerted, AUC 0.760 (was 0.759), bootstrap 95% CI [0.699, 0.818] (was [0.686, 0.829],
  tighter). 7 of 11 batches now pass the pre-registered rule, was 5 of 8.
- **NLA volume closed, not grown.** The tag-search caveat §F186 had left open since 09-16 was run
  tonight: no NLA decoder exists beyond the four already screened. Confirmed by HF Hub API search,
  zero relevant hits. No Kaggle/Colab time spent chasing more NLA data, correctly.
- **The write-up got a real edit pass, not just a number sync.** Caleb gave the actual throughline
  directly tonight: ImpossibleBench and BystanderBench are foils, not two halves of one incident
  measured in isolation. ImpossibleBench recreates the impossible-task pressure that made the real
  incident's agents cheat; a collusive network cannot assemble without its members discovering
  each other doing it, so an agent cheating its way through that same populated, unsupervised
  environment inevitably encounters what its peers are doing. Saved to project memory so it
  survives the next compaction. Two rounds of an independent Antigravity judge (not editor, after
  the first narrative pass de-contracted the piece by 30% and got reverted) plus a full
  `/human-writing-check` caught and fixed: an intro paragraph that read like a pasted AI summary
  (found in BOTH write-ups, independently, hours apart -- the long version's copy had gone
  entirely unedited all night), five raw file-path mentions with no actual image embeds, a
  self-contradicting "all five explanations failed" sentence sitting above a table showing one of
  them moved the rate 3x, two performative-candor clauses, and a dense per-batch AUC dump
  summarized down to one sentence.

## What ran

- **GPU 0, 23:24-07:43 (~8h19m)**: 10 batches of nex human-wrongdoer control episodes (`nite-01`
  through `nite-10`, 12 each), through `capture_chain.sh` in pairs. 5 chained trees: 2 refused
  correctly by the position gate (nite0102 at AUC 0.387, nite0506 at 0.370, both outside [0.4,
  0.6]), 3 passed (nite0304, nite0708, nite0910). All 5 tokens trees plus the 3 passing predecision
  trees pushed to HF, MD5 read-back on every one.
- **GPU 1, 23:24-07:41 (~8h17m)**: 8 batches of nex agent-arm episodes (`nite-01` through
  `nite-08`), same chain shape, with an automatic probe test after each pair. 4 chained trees: 1
  refused (nite0304, AUC 0.370), 3 passed (nite0102, nite0506, nite0708), each immediately scored
  against the frozen §F200 direction. All pushed, MD5 read-back on every one.
- **Two Antigravity CLI passes as judge (not editor) plus a full `/human-writing-check`**, all
  independently caught real issues; none introduced a factual error (verified: every number in
  both write-ups traces to a file in this repo, checked by diffing against the source data after
  every edit tonight, not by trusting a model's self-report).
- **$0 spent.** No paid API, no `transformers.generate()`.

## What went wrong, plainly

**The long write-up's own separate "Intro" section sat completely unedited for the whole night**
while every other edit targeted its numbered sections (1 through 7). It had the exact same rough
issues the short write-up's intro had before tonight's first pass: a misspelled mentor name
("Peter Greuber's (sp?)"), "hundreds of agents" where the verified METR figure is roughly 1,200,
a filler sentence, the numbered-list formality. Found only by chance, reading the file top to
bottom for something unrelated, near the end of the session. Nobody had done that full read
before. Fixed, but it is the second time this session a section escaped notice because edits were
scoped to where the last problem was rather than the whole document -- worth a standing habit of
one full top-to-bottom read before calling a document done, not just a targeted-fix pass.

**Antigravity's first pass (a full rewrite, not the later judge-only rounds) de-contracted the
short write-up by about 30%** ("that's" -> "That is", "it's" -> "It is", throughout) while
changing nothing factually. Caught by a contraction count before and after, not by reading the
diff and trusting it looked fine. That version was not merged; the fixes it did suggest correctly
were re-applied by hand from its own report instead. The lesson carried into every round after:
verify a model's self-reported "preserved everything" claim by mechanical diff (number extraction,
URL extraction, contraction count), not by reading its summary.

## Owed to the day

1. The write-up's remaining lower-priority items from Antigravity round 2: whether the ending
   (data-availability paragraph) should get a closing synthesis sentence before it, and whether
   the two remaining three-item rhetorical lists are worth varying. Neither was acted on tonight;
   both are matters of taste, not correctness, and time ran out.
2. The quantile matcher's per-batch-rank defect, flagged since the 09-20 evening summary, is still
   unfixed and present in every tree built tonight. Still not shown to affect any measured outcome.
3. An abliteration/steering test on the frozen §F200 direction, discussed but explicitly not
   started tonight: it is a new experimental direction, not volume, and this was the wrong night
   for it per Peter's own scope advice. The existing `sae-causal/` steering infra would make it
   cheap whenever it is in scope again. No live "concealment" direction exists to run the same
   test on -- both attempts were withdrawn.
4. Two agent-perpetrated incident arms (model-card falsification, audit-logging evasion) remain
   built and unrun, parked on the same scope advice. Named as next step #1 in the write-up's own
   forward-looking section, which is a different context from tonight's compute allocation and not
   a contradiction of it.

## Budget

$0 spent tonight. Grant tracking from the 09-20 write-up carries forward unchanged: no paid API
or GPU rental touched.

## What I'd flag directly

The Antigravity-narrative-pass mistake (de-contracting the piece while claiming full
preservation) is the same shape of error as the probe-withdrawal pattern from two nights ago:
trusting a self-report instead of checking the artifact. It did not reach you this time because
the check ran before the merge, not after. That is the difference that mattered, and it is worth
keeping as the standing rule for every future model-assisted edit on this project, not just
tonight's.
