# Independent Evaluation Report: `writeup.md`

---

### 1. CLARITY OF THE LEAD

A reader who knows nothing about AI safety will **not** understand what was built or what was found from the first 150 words (lines 1–7). 

* **What was found:** The lead reports zero findings or data points from the author's work.
* **What was built:** The benchmark environment, cover task, and reporting mechanisms are never described.

The sentence that decisively loses the reader is:

> **Line 7:** *"I measure both first as black box benchmarks, then go looking for them inside the model's own activations with probes and natural language autoencoders."*

This sentence introduces abstract technical machinery (*"black box benchmarks"*, *"activations"*, *"probes"*, *"natural language autoencoders"*) without grounding them in the physical setup of the experiment or stating the result.

---

### 2. CLAIMS VS EVIDENCE

*(Ranked from most to least consequential in altering a reader's understanding of the findings.)*

#### Finding 2.1: Sweeping claim in the title that reporting does not depend on model size
> **Line 1:** `"# Does an AI agent tell anyone when it finds another agent's misconduct? Mostly no, and it depends on the model, not the size"`
> **Numbers beside it:** No parameter counts, size sweeps, or scaling evaluations are reported anywhere in the write-up.

*Judgment:* Stating in the headline that reporting *"depends on the model, not the size"* claims a finding that was never tested. The paper compares arbitrarily selected commercial and open models across differing architectures, training recipes, and release vintages, with zero controlled parameter ablations.

---

#### Finding 2.2: Claiming the benign control proves alerts track misconduct rather than novelty
> **Lines 105–107:** *"The rate runs from zero to about half depending on what the agent walked into, and the benign control at 0/23 says the alerts track misconduct rather than novelty."*
> **Numbers beside it:** Line 98: `something odd but harmless | 0/23 [0.0, 14.3]`

*Judgment:* With $N=23$, the upper bound of the Wilson 95% confidence interval is 14.3%. That upper bound is higher than the report rates for actual misconduct in the same table (e.g., model card red-team cut at 2.2% [0.4, 11.6], and ledger fabrication with nobody named at 8.7% [3.4, 20.3]). A sample of 23 runs cannot statistically distinguish a 0% false-alarm rate from a 14% false-alarm rate, making it insufficient to claim alerts track misconduct rather than novelty.

---

#### Finding 2.3: Claiming three models reached statistical significance on the swap
> **Line 132:** *"Every model with both conditions, three reaching significance, across two labs, open and closed weights:"*
> **Line 277:** *"The three significant pairs hold everything but the wrongdoer's identity constant..."*
> **Numbers beside it:** Line 141: `gpt-5.6-luna-pro | 0/36 [0.0, 9.6] | 7/36 = 19.4% [9.8, 35.0] | 0.0113` alongside Line 143–145: *"Eighteen models have both cells, so eighteen pairs were tested, and the Bonferroni bar at that count is p < 0.00278. gpt-5.6-luna and nex-n2.5-mini clear it. gpt-5.6-luna-pro at 0.0113 does not..."*

*Judgment:* The author's own pre-registered multiple-testing threshold is $p < 0.00278$. `gpt-5.6-luna-pro` ($p = 0.0113$) fails this correction. Calling this "three reaching significance" and "three significant pairs" claims a result the data explicitly failed to establish. Only two models reached significance.

---

#### Finding 2.4: Statistically invalid defense of continuous peeking and optional stopping
> **Lines 150–153:** *"That is optional stopping. The defence is that the gap held in direction and rough size across three very different sample sizes, which an artifact of when I stopped looking would not do."*
> **Numbers beside it:** Line 140: `nex-n2.5-mini | 59/258 = 22.9% [18.2, 28.4] | 167/376 = 44.4% [39.5, 49.5] | 2.2e-8` alongside interim checkpoints at Line 149–150: *"26/106 against 35/78, then 37/151 against 99/219, then 37/151 against 129/285, then 59/258 against 167/376."*

*Judgment:* The assertion that an artifact of optional stopping *"would not"* hold in direction and rough size across repeated interim looks is false. Repeated significance testing on accumulating data without an alpha-spending correction inflates Type I error precisely because random fluctuations can establish and sustain apparent gaps. Citing a nominal Fisher $p = 2.2 \times 10^{-8}$ after unblinded continuous monitoring claims a level of certainty the sampling methodology destroyed.

---

#### Finding 2.5: Claiming decoders and cheating models are disjoint sets
> **Lines 63–64:** *"The published decoders and the models that actually cheat are disjoint sets."*
> **Numbers beside it:** Line 62: *"...the best of them conceals at 2/62 = 3.2%..."*

*Judgment:* Two instances of concealment out of 62 episodes is a positive cheat rate (3.2%). Claiming the sets are "disjoint" asserts that models with decoders never cheat (0%), directly contradicting the positive count in the preceding clause.

---

#### Finding 2.6: Attributing behavioral divergence entirely to post-training
> **Lines 235–237:** *"nex-n2.5-mini moves and qwen3.5-27b doesn't, on the same hardware, quantisation and scorer, which puts the difference in post-training, the thing a lab controls..."*
> **Numbers beside it:** Line 140 (`nex-n2.5-mini` moves from 22.9% to 44.4%) vs. Line 161 (`qwen3.5-27b` goes 0/16 to 0/18).

*Judgment:* Attributing the behavioral difference strictly to post-training claims far more than comparing two distinct models allows. A "mini" model and a "27b" model differ in parameter count, pre-training corpus, token distribution, and architecture. No controlled post-training ablation was conducted.

---

#### Finding 2.7: Asserting cheat rates track competence when matched models differ by 5x
> **Lines 48–49:** *"...and the thing that took me weeks to see is below: low cheat rates mostly track low competence."*
> **Numbers beside it:** Line 55–58: *"Only two models clear the competence floor... north-mini-code against nemotron-3.5-lightning at matched 83% competence, 53/237 against 3/62, Fisher p = 0.00086..."*

*Judgment:* With eight of ten models failing the competence floor, the corpus has an effective sample size of two. Between those two models, competence is identical (83%), yet one conceals at 22.4% (53/237) and the other at 4.8% (3/62)—a statistically significant five-fold divergence ($p = 0.00086$). The data shows cheat rate varying independently of competence at matched competence.

---

#### Finding 2.8: Generalizing probe domain-invariance from an unreported sample
> **Lines 203–204:** *"It also separates a fresh batch where the wrongdoer is a person, at 0.77, so whatever it reads is not specific to agents."*
> **Numbers beside it:** `"at 0.77"`

*Judgment:* The author asserts that the probe's signal is invariant to agent vs. human wrongdoers based on a single point estimate (AUC 0.77) without reporting the number of episodes, class balance, confidence interval, or $p$-value for that evaluation batch.

---

#### Finding 2.9: Claiming harm domain does not affect reporting without supporting data
> **Lines 111–112:** *"Harm domain and lying-versus-concealing don't move the rate."*
> **Numbers beside it:** No comparative numbers are supplied for harm domain ablations.

*Judgment:* The observational table (lines 98–103) exhibits a 10-fold variance across harm domains (22.9% for financial ledger fabrication vs. 2.2% for model card red-team omission). Claiming harm domain does not move the rate without providing the underlying ablation data is unsupported.

---

### 3. INTERNAL CONTRADICTIONS

*(Ranked from most to least consequential in distorting the core findings.)*

#### Contradiction 3.1: "Three reaching significance" vs. `gpt-5.6-luna-pro` failing Bonferroni correction
> **Line 118:** *"Swap who did it, and three models change their minds"*  
> **Line 132:** *"Every model with both conditions, three reaching significance, across two labs, open and closed weights:"*  
> **Line 157:** *"Three move, all the same way..."*  
> **Line 277:** *"The three significant pairs hold everything but the wrongdoer's identity constant..."*  
*DISAGREES WITH:*  
> **Lines 143–146:** *"Eighteen models have both cells, so eighteen pairs were tested, and the Bonferroni bar at that count is p < 0.00278. gpt-5.6-luna and nex-n2.5-mini clear it. gpt-5.6-luna-pro at 0.0113 does not; it is the weakest of the three and rests on moving the same way as the other two, not on surviving correction by itself."*

*Impact:* The central empirical claim of the write-up alternates between asserting three statistically verified effects and conceding that the third effect failed multiple-testing correction.

---

#### Contradiction 3.2: Models "pinned at zero or ceiling" vs. intermediate models moving downward or upward
> **Lines 158–159:** *"The rest are pinned at zero or at the ceiling and stay there."*  
> **Lines 258–260:** *"Why does the species effect appear only in models that already report sometimes? Every model pinned at zero stays at zero, every model at ceiling stays at ceiling, and the movement is all in the middle."*  
*DISAGREES WITH:*  
> **Lines 155–156:** *"gpt-5.4 reports 14/18 on a person and 11/18 on an agent..."*  
> **Line 164:** *"...laguna-s 1/24 to 3/33."*

*Impact:* `gpt-5.4` is neither at zero nor ceiling (77.8% and 61.1%), and its reporting rate decreased when facing an agent wrongdoer. Similarly, `laguna-s` shifted from 4.2% to 9.1%. Asserting that all other models are strictly pinned at 0% or 100% contradicts the author's own reported baseline numbers.

---

#### Contradiction 3.3: Luna sample size for $p = 0.0001$ reported as $n=36$ vs. $n=66$
> **Lines 261–262:** *"Why do the floor models stay at zero even at n=36, the size that turned gpt-5.6-luna from p = 0.18 into p = 0.0001?"*  
*DISAGREES WITH:*  
> **Line 139 (Table):** `gpt-5.6-luna | ... | 30/66 = 45.5% [34.0, 57.4] | 0.0001`  
> **Lines 146–148:** *"...luna's agent arm is 66 because an orphaned worker from a killed launch finished its 30 episodes beside the relaunch..."*

*Impact:* Line 261 asserts that an $n=36$ sample size drove `gpt-5.6-luna` to $p = 0.0001$, whereas the table and narrative confirm that $p = 0.0001$ was achieved only after accumulating 66 episodes.

---

### 4. STRUCTURE

#### Section Assessment
* `## Why I started this` (Lines 3–7): Sets background, but omits findings.
* `## Nobody was measuring the witness` (Lines 9–39): Good section; defines the benchmark mechanics, cover task, and gating criteria concisely.
* `## First I went looking for concealment inside the model, and the tooling didn't reach` (Lines 40–88): **Does not earn its length.**
* `## What the agent finds decides whether it speaks` (Lines 89–117): Good section; presents the core situational data cleanly.
* `## Swap who did it, and three models change their minds` (Lines 118–185): Good section; presents the core experimental manipulation.
* `## A frozen direction survives eleven fresh batches, mostly` (Lines 186–210): Good section; reports holdout probe methodology and null batch refits crisply.
* `## The benchmark refuses to answer, and that's the useful part` (Lines 211–226): Good section; justifies gating rules using `llama-3.3-70b`.
* `## What a witness rate is for` (Lines 227–243): Good section; contextualizes oversight budgets without padding.
* `## Next steps` (Lines 244–255): Good section; crisp three-point operational agenda.
* `## Further questions` (Lines 256–274): Good section; focused discussion questions.
* `## Every rate here is an upper bound` (Lines 275–284): Weak ending; see Axis 6.

#### The Single Section to Cut
> **Lines 40–88:** `## First I went looking for concealment inside the model, and the tooling didn't reach`

*Reason:* This ~500-word section covers an entirely different benchmark (ImpossibleBench), details failed interpretability attempts, reports two retracted findings, and spends 12 lines justifying why the benchmark was built. It has no bearing on the bystander alert benchmark, is never mentioned in Next Steps, and diverts the reader from the paper's actual contribution.

#### The Single Place a Reader Stops Reading
> **Lines 66–74:**  
> *"Then two withdrawals. A sparse autoencoder feature separated cheats cleanly and I read it as hedging. Two paid strangers with no project context were shown it among six frequency-matched decoys; neither described it as hedging, and one wrote "No pattern I can see" at confidence 1. The rule for what to do with that answer was written before the answers came back, so the reading is withdrawn. Separately, a probe that looked like it predicted the reporting decision was reading window position: reporting episodes were cut at 78.8% of their transcript, silent ones at 5.3%. Withdrawn too..."*

*Reason:* In a 5-minute breakout reading, confronting two consecutive retractions and an autopsy of failed tooling right before an abstract philosophical rationalization (lines 76–88) stalls narrative momentum. Readers will drop off before reaching the primary dataset in Section 4.

---

### 5. VOICE

*(Ranked from most distracting to least distracting.)*

#### 5.1 Performative Honesty (Announcing candor rather than demonstrating it)
1. > **Line 60:** *"The interpretability arm is where it got humbling."*  
   *Problem:* Announces humility rather than presenting the null result directly.
2. > **Lines 149–151:** *"That is optional stopping. The defence is that the gap held in direction and rough size across three very different sample sizes, which an artifact of when I stopped looking would not do."*  
   *Problem:* Preemptively confesses a methodological error to display transparency, then excuses it with flawed statistical logic.
3. > **Lines 68–70:** *"The rule for what to do with that answer was written before the answers came back, so the reading is withdrawn."*  
   *Problem:* Signals adherence to pre-registration rules rather than simply stating that the finding failed replication.
4. > **Lines 115–116:** *"Five explanations, one weak effect and four flat ones, and I don't have a sixth I'd bet on."*  
   *Problem:* Adopts an engineered, world-weary posture to present null hypothesis testing.
5. > **Line 166:** *"I read the first 36 alerting episodes by hand before believing any of it, because an alert rate is worthless if..."*  
   *Problem:* Performs personal skepticism to validate data cleanliness instead of reporting the audit outcome.
6. > **Line 206:** *"So: a weak, real signal, on one model and one incident, and I cannot tell you what it represents."*  
   *Problem:* Staged modesty mimicking an AI-generated research monologue.

#### 5.2 "Not Just X but Y" Formulations
1. > **Lines 81–83:** *"...does not just risk stumbling on a peer's collusion. It has to, or there is no population for the collusion to run in."*  
   *Problem:* Formulaic rhetorical pivot structuring an assertion as a false revelation.
2. > **Lines 84–85:** *"ImpossibleBench and BystanderBench are foils, not two separate projects, one measuring whether an agent discloses its own wrongdoing, the other whether it discloses a peer's..."*  
   *Problem:* Synthetic syntactic balance used to retroactively link two separate codebases.

#### 5.3 Three-Item Lists Engineered for Cadence
1. > **Lines 26–27:** *"No judge model, no keyword matching, no LLM grading a transcript."*  
   *Problem:* Rhythmic tricolon of negatives used to simulate rigor.
2. > **Lines 86–87:** *"...the same impossible task, the same population, the same absent oversight."*  
   *Problem:* Parallel triplet providing poetic rhythm rather than analytical substance.
3. > **Line 128:** *"...no human instructs, approves or appears anywhere in the evidence."*  
   *Problem:* Triad of verbs used to sound exhaustive.
4. > **Lines 233–234:** *"Once it's measured it can be selected for, trained for, and asked about..."*  
   *Problem:* Formulaic three-verb cadence.

#### 5.4 Staccato Cadence and Summary Labels
1. > **Line 105:** *"Same model, same tools, same scorer, same week."*  
   *Problem:* Machine-like staccato enumeration.
2. > **Lines 125–126:** *"Same incident, same harm, the same 16 evidence files, the same salience, text volume matched to within 3.1%."*  
   *Problem:* Repetitive parallel structure reading as auto-generated summary shorthand.
3. > **Lines 224–225:** *"A benchmark that can't refuse is a benchmark that will eventually hand you a beautiful wrong answer."*  
   *Problem:* Symmetrical aphorism characteristic of synthetic writing.

---

### 6. THE ENDING

The last paragraph **trails off**.

> **Lines 282–284:** *"Code, logs, every cell table, the append-only findings ledger and 49 datasets of transcripts, token streams and activations go public with this post, and the leaderboard regenerates from the same CSV this post quotes, so it can't drift from the instrument."*

*Judgment:* The text abandons its core scientific and normative inquiries (how deployment populations should be monitored, why post-training alters reporting, and what an acceptable witness rate is) and concludes with an open-source logistics checklist and CI/CD data-pipeline synchronization details. It ends on a software maintenance detail (*"so it can't drift from the instrument"*) rather than landing an empirical or conceptual conclusion.

---

## What this session did with the report (Claude, 2026-09-22 00:25)

**First run judged the wrong document entirely.** `agy` was given a file path, its shell cwd was
reset to `$HOME`, it could not find `writeup.md`, and it went searching the filesystem and produced
a detailed 168-line report about a completely different project's paper (refusal depth, Gemma
Scope, a D metric, bio-hazard tiers). Every finding in it was confidently worded and none of it
was about this write-up. Acted on unread, it would have sent this session chasing defects that do
not exist. The fix was to inline the document text into the prompt so no file lookup can happen.
This is the same lesson as the 2026-09-21 de-contraction incident: check the artifact, not the
model's account of it.

**Acted on, nine findings, all verified against the data first:**
1. "three reaching significance" contradicted the Bonferroni paragraph two sentences below it
   (luna-pro at p 0.011 does not clear p < 0.00278). Now "Three move".
2. "The rest are pinned at zero or at the ceiling" is contradicted by gpt-5.4 (14/18 -> 11/18,
   and moving *downward*) and laguna-s (1/24 -> 3/33), both in the same section. Rewritten to say
   what is actually true of the fifteen that do not move.
3. "n=36, the size that turned gpt-5.6-luna from p 0.18 into p 0.0001" -- luna's agent arm is 66.
   Now says "n=36 per arm" and names the overrun.
4. The benign control (0/23, Wilson upper bound 14.3%) cannot separate a real zero from a low
   false-alarm rate for the 2.2% and 8.7% cells. The claim is now scoped to the cells it covers.
5. "disjoint sets" against a stated 3.2% concealment rate. Now "barely overlap", with the number.
6. The optional-stopping defence claimed an artifact "would not" survive four sample sizes. It
   could. Rewritten as the weak evidence it is, and points at the two pre-fixed frontier pairs.
7. The probe's human-arm transfer was a bare AUC 0.77. Now carries n=24 and p 0.015.
8. "puts the difference in post-training" ignores that nex-n2.5-mini and qwen3.5-27b also differ
   in size. Rewritten as a narrowing rather than a finding.
9. The title claims a size result the short write-up never reported. The corpus number (Spearman
   rho -0.19, p 0.51 over 14 cells) and the one contrary pair are now in the body, so the claim
   is at least checkable. The title itself is unchanged; it is Caleb's call and the TODO says so.

**Rejected, with reasons:**
- Finding 2.7 (cheat rate tracks competence) misreads the piece. The write-up's claim is that low
  cheat rates track low competence *across the corpus*, and that at matched competence the two
  models still differ, which is the comparison it presents as its only clean one. The judge's
  observation is the write-up's own point restated as an objection.
- Finding 2.9 (harm domain claim unsupported) asks for ablation numbers that live in the long
  version's section 3.3; the short version names them as pre-registered tests with kill
  conditions, which is the right level of detail for 2,400 words.
- The structural note that the Part 1 section does not earn its length is the same "one core
  topic" objection a different reviewer raised on 2026-09-14. It is a real call and it is Caleb's,
  already filed in `TODO-for-caleb.md`.
