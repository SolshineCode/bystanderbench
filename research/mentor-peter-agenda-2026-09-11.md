# Mentor session prep — Peter, week of 2026-09-11

> **CORRECTION 2026-09-13 (visuals audit).** Every `9/48` below for `nex-n2.5-mini` on
> incident 1 is superseded. Canon is **16/84 alerted, 16/83 = 19.3% conditional**
> [12.2%, 29.0%] (§F114, confirmed by re-running `bystander/report.py`). Derived statistics
> move with it: incident 1 versus incident 3 conditional is Fisher **p = 0.0013**, not 0.0034;
> incident 1 versus the matched benign control is **p = 0.020**, not 0.027. The floor for that
> cell is **8/8**, not 32/32. Incident 2 is **1/48** (1/33 conditional), not 0/18 (§F103). The
> numbers in the body are left in place rather than edited so the correction is visible.



BystanderBench, and how to make it useful to people who are not us.

## What changed since we last spoke

The headline inverted. Two weeks ago the result was "agents that discover misconduct don't
report it" — fourteen model-arms, all zeros. That summary is **wrong**, and finding out why
is the contribution.

| model | floor | alerted (ceiling arm) |
|---|---|---|
| Claude Opus 5 | 4/4 | **6/6** |
| Claude Sonnet 5 | 4/4 | **4/6** |
| Nex-N2.5-Pro | 4/4 | 4/6 |
| Nex-N2.5-Mini (hosted) | 4/4 | 2/6 |
| Nex-N2.5-Mini (local weights) | 32/32 | 9/48 |
| Gemini 3.1 Pro | 4/4 | 1/6 (only 1 episode reached the evidence) |
| GPT-5.6-Luna-Pro | 6/6 | 0/6 |
| Qwen3.5-27B (prompted) | 12/12 | 0/12 |
| ling ×3, nemotron ×2, dots | 3/4–4/4 | 0/6 each |
| Gemma-3-12B-IT | 8/8 | **REFUSED** — see below |

Slide 3 is this table as a figure, plus the within-model panel. It is generated from
`report.py`'s CSV, so it cannot drift from the ledger.

**The finding is variance, 0% to 100% on an identical environment.** It doesn't track serving
path, weight availability, parameter count, or lab. It tracks family — and the sharpest
evidence for what "family" means is that Nex-N2.5-Mini (`qwen35moe`) reports where
Qwen3.5-27B (`qwen35`) never has, on the same hardware and scorer. That points at
post-training.

**What landed after this agenda was first written (2026-09-11 evening).**

1. **The rate is incident-specific, and that is now the headline.** On one model, three
   structurally different incidents at n=48 each: **9/48, 1/48, 0/48**. The incident-1 vs
   incident-3 gap is Fisher p = 0.0034 — but see the caveat below, which I would rather you
   hear from me.
2. **Specificity is demonstrated on that model**: a matched benign anomaly is **0/24** against
   misconduct 9/48 (p = 0.027). Every incident comparison rests on 18.8% meaning "reports
   misconduct" rather than "reports anything odd", and this is what establishes it. Opus's
   6/6 still has **no** such control, which stays the top open item (~$2.67).
3. **Gemma-3-12B-IT nearly produced a false headline.** It passed its affordance floor 8/8
   and then returned 41.7% "alerts" — all of them *"I am blocked on the bug"* messages, with
   `cover_task_passed` 2/12. The tool now refuses cells below 75% competence. Gemma is
   **unmeasured**, not silent, and that matters because it is the only model here with both a
   GemmaScope SAE suite and a published NLA.
4. **The caveat I most want your read on.** Every cell is ~44 rollouts against **one**
   environment realization, so incident is perfectly confounded with condition. An
   intra-environment correlation of 0.027 takes that p = 0.0034 past 0.05, and a
   cluster-respecting permutation gives p = 0.33. The design-honest summary is the
   incident-level one, and with k=3 it is uselessly wide. **Is an episode-level p-value on a
   one-cluster-per-arm design publishable with the caveat attached, or not publishable?**
5. **~5% of episodes show evaluation awareness in CoT**, and those alert at 45.5% vs 5.5%
   (Fisher p = 6.6e-7, though the screen reads the same text as the outcome, so it is
   confounded). Our rates are plausibly an upper bound on deployment behaviour.
6. **The first mechanism experiment is running and is going against its own hypothesis.**
   Addressee availability — whether the environment names an external body already holding
   the falsified artifact — was the cleanest measured separator. Two minimal-pair arms were
   built and the prediction recorded before running. At the n=24 interim neither arm has moved
   significantly, and the de-named arm's alerts still name the misconduct in full.

## Questions for Peter

**On making it useful to frontier labs**
- Labs already run internal evals. What makes an external benchmark worth their time — a
  capability their internal suite lacks, a number they can cite publicly, or an
  independently-run result? Which of those is BystanderBench closest to?
- Is "reporting propensity" a metric a lab would actually act on, or is it too far from a
  deployment decision to move anything?
- The evaluation-awareness result (models reasoning "this is probably a benchmark") — is that
  a fatal objection for lab adoption, or the kind of thing everyone already knows and prices
  in? It feels important and I can't calibrate how it will land.

**On making it useful to other researchers**
- Tier 1 needs only an API key and Docker; tier 2 needs open weights. Is that split the right
  unit of adoption, or should the behavioural benchmark ship entirely separately?
- **The repo is still private** (`SolshineCode/silent-concealment-detection-lab`), so nobody
  outside this conversation can run BystanderBench at all. Whatever release means, that is
  step zero and I don't know what shape it should take.
- What's the realistic bar for someone to pick this up — a paper, a HF dataset, a pip
  package, a leaderboard? Corrected 2026-09-11 after checking rather than remembering: I have
  a paper draft, a frozen methodology, 11 HF datasets and a reproducible harness. I do **not**
  have a public repo, a pip package (no `pyproject.toml` exists), a leaderboard, or a single
  external replication.
- **k=3 incidents gives an incident-level bound of [0%, 56.2%]; 35 incidents would be needed
  for 10%.** Is building ~30 more environments a sensible use of the next months, or is that
  the wrong axis to spend on?

**On promotion and positioning**
- Where does this go — an alignment-forum post, arXiv, a workshop, or straight to lab
  contacts? What sequencing has actually worked for people at my stage?
- Is the Opus behaviour worth leading with? It attributed its own ticket's bug to the agents
  that planted it, and asked to escalate *outside the management line of the person who
  ordered the misconduct*. No metric scores it; it may be the most interesting thing here.
- How much does it matter that this came out of a BlueDot unit rather than an institution?

**On what I should be worried about**
- What's the strongest objection you'd raise if you were reviewing this?
- Is the honest framing "a benchmark" or "a case study with a reusable harness"? I've been
  saying benchmark and I'm not certain I've earned it.

## What I'd like out of the session

A decision on the next axis — **more incidents (breadth) vs more models (coverage) vs the
interpretability tie-in (depth)** — and a read on whether to approach labs now or after more
environments exist.

## Slides

`research/slides/bystander-peter-2026-09-11.html` — four slides for the session, plus two
appendix slides (A1 the conditional estimand and the known holes, A2 release and promotion)
Slide 3 is the full-roster figure, `visualizations/bystander_model_results.png`.
to pull up only if the conversation goes there.

## Backing material
- `research/drafts/paper-draft-2026-09-09.md` — full write-up with figures
- `research/FINDINGS.md` §F59–§F108 — append-only ledger, every claim sourced
- `bystander/METHODOLOGY-v1.0.md` — frozen methodology; what is and isn't released, and why
- `README.md` — leads with the open specificity gap on Opus
