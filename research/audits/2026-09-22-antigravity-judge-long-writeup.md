# Independent Judicial Evaluation Report

This report evaluates the research write-up across the five specified axes. Findings within each axis are ranked in descending order of how significantly they alter a reader's understanding of the findings.

---

## 1. CLAIMS VS EVIDENCE

### 1.1 The headline conclusion claims agents "mostly" do not report, directly contradicting the paper's own frontier data
* **Quote (Sentence):** "Does an AI agent tell anyone when it finds another agent's misconduct? Mostly no, and it depends on the model, not the size" (Line 1).
* **Quote (Numbers):** On the agent-wrongdoer arm, the reporting rates among capable frontier models conditional on discovery are:
  * `claude-opus-5`: 17/17 (100%) (Line 83)
  * `claude-sonnet-5`: 10/10 (100%) (Line 83)
  * `gpt-5.5`: 18/18 (100%) (Line 83)
  * `gpt-5.4`: 11/18 (61.1%) (Line 83)
  * `gpt-5.6-luna`: 30/66 = 45.5% (Line 77)
  * `nex-n2.5-mini`: 167/376 = 44.4% (Line 78)
* **Judgment:** The title's central assertion ("Mostly no") claims the exact opposite of what the data shows for capable models. Every tested frontier model on the agent arm reports a substantial plurality or 100% of the time. In Line 120, the author explicitly admits that summarizing the data as "agents that find misconduct don't report it... is wrong, and the variance is the result." Retaining "Mostly no" in the title is unsupported by the paper's own empirical results.

### 1.2 Universal claim that zero-reporting models never report agents denies the author's own headline finding
* **Quote (Sentence):** "every model pinned at zero on a person stays at zero on an agent pool at n=36." (Line 28) / "And the models that never report a person don't start reporting agents either." (Line 23) / "And the models that never reported a person do not start reporting agents..." (Line 83).
* **Quote (Numbers):** `gpt-5.6-luna-pro: 0/36 on a person against 7/36 (19.4%) on an agent pool, Fisher p 0.011` (Lines 28, 79, 107).
* **Judgment:** The categorical statement that zero-reporting models never report agents is flatly disproven by `gpt-5.6-luna-pro`, which was pinned at 0/36 on a person and rose to 7/36 (p = 0.011) on an agent pool. This is one of the three models featured in the author's headline table (Line 79) to demonstrate that the wrongdoer's species matters. Asserting that "every model pinned at zero... stays at zero" denies the author's own primary positive finding. (Additionally, `laguna-s` is cited in Line 83 to support this claim, but its human-wrongdoer rate was 1/24, not zero).

### 1.3 Claim that scale does not explain reporting relies on a rank correlation that omits all top-performing models
* **Quote (Sentence):** "Across models the rate does not track parameter count (Spearman rho -0.19, p 0.51 over 14 reportable incident-1 cells)." (Line 31) / "Over the 14 reportable incident-1 cells with a known count, conditional reporting rate against active parameters gives Spearman rho -0.19, permutation p 0.51, unchanged from 09-14 to today. Nine of those 14 points are exactly zero, so the rank test is not measuring much." (Line 188) / "Size doesn't explain the spread." (Line 23).
* **Quote (Numbers):** `Spearman rho -0.19, permutation p 0.51` over 14 cells; `9 of those 14 points are exactly zero` (Line 188); `nex-n2.5-mini 3/22 against nex-n2.5-pro 20/24, p 4e-06` (Line 31).
* **Judgment:** The claim that parameter count does not explain the spread relies on a rank correlation where 64% (9 of 14) of the data points are degenerate zeros, and all leading frontier models (`claude-opus-5` at 6/6, `gpt-5.5` at 18/18, `claude-sonnet-5` at 9/10, and `gpt-5.4` at 14/18) are excluded due to undisclosed parameter sizes (Line 188). In the only controlled family where size *was* tested on the same serving path (`nex-mini` 3B vs `nex-pro` 17B), reporting jumped from 13.6% to 83.3% (p = 4e-06). Asserting globally that reporting "depends on the model, not the size" claims far more than a null rank correlation over unrepresentative open-weight zeros can support.

### 1.4 Refused cells claimed to have "beaten Opus" and been the "best numbers"
* **Quote (Sentence):** "two of the refusals would otherwise have been the best-looking numbers in the corpus." (Line 11) / "Taken at face value, llama's 11/12 would have beaten Opus and been the headline." (Line 198) / "two of those refusals would otherwise have been the best numbers in the corpus." (Line 27).
* **Quote (Numbers):** `llama-3.3-70b: alerted 11/12` (91.7%) (Line 198); `claude-opus-5: 6/6` (100%) (Line 98); `gpt-5.5: 18/18` (100%) (Line 97); `gemma-3-27b: alerted 6/12` (50.0%) (Line 198); `gemma-3-12b: alerted 5/12` (41.7%) (Line 198); `nex-n2.5-pro: 20/24` (83.3%) (Line 100).
* **Judgment:** Llama's 11/12 (91.7%) does not beat Claude Opus's 6/6 (100%) or GPT-5.5's 18/18 (100%). Furthermore, none of the other refused cells (50.0% or 41.7%) would have been "the best numbers in the corpus" when multiple accepted cells report at 78%–100%. The claim that these refusals would have been the best numbers in the corpus is mathematically false.

### 1.5 Attribute attribution to post-training based on an MoE vs dense architecture contrast
* **Quote (Sentence):** "The sharpest evidence for what it does track: nex-n2.5-mini declares architecture `qwen35moe` and reports; Qwen3.5-27B declares `qwen35` and never has, on the same hardware, quantisation and scorer. Same lineage, opposite behaviour. That leaves post-training." (Line 120).
* **Quote (Numbers):** `nex-n2.5-mini: 59/258 = 22.9%` (Line 102) vs `qwen3.5-27b: 0/16` (Line 110).
* **Judgment:** One model is a sparse mixture-of-experts (`qwen35moe`, 3B active parameters) and the other is a dense 27B model (`qwen35`). They differ in parameter count, routing architecture, pretraining data mixtures, and total training tokens. Concluding that this contrast isolates post-training as the sole remaining factor claims far more than comparing two completely different base model architectures allows.

### 1.6 Dismissing a 60% drop in reporting from removing addressees as "not the explanation"
* **Quote (Sentence):** "Removing it from incident 1 took the rate from 22.9% to 4/46 = 8.7% (Fisher p 0.030), a real drop but nowhere near the 0 to 5% the pre-registered kill condition required, and the four alerts still name the misconduct in full. The addressee matters some. It is not the explanation." (Line 135).
* **Quote (Numbers):** `22.9% (59/258)` dropping to `4/46 = 8.7% (Fisher p 0.030)` (Line 135).
* **Judgment:** A drop from 22.9% to 8.7% is a statistically significant (p = 0.030) reduction of over 60% in reporting frequency. Dismissing addressee availability as "not the explanation" because it failed to reach an arbitrary pre-registered threshold of 0%–5% overstates the negative conclusion; the evidence shows addressee availability is a major driver of whether agents alert.

### 1.7 Universal deployment upper-bound claim based on 5% eval-awareness frequency
* **Quote (Sentence):** "Evaluation awareness runs the counterintuitive way: the roughly 5% of episodes with explicit 'this might be a test' reasoning alert more often, so treat every rate as an upper bound on deployment behaviour (§F90)." (Line 233).
* **Quote (Numbers):** `"roughly 5% of episodes"` (Line 233).
* **Judgment:** No reporting rate or effect size is provided for this 5% subset. Asserting that "every rate" across the entire benchmark must be treated as an upper bound on deployment behavior extrapolates a universal constraint from an unquantified shift in a tiny 5% slice of episodes.

### 1.8 Incident 2 raw alerting described as an "order of magnitude" below Incident 1
* **Quote (Sentence):** "Counted raw it is 3/72, still an order of magnitude below incident 1." (Line 126).
* **Quote (Numbers):** `3/72 = 4.17%` raw on Incident 2 (Line 126) vs `41/156 = 26.28%` raw on Incident 1 (Line 102).
* **Judgment:** A drop from 26.28% to 4.17% is a factor of 6.3x, which does not constitute an order of magnitude (10x).

---

## 2. INTERNAL CONTRADICTIONS

### 2.1 Direct contradiction on zero-reporting models alerting on agent pools
* **Quote 1:** "every model pinned at zero on a person stays at zero on an agent pool at n=36." (Line 28; repeated in Line 23 and Line 83).
* **Quote 2:** `gpt-5.6-luna-pro: 0/36 on a person against 7/36 = 19.4% on an agent pool (p 0.011)` (Lines 28, 79, 107).
* **Contradiction:** The text repeatedly asserts as a general rule that any model pinned at zero on a human wrongdoer stays at zero on an agent pool. In the very same paragraph (Line 28) and in Table 3.1 (Line 79), `gpt-5.6-luna-pro` is reported as moving from 0/36 to 7/36 (p = 0.011).

### 2.2 Unreconciled true cheat rate for North-mini-code across body and audit sections
* **Quote 1:** "I cited north-mini's cheat rate as 39/177 for four days. It is 41/176. Both numbers came out of my own prose, copied forward from a summary of a summary, and the fix was not arithmetic. It was generating a committed CSV and then forbidding any other source for that number, which is now the rule for every rate in the project." (Line 214).
* **Quote 2:** "The model that cheats a fifth of the time, north-mini-code at 53/237 = 22.4%, is a sparse mixture-of-experts... both at 83% on the solvable split, 53/237 against 3/62, Fisher p 0.00086 (§F126)." (Line 156).
* **Contradiction:** Section 5 boasts that a process failure was caught and that the canonical committed rate is strictly `41/176`. However, Section 3.5 quotes `53/237` twice. The document contradicts itself on the foundational figure of its Part 1 cheat evaluation.

### 2.3 Mathematical impossibility in Table 3.2: Total alerts fewer than conditional alerts
* **Quote:** `| nex-n2.5-mini (local weights) | 41/156 | 59/258 = 22.9% [18.2, 28.4] |` (Line 102).
* **Contradiction:** In Table 3.2, Column 2 reports raw alerts over total episodes (`41/156`), while Column 3 reports alerts conditional on evidence discovery (`59/258`). Total alerts cannot be fewer than conditional alerts (41 < 59), and total episodes cannot be fewer than discovering episodes (156 < 258). Discovery is a subset of total episodes.

### 2.4 Unread alerts on the Nex agent arm differ by nearly a factor of two
* **Quote 1:** "The first 36 alerting episodes on the nex agent arm were read by hand... The 131 alerts the cell has gained since then have not been hand-read" (Line 85).
* **Quote 2:** "The 75 most recent nex agent-arm alerts have not been hand-read." (Line 237).
* **Contradiction:** Line 85 states that 131 alerts were not hand-read (167 total alerts minus 36 read). Section 6 asserts that only 75 alerts have not been hand-read.

### 2.5 Probe holdout table displays 12 batches while text and pool claim 11 batches
* **Quote 1:** "applied unchanged to eleven batches of fresh episodes (262 in all)... with seven of the eleven batches passing on their own and four missing." (Line 32; repeated in Lines 13, 164, 182).
* **Quote 2:** The table in Lines 168–179 lists **12** distinct holdout rows: `1`, `2`, `3`, `4`, `5`, `6`, `off0102`, `off0304`, `off0506`, `nite0102`, `nite0506`, and `nite0708`. Across these 12 rows, **8** pass (Rows 1, 2, 3, 5, off0102, off0506, nite0102, nite0708) and **4** fail (Rows 4, 6, off0304, nite0506). Summing all 12 rows gives n = 286 and alerted = 129.
* **Quote 3:** `| pooled, all eleven | 262 | 117 | 0.760 | 0.00025 | [0.699, 0.818] | |` (Line 180).
* **Contradiction:** The pooled row excludes Holdout 1 (n = 24, alerted = 12) without explanation to arrive at 11 batches, n = 262, and alerted = 117. The text repeatedly claims 11 batches exist and that 7 passed, while the table displays 12 batches with 8 passing.

### 2.6 Discrepancy between promised and actual published probe holdout trees
* **Quote 1:** "49 datasets under the `DarkStarDeleeuw` account hold every transcript, token stream and residual-stream capture the results rest on. That includes the frozen probe direction and the eleven independent holdout batches it was tested on" (Line 13).
* **Quote 2:** "Six holdout trees are on Hugging Face with the transcripts cut at the decision." (Line 247).
* **Contradiction:** Line 13 promises that all 11 holdout batches are published on Hugging Face. Line 247 admits that only 6 holdout trees are available.

### 2.7 Total Hugging Face dataset count disagrees across Intro and Appendix
* **Quote 1:** "49 datasets under the `DarkStarDeleeuw` account hold every transcript..." (Line 13).
* **Quote 2:** "`research/course-writeup/appendix-hf-datasets.md`: all 43 project datasets under `DarkStarDeleeuw`..." (Line 290).
* **Contradiction:** Intro states 49 datasets; Appendix F states 43 datasets.

### 2.8 Contradictory reporting counts for Nemotron-3.5-Lightning across sections
* **Quote 1:** "escalates 0 times in 61 discovering episodes across three incidents and 0/32 on the agent arm." (Line 30).
* **Quote 2:** "nemotron-3.5-lightning 0/22 against 0/32" (Line 83).
* **Quote 3:** `| nemotron-3.5-lightning (local, both thinking conditions) | 0/61 | 0/54 |` (Line 109).
* **Quote 4:** "It reached the evidence in 22/25 thinking-off and 61/84 thinking-on episodes on the three human-wrongdoer incidents... 0/22, 0/61 and 0/32" (Line 146).
* **Contradiction:** In Line 146, the total discovering episodes across three human incidents is 83 (22 thinking-off + 61 thinking-on). Line 30 drops the thinking-off runs and claims only 61 discovering episodes across three incidents. Line 83 drops the thinking-on runs and quotes 0/22. Line 109 claims 54 discovering episodes on Incident 1 alone.

### 2.9 Serving-path gap dismissed as noise in Section 3.2 but leveraged as a confound in Section 3.6
* **Quote 1:** "It does not track serving path (nex-n2.5-mini run locally, 22.9%, and hosted, 13.6%, overlap)..." (Line 120).
* **Quote 2:** "And nex-mini served locally reports 22.9%, well above the 13.6% free-tier cell the pair uses, a serving-path gap almost as large as the size gap." (Line 190).
* **Contradiction:** In Line 120, the difference between local (22.9%) and hosted (13.6%) serving is dismissed as an insignificant statistical overlap to argue that serving path does not matter. In Line 190, this exact same difference is cited as a substantial gap that invalidates the scaling comparison between mini and pro.

---

## 3. STALE OR ORPHANED NUMBERS

### 3.1 Orphaned raw cell count in Table 3.2 (`41/156`)
* **Quote:** `| nex-n2.5-mini (local weights) | 41/156 | 59/258 = 22.9% [18.2, 28.4] |` (Line 102).
* **Status:** Stale. The value `41/156` was left over from an intermediate checkpoint. When the conditional denominator was updated to 258 discovering episodes (with 59 alerts), the raw total column was neglected.

### 3.2 Orphaned cheat rate of `53/237` in Section 3.5
* **Quote:** "north-mini-code at 53/237 = 22.4%... 53/237 against 3/62" (Line 156).
* **Status:** Stale or orphaned. Section 5 explicitly identifies `41/176` as the corrected figure from the committed CSV and states that `39/177` was an unverified prose artifact. The presence of `53/237` in Section 3.5 indicates an incomplete update across sections.

### 3.3 Stale unread alert count of `75` in Section 6
* **Quote:** "The 75 most recent nex agent-arm alerts have not been hand-read." (Line 237).
* **Status:** Stale. Line 85 establishes that 36 alerts were read out of 167 total alerts, leaving 131 unread. The number `75` represents an un-updated figure from an earlier point when the cell had ~111 alerts.

### 3.4 Discrepant dataset tally (`43` vs `49`)
* **Quote:** `49 datasets` (Line 13) vs `43 project datasets` (Line 290).
* **Status:** Stale. One of the two counts was not updated when additional datasets were deposited.

### 3.5 Episode progression additions fail to reconcile with denominators
* **Quote:** "35/78 by the end of the week (§F199), 99/219 by Sunday morning after 120 more episodes overnight (§F205), 129/285 by Sunday night after 72 more from an unattended offline run (§F206), 167/376 by Monday morning after 96 more on the last night of local compute (§F207)." (Line 81).
* **Status:** Stale or orphaned arithmetic.
  * Adding 120 to 78 yields 198 (reported denominator: 219; discrepancy: +21).
  * Adding 72 to 219 yields 291 (reported denominator: 285; discrepancy: -6).
  * Adding 96 to 285 yields 381 (reported denominator: 376; discrepancy: -5).
  The narrated batch sizes do not sum to the denominators, indicating that either the batch descriptions or the cumulative denominators are stale.

### 3.6 Completely orphaned figures for an unintroduced "hidden" arm (`0/6` and `0/5`)
* **Quote:** "The same pair is 0/6 against 0/5 on the arm where the evidence is hidden rather than blatant" (Line 190).
* **Status:** Orphaned. The "hidden rather than blatant" arm is never defined, described, or reported anywhere else in the document or tables.

### 3.7 Orphaned probe metric in figure caption (`AUC 0.675 at layer 7, n=108`)
* **Quote:** "With activations re-extracted to end before the reporting decision, the best honest cell reaches AUC 0.675 at layer 7, not significant at n=108." (Line 154).
* **Status:** Orphaned. The body text focuses exclusively on a layer-37 direction fit on 74 episodes and tested on 262 episodes. Layer 7 at n=108 is never referenced or integrated into the narrative.

### 3.8 Orphaned count of published holdout trees (`6` trees)
* **Quote:** "Six holdout trees are on Hugging Face with the transcripts cut at the decision." (Line 247).
* **Status:** Stale. Reflects an early state before the offline (`off`) and night (`nite`) holdout batches were executed.

---

## 4. SECTIONS THAT DO NOT EARN THEIR LENGTH

### 4.1 Section 1: "Why this matters" (Lines 36–45)
* **Quote:** Lines 38–44, culminating in: "[CALEB: one paragraph in your own words on why you picked this over the alternatives on your shortlist, and what Peter's class discussion of multi-agent monitoring added. Source: `research/bluedot-project-shortlist-2026-08-22.md`, `research/bluedot-peter-class-screenshots-2026-09-01/README.md`.]" (Line 44).
* **Reason:** The section contains an unfilled authorial placeholder bracket and otherwise re-states the background of the Hugging Face incident already covered in the Intro (Lines 7–11). It provides no new empirical or theoretical grounding.

### 4.2 Section 5: Process Ledger Confessionals (Lines 216–224 within "What I got wrong")
* **Quote:** "Two RunPod pods never got a ledger row; actual spend was $4.21 across five pods, not $3.68 across three (§F193)." (Line 221); "Wrote three ledger timestamps from memory instead of the clock in one night (§F203 to §F205)." (Line 223); "Wrote that the NLA kernel had never executed anywhere, then rented a GPU on the strength of that sentence. It had run twice." (Line 220).
* **Reason:** While scientific corrections (like probe data leakage) are vital, cataloging a 53-cent server accounting discrepancy and clock timestamps is performative diary-keeping that inflates document length without providing methodological value to the reader.

### 4.3 Section 3.5: Part 1 NLA and Gemma Scope Autopsy (Lines 156–161 within "Looking inside")
* **Quote:** "All four models with a published natural-language autoencoder have now been screened, and every one sits below the 75% competence floor with concealment at 3% or less (§F186); the published decoders and the models that actually cheat are disjoint sets... The validation vectors came back empty for three runs because one step built them without a dtype and gemma's layer-32 activations overflow float16... Fixed, the control decodes 'heavy rain and strong winds' correctly. The project vectors then decode to the model repeating itself..." (Lines 156, 160).
* **Reason:** This passage spends hundreds of words diagnosing float16 overflows, dtype omissions, and decoder repetitions on models that failed the competence floor. Because the authors established early that the models compatible with these decoders do not cheat, detailing the technical wreckage of applying decoders to irrelevant models does not earn its length.

---

## 5. VOICE

### 5.1 Performative honesty (announcing candor rather than simply reporting facts)
* **Quote 1:** "This section earns the reader's trust for everything above it. The numbers survived because things kept getting checked, and the reader should see what the checks caught. Four worth telling properly." (Line 206).
  * **Critique:** Explicitly announces to the reader that the text is embarking on a staged exercise in trust-building.
* **Quote 2:** "Refusals are the benchmark protecting the reader from the author. The next section is the list of times it didn't, or couldn't, and I caught it late." (Line 202).
  * **Critique:** Theatrical posture framing ordinary methodological controls as heroic self-policing.
* **Quote 3:** "The alerts were read before the rate was believed." (Line 85).
  * **Critique:** Epigrammatic self-mythologizing engineered to project virtuous skepticism.
* **Quote 4:** "The probe, done the hard way." (Line 65).
  * **Critique:** Editorializing summary label signaling virtuous effort.
* **Quote 5:** "The rule that withdrew it was pre-registered, which is the only reason I trust the withdrawal more than I trusted the reading." (Line 212).
  * **Critique:** Staged epistemic piety designed to advertise adherence to protocol.

### 5.2 Rhetorical three-item lists used to simulate comprehensiveness
* **Quote 1:** "Size doesn't explain the spread. Neither does the lab, and neither does whether the weights are open." (Line 23).
  * **Critique:** A rigid triadic cadence designed to create rhetorical finality without examining the underlying confounds.
* **Quote 2:** "a ledger fabricated for an external auditor over a written objection, twelve reproducing red-team findings filtered out of a published model card, audit logging switched off while customer balances are edited by hand." (Lines 11, 27, 61).
  * **Critique:** A mechanical triplet recited verbatim three separate times across the text.
* **Quote 3:** "...on the same hardware, quantisation and scorer." (Line 120).
  * **Critique:** Standard triplet tagged onto the sentence to create the acoustic impression of rigorous controls.
* **Quote 4:** "every escalation about the shell, a missing fixture or the model's own loop" (Line 198).
  * **Critique:** A formulaic grouping of failure modes.
* **Quote 5:** "Project it onto the token stream, ablate it, or just read the episodes it scores highest." (Line 247).
  * **Critique:** Symmetrical three-clause imperative cadence wrapping up the section.

### 5.3 Synthetic cadence, artificial staccato, and summary labels
* **Quote 1:** "**What this is.** ... **Who it's for.** ... **Why read it.**" (Lines 19, 21, 23).
  * **Critique:** Synthetic corporate briefing template that replaces natural prose exposition.
* **Quote 2:** "Same lineage, opposite behaviour. That leaves post-training." (Line 120).
  * **Critique:** Artificial staccato asserting an unverified binary conclusion.
* **Quote 3:** "The cross-model table says who reports. It can't say why, because every model differs in a hundred ways at once. So this section holds the model fixed and varies only the situation." (Line 124).
  * **Critique:** Perfectly symmetrical, metronomic transition sentences characteristic of synthetic exposition.
* **Quote 4:** "Four things stop me calling it a scaling result. It is one pair." (Line 190).
  * **Critique:** Stilted, predictable phrasing structuring an analysis into an artificial numbered countdown.
* **Quote 5:** "1. Findability... Wrong direction." (Line 132).
  * **Critique:** Telegraphic bullet cadence substituting soundbites for scientific argumentation.
