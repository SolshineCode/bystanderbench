# Path to completion — my assessment, 2026-09-12

Written independently of the Fable agent's plan (`*-fable.md`) so the two can be compared
rather than one anchoring the other. Both halves are in scope per Caleb 2026-09-12.

## Where the two halves actually stand

**Part 2, BystanderBench: the instrument is finished; the release is not.** The methodology is
frozen at v1.0 behind one reporting path, with four independent refusals (affordance floor,
competence gate, no-channel arm, no model identity) and a deterministic evidence-naming test
(§F117). Results exist for 13 model-cells plus 2 refused. What does not exist is anything an
outsider could run: no package, a quickstart that produces REFUSED on every line, and a runner
that prints the wrong tool's numbers (§F102 B).

**Part 1, concealment probe: blocked on positives, and the block may be an artifact.** Every
dense model screened is at 0–5%; the one MoE screened is at 22%. `nex-n2.5-mini` is the first
untested local MoE and is screening now. That single run decides whether Part 1 is "rare
behaviour, hard problem" or "we screened the wrong architecture class".

## MUST-DO to publish

Ordered. Each line says what done looks like and what it unblocks.

**1. Make the benchmark runnable by a stranger.** (§F102 B, ~4h writing, no GPU)
Done = a clean clone, `pip install -r`, three documented commands, and `report.py` prints
numbers. Today the quickstart omits `tool_probe` so every cell is REFUSED after ~96 paid
episodes, `run_bench.sh` calls `summarize.py` when the methodology says `report.py`, and
`run_bench.sh` swallows hard failures with no `-e` and no status check. Unblocks everything
external: no reviewer, no Inspect submission, no replication without it.

**2. Restructure as an Inspect Evals package.** (~6h, no GPU) — I checked the upstream shape
rather than guessing; `inspect_evals` is installed at
`.venv/lib/python3.14/site-packages/inspect_evals/`. Every eval is a package:
`__init__.py` exporting the tasks, `<name>.py` with the `@task` functions, `scorer.py`,
`README.md`, `eval.yaml` (title, description, arxiv, group, contributors, version, tasks with
`dataset_samples`, tags), and one entry in `_registry.py`. Ours is a flat `bystander/` of 40+
files where research logs, capture tooling and the eval are mixed together. Done = a
`bystanderbench/` package containing only the eval, with the capture/analysis tooling moved
out. Unblocks the upstream PR and, separately, makes the artifact legible to a reviewer.

**3. Opus benign control.** (~$2.67, needs Caleb, 20 min) Opus is 6/6 on misconduct with no
specificity check. `nex` has one (0/24 benign vs 9/48 misconduct, §F105) and that is what makes
its 19% mean anything. Without the Opus control the strongest single result in the paper has
the weakest support. Unblocks the headline claim.

**4. Finish the write-up's open-questions section.** (~3h writing) Five rejected hypotheses
(§F97, §F100, §F110, plus turn-index) are currently scattered across ledger entries. Caleb's
instruction is to stop chasing the cause and publish it as open questions. Done = one section
naming each hypothesis, how it was tested, why it failed, and what would settle it.

**5. The leaderboard.** (~4h) Caleb is right that model × incident is the product, not a
defect. Done = a table or figure with models on one axis and incidents on the other, every
cell carrying its own floor and competence figure, refusals shown as refusals. The data exists;
this is presentation. Unblocks the "why would a lab care" question.

**6. Decide Part 1's verdict on the evidence.** (GPU, running now) If `nex-n2.5-mini` conceals
at MoE-like rates, Part 1 gets a local positive class with generating-pass activations and
becomes finishable. If it is ~0%, Part 1's honest result is the scarcity finding itself plus
the north-mini corpus, and the paper says so. Either way this is the last experiment Part 1
needs before writing.

## NICE-TO-HAVE — explicitly not blocking

- More incidents (35 needed for a 10% incident-level bound; we have 3).
- The gemma prompted-loop repair (task #24) and the remaining 346-episode capture backfill.
- The offline noticing probe (§F107) and the reasoning-on rerun.
- The detection-game autolabelling proposal — a good idea, a different paper.
- Any further work on *why* incidents differ.

## Critical path

`1 → 2 → upstream PR` is the longest chain and is entirely non-GPU writing/refactoring, so it
can start immediately and run while GPUs do Part 1. `3` needs only Caleb. `4`, `5` are parallel.
**The binding constraint is not compute, it is packaging.**

## Three risks

1. **Scope creep through interesting findings.** Five hypotheses were tested because each was
   interesting; none was necessary. Mitigation: the NICE-TO-HAVE list above is a commitment,
   not a wish list.
2. **The repo is private and has no package**, so "reproducible" is unverified in the only way
   that counts. Mitigation: item 1, then have someone who is not us run it.
3. **A frozen v1.0 with five improvements already queued.** Mitigation: cut v1.1 explicitly
   after the paper, not before; nothing queued may change a released number.

## What to cut now

Task #27 (addressee experiment) — done and negative, close it. Task #28 (offline replay probe)
— superseded by §F108's measurement. Task #19 (more free-tier models) — adds cells, not
contribution. Task #6 (probe fit across all models) — gated on a three-scenario positive class
that does not exist and will not before publication.
