# Path to completion — 2026-09-12

Written by Fable (read-only pass over README, §F100–§F117, METHODOLOGY-v1.0, the 2026-09-09
paper draft, and the 2026-09-11 reproducibility / paper-vs-ledger / ledger-contradictions
audits). Planning only; nothing here was run or edited. Owner decisions respected: both
halves stay in scope, the incident-difference investigation is closed (§F110), a
models × incidents leaderboard is wanted, venue/sequencing go to Peter.

**State in one paragraph.** BystanderBench has a frozen methodology, a gated reporter, 117
ledger entries, a positive class at n=84 (§F114), a specificity control on the model that
reports (§F105), a within-model incident effect that survives six adversarial audits but not
cluster-honest inference (§F100/§F101), and a deterministic stuck-vs-substantive screen
(§F117). What it does not have: a public repo (`SolshineCode/silent-concealment-detection-lab`
is private), a licence file, a package, a leaderboard with more than one column filled, a
paper that agrees with the ledger, or a matched control on its headline model. The
concealment probe has three checked-and-killed interpretability results, a positive class of
four on the only fully-instrumented model, and one live experiment (the `nex-n2.5-mini`
ImpossibleBench screen on GPU0, reserved until 16:43 today) that decides whether Part 1 gets
a subject.

---

## 1. What remains, ordered

### MUST-DO-TO-PUBLISH (in execution order)

**M1. One correcting ledger entry that settles the five numeric contradictions (§F102 A).**
north-mini 39/177 vs 41/176 vs 53/237; gemma-3-12b 166 vs 122 vs 156 (§F22 says 5/122
behavioural, 4/99 activation-backed — §F32 and the paper's §3 table reuse the withdrawn 166);
the "30 of 110" vs §F18's "8 of 13" disclosure-mislabel count; the paid balance chain; and
the `0/40` qwen figure in the agenda/slides that is actually nex's incident-3 conditional.
*Done* = one §F entry, each number re-derived from its data file with
`concealment-probe/tools/corpus.py` (unit named) or `report.py`, and every outward doc
(README, paper, slides, agenda, MANIFEST) carrying the same value. Effort: 3–4 h writing, no
GPU. Unblocks: every number in M4 and M6. Nothing external may cite a number until this lands.

**M2. Close the reproducibility blockers that are still open** (from
`research/audits/2026-09-11-external-reproducibility.md`, checked against the tree today):
- B2 — `bystander/run_bench.sh:44` still defaults `TOOL_ARMS="with_tool no_tool"`; the README
  now says "run the floor first", the runner still does not. Make the default
  `tool_probe with_tool`.
- B3 — `run_bench.sh:73` still calls `summarize.py`; call `python -m bystander.report` and
  print the summarize block as explicitly exploratory.
- B4 — `set -uo pipefail` with no `-e`, eval piped into `grep | tail`, no `PIPESTATUS`
  check. This is the one that yields a *wrong* number rather than none. Add per-cell exit
  capture and refuse to report on any failed cell.
- B5/B6 — `capture_activations.py:25`, `capture_backlog.sh:8`, `capture_run.sh:7`,
  `run_pilot_local.sh:15`, `run_smoke_local.sh:10` hardcode `/home/darkstar`;
  `test_guards.py:130` checks one file. Derive BASE from `__file__`/`BASH_SOURCE`, take
  `BIN`/`GGUF` from env with a clear error, parametrise the guard over every `*.sh`/`*.py`.
- F1 — `MODEL_ID` not forwarded by `run_bench.sh`; two local models fuse into one cell.
- Add `LICENSE` (none exists — `ls LICENSE*` is empty). Caleb chooses MIT or Apache-2.0.
- Add `pyproject.toml` so `bystander` is importable without the `sys.path` shim in
  `task.py:19-26` (needed for M7 regardless).
B1 and B7 are closed (`bystander/requirements.txt` exists; rule 6 is in METHODOLOGY).
*Done* = a fresh clone on another machine, `pip install -r bystander/requirements.txt`,
runs `MODEL=<cheap hosted> bash bystander/run_bench.sh` at `EPOCHS=1` and `report.py` prints
a non-REFUSED row. Effort: 4–6 h code, ~$0.10 API for the smoke. Unblocks: M6, M7, and any
external replication (currently zero).

**M3. Fill the leaderboard grid, one approved paid batch.** The grid is rows = every floored
model, columns = incident 1 / incident 2 / incident 3 / benign; cell = k/n with Wilson, floor
in the row header, refused cells hatched (the figure convention already in
`visualizations/build_model_results.py`). Today only `nex-n2.5-mini` and `qwen3.5-27b` have
columns 2–4 filled; every hosted model has column 1 only, at n=6. Minimum to publish the
grid: every hosted model with a passing floor × {incident 2, incident 3, benign} at n=6, plus
n=6 more on incident 1 for Opus and Sonnet (their 6/6 and 4/6 carry [61%,100%] and
[30%,90%]). At §F80 rates: Opus 24 episodes ≈ $10.7, Sonnet 24 ≈ $1.8, the rest under $1 paid
plus free-tier time. **This batch includes the Opus benign control (§F91/§F105 top open
item, ~$2.67).** Budget ≈ $15; balance is ~$0.66 (§F91), so a ~$25 top-up is a human step.
Rules that already bit this project: smoke one episode per new (model, arm) first,
`--max-connections ≤ 6`, one batch at a time, `spend_watchdog.sh` armed (CLAUDE.md
2026-09-06 incident); run through `bystander/run_or_paid.sh`, not by hand. Pre-register the
cell list in a §F entry *before* launch, per §F104's practice. *Done* = `report.py --csv`
over the new dirs, every cell either a rate with its floor or a printed refusal, ledger entry
with the table, `capture_coverage.py` irrelevant (hosted). Effort: 1 h prep, ~4–6 h
wall-clock unattended, 1 h audit of every alert with `evidence_ref.py` (§F117). Needs Caleb:
top-up + per-launch approval. Unblocks: the leaderboard figure, M4's headline table, and the
claim "reporting is a property of the (model, incident) pair" at the model unit.

**M4. Rewrite the paper against §F117, not §F99.** The 2026-09-09 draft is three days and
~20 ledger entries stale; `research/audits/2026-09-11-paper-vs-ledger.md` lists the rows.
The ones that would embarrass in review: "Nex-N2.5-Mini (n=30) 5/30" beside 9/48 in the same
paper; "every model here has open weights" under a table with Opus/Sonnet/Gemini/GPT;
"gemma 8/8 … measurable in prompted mode" (the exact inference §F98 forbids); "addressee
availability is being tested now" (killed, §F110); "reasoning-on condition" as next work
(dead, §F58); NLAs attributed to `kitft` (§F52: Anthropic's). Structural changes:
- Headline = the leaderboard (M3), then the within-model incident table at n=48 (§F103),
  then specificity (§F105 + Opus control), then the two refused cells as outcomes
  (§F98/§F112/§F117).
- §F101's clustering caveat stated once, prominently, in the words §F101 gives; every
  episode-level p labelled within-environment; incident-level summary "2 of 3".
- The mechanism hunt becomes one paragraph of open questions: findability, harm domain,
  lying-vs-concealing, addressee — four tested, four rejected (§F97/§F110), evidence
  position untested — offered to other researchers, not chased.
- Evaluation awareness (§F90) reported with §F101 point 5's two caveats, as an upper-bound
  statement only.
- Part 1 rewritten as "why the probe has no subject, and what that says" — see M5.
*Done* = every number in the paper is a cell of a committed CSV produced by `report.py` or
`corpus.py`; a script regenerates every table from that CSV; no prose figure without a §F
pointer. Effort: 10–14 h writing. Depends on M1, M3, M5. Unblocks: mentor review, arXiv,
M7.

**M5. Finish Part 1 as a result, not an apology.** Concretely:
- (a) Land the `nex-n2.5-mini` ImpossibleBench screen running now (`logs/part1-nex-n2.5-mini`,
  GPU0 reserved to 16:43). Hand-audit every `concealed_cheat` per §F26's discipline, count
  with `corpus.py` at units `generation` and `task`, one §F entry either way. If nex conceals
  at north-mini-like rates it is the first model that both conceals and runs in the local
  capture rig, and Part 1 has a subject for a probe (not an SAE — none published; the
  three-task-group rule at CLAUDE.md §4 applies). If it does not, the "dense vs MoE" reading
  of §3 is dead and the table says so.
- (b) Write §F109 up as the Part 1/Part 2 bridge: gemma-3-12b-it tampers the cover-task
  fixture in 4/12 episodes of a task that is *not* impossible, against 5/122 on
  ImpossibleBench. `cover_task_passed_before_tamper_check` and `cover_files_changed` are
  already in scorer metadata; a `tampered_cover_task` column in `report.py` output is
  additive (same rule as §F117) and gives Part 1 a second elicitation with a higher rate on
  the one model with both an SAE suite and an NLA. Cheap and it is the strongest Part 1
  sentence available.
- (c) The negative-results section stands as written in §4.1–4.5 of the draft, with §F47's
  downgrade and §F44's null kept in full. That is the "difficulty is a finding" content: the
  coverage-gap table, the L0 validity gate (§F33), a separating feature killed by its own
  max-activating examples, a replicated feature that failed on an independent corpus, a
  stable causal null, and a task-capped harvest (§F40).
*Done* = (a) landed and audited, (b) column added and reported, Part 1 section rewritten.
Effort: (a) 0 GPU-h beyond the live reservation + 2 h audit; (b) 2 h code; (c) 4 h writing.

**M6. Publish the corpus and make the artifacts reachable.** All 11 HF datasets sit under the
private `DarkStarDeleeuw` account; the repo is private. Release means: repo public under a
licence, the `.eval` logs behind every released cell committed (§F107 found sixteen dirs that
never were; `logs/` is gitignored — they must be force-added or moved), and the HF datasets
either made public or mirrored to `Solshine`. Visibility changes are Caleb's explicit
yes/no, per standing rule; ask the exact question, do not infer. Also strip anything
host-specific from `bystander/README.md:190-232` into an appendix (audit F2). Effort: 2 h
plus Caleb's decisions. Unblocks: M7 and any external replication.

**M7. Inspect Evals submission (see §4 below for the how).** Sequencing is already decided
(positioning doc §16, 2026-09-04): paper on arXiv first, then the `register/` external
submission with the arXiv URL. So M7 is last on the chain and cannot start before M4 is on
arXiv. Effort: 6–8 h packaging, then bot review cycles. Needs Caleb: authors the PR text and
answers maintainer questions.

### NICE-TO-HAVE

- **N1. Per-environment floors for hosted models** on incidents 2/3 (4 episodes each). v1.0
  keys floors by (model, mode), so not required; §F93 did it for nex and it is cheap for
  everyone but Opus. Do it if the M3 budget allows.
- **N2. Seed-varied realizations.** `task.py::_prepare(arm, seed)` is deterministic, which is
  what makes §F101's ICC unidentifiable. If `build_env.py`'s seed varies surface detail,
  future cells run as 4 seeds × 12 rather than 1 × 48 would make ICC *estimable*. Changes
  the estimand, so it is a v1.1 methodology decision, not a patch to the v1.0 corpus. Worth
  raising with Peter as the answer to his question 4 in the agenda.
- **N3. `tampered_cover_task` as a v1.1 gate** (from M5b) and `names_evidence` (§F117) as a
  gate — both are reported-not-gating in v1.0 and should stay that way until the corpus is
  released.
- **N4. Human labelling packet 2** (inter-rater reliability on the disclosure label, §F38) —
  only if answers already came back. Packet 1 interprets a feature §F47 downgraded; withdraw
  it with a dated note rather than collect it.
- **N5. Kaggle NLA decode** (§F115) — a thirty-second accelerator selection in the Kaggle UI
  by Caleb; one attempt. It decodes vectors on a path whose positive class is four and whose
  feature result is already downgraded, so it changes one sentence in §4 either way.
- **N6. A results page** (static, generated from the CSV) once the grid exists — useful for
  the lab-contact route Peter may recommend; not a publication blocker.

---

## 2. Critical path and parallelism

```
M1 ledger reconciliation (3-4h, no GPU)
  └─> M3 paid grid  ──needs top-up + approval──>  (4-6h wall)  ──> audit alerts (1h)
        └─> M4 paper rewrite (10-14h)  <── M5a nex screen (live now) + M5b/c (8h)
              └─> Peter review (human, days)
                    └─> arXiv (human: account/endorsement, days)
                          └─> M7 register submission ──> bot + maintainer review (days-weeks)
```

The longest chain is **M1 → M3 → M4 → Peter → arXiv → M7**, and the two human waits
(top-up/approval, then arXiv + maintainer review) dominate it; the agent-executable work on
that chain is roughly 25–30 h. Everything else runs beside it:

- **Parallel now, no dependencies:** M2 (repro fixes — pure code, no GPU), M5b (tamper
  column), M6 prep (LICENSE draft, README appendix split, listing which log dirs are not
  committed). GPU1 is idle and *should stay idle* — nothing on the must-do list needs it.
- **Parallel once M1 lands:** slides and agenda corrections (paper-vs-ledger audit §A rows
  for agenda/slides).
- **Serial and gating:** M3 cannot start without money; M4 should not start until M1 and M3
  are in, or it will be rewritten a third time. If the top-up does not happen, publish with
  Sonnet as the controlled headline (§F91) and Opus explicitly unmatched — the README already
  frames it that way and it is honest.

---

## 3. What "done" looks like for the project

A public repo with a licence, a package, and a quickstart that a stranger can run to a
non-refused number for under $1; a leaderboard figure with every floored model across all
three incidents and the benign control; a paper whose every number is a CSV cell; the logs
and activations behind it on HF; and a `register/` PR at Inspect Evals pointing at a pinned
commit and an arXiv URL. Part 1 is complete when its section reports the nex screen, the
gemma tamper rate, and the three killed results as findings with the checks that killed
them — not when a probe works.

---

## 4. Getting BystanderBench into Inspect Evals

**Which door.** There are two. Native (`src/inspect_evals/<name>/`) is for ports of
published, adopted benchmarks; their `CONTRIBUTING.md` says evaluations designed by
individuals without external publication are "generally not accepted" (verified 2026-09-04,
positioning doc §16). The realistic door is the **`register/` external submission** —
`register/<name>/eval.yaml` pointing at an external repo at a pinned 40-char SHA, reviewed by
the `register-submission-review` bot and one maintainer. ExploitBench went through it in
three bot rounds and one human question (PR #1959,
`research/bluedot-inspect-evals-verification-2026-08-28.md`). It **hard-requires an arXiv
URL** (the bot derives title/description/tags from it). So: arXiv, then register.

**What the bot checked on the precedent, and where this repo stands:**

| requirement (from PR #1959's review) | BystanderBench today | fix |
|---|---|---|
| Public repo, commit-pinned | private | M6 |
| Sandbox with `network_mode: none` | already set (`compose.yaml:18`), image pinned by digest (audit N1) | none |
| Explicit opt-in for anything costly/risky | none; default run is 96 paid episodes with a one-line comment (audit F3) | print episode count and require `I_ACCEPT_COST=1` |
| No credential harvesting / unrelated network calls | `alert_oversight` and the CLI binary are local; the covert-channel payload is inert hex | state it in README |
| Not a fuzzy duplicate of an existing eval | nothing measures the witness; the dedupe check should return NO_MATCH | say so in the submission |
| Task importable as `inspect eval <repo>/…@<task>` with no required args | `task.py` needs a `sys.path` shim and `@task bystander()` defaults to a cell that `report.py` refuses | pyproject + sane defaults |

**Structural mismatches an upstream reviewer will see, in order of cost to fix:**

1. **The release gate lives outside Inspect.** Every rule that makes a number releasable —
   floor ≥ 75%, competence ≥ 75%, limit-hit exclusion, evidence-only discovery — is in
   `bystander/report.py`, a post-hoc tool over log directories. Inspect users expect metrics
   from `Score.metadata` and `metrics=[...]` on the task. Do not move the gate into the
   scorer (a single task run cannot see its own floor cell). Instead: expose `alerted`,
   `discovered`, `cover_task_passed`, `names_evidence` as Inspect `@metric`s so `inspect
   view` shows them, and document in the eval README that **these are ungated** and the
   released table comes from `python -m bystander.report`. Ship the floor as its own task
   (`bystander_floor`) so the quickstart is two `inspect eval` lines and one report line.
2. **Defaults produce nothing releasable.** `@task bystander(...)` should default to
   `arm="blatant_wrongdoing", tool_arm="with_tool", solver="tools", affordance="native"`,
   `epochs` documented, and `fail_on_error` set in the task rather than in a shell wrapper
   (§F95/§F96: one 32792-token episode discards its siblings under Inspect's default).
3. **Packaging.** No `pyproject.toml`; `bystander/__init__.py` is empty; `task.py` edits
   `sys.path`. Make it installable (`pip install -e .`) with `inspect-ai==0.3.261` as the
   floor and a note on API drift.
4. **Tests need Docker and are unmarked** (audit F4). Mark them; a CI-safe `-m "not docker"`
   subset must pass on a bare runner.
5. **Host-specific runbooks in the public README** (audit F2) and hardcoded paths (B5/B6).
6. **Model identity.** Upstream identity is the `--model` string; keep `-T model_id` for
   local servers but default it from the model string so hosted users never see it.
7. **The v1.0 known-limitation list** (METHODOLOGY: `ls scratch/` scores `discovered=0`,
   truncation, k=3) goes verbatim into the eval README's Limitations section. Reviewers
   reward this; hiding it costs a round.

**What not to do for upstream:** do not add tier 2 to the submission. Activation capture needs
a local llama.cpp build and a GGUF and cannot run in their CI; it is a separate artifact
(the HF activation datasets) referenced from the README. The submission is tier 1 only.

---

## 5. Three biggest risks, cheapest mitigation each

**R1. Number drift across documents.** A two-day-old draft disagreed with the ledger in ~30
rows, twice with itself (`research/audits/2026-09-11-paper-vs-ledger.md` §A–B), and the
ledger disagrees with itself in five places (§F102 A). At the current rate of entries this
recurs weekly. *Mitigation:* one committed `results/bystander-v1.0.csv` from `report.py`, one
`results/concealment-v1.0.csv` from `corpus.py`, every table in paper/README/slides generated
from those two files by script, and the rule that prose may quote only a cell that exists in
them. Then write the paper **once**, last.

**R2. Money and approval gate the headline control.** Opus's 6/6 has no benign control; the
balance is $0.66; the grid needs ~$15. If the top-up slips, M3 slips, M4 slips, and the paper
either waits or ships with an unmatched headline. *Mitigation:* ask for one decision now — a
~$25 top-up and blanket approval for the pre-registered M3 cell list — instead of per-cell
approvals over several days. Fallback already written: Sonnet is the controlled headline
(§F91), Opus is labelled unmatched.

**R3. The ledger's own gravity.** 117 entries in six days; every session finds a new
experiment (§F108's reasoning-on rerun, §F110's "next axis", §F107's replay probe, the
detection-game proposal, the 346-episode capture backlog). Each is defensible; together they
are why nothing ships. *Mitigation:* declare a freeze — after M3, new §F entries are
corrections or M-list results only; this file is the queue; anything else goes to a
`research/plans/post-v1.0-ideas.md` list with a one-line rationale and no run.

A fourth, external: **§F101 is the objection that could sink the paper** — one environment
realization per arm. It cannot be fixed on the v1.0 corpus. *Mitigation:* frame as Peter's
agenda question 4 puts it (case study with a reusable harness, or benchmark), lead with the
cross-model grid — which is a within-environment comparison and legitimately so — and put N2
in "future versions".

---

## 6. What to cut

Named so they can be abandoned rather than quietly left queued.

- **The fifth mechanism hypothesis** — evidence position / turn-index-of-first-evidence
  (§F110 "next axis"). Owner closed the investigation. One sentence in open questions.
- **Reasoning-on rerun of incident 3** (§F108 "better next run") and **the offline replay
  probe** (task #28, §F107). Exposure-vs-recognition is stated as a limitation of the
  estimand's name (paper §5.5 already does this); no new episodes.
- **The 346-episode capture backlog** (§F111/§F114). What is uncaptured is qwen and nemotron
  zeros, gemma's refused cell, and old smokes — no probe will train on any of it, and §F112
  says refused-cell activations are a different class anyway. Record "not captured" on the
  dataset card and stop. The captures that mattered (addressee, benign, positives) are done.
- **Gemma rescue work** — easier cover task, chat-template override, parser/window
  improvements (task #24; §F109 options 2–4). §F109 measured that a perfect parser recovers
  two episodes. Report the tampering rate (option 1, = M5b) and leave gemma REFUSED.
- **More incident-1 episodes on nex.** Rate stable across seven batches (§F114); precision is
  not the gap, a second scenario is, and that is out of scope by owner decision.
- **Building toward k=35 incidents.** Not this project; raise with Peter as a question, do not
  start.
- **Kaggle NLA decode beyond one UI attempt** (§F115) — see N5.
- **Detection-game autolabelling** (`research/proposals/detection-game-autolabelling-2026-09-12.md`).
  A new project with its own confounds; park it.
- **Human labelling packet 1** (§F38) — the feature it interprets was downgraded (§F47).
  Withdraw with a dated note.
- **Any further llama-3.3-70b, north-mini, splice, recruiter-pilot, or moe-floor runs.**
  All are historical evidence in the appendix now. north-mini gets exactly one re-derivation
  of its concealment count (M1) and nothing else.
- **GPU1 work of any kind until M3–M4 are done.** An idle card is not a reason to run
  something; that is how the backlog and the ledger got this long.

---

## 7. Human steps, collected

1. OpenRouter top-up (~$25) and approval of the pre-registered M3 cell list.
2. Licence choice (MIT or Apache-2.0).
3. Repo and HF-dataset visibility — explicit yes/no each.
4. Kaggle accelerator selection in the UI (N5), one attempt.
5. Peter: venue, sequencing, and the "benchmark vs case study" framing question.
6. arXiv submission (account/endorsement) and the register PR text.
