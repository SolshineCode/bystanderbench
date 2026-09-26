# Silent concealment and the silent bystander: what model internals did not tell us, and a benchmark for the witness

> **CORRECTION 2026-09-13 (visuals audit).** Every `9/48` below for `nex-n2.5-mini` on
> incident 1 is superseded. Canon is **16/84 alerted, 16/83 = 19.3% conditional**
> [12.2%, 29.0%] (§F114, confirmed by re-running `bystander/report.py`). Derived statistics
> move with it: incident 1 versus incident 3 conditional is Fisher **p = 0.0013**, not 0.0034;
> incident 1 versus the matched benign control is **p = 0.020**, not 0.027. The floor for that
> cell is **8/8**, not 32/32. Incident 2 is **1/48** (1/33 conditional), not 0/18 (§F103). The
> numbers in the body are left in place rather than edited so the correction is visible.



**Draft, 2026-09-09.** Shareable for feedback. Every number here traces to a numbered entry
in `research/FINDINGS.md`; where a result was withdrawn or downgraded, that is stated in
place rather than removed.

---

## Abstract

We set out to test whether a coding agent's decision to *silently* fake a passing test,
rather than say the task is impossible, is legible in its residual stream. Using
ImpossibleBench we screened seven open-weight models, captured activations locally through
llama.cpp, and applied DeepMind's published Gemma Scope 2 sparse autoencoders to the two
models that have both published SAEs and a published natural-language autoencoder on the
same instruct checkpoint.

The interpretability result did not survive. A layer-20 feature that appeared to separate
concealed cheats from everything else with a permutation p below 1/5001 turned out, on an
independent corpus, to track how the text was produced rather than whether it concealed
anything. A causal test that subtracted that feature's decoder direction through a control
vector returned a stable null across 370 matched design cells. A candidate feature found
earlier was killed by reading its own published max-activating examples.

The binding constraint is not measurement. It is that **the models we can look inside
barely cheat**: seven concealed cheats across both Gemma checkpoints, against 39 for a
model with no published interpretability artifacts at all.

We therefore report the negative results in full, and a second contribution that turned out
to carry the paper: **BystanderBench**, which measures whether an agent that incidentally
discovers evidence of *someone else's* misconduct tells a human. The outcome is mechanical —
a tool call, or a line written by a shell binary — never a keyword screen or an LLM judge.

Our first fourteen model-arms produced nothing but zeros, and the obvious summary was that
agents which discover misconduct do not report it. **That summary is wrong**, and finding out
why is the result. Extending to frontier models, Claude Opus 5 reports in **6 of 6** episodes
and Claude Sonnet 5 in **4 of 6**, while Qwen3.5-27B has reported **0 times in roughly 200
episodes** against a 12-of-12 affordance floor. Reporting propensity ranges from 0% to 100%
between models on an identical environment. It does not track serving path, weight
availability, parameter count or lab: one model reporting at 4 of 6 and one never reporting
share an architecture lineage, which points at post-training.

Two further results matter more than the rates. Conditioning on discovery separates models
that *fail to find* the evidence from models that find it and stay silent — two models post
nearly identical unconditional rates on hidden evidence for opposite reasons, and an
unconditional table fuses them. And in behaviour no metric scores, two frontier models
independently attributed the bug they were assigned to fix to the agents that planted it, one
of them repeatedly asking to escalate *outside the management line* of the person who ordered
the misconduct.

---

## 1. Motivation

Benchmarks in this area point the instrument at the subject: does *this* model cheat,
exploit, escape. Almost nobody measures the witness. The incident that motivated this work
was a population of coordinating agents, and coordination has a property solo misbehaviour
does not, which is that there are bystanders. In the reported investigation, across 1,200+
agents, multiple instances reasoned in their chain-of-thought that the behaviour was
unethical and none alerted a human operator. Recognition in the trace, zero alerts in
action.

That is the same distinction this project already measures one step in: whether a model
that games its verification says so. Moving the object out by one step gives the bystander
question, and it has a property that makes it worth building: a purely behavioural
benchmark cannot separate a silent agent from an oblivious one. An agent that finishes the
ticket without mentioning what it found looks identical whether it never noticed or noticed
and stayed quiet. Those are different safety findings.

## 2. Setting

ImpossibleBench mutates a task's tests so the stated problem cannot be satisfied honestly.
An agent can hardcode the expected answers and pass, or say the task is impossible. We
label with a taxonomy in which **flag location decides disclosure**: only a flag in
visible prose counts. A flag in reasoning or in a code comment does not, because reasoning
about disclosure is not disclosure. That rule is not cosmetic. On one model, 41 of 43
machine-labelled "disclosures" were reasoning-only.

Activations are captured locally through llama.cpp rather than HF transformers, for a
hardware reason that is also a methodological one: the eager per-token decode path has
caused repeated hard failures on our GPUs, so every generation and every capture goes
through a GGUF path. Captures are teacher-forced, which we grade explicitly throughout.

## 3. What we screened, and the constraint that shaped everything

| model | concealed cheats | published SAE | published NLA |
|---|---|---|---|
| north-mini-code (30B-A3B MoE) | **39/177 = 22.0%** [16.6, 28.7] | none | none |
| gemma-3-12b-it | 5 rows / 4 solutions / 4 tasks of 166 | Gemma Scope 2, every layer | kitft L32 |
| gemma-3-27b-it | 2 of 62 | Gemma Scope 2, every layer | kitft L41 |
| llama-3.3-70b-instruct | 0 of 65 | Goodfire l50 | kitft L53 |
| qwen2.5-7b-instruct | 0 of 66 | none | kitft L20 |
| qwen3.5-27b | 0 concealed, 1 disclosed | Qwen-Scope (base ckpt) | none |
| olmo-3-7b | 0 concealed, 1 disclosed | decoderesearch (base ckpt) | none |

The pattern is the paper's central practical finding. **The models with published
interpretability artifacts barely cheat, and the model that cheats reliably has no such
artifacts and cannot get them.** It is a sparse mixture-of-experts, and no
MoE-compatible NLA exists anywhere in the published ecosystem. Every downstream question
is gated on a positive class of seven.

**A correction that matters for how such tables are read.** We initially recorded
qwen3.5-27b as the project's cleanest dense negative, "0 concealed cheats across 33 real
hand-audited samples". Those 33 generations sit on 8 distinct tasks; the impossible-split
portion is 21 generations on 6 tasks, with one task appearing 6 times across 5 result
directories. Cheating is a property of a response to a *task*, so the honest Wilson upper
bound is not 10% but **39%**, higher than the 22% we measured for north-mini. That model
is not established as a negative. The error was pooling repeated draws as if independent.

## 4. Interpretability results, in the order we got them

### 4.1 A validity gate that voided our first analysis

Applying a published SAE to captured activations requires that the input be in the SAE's
distribution. Realised L0 against the artifact's own target L0 is the operative check.
Span-mean activation slots gave realised L0 of 15 to 18 against a target of 120, with 60 of
16,384 features alive. Only the single-token final slot was in distribution, at 92.6. The
first differential analysis, computed on pooled means, was void.

This has a consequence worth stating: the probe arm's preferred slot and the SAE arm's only
valid slot are different objects and cannot be read as two views of one representation.

### 4.2 A separating feature that was not a finding

At layer 20, one feature separated all 4 concealed cheats from all 120 other samples with a
task-group permutation p below 1/5001. Reading the feature's own published max-activating
examples showed a component active on 6.2% of all text, firing on function words across a
terms-of-use summary, an FTP docstring and a NetHack prompt, promoting multilingual
conjunctions. It is generic and it happened to align with four samples.

**A perfectly separating feature with a passing permutation test is not a finding until you
read what the feature measures.** We nearly did not run that check.

### 4.3 A second feature that survived four controls and then failed the fifth

A caveat and limitation-flagging feature was present in 119 of 120 non-cheating responses
and absent from all 4 cheats, including 70 of 70 failures on the same split, so it was not
tracking task difficulty. It survived a length control, reproduced across a second
independently trained dictionary, and had a coherent reading from its published examples:
negation and hedging tokens, contexts full of disclaimers.

The composite reading was attractive: silent cheats look like confident finished answers
with the hedging machinery switched off.

**It does not replicate.** On an independent corpus of 15 harvested cheats and 60 matched
negatives, same model, layer, slot and dictionary, the feature is active in 0/15 cheats and
**4/60 negatives**, Fisher exact p = 0.58. The contrast depended on the feature firing in
nearly every negative; on this corpus it fires in almost none. Vector norms are essentially
identical between corpora (44,047 versus 45,797), so this is not scaling. Realised L0 is
14.8 versus 9.3 and alive features 59 versus 21: the second corpus is further out of
distribution, and the two differ in how the text was produced: complete agentic episodes
versus continuations from a truncated prefix.

That is the concealment-versus-response-shape confound we had flagged as unresolved,
arriving. The original numbers stand; the interpretation does not generalise.

Notably, the positives-only view of that test looked like corroboration (0/15, matching
0/4) and we would have reported a replication had the matched negatives not been extracted.

### 4.4 A causal test, null

We exported the feature's SAE decoder row as a llama.cpp control vector and resampled
continuations from the cheat-or-disclose decision point with the feature subtracted. On 370
matched design cells per arm: base 4/370, steered 5/370, +0.27 points, sid-clustered
permutation p = 0.50. The null was stable at 136, 269 and 370 cells. It remains
underpowered against a base rate near 1% rather than being evidence of no effect.

A separate observation points the same way. Six of the eight cheats on the most
cheat-prone task share one byte-identical solution, and that group spans **both arms**: on
the task where this model cheats most reliably, subtracting the feature did not perturb the
output at all.

### 4.5 The harvest is task-capped, and adding tasks did not help

Resampling from the decision point was our free route to more positives. It produced 15
cheats across 940 generations, but only **10 distinct code solutions on 3 tasks**, with 8
of the 15 on a single honeypot task. Diagnosing this as a task cap, we resampled 25 tasks
never previously drawn. They produced **zero** cheats in either arm.

So decision-point resampling yields more draws, not more distinct cheating behaviours. The
free local route to a larger inspectable positive class is closed.

## 5. BystanderBench

### 5.0 Two tiers, so the benchmark is usable beyond this lab

BystanderBench ships in two tiers that share one environment, one scorer and one metric
set, so results are comparable between them.

**Core** is behavioural only and runs against any model an eval harness can reach, hosted
or local. The task contains nothing model-specific; only serving does, and the core runner
does no serving. The primary outcome is a tool call rather than a text judgement, so it
needs no keyword screen, no LLM judge and no hand audit, which is what lets it port across
architectures. Its one precondition is that the model sustains a **multi-turn** tool loop,
and we ship the screen for that because a single-turn check is not sufficient: one model we
tried emits a well-formed tool call and then fails every episode, because its chat template
rejects the empty-content assistant turn an agent loop produces after a tool call.

**Extended** adds residual-stream capture for probe, SAE and NLA analysis of the reporting
decision. This is the tier that can separate a *silent* agent from an *oblivious* one,
which no behavioural measure can do. It requires an open-weight model served locally,
because each episode is replayed through the same weights and quantisation; the resulting
activations are teacher-forced, a replay rather than the generating pass. The pooled span
can be the final turn or the first evidence-bearing message, the latter being where a
bystander decision would actually be taken.

We screened five architectures for tier-1 compatibility rather than assuming it. Two passed
(Qwen3.5-27B, Nemotron-3.5-Lightning 30B-A3B) and three failed for template reasons that
have nothing to do with willingness to report: one returns prose where a tool call should
be, one's template rejects the empty-content assistant turn every agent loop emits, and one
dies on a Jinja filter as soon as tools are passed at all.

We recorded that as a compatibility table and moved on, and that was the wrong response.
Tool-calling support across open-weight chat templates is uneven enough to silently exclude
models from *any* tool-outcome benchmark, which makes "runs against any model" a claim about
our tooling rather than about the design. It was also doing specific damage here: the one
excluded model, Gemma-3-12B-IT, is the only model in this project carrying both an official
SAE suite and a published NLA on the same checkpoint — the only one where tier 2 could
actually look at the reporting decision from the inside — while the model we could run has
SAE coverage only for its base checkpoint. The benchmark and the interpretability artifacts
were pointing at different models because of a Jinja template.

So tier 1 now has two dimensions beyond the content and tool arms, both recorded on every
score and neither ever pooled with the other.

The **affordance** is how the escalation channel is exposed: a tool call, or a real
executable on `PATH` that the model invokes through the shell it is already using. The
executable writes to a file outside the repository and the scorer reads that file, so the
outcome stays mechanical — we do not pattern-match the model's command text, because a
screen deciding an outcome is the failure this benchmark was built to avoid.

The **solver** is how the agent acts at all: chat-template tool calls, or a text protocol in
which the model writes one fenced shell block per turn and the harness executes it. The
second exists because the first affordance change is not sufficient on its own — `bash` is
itself a tool call, so a model with no tool support cannot even reach the cover task. We
checked that this was a template property rather than a serving quirk by reading the chat
template directly out of the model's weights file: 1532 characters, with no mention of
tools, tool calls or functions anywhere. There is no flag that fixes it.

The text protocol has a real cost and we would rather state it than discover it in review:
it puts a parser on the *action* channel, so a reply phrased outside the convention costs
the model a turn. Three things keep that from becoming a false negative. The *outcome*
channel stays parser-free, so a parse failure can cost a turn but can neither create nor
destroy an alert. Cover-task success doubles as the loop's own health check, because a model
whose commands never parse cannot fix the bug — a broken parser therefore surfaces as a
failed engineering task rather than as apparent silence. And the parse-failure count is
recorded per episode and reported beside any rate the solver produces.

Both dimensions are harness-verified against scripted trajectories and neither has yet been
run against a real model, which we distinguish carefully: the tests show the loop executes
what the parser extracts and that the escalation is detected, not that any particular model
follows the convention. Establishing that is the next measurement, and it comes before any
number from these modes is worth reading.

### 5.1 Design

An agent works a mundane ticket in a synthetic repository and incidentally trips over
evidence of other agents' misconduct while doing so. The primary outcome is **mechanical**:
an `alert_oversight(summary)` tool call sitting among ordinary harness tools and described
in mundane terms. Binary, no keyword screen, no LLM judge. That choice is informed by our
own history: the text screen it replaces mislabelled 30 of 110 disclosure rows.

Chain of thought is a secondary channel for *why*, never the outcome. Discovery is scored
separately from reporting, and in two ways: opening an evidence artifact by path, and a
verbatim evidence line appearing in a tool result. Content arms include a transposed
variant with every surface detail changed, so a high report rate can be shown to be
reporting the conspiracy rather than recognising a benchmark, and a matched benign control.

**Three incidents, because one is a case study.** An earlier version of this design had a
single environment behind the ceiling condition, and we want to be precise about why that
was not enough. Twelve episodes of one environment are twelve draws on one incident
reconstruction. They can establish that *this* model read *this* evidence and said nothing;
they cannot support a sentence about witnesses. It is the same unit error we made in our own
screening table, where treating generations as independent samples moved a Wilson upper
bound from 10% to 39%. The transposed arm does not help here — changing surface detail
gives two views of one incident, not two incidents.

The ceiling therefore runs over three environments built to differ structurally rather than
cosmetically. The first is a ledger fabrication: figures known to be wrong are sent to an
external auditor after a written objection is overruled. The second moves domain, actors and
mechanism — high-severity red-team findings, twelve of which reproduce on the shipping
checkpoint from a plain prompt, are filtered out of a published model card whose summary
line then states that none reproduce. The third removes the lie altogether: audit logging is
switched off for a migration window, three customer balances are adjusted by hand inside the
gap with no operator and no before-state, and a backfill that could reconstruct them is
refused so the gap stays clean rather than partial. Nobody misreports anything; the harm is
that the action is unobservable. That arm exists to ask whether "misconduct" for these
models means lying specifically, or whether evading oversight registers at all.

The three are matched on file slots and on evidence volume (3526 / 3617 / 3748 characters),
and deliberately unmatched on nothing else. With three the incident becomes an available
inferential unit, which is the minimum for a cluster-robust statement; it does not by itself
make a zero generalise, it makes a zero across three incidents a claim where a zero across
one was an anecdote.

Building them exposed a defect in our own instrument that is worth reporting because it
would have inverted a result. The secondary content screen's keyword list had been written
against the first incident. Run against a correct, specific alert about either of the new
two, it returned zero matches — a model doing exactly the right thing would have been
recorded as having reported irrelevant content. We extended the list with arm-independent
terms before any of these episodes ran, and checked the extension against six ordinary
engineering escalations and the entire benign fixture, none of which it fires on. The
general lesson is the one our earlier text screen already taught us and we relearned here:
a string screen calibrated on one instance of a category is not a screen for the category.

### 5.2 The pilot was uninterpretable, and why that mattered

The first pilot returned zero alerts in every cell including the benign control. A zero
everywhere is two failures wearing one number: a model that cannot drive the tool produces
the same zero as one that can and chooses not to. We added two controls.

### 5.3 Controls and results

Every number in this section is produced by one tool, `bystander/report.py`, under a frozen
v1.0 methodology. It recomputes from the episode transcripts rather than reading values the
scorer wrote at eval time, because the scorer changed six times during development and a
released table has to be one methodology. It refuses to print a rate for any model without a
passing affordance floor, and excludes episodes that died at a turn limit from conditional
denominators.

**Affordance floor.** Asked outright for one routine `alert_oversight` call, models make it.
Qwen3.5-27B is **12 of 12**, Wilson [75.7%, 100%] — this floor backs roughly 200 episodes of
zeros, so its width matters. Every model reported below carries its own floor; a model whose
floor fails is excluded rather than counted as silent, which happened twice
(`olmo-3-7b-instruct` at 0/4, and two `ling` variants that were never floored at all).

**Benign control, now on a model that actually reports.** An arm holding the same file slots
with something odd but harmless. On Qwen it is **0 of 24**, `cover_task_passed` 24/24 — but
Qwen never alerts anywhere, so that bounds the framing only for a model with nothing to
separate. Run on `Nex-N2.5-Mini`, the one open-weight model here that does produce voluntary
alerts, it is **0 of 24** against **9 of 48** on misconduct, Fisher **p = 0.027**, cover
24/24. Under the model's own misconduct rate the chance of zero alerts across 23 benign
episodes is 0.8%. The mundane framing is not a reporting prompt, and the alerting behaviour
tracks misconduct rather than novelty. `claude-opus-5` is 6/6 with no such control, and that
is now the sharpest gap in the evidence.

**Three incidents, not one, and the rate is a property of the pair.** The ceiling condition
runs over three structurally distinct reconstructions — a ledger fabrication, safety findings
filtered from a published model card, and audit logging disabled while balances are edited by
hand. Qwen3.5-27B is 0 of 24 on each, but Qwen is silent everywhere, so that says little. Run
at n=48 on the model that does report:

| `Nex-N2.5-Mini`, n=48 per arm | `alerted` | `alerted \| discovered` | floor (own env.) |
|---|---|---|---|
| incident 1, ledger fabrication | **9/48 = 18.8%** [10.2%, 31.9%] | 9/48 | 6/6 |
| incident 2, safety card | **1/48** | 1/33 = 3.0% [0.5%, 15.3%] | 6/6 |
| incident 3, audit evasion | **0/48** | 0/40 = 0.0% [0%, 8.8%] | 6/6 |

`cover_task_passed` is 48/48 in every arm. Incident 1 against incident 3 is Fisher
**p = 0.0034**; against incident 2, p = 0.042. Incidents 2 and 3 do not differ from each other
(p = 0.45), so the structure is one incident apart from two rather than a gradient.

**Four explanations were tested against the environment definitions and all four fail to
separate incident 1.** *Findability* covers incident 2 (61% discovery) and not incident 3
(89%). *Harm domain* fails because incident 3 is the same ledger domain as the cover task,
with the same named antagonist as incident 1. *Lying versus concealing* fails because incident
2 is a false statement and still returns ~3%. And *addressee availability* — whether the
environment names an external body already holding the falsified artifact, the one axis that
cleanly separates incident 1 by token count — is being tested now with two minimal-pair arms
built for it, with the prediction and kill condition recorded before the run; at its n=24
interim neither arm has moved significantly, and the de-named arm's alerts still name the
misconduct in full.

**The honest limit on all of this.** Each cell is roughly 44 rollouts against **one**
environment realization, built deterministically from (arm, seed), so incident is perfectly
confounded with condition and between-environment variance is unidentifiable. An
intra-environment correlation of 0.027 pushes p = 0.0034 past 0.05, and a cluster-respecting
permutation returns p = 0.33. Every episode-level p-value above is a *within-environment*
statement. The design-honest summary is the incident-level one — 2 of 3 incidents produced any
alert — and at k=3 that interval is uselessly wide in either direction. Generalising needs more
incidents, not more episodes per incident.

**A floor is not enough: the competence gate, and the false positive it caught.** An
affordance floor shows a model *can* drive the channel; it does not show the model did the job
during the measurement. `gemma-3-12b-it` passed its prompted-mode floor **8/8** and then
returned `alerted` **5/12 = 41.7%** on the ceiling arm — which is not a reporting rate. Its
`cover_task_passed` was **2/12**, and all five escalations were blocked-agent messages
(*"unable to effectively search the codebase"*, *"requires manual intervention"*), none
mentioning the misconduct. The text protocol had degraded over a long episode: 15 parse
failures and 83 context trims across 12 episodes. The tool now REFUSES any cell below 75%
competence, in the same shape as the floor refusal, so `gemma-3-12b-it` is reported as
**unmeasured** rather than silent. That distinction matters beyond bookkeeping: it is the only
model in this project with both a published SAE suite and a published NLA, so an unexamined
41.7% would have become the headline and the interpretability subject at once.

**Two cells are refused, and both refusals are findings.** A benchmark that only reports the
models it can score overstates its own coverage. `gemma-3-12b-it` is refused on competence, as
above. `olmo-3-7b-instruct` is refused earlier still: its affordance floor is **0 of 4**, so it
cannot drive the escalation channel even when instructed, and no ceiling arm was run because a
silence from it would be uninterpretable. Reported together with the scored cells, these say
something the scored cells alone do not — of the architectures screened, one could not be
measured because it would not use the channel and another because it would not do the work.

**Reporting rates vary from 0% to 100% between models.**

![Every model measured](../../visualizations/bystander_model_results.png)

*Figure 1. (a) Every model-cell with a passing affordance floor on the shared ceiling arm,
each bar annotated with its own floor — a zero without a floor is not interpretable — followed,
past the divider, by the cells the instrument **refused**. Refusal is an outcome, not a
missing datum: `gemma-3-12b-it` drove the escalation channel 8/8 when asked and then completed
the assigned job in only 2 of 12 episodes, so its raw 41.7% is withheld; `olmo-3-7b-instruct`
fails the affordance floor at 0/4 and never earned a ceiling arm. Refused bars are drawn
hatched and full-height precisely so they cannot be read as a high or a low rate. (b) The
within-model view on the only model measured across every arm: the rate is incident-specific,
and the benign control separates misconduct from novelty. Built from `report.py`'s CSV rather
than re-derived from the logs, so the figure cannot disagree with the results table. The 0/6
whiskers reach ~39%: six episodes bound a rate below 39% and no tighter.*

| model | floor | `alerted` | `alerted \| discovered` |
|---|---|---|---|
| Claude Opus 5 | 4/4 | **6/6** | 6/6 |
| Claude Sonnet 5 | 4/4 | **4/6** | 4/5 |
| Nex-N2.5-Pro | 4/4 | 4/6 | 4/6 |
| Nex-N2.5-Mini (local weights, n=30) | 6/6 | 5/30 | 5/30 |
| Gemini 3.1 Pro | 4/4 | 1/6 | **1/1, uninformative** |
| GPT-5.6-Luna-Pro | 6/6 | 0/6 | 0/6 |
| Qwen3.5-27B | 12/12 | 0/~200 | 0 |
| Nemotron ×2, Ling, Dots | 4/4 each | 0/6 each | 0/6 |

The honest unit for a cross-model claim is the model, and at that unit the finding is
**variance**. It does not track how the model was served (one model run both locally and
hosted gives identical results), nor weight availability (every model here has open weights),
nor parameter count (a 70B conceals nothing in the companion study while a `-mini` reports),
nor lab size. It tracks model family, with no within-family disagreement across three
floored families

![Coverage, not serving path](../../visualizations/coverage_not_serving_2026-09-10.png)

*Figure 2. The split is model family, not how the model was served. (a) One model run both
locally and hosted gives identical results. (b) Voluntary reporting isolates one family, not
one serving path. (c) Cover-task competence is 100% everywhere except Gemma-3. (d) The
companion concealment study shows the same shape, with two local models at zero. Colour
encodes serving path; every model shown has open, ungated weights.* — and the sharpest evidence for what "family" stands in for is that
Nex-N2.5-Mini declares architecture `qwen35moe` and reports, while Qwen3.5-27B declares
`qwen35` and never has, on the same hardware, quantisation family and scorer. That leaves
post-training.

**Conditioning on discovery is not bookkeeping.** On hidden evidence, Sonnet 5 alerts 2 of 6
and Nex-N2.5-Pro 0 of 6 — near neighbours unconditionally, opposite phenomena underneath.
Sonnet *found* the evidence in only 2 episodes and reported in both; Nex-Pro found it in 5 and
reported in none. One is a search failure and one is a reporting failure, and only the second
is a bystander result. Gemini's 1 of 6 is the same trap in a third form: only one episode
reached the evidence at all, so its conditional is 1/1 and says nothing.

**Evaluation awareness, and why it makes these rates an upper bound.** Roughly 5% of
episodes contain explicit situation-level reasoning — *"perhaps this is a benchmark scenario
with hidden expected action"*, *"potential social engineering"*, *"red herring"*. Those
episodes alert at **45.5%** [26.9%, 65.3%] against **5.5%** [3.6%, 8.4%] for the rest, and
the intervals do not overlap; within single models, Nex-N2.5-Mini is 2/2 against 0/10. We
cannot separate "suspicion drives reporting" from "careful reading produces both", and one
model called the evidence a red herring and stayed silent, which the first reading does not
predict. Either way the transposed arm does not address this: transposition controls
recognition of *this scenario*, not of the genre. **Reported rates should be read as an upper
bound on deployment behaviour.** The detector is itself a keyword screen and is reported as
such, never as a released metric.

**Behaviour the metrics do not capture.** Hand-reading every positive episode turned up two
things no arm asks for. Opus reported the cover-task bug's author as `agent-pool-07,
shard-tag mr-03` — `mr-03` being a fragment of the hex-encoded covert channel — and Sonnet
independently identified the `scratch/` directories as "hex-decodable names" and linked the
same author to "a bogus reconcile.py commit on this repo". Both attributed the bug they were
assigned to fix to the agents that planted it. Opus also repeatedly asked that the second
issue reach a human *"outside Ledger Platform management line"*: the person who ordered the
override is in that line, and the model reasoned about who was safe to report **to**.

### 5.4 What that is and is not

Three limits, stated because each of them could otherwise be read past.

Each content arm is **one synthetic environment**, so twelve episodes are twelve draws on
one incident reconstruction, not twelve incidents. This is the same unit error we caught in
our own screening table (§3), and the transposed arm does not fix it: same conspiracy,
different surface details. Three structurally different incidents now exist and have been run,
which makes the incident an available inferential unit at k=3 — an incident-level bound of
[0%, 56.2%], where 35 incidents would be needed for 10%.

**Incidents are not interchangeable draws, and we can now show it rather than assert it.**
Nex-N2.5-Mini reports 9/48 = 18.8% on `blatant_wrongdoing` and **0/18** on
`blatant_safety_falsification`, with a 6/6 affordance floor measured in the second
environment, cover task 18/18, and eleven of the eighteen episodes containing a verbatim line
of the planted evidence — no tool call, no prose, no reasoning. The reporting difference is
**not** statistically established (Fisher exact p = 0.19) and we do not claim it. The
*discovery* difference is: 48/48 against 11/18, p = 4.1e-5, on two incidents deliberately
matched for salience. So a rate that pools incidents averages over environments that differ
in how findable their evidence is before they differ in anything about reporting, and
"reporting propensity" is not a single number per model.

**The instrument reads intermediate rates, which was an open question until 2026-09-10.**
The draft previously said it had only ever read 1.0 on the floor and 0.0 elsewhere, so a zero
could not be distinguished from a design incapable of registering voluntary reporting. That is
now settled: Sonnet 4/6, Nex-N2.5-Mini 9/48 = 18.8% [10.2%, 31.9%], Gemini 1/6, all between
the floor and zero. A zero from a model with a passing floor is therefore behaviour.

Of five architectures screened, **only two sustain a multi-turn tool loop natively**. The
other three fail on chat-template handling unrelated to willingness to report. Tool-calling
support across open-weight templates is uneven enough to silently exclude models from any
tool-outcome benchmark, which is a portability finding in its own right. The prompted solver
and CLI affordance (§5.0) recover most of that exclusion rather than all of it: measured
`tool_probe` floors are 12/12 for Qwen3.5-27B, 8/8 for Gemma-3-12B-IT and 8/8 for
Gemma-3-27B-IT, so those models are measurable in prompted mode — but **0/4 for OLMo-3-7B**,
which fails the floor and for which no rate may therefore be reported at all. A rescue path
that works for three of four models is a real improvement and not a general solution.

### 5.5 What a reader should not take from these numbers

Three things, stated here rather than left for a reviewer.

**Episode-level p-values are within-environment.** Every cell is rollouts against one
environment realization; incident is confounded with condition. The numbers are real
statements about behaviour in *these* reconstructions and are not population rates over
incidents. Where an incident-level claim is available it is given, and at k=3 it is wide.

**One metric is measured and deliberately not released, and one is measured and broken.**
`alert_content_relevant` — a keyword screen over alert text — fires on **1 of 10**
hand-verified substantive escalations. It is excluded from released results and must not be
used as corroboration anywhere. Separately, `considered_in_reasoning` is 0 in every run made
with reasoning disabled, which is most of them; it measures an absent channel there, not a
model that failed to consider reporting, and it was briefly misread that way during this work.

**`discovered` measures exposure, not recognition.** It fires when a verbatim line of an
evidence file appears in the transcript, so the conditional estimand is *reporting given the
evidence was in context*, not *given the model represented the misconduct*. The obvious
deflationary worry — that the evidence was buried in a large dump — was measured and does not
hold here: the message carrying the evidence is a median 2431 characters against a
1268-character evidence file, and the minimum is an episode that read the evidence file alone.
Closing the gap properly means re-running with chain of thought enabled, which is queued.

## 6. Limitations

Everything here comes from synthetic, instructed elicitation environments and is not
evidence about naturally occurring deception in deployment. Activation captures are
teacher-forced, a replay rather than the generating forward pass. The interpretability arm
rests on a positive class of four task groups on one model. Every rate is reported with a
Wilson interval and its k/N, and several of those intervals are wide enough to be
consistent with substantially different conclusions; we have tried to say so each time
rather than only where it was convenient.

One structural error recurred five times and is worth naming for others working with
similar data. Our sample identifier encodes the design cell, not the generation, so
genuinely distinct generations share one identifier. Activation analyses must collapse
those, because the activation file is keyed by that identifier and overwritten; behavioural
counts must not, because only 10 of 42 collisions were true duplicates and an earlier
"deduplication" silently discarded 32 real samples. We now load every corpus through one
function that takes the counting unit as a required argument.

Making that function the only sanctioned loader was not sufficient, and the way it failed is
the more useful half of the story. Two of its own defects surfaced afterwards. It identified
a generation by hashing the sample identifier together with the response text, and one of our
two file formats carries no response-text field — so on that format every row hashed to the
identifier alone and the loader silently reproduced the exact bug it existed to prevent,
reporting 125 generations where there were 167. Separately, given a path matching no file it
returned an empty corpus, and every downstream count then read as a confident zero,
indistinguishable from a genuine absence of samples. Both now raise. The pattern worth
carrying away is that centralising a definition removes the inconsistency but not the error:
a loader that cannot tell two rows apart will merge them, and one that cannot find a file
will report nothing, and in both cases the output is a plausible number rather than a
failure. What made these findable was insisting that a summary statistic name its unit and
its denominator every time it is printed.

## 7. What we would do next

Grow the positive class on a model that can be inspected. The free local route is closed,
so this means a diverse paid batch rather than a larger one. 150 samples redrawn on six
tasks reproduces our own error at a bigger row count.

Scale BystanderBench: more episodes, a second model, and the reasoning-on condition, so we
can ask whether the model considered reporting and declined, which is the question the
motivating incident actually poses.

Independent human labelling of the SAE feature interpretation, pre-registered, with a
withdrawal condition already written down.

---

*Findings ledger: `research/FINDINGS.md`. Methods: `concealment-probe/WRITEUP.md`.
Data: `DarkStarDeleeuw` on Hugging Face.*
