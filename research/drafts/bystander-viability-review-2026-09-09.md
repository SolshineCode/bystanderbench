# BystanderBench viability review, 2026-09-09

Written against the repo state at commit e0279f2 (§F45, §F46, paper draft). This is a
review of the benchmark's viability, not of the code's correctness; the construction
check already exists (`research/drafts/agy-bystander-review-2026-09-08.md`) and the repo
verified it item by item. What follows asks the next question: can this instrument
support the claims it wants to support, at what n, and what would falsify it.

## Verdict

Viable today as a within-model measurement instrument. Three conditions stand between
that and viability as a benchmark in the comparative sense: more than one environment
per arm, more than one model, and a conditional estimand. None is blocked on new
machinery; all are blocked on run volume.

## What is already established

- The instrument is not the explanation for the zeros. Affordance floor 4/4 (§F45): the
  model calls `alert_oversight` when asked, so absence elsewhere is behaviour.
- The scorer discriminates procedural from substantive alerts. `alert_content_relevant`
  0/4 on the instructed check-in is a designed-in negative control that fired correctly
  (§F45).
- Specificity exists so far. The benign control produced zero alerts in the pilot, and
  `blatant_wrongdoing` at the ceiling produced zero alerts while discovery was 3/4 (§F46).
  Recognition without action, in the easy case, on record.
- The primary outcome is mechanical, immune to the text-screen failure mode that
  mislabelled 30 of 110 disclosed rows in this repo's earlier work (§F18).

## Threats, with dispositions

| # | Threat | Status | Note |
| --- | --- | --- | --- |
| T1 | One environment per content arm | OPEN, most serious | See below |
| T2 | Prompt cueing of reporting (agy C1) | MITIGATED, direction known | The mundane framing invites reporting, which inflates alert rates. That makes observed zeros conservative: cueing cannot explain a zero, only a high rate. The `tool_probe` vs `with_tool` contrast is what isolates instructed from voluntary reporting, and it exists. |
| T3 | Context truncation on large tool outputs (agy C2) | OPEN, pre-scaling fix | `bash`/`python` outputs have no explicit cap; the README's own disposition says set one before scaling. A silent truncation mid-episode manufactures a fake zero. |
| T4 | `message_limit=40` (agy C3) | CONFIRMED, fix queued | 2 of 18 pilot episodes hit the cap before `submit`. A timeout can masquerade as reticence. Raise it and report hit-rate as a metric. |
| T5 | Discovery regex over-fire (agy B1) | CONFIRMED AND FIXED | `cat scratch/recon_fixture_*.json` matched the listing pattern; 42 of 54 listing hits were fixture reads. The fix requires the directory to end the token. Consequence: pre-fix pilot discovery numbers must not be cited. |
| T6 | Estimand dilution | OPEN, definitional | `alerted` pools oblivious episodes with silent ones. The scientific quantity is reporting conditional on discovery, `alerted / discovered`, with discovery reported alongside. At the ceiling that is 0/3, not 0/4. |
| T7 | Single model | OPEN | One model cannot support a claim about witnesses generally. gemma is excluded (llama.cpp tool-call handler); a second qwen, nemotron, or an OpenRouter model are the options already built. |
| T8 | Benchmark recognition / contamination | MITIGATED | The transposed arm changes every surface detail; the benign control bounds "reports anything unusual". |
| T9 | Keyword screens as judges | MITIGATED | `alert_content_relevant` and `mentioned_in_final` are labelled screens; `no_tool` hits are flagged `needs_hand_audit`. They are secondary channels; the primary is mechanical. |

## T1, the one that matters

Each content arm is one synthetic environment. Four episodes of `blatant_wrongdoing` are
four draws on one incident reconstruction, not four environments. This is the exact error
this repo corrected in itself on 2026-09-09 (§F43): 33 generations on 8 tasks were being
read as 33 independent samples when the honest unit was the task group, and the Wilson
upper bound moved from 10% to 39% when the unit was corrected.

Applying that discipline here: the honest unit for a generalisation claim is the
incident, and each arm currently has one. Scaling epochs within the arm buys precision
on that one stimulus; it cannot buy a claim about "witnesses" plural. Two ways out, and
they can be combined:

1. Build k incident-derived environments per arm (k >= 3 is the minimum for any
   cluster-robust statement), then cluster the inference on environment.
2. Keep n=1 environment per arm and state every claim as single-incident: "in this
   reconstruction, qwen3.5-27b read the evidence and reported nothing." That is a valid
   and publishable observation, but it is a case study, not a benchmark.

The transposed arm does not solve this. It controls recognition, not diversity: it is
the same conspiracy with different surface details, so realistic plus transposed is two
views of one incident, not two incidents.

## Statistical viability

At the observed ~8 minutes per episode (qwen3.5-27b, reasoning off, local):

- Zero alerts at n=16 per cell bounds the true rate below 20% (Wilson); n=35 bounds it
  below 10%.
- If the true ceiling rate is 20%, n=15 per cell yields at least one alert 96% of the
  time. A continued zero at n=15 is informative, not a sampling accident.
- Full 4x2 grid at n=15 is about 15 hours on one card; at n=30, about 31 hours. Both
  cards are free since §F44 closed the causal run.
- With k=3 environments per arm, the per-model cost triples only if n is held per
  environment; holding total n and splitting across environments is the efficient
  design, at some cost in per-environment precision.

## Preconditions for the scaling run, in order

1. Raise `message_limit` and record hit-rate; an episode that dies at the cap is a
   missing cell, not a zero.
2. Cap `bash`/`python` output so truncation is loud, not silent.
3. Add the conditional estimand (`alerted / discovered`) to `summarize.py` and make it
   the headline; keep unconditional `alerted` for comparability with §F31/§F45/§F46.
4. Decide the T1 route (k environments, or single-incident framing) BEFORE launching,
   because it determines the launch size and cannot be recovered afterward.
5. Second model in the `with_tool` ceiling cell first; that single cell is the cheapest
   check that the zero is not a qwen idiosyncrasy.
6. Reasoning-on condition on the ceiling cell; it is also the precondition for the
   activation-probe tie-in that justifies this benchmark living in a probing repo.

## Falsification criteria

The benchmark is healthy if, as models and incidents vary: the floor stays ~1.0, the
benign control stays ~0, and some model or some incident produces alerts (a nonzero
between floor and ceiling demonstrates the instrument can detect intermediate rates). It
is falsified if the floor fails on a second model (instrument is qwen-specific), or if
the benign control alerts (the mundane framing is a reporting prompt, and every high
rate is cueing). Both failures are cheap to test and should be the next two runs after
the preconditions above.
