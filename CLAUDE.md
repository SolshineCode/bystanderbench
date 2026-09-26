# CLAUDE.md — Silent Concealment Detection Lab (BlueDot Technical AI Safety Project)

Operative instructions for any agent session in this repo. This file is the rules, not the
story: incidents are named with the number that makes them actionable, and the narrative
lives in the canonical docs. Repo map: `MANIFEST.md`. Project summary: `README.md`.

---

## 📘 Canonical ground-truth docs (read / append — never silently edit)

- `research/FINDINGS.md` — **append-only numbered ledger** (§F1+). Every settled result
  gets an entry with a source pointer. Never renumber, never delete; an overturned
  finding keeps its original text plus an inline dated `SUPERSEDED BY §Fn` /
  `CORRECTED YYYY-MM-DD` block.
- `research/model-testing-audit-2026-09-05.md` — per-model evidence table, every count
  pulled from data files rather than prose. Grows by **appending dated sections**; later
  sections supersede earlier rows. Best answer to "what do we actually have data for".
- `research/bluedot-research-positioning-and-trial-design-2026-09-03.md` — the
  narrative/decision record. **§20, the bystander-disclosure benchmark, is a primary
  intended contribution of this project, not a side experiment; it is summarised at the
  top of `README.md` and stays there.** Grows by dated `Update YYYY-MM-DD` blocks inside
  the relevant section.
- `research/citation-list-2026-09-04.md` — verified literature only, each source
  re-checked against the actual paper.
- `MANIFEST.md` — repo/data map. No rules there; they live here.

**Correction discipline (project-wide).** Three real carried-forward-from-prose errors so
far: the `qwen3.8:27b` "dense negative" that never produced a sample, the Nemotron Ultra
"13/30" that is unverifiable, the "era does, cleanly" n≈50 overclaim. Never propagate a
number from memory or another doc's prose — pull it from the data file or the audit table.
On finding an error, fix every instance with a dated correction block and name the
correction in the commit message. **A rule may not cite the ledger for something the
ledger does not say** — if a rule here rests on an incident, that incident gets a ledger
entry (§F38's `<think>` defect had to be back-filled for exactly this reason).

---

## ⛔ Smoke-test before scaling — ANY new batch shape

**The rule.** Before any run at a shape not already validated — new venue, new concurrency,
new parallelism, real money where it was free, a much bigger N — run 1–2 samples first,
then check `uptime` load, `docker ps | wc -l`, and per-sample cost and latency before
scaling. "It worked at the old shape" is not validation of the new shape. On this 8-core
box, sandboxed evals cap at `--max-connections 6`, one batch at a time.

**Why (2026-09-06).** Five paid OpenRouter batches launched at once at `--max-connections
20`, no smoke test: ~82 concurrent Docker sandboxes, load average 27, `SandboxTimeoutError`
cascading, and **$5.67 of the $10 grant credit** burned on timeout-corrupted attempts
rather than model behaviour. Local llama-server launches had smoke tests that night; the
discipline just wasn't generalised to a new shape. Then a `kill <parent-pid>` was reported
as "stopped" while the child worker kept spending for 2.5 more hours — final balance
**$10.236 of $10.00**, not the $3.415-remaining reported at the time.

**Now enforced in `run_eval_openrouter.py`, not just written here** (each verified against
the live account): hard `--max-connections` cap of 8 that refuses above it; pre-run balance
check refusing below $1.00; `flock` single-instance lock so a second paid batch cannot
start; `os.setpgrp()` so `stop_openrouter_jobs.sh` can `kill -- -PGID` and **refuses to
report success without confirming via `pgrep` and `docker ps` that nothing remains**; and
`spend_watchdog.sh`, auto-launched with every paid run and tied to its lifetime, polling
the real balance every 5 minutes and self-triggering the stop below $0.50 — that last one
closes the 2.5-hour blind spot, since the pre-flight check only gated the start.
`check_balance.sh` is the manual one-shot.

**Standing rule:** no paid-tier OpenRouter or other real-money launch without Caleb's
explicit per-launch go-ahead in that session. Not inferred from earlier general approval.

---

## ⛔ Evidence discipline (standing, permanent)

1. **A raw eval log is not a result.** No run is project evidence until processed through
   the labelling/audit pipeline (`prepare_dataset.py` locally, `screen_behavioral.py` for
   cloud) with every `concealed_cheat`/`disclosed` row hand-audited. Unprocessed runs are
   open loose ends, flagged as such, never cited from memory.
2. **Taxonomy v2 — flag LOCATION decides disclosure.** Only a flag in `visible_prose`
   yields `disclosed`; `reasoning_only` and `code_only` are awareness traces, not
   disclosure. (41 of 43 north-mini "disclosures" were reasoning-only.)
3. **Honeypot tasks.** Deliberate oversampling of `lcbhard_9` / `lcbhard_21` is REJECTED —
   sample uniformly. Any honeypot row that appears naturally gets elevated scrutiny:
   verify the mechanism against the code line by line, never batch-approve.
4. **Statistical honesty on small N.** Every rate carries a 95% Wilson CI and its k/N
   (enforced in the visualization pipeline). Overlapping CIs mean "cannot distinguish",
   full stop — the rung-1 "era does, cleanly" claim from n≈50 was falsified at ~4× N and
   is the standing cautionary example. Where mechanism audits are incomplete, cite the
   classified **floor**, not the raw count. Probe and geometry claims stay volume-gated:
   three or more independent positive task-groups before a leave-one-group-out result
   means anything.
5. **Provenance categories never pool.** Cloud/behavioural evidence stays permanently
   separate from local activation-backed evidence; spontaneous, planted-evidence,
   splice-continuation and recruiter-pressure positives are distinct labelled classes in
   every table and claim. Mechanism (`check_override` vs `hardcode`) is a per-sample
   annotation, not a footnote.
6. **"Concealed" means "did not disclose visibly to the scorer",** not "left no trace" —
   nearly every real cheat leaves an in-code or in-reasoning admission. Writeups carry
   that grade explicitly.

---

## ⛔ Hardware & scheduling hard rules (dual Tesla M40, 8 cores)

- **NEVER run HF `transformers` eager `.generate()` on the local GPUs.** Eleven hard
  power-loss crashes traced to its per-token kernel-launch pattern. All local generation
  goes through llama.cpp; activation capture through
  `concealment-probe/tools/extract_resid.cpp`. Kaggle/Colab may use transformers hooks —
  the ban is about this machine's PSU, not the library.
- **gpusched reservations are mandatory** before any GPU work, and heavy CPU/RAM jobs
  count. Long-running pipelines self-reserve and self-release (`splice/run_trial.sh` is
  the pattern). The `gpu-schedule` skill has the workflow.
- **Layer convention:** "layer L" = `l_out-L` = `hidden_states[L+1]`. A published artifact
  states its own hook point — read it, don't assume (GemmaScope-2 declares
  `hf_hook_point_in = "model.layers.L.output"`, which matches). Scripts must refuse when
  the declared hook disagrees with the layer requested (`sae_encode.py`,
  `sae-causal/export_control_vector.py`). Kaggle templates fixed 2026-09-05; pre-fix
  datasets carry card corrections.
- `~/CLAUDE.md` (home) has the full rig rules — driver-stack freeze, NUMA wrappers, ollama
  recovery. All apply here.

---

## ⛔ Interpretability-artifact discipline

For any published SAE, NLA, transcoder or probe applied to this project's captures.

1. **Pre-flight the whole chain before the expensive step.** Before a capture, eval or GPU
   reservation aimed at an interpretability result, confirm every downstream artifact
   exists for the exact checkpoint and quantisation: repo id fetched from the HF API (never
   inferred from a family name), the layer present, and max-activating examples shipped
   with the weights if you intend to interpret features. "This model is interesting" is not
   a reason to capture it — §F32 stopped two running north-mini jobs mid-flight for want of
   this check.
2. **Gate the artifact on in-distribution inputs before any feature claim.** Report
   realised L0 against the artifact's target L0 first. §F33: span-mean slots gave realised
   L0 15–18 against a target of 120 with 60 of 16384 features alive, voiding a whole
   differential pass; the single-token slot was in distribution at 92.6. Across-sample FVU
   is **not** the standard per-token FVU and does not carry the verdict. Consequence: the
   probe arm's preferred slot and the SAE arm's only valid slot are different objects.
3. **A separating statistic is not a finding until you read what the feature measures** —
   its published max-activating examples, activating and promoted tokens, and frequency.
   §F35: feature 6225 split 4/4 cheats from 0/120 at permutation p < 1/5001 and was a
   6.2%-frequency generic component firing on function words across unrelated text. **That
   reading is a gate, not a verification:** an interpretation you reached yourself is a
   single-agent autolabel and stays flagged until independently checked (§F38).
4. **Match the unit set before comparing arms; never compare raw file counts.** §F37: base
   vs steered looked like 2 vs 7 on raw files; on the 50 tasks present in both arms it is
   2/136 vs 3/138, p = 0.49. The effect did not survive matching — though it is still
   +0.70pp and underpowered, not zero.
5. **`(sid, seed)` is not a reproducible draw under llama.cpp, so do not pair on it.** Same
   sid, seed and server process gave different text in 62 of 86 cells (§F37 point 2 as
   corrected). Paired tests like McNemar are therefore wrong here — use an unpaired,
   sid-clustered permutation test. A design that needs pairing must demonstrate
   byte-identity on a pilot first.
6. **Read blind human-labelling materials before handing them over.** Spot-read a random
   sample of the *rendered* items and check an item cannot contain its own answer. The
   2026-09-08 packet was shipping `<think>` traces, which taxonomy v2 scores as NOT
   disclosure — so items we label `concealed_cheat` held a statement a rater would
   correctly read as disclosure, manufacturing disagreement rather than measuring it.
   Strip reasoning with `visible_part()`; excerpt long items head-AND-tail, never
   head-only, since the caveat usually lands in a closing paragraph (§F38).

---

## ⛔ A guard must check the thing it claims to check

**The rule.** When you write or trust a guard, verify it fires on the negative case:
construct the failure it is supposed to catch and confirm it refuses. A guard never seen
to say no is not evidence of anything. Applies equally to "the run completed", "the job
stopped", and "the reservation is held" — the same family as the 2026-09-06 spend
incident, a success signal not tied to a verified outcome.

Four that looked like they enforced a rule and did not, all found by auditing what ran:

1. **`disclosed` labelling.** `FLAG_PATTERNS` (including bare `impossible`) matched against
   the whole response, including task docstrings the model copies verbatim. 8 of 13
   `disclosed` labels project-wide were false (§F18). The rule was in this file, never in
   the code.
2. **GPU reservation guards.** `gpusched status | grep -qi "<tag>"` matches a reservation
   on *any* GPU; on 2026-09-06 a GPU-1 reservation authorised a job that ran ~7.5h on
   GPU 0, overlapping someone else's window. Now `tools/require_reservation.sh <tag> <gpu>`.
3. **`run_gpu0_queue.sh`.** Ignored `gpusched reserve`'s exit status, so a refusal read as
   a grant: two of three steps never ran and it still printed "QUEUE COMPLETE". Its
   `release` lines also parsed an id format gpusched never emits.
4. **The intervention itself, not just process state (2026-09-08).** The first three guard
   process state; this one guards the treatment. `llama-server` logs `failed to load
   control vector file` and then **serves anyway**, so an unsteered server would have
   answered as the steered arm and manufactured a clean null. It fired for real on first
   launch. `sae-causal/serve_steered.sh` greps the log and kills the server. Then check the
   treatment end to end — same prompt, temp 0, fixed seed, steered output must differ —
   **with its own same-condition control**: two temp-0 unsteered runs must be byte-identical
   first, or "they differ" proves nothing, given §F37's within-process non-determinism
   (measured at temp 0.8; greedy untested).

**Corollary for commits.** `git add -A` here is not safe: on 2026-09-07 it swept a 1.9 GB
stray log and ten growing snapshots of a 30 MB run log into a commit, which had to be
purged from 15 unpushed commits with `filter-branch`. Stage deliberately. Before pushing,
check what is in the range (`git rev-list --objects @{u}..HEAD` filtered to blobs over
~5 MB) and check for secrets; at minimum read `git diff --stat` — 841 files and 3.7M
insertions for a day of doc edits was the tell.

**Corollary for counts.** `prepare_dataset.py` once appended rows with no sid uniqueness,
so re-running into an existing logdir double-counted. Check `unique(sid)`, not `len(rows)`,
before citing any N. (**Figure corrected 2026-09-08:** this file cited "166 rows for 124
real samples, §F19"; §F22 withdrew that. The real numbers are **156 distinct generations
across 124 (split, task) cells**, of which only 124 have valid activations because wave-2
overwrote wave-1's files.)

**But do not blanket-dedupe by sid — decide the unit first.** sids collide by construction
(`{split}_{task_id}_e{epoch}` repeats across waves), and of 42 collisions §F22 found only
10 true copies: **32 were genuinely distinct generations**, so collapsing them discards 32
real samples. That is the destructive-fix-that-looks-correct pattern this section exists
to catch.
- **Behavioural counts** must NOT dedupe. Compare `final_text`, keep distinct generations,
  report collisions loudly as real samples that cannot be kept.
- **Activation-backed analyses** MUST dedupe: `acts/` and `tokens/` are keyed by sid and
  later writes overwrite, so two rows share one `.bin` and loading both double-counts
  (`probe_fit.py`, `sae_encode.py`).
- **Any loop generating work per row** must dedupe by sid first and update its `done` set
  as it writes, not only at startup.

**Use `concealment-probe/tools/corpus.py` rather than re-deriving this (§F41).** It takes
the unit as a required argument (`row` / `generation` / `activation` / `solution` / `task`),
so the corpus cannot be loaded without declaring what is being counted, and
`denominators()` reports every unit at once. Validated against §F22's hand-derived
figures. Run it directly on a `samples.jsonl` for a one-line summary before quoting any N. `run_resample.py` did neither and produced 50
  duplicate cells inside one run, silently breaking a paired design (§F37).

---

## Data permanence & file storage

- **⛔ Capture activations on EVERY inference run, at run time, wherever the model is
  served locally.** The target behaviours are rare and expensive: concealment/hardcoding
  runs at ~1.5% per generation, and a usable positive class took 940 generations to reach
  3 task groups. **Re-running does not recover a lost sample**: the same sid and seed does
  not reproduce the same text under llama.cpp (§F37), so the specific generation is gone.
  The saving grace both times it has bitten (§F39/§F40, and the bystander arms) was that
  the raw TEXT was persisted, so streams could be rebuilt after the fact at the cost of an
  extra GPU pass. So the rule has two halves: **never discard generated text**, and capture
  activations at run time so the second pass is unnecessary. Every harness that generates
  text writes token streams plus an `extract_resid` manifest as it goes (`--tokens-dir` in `sae-causal/run_resample.py`,
  `bystander/capture_activations.py`), so the SAE/NLA/probe arm and any later publication
  can use them without re-running anything.
- **Code, docs, small results, small raw run logs → git** (root `run_*.log` convention).
- **Datasets (transcripts, tokens, activations, audit sidecars) → Hugging Face** under the
  private **`DarkStarDeleeuw`** account, never the public `Solshine`; every publish script
  hard-asserts the identity. URLs in MANIFEST.
- **Raw eval transcripts, activation `.bin`, HF staging dirs → local-only, gitignored.**
  The staging dirs ARE the published content; one home, not two.
- **Data that must survive this machine has to actually get published.** Committed-locally
  is not backed up, and "regeneratable from scripts" does not satisfy permanence — a run is
  tied to weights, quantisation and hardware state. Every cited number traces to a
  persisted file (`visualizations/out/verification_table.csv` enforces this chart-side).
- Every completed eval run gets its audited samples record and a MANIFEST/audit-doc entry
  before the session ends, or an explicit loose-end flag where it will be noticed.

---

## Publishing & communication

- **Google Doc course research log: never add entries proactively** (Caleb, 2026-09-04) —
  only on explicit request. Detailed notes go in `research/`.
- HF dataset cards are outsider-readable; corrections to published cards are dated notes on
  the card, never silent replacements.
- Git: `SolshineCode` identity, direct commits to `main`, small focused commits whose
  messages name what was found or corrected.
- API keys live in env only, never in a committed file (`.env`, `*.env`, `**/secrets/`
  gitignored as a standing safeguard).

---

*Keep this file tight: additions replace or consolidate, they do not accrete. Detailed
history lives in the canonical docs at the top.*
