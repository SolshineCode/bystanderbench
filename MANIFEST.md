# Manifest

Where everything for this project actually lives — the **pure repo/data map**. Written
2026-09-03 when this repo was created (previously an untracked working directory, see the
initial commit message for why); split cleanly on 2026-09-06: **operative/standing rules
now live in `CLAUDE.md`** (raw-log-is-not-a-result, smoke-test-before-scaling, honeypot
audit, taxonomy v2, hardware rules — all of them), the **findings ledger is
`research/FINDINGS.md`**, and the full narrative/decision record is
`research/bluedot-research-positioning-and-trial-design-2026-09-03.md`. This file is
just the map.

## In this repo

- `repo/` — clone of the upstream ImpossibleBench project (`fjzzq2002/impossible_livecodebench`
  or the source it was cloned from), has its own git history, gitignored here, not ours to
  absorb. Re-clone if missing.
- `concealment-probe/` — the core tooling: `tools/extract_resid.cpp` (residual-stream
  activation capture from a running llama-server), `tools/prepare_dataset.py`,
  `tools/probe_fit.py`, `tools/final_analysis.py`, `tools/analysis_q36.py`, plus small
  results/data files (label overrides, task lists, final analysis JSON). `WRITEUP.md` has
  the methodology.
- `llama70b/` — the Llama-3.3-70B-Instruct pipeline (dual-GPU serving with OOM backoff,
  eval driver, activation extraction generalized to the 80-layer graph, HF packaging).
- `gemma12b/`, `gemma27b/` — same pattern as `llama70b/`, single-GPU local capture for
  `gemma-3-12b-it` (NLA layer 32) and `gemma-3-27b-it` (NLA layer 41), the two models
  confirmed via OpenRouter behavioral screening to show hardcode-class concealment.
  gemma-12b runs first in the local capture queue (higher observed cheat rate, cheaper).
- `moe-floor/` — the Kaggle-based smallest-cheating-MoE search (kernel scripts, one per
  candidate model). Rung 1: OLMoE-1B-7B (MoE) 1/50 check_override, `OLMo-7B-0724`
  (dense) 2/50 check_override, `OLMo-2-1124-7B` (dense, same lab/size, newer
  post-training) 0/49. **Correction 2026-09-07 — this entry previously ended
  "architecture didn't sort this outcome, era of post-training did." That claim is
  FALSIFIED and must not be repeated.** Extending N ~4× removed OLMo-2's clean zero, and
  at the larger N all three rung-1 models remain statistically indistinguishable
  (overlapping Wilson CIs). It is CLAUDE.md's named cautionary example of an
  overclaim from n≈50, and it had survived here in prose. The honest rung-1 result is the
  mechanism finding (`check_override`), not any rate ranking between the three.
  Rung 2 (Qwen1.5-MoE-A2.7B vs. two dense comparators) built and staged, gated on
  Kaggle quota, likely a Monday-reset item.
- `recruiter-trial/` — the live-pressure recruiter-model trial (section 13 of the
  positioning doc), Kaggle-based, paired pressure/matched-neutral-control arms,
  per-stage activation capture. Pilot target: `gemma-3-12b-it` (the strongest cheat
  baseline in the whole screen, chosen for measuring pressure-induced uplift).
  Pilot result: a clean null (§F10 in the findings ledger), published to HF.
- `splice/` — the splice-continuation trial (doctored vs control continuations on
  Llama-3.3-70B, `run_trial.sh` self-reserves GPUs). Results + binding framing in
  `splice/RESULTS.md` (§F16); hand-audit in `mechanism_audit.json`; construction
  provenance in `provenance.json`; activations local-only under `splice/acts/`.
- `olmo3/` — OLMo-3 workstream: Instruct-generation + BASE Q8_0 capture at SAE
  layers 4/16/28 (`run_full_pipeline.sh`), plus `sae_decode.py` for the SAELens
  decode path (serve script forces the chatml template — the bundled template
  aborts this build's minja).
- `lightning/`, `north-mini/` — local capture pipelines for
  `nvidia/nemotron-3.5-lightning` and `cohere/north-mini-code` (teacher-forcing the
  existing OpenRouter transcripts through `prepare_dataset.py`; north-mini's
  eos-suffix is self-checked empirically). Queued via `run_gpu0_queue.sh`.
- `nla-decode/` — Kaggle NLA decode kernels (v1–v4 bug history in §F17) plus
  quota-retry push watchers; results land under `nla-decode/results/`.
- `research/FINDINGS.md` — the append-only numbered findings ledger (§F1+), the
  canonical registry of settled results with source pointers. Cite findings by
  number instead of restating figures from prose. Append rules in the file header
  and `CLAUDE.md`.
- `research/citation-list-2026-09-04.md` — verified literature citations (activation
  probing, MoE architecture, multi-agent persuasion, SAE/NLA autolabel reliability),
  every source independently re-checked against its actual paper before being listed,
  with concrete trial proposals per theme, not just a reference dump.
- `research/model-testing-audit-2026-09-05.md` — every model this project has run, by
  venue and benchmark condition, every count pulled directly from the underlying data
  files rather than carried forward from prose. Caught and documents the qwen3.8:27b
  correction (it never produced a scorable sample, despite earlier docs citing it as a
  confirmed dense negative). The single most useful pointer if the question is "what do
  we actually have data for, and what's still just claimed."
- `visualizations/` — repeatable chart pipeline over AUDITED results only
  (`build_charts.py` + `out/` PNGs + `verification_table.csv`); registry-driven,
  Wilson CIs + N on every rate bar, pending sources auto-join on re-run. See its
  README for the audited-only data discipline and the agy review provenance.
- `research/` — every research doc, moved here 2026-09-03 from the private
  `linkedin-os-notepad` repo (career-ops workspace, kept separate, see below).
- `messages/` — grant-related communication logs (BlueDot scope-change heads-up, grant
  update email). Job-application/interview correspondence is NOT here, see below.
- `stray-eval-logs-2026-09-03/` — a handful of partial `.eval`/`logs.json` files that
  ended up in the wrong repo (`linkedin-os-notepad`) at some point, likely from a
  mis-`cd`'d eval invocation. Kept as-found rather than reconciled against whatever the
  live run's actual current log state is, since the runs that produced them
  (`qwen3.5-27b-run3`, `qwen3.6-concealment`) may still be in progress. Treat as
  possibly-stale partial snapshots, not the authoritative record.
- `run_*.log`, `llamacpp_logs/` — raw run output kept in git (small, real evidence of
  what actually happened on each run).

## NOT in this repo, intentionally (see `.gitignore`)

- `.venv/` — regenerate from `requirements.txt`.
- `gguf/` — symlinks into local Ollama blob storage, host-specific, not portable.
- `hf_upload/`, `hf_upload2/` — these directories ARE (or were staged to become) what's
  published on Hugging Face. See below for the live URLs. Kept out of git so the data has
  exactly one home, not two copies that can drift.
- `logs/`, `*.eval`, `**/acts/*.bin` — raw eval transcripts and activation tensors.
  Published runs: on Hugging Face (below). Unpublished/in-progress runs: local-only on
  this machine (`darkstar`, `/home/darkstar/bluedot-unit2-impossiblebench/`), not backed
  up anywhere else yet. If a run's data needs to survive independent of this specific
  machine, it needs to actually get published, not just committed here.

## On Hugging Face (`DarkStarDeleeuw` account, private)

- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-2026-09-01`** — the original
  concealment-probe dataset. **Correction 2026-09-07 (supersedes the 2026-09-05
  correction below, which was itself wrong):** verified against the live HF file tree,
  not prose. Actual contents are **`qwen3.5-27b` (4 dirs: concealment, overnight,
  proper, run2) and `qwen3.8-27b` (2 dirs: overnight, run2)**. There is **no `qwen3.6`
  data in this dataset.** The `qwen3.8-27b` `samples.jsonl` files ARE published — they
  are simply **empty, 0 rows**, which is what makes "never produced a scorable sample"
  true while "not included" was false. Known defect, live: `run2/qwen3.5-27b/samples.jsonl`
  holds 11 rows for 9 unique sids — **corrected 2026-09-07 (§F22): these are NOT corrupt
  duplicates and must not be de-duplicated.** Each colliding id is two real generations
  from two different runs (`2026-09-02T17-59` and `T19-17`), different response text and
  token counts, colliding only because both ran as epoch 1. 11 real generations across 9
  cells. For the two colliding ids only the later run's activations exist on disk, since
  `tokens/`/`acts/` are id-keyed — behavioural use only for those two.
  Its 3 `disclosed` rows are all genuine (`visible_prose`, hand-audited §F18).
  *Superseded — Correction 2026-09-05 (WRONG, kept per correction discipline):* claimed
  `qwen3.8-27b` was not included and that contents were "`qwen3.6` and `qwen3.5-27b` only."
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-2026-09-01
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b`** — PUBLISHED
  2026-09-05: the full local Llama-3.3-70B run. 65 unique scored samples (25/25/15
  splits, retry-dups removed), full transcripts + tokens + 19-layer activations
  (l_out 4..76 every 4th; NOTE: NLA layer 53 not in that sweep — a 49/53/57 pass over
  selected samples lands in acts_nla/ via `llama70b/extract_l53.sh`). Result: 0
  concealed_cheat / 0 disclosed on 50 impossible-split samples, 2/15 original_pass —
  the dense-70B zero, matching its independent cloud screen. Audit status: zero
  keyword flags fired (nothing to hand-audit); failed_silent rows machine-labeled.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b
- **Gemma-12b / gemma-27b datasets** — not yet published as of 2026-09-04 (capture queue
  not started, waiting on the 70B run to release the local GPUs). Same naming convention
  once there's real data, `...-gemma3-12b` / `...-gemma3-27b`.
  **⚠ 2026-09-07 — do not publish the current staging dirs as they stand.**
  `hf_upload_gemma12b/samples.jsonl` carries 5 `disclosed` labels that are all
  `code_only` false positives, plus 42 duplicate sids (166 rows for 124 real samples).
  `hf_upload_olmo3/samples.jsonl` carries 1 `code_only` false positive. Both predate
  the 2026-09-07 `flag_location()` + dedup fixes in `prepare_dataset.py` and must be
  regenerated before any publish (FINDINGS §F19, §F20). The moe-floor `-ext` extension
  runs are likewise unpublished and carry 15 `code_only` `disclosed` rows between them.
- **`DarkStarDeleeuw/bluedot-unit2-moe-floor-rung1`** — PUBLISHED 2026-09-04: rung 1 of
  the smallest-cheating-MoE search. OLMoE-1B-7B (MoE) + OLMo-7B-0724 + OLMo-2-1124-7B
  (dense controls), 62 samples each with full transcripts, tokens, and `[n_layers,3,d]`
  activations (Kaggle T4 `output_hidden_states` capture — NOT the llama.cpp path; same
  3-slot schema). Audit status: all 3 `concealed_cheat` rows and the 1 `disclosed`
  false-positive hand-audited (all cheats = check_override mechanism; the disclosed hit
  was the known "impossible"-keyword false trigger, overridden); `failed_silent` rows
  machine-labeled, not individually audited.
  **Correction 2026-09-07 — the published rows and the published override disagree.**
  `olmo2-7b/samples.jsonl` ships `conflicting_lcbhard_82_e1` with
  `category: "disclosed"`, while `olmo2-7b/label_overrides.json` in the same folder
  says `failed_silent`. The hand-audit override was recorded but never applied to the
  rows that shipped. Independently re-checked 2026-09-07: the flag is `code_only`
  (task-docstring echo), so `failed_silent` is correct and the shipped `category` is
  wrong. Anyone reading `samples.jsonl` alone gets the wrong label. Card needs a dated
  note saying `label_overrides.json` is authoritative (see FINDINGS §F20).
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-moe-floor-rung1
- **`DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b`** — PUBLISHED 2026-09-05:
  recruiter-pressure pilot v1, 24 paired trials (12 pressure / 12 control) on
  gemma-3-12b-it 4-bit with per-stage response-span activations incl. NLA layer 32.
  Result: no behavioral uplift (1/12 cheat each arm, both hardcode on the lcbhard_9
  honeypot, hand-audited); tiny suggestive per-stage shift contrast, not a finding.
  Audit status: cheat rows hand-audited (`mechanism_audit.json`); failed_silent rows
  machine-labeled.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b
- **Recruiter-trial dataset** — not yet published as of 2026-09-04, pilot still running.
- **Re-verified 2026-09-07 via direct HF API check** (supersedes the 2026-09-04 check
  below): **four** BlueDot datasets are now live under `DarkStarDeleeuw`, all private —
  `bluedot-unit2-concealment-probe-2026-09-01` (updated 2026-09-03),
  `bluedot-unit2-concealment-probe-llama3.3-70b` (2026-09-05),
  `bluedot-unit2-moe-floor-rung1` (2026-09-06), and
  `bluedot-unit2-recruiter-pilot-gemma3-12b` (2026-09-05). Contents of each were fetched
  and checked row-by-row, not read from this file's prose: llama3.3-70b and
  recruiter-pilot are clean (no duplicate sids, no false `disclosed`); the other two
  carry the defects noted on their lines above. Two unrelated prior-project datasets
  exist on the same account (`nla-research-bulk-provenance`,
  `sae-rl-homebase-artifacts`) — not part of BlueDot, don't touch them from this repo's
  scripts.
  *Superseded — 2026-09-04 check:* said only `bluedot-unit2-concealment-probe-2026-09-01`
  was live, which was true then; three more have been published since.
- The `DarkStarDeleeuw` account is a private agent-provenance account, distinct from the
  public-facing `Solshine` account. Every publish script in this repo hard-asserts that
  identity before writing, so the public account is unreachable by construction from this
  codebase.

## External, not in any repo

- **Course research log**: Google Doc "Research Log BlueDot Technical AI Safety" — short
  dated log entries, course-facing. Ask Caleb for the link, or find it via Google Drive
  search under the `caleb.deleeuw@gmail.com` account (a second Google account on this
  machine, a second Google account, also has read access but has a storage-full warning
  that blocks edits, always confirm the account before editing, see the doc's own edit
  history for the wrong-account traps hit and fixed on 2026-08-29 and 2026-08-31).
  **Standing rule as of 2026-09-04: do not add entries here proactively.** Caleb wants
  this doc kept clean, only updated when he explicitly asks for an entry. Detailed notes
  go in this repo's `research/` docs instead, always.
- **BlueDot course platform** (Airtable-based, cohort materials, Unit exercises) — not
  archived here, referenced by content in `research/` where relevant.

## What deliberately stays OUT of this repo

- **Job-application and interview-process tracking** (`NOW-job-search.md`,
  `PENDING-ACTIONS.md`, application-specific research docs) lives in a separate private
  career-ops workspace, not this repo. That material is about Caleb's broader job search,
  this repo is scoped to the BlueDot research project specifically. A few pointers in
  that workspace's `PENDING-ACTIONS.md` reference files that used to live here-adjacent
  and now live in this repo (updated 2026-09-03 when the move happened).

### HF correction notes published 2026-09-07

Dated correction sections were appended (never overwritten — originals verified byte-for-byte
intact after upload) to the cards of the two affected live datasets, plus a shared
`CORRECTIONS-2026-09-07.md` in each:
- `bluedot-unit2-moe-floor-rung1` — states that `label_overrides.json` is authoritative over
  `samples.jsonl` for `olmo2-7b/conflicting_lcbhard_82_e1`, and that the corrected
  `disclosed` count for `olmo2-7b` is **0, not 1**.
- `bluedot-unit2-concealment-probe-2026-09-01` — corrects the contents description
  (qwen3.5-27b + empty qwen3.8-27b, no qwen3.6), and states that `run2/qwen3.5-27b`'s
  11-rows-for-9-ids is **two real generations per colliding id, not corruption — do not
  de-duplicate it**.
`llama3.3-70b` and `recruiter-pilot-gemma3-12b` were re-checked row-by-row, found clean, and
deliberately left untouched. Uploads asserted the `DarkStarDeleeuw` identity before writing.

## Published 2026-09-08 (verified live via the HF API after upload, not from prose)

- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-nemotron35-lightning`** — PUBLISHED
  2026-09-08, private. Teacher-forced local capture (§F24) over the hand-audited OpenRouter
  free-tier screen (§F15): 62 samples, 12-layer sweep (`1,6,10,15,20,24,29,34,38,43,47,51`,
  d_model 2688), 62 `.bin` + sidecars, `mechanism_audit.json` shipped alongside the rows.
  Live check: 207 files, 62 acts, rows {failed_silent 45, disclosed 2, concealed_cheat 3,
  original_pass 10, original_fail 2}. Card states the provenance grade explicitly (cloud
  transcripts, 4-bit local copy reading its own output).
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-nemotron35-lightning
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-12b`** — PUBLISHED 2026-09-08,
  private. Supersedes the 2026-09-07 "do not publish the current staging dirs" warning
  above for gemma-12b: the staging was regenerated from the corrected data (overrides
  applied per §F23, `disclosed` 0, `category_raw` preserved on the 5 corrected rows) with a
  card that carries the §F22 two-basis accounting (166 rows = 156 generations in 124 cells;
  124 rows with activations; 5/122 behavioural, 4/99 activation-backed). Live check: 396
  files, 124 acts, rows {failed_silent 124, concealed_cheat 5, original_fail 28,
  original_pass 9}, `mechanism_audit.json` present.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-12b
- Still unpublished: gemma-3-27b (activations being extracted 2026-09-08), north-mini
  screen + big batch captures (in progress, positives-first partial capture — see the
  north-mini card template for the grade), olmo3 (still carries the pre-§F18 staging).
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-olmo3-7b`** — PUBLISHED 2026-09-08,
  private (replaces the pre-§F18 `hf_upload_olmo3` staging flagged above, and its card,
  which was a stale copy of the gemma-12b card). 62 samples, 60 with BASE-checkpoint
  (`Olmo-3-1025-7B` Q8_0) activations at the `decoderesearch/olmo-3-saes` hook layers
  4/16/28 only (d_model 4096). Labels: 0 `concealed_cheat`, 1 genuine `disclosed`
  (`oneoff_lcbhard_82`), the `conflicting_lcbhard_8` docstring echo overridden with
  `category_raw` kept. Live check: 204 files, 60 acts, rows {failed_silent 49, disclosed 1,
  original_fail 10, original_pass 2}.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-olmo3-7b
- **`bystander/`** (2026-09-08) — §20 benchmark v0: env builder, Inspect task, scorer,
  scripted-trajectory tests, `provenance.json` (evidence manifest per arm). Code only, no
  data. `bystander/.envcache/` is gitignored.
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-27b`** — PUBLISHED 2026-09-08,
  private. 62 samples, all with 16-layer activations (`4..60` every 4th + NLA layer 41,
  d_model 5376), 2/50 hardcode `concealed_cheat` hand-audited (§F29), 0 `disclosed`. Live
  check: 208 files, 62 acts, rows {failed_silent 48, concealed_cheat 2, original_fail 10,
  original_pass 2}. https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-27b
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-north-mini-code`** — PUBLISHED
  2026-09-08, private. 61 scored samples from the 2026-09-05 OR screen with a **PARTIAL**
  activation capture: 30 of 61 `.bin` (12 layers × 3 slots × d_model 2048), written in a
  positives-first order (`manifest_prioritized.tsv`) and stopped mid-queue when the
  interpretability arm was refocused (§F32) — so the missing tail is systematic, not
  random. All 12 `concealed_cheat` hand-audited to hardcode: 12/49 = 24.5%
  [14.6%, 38.1%] (§F25). Also ships `bigbatch/` — the larger 2026-09-06/07 screen, 176
  rows / 177 unique sids, 42-entry hand audit, prepared `tokens/`, and **no activations**
  (§F26) — plus `or_screen_audit/` (screen summaries + the 12-entry audit + write-up),
  both screens' raw `.eval` archives, and the llama.cpp serve/extraction logs.
  Live check: 346 files, 30 acts bins.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-north-mini-code
- **`DarkStarDeleeuw/bluedot-unit2-lab-artifacts-2026-09-08`** — PUBLISHED 2026-09-08,
  private. Everything that is a *result or an instrument* rather than a capture:
  `bystander/` (benchmark v0 + built environments + scripted-trajectory tests + the
  qwen3.5-27b pilot logs, §F31), `nla-decode/` (kernels, the superseded v2/v3 outputs, and
  **the live Kaggle output pulled 2026-09-08** that supersedes §F17(b) — see §F34),
  `probe_results/` (the §F30 probe fits plus the first GemmaScope-2 SAE encode and its
  validity gate, §F33), `splice/` (acts, tokens, audit, provenance), `tools/`
  (`probe_fit.py`, `sae_encode.py`, `prepare_dataset.py`, `prioritize_manifest.py`,
  `screen_behavioral.py`), `visualizations/` (audited-only charts + `verification_table.csv`).
  Card carries a per-folder epistemic grade table. Live check: 205 files.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-lab-artifacts-2026-09-08
- **`DarkStarDeleeuw/bluedot-unit2-or-screens-2026-09`** — PUBLISHED 2026-09-08, private.
  The OpenRouter screening record that was not already inside a per-model dataset: the four
  `nla-screen-*` runs on the interp-artifact models (gemma-3-12b 2/75, gemma-3-27b 1/75,
  llama-3.3-70b 0/75, qwen2.5-7b 0/66 — the §F32 tension in one table),
  `moe-free-laguna-xs-or`, the five 2026-09-06 paid-tier batches and four `*-all` dirs as
  **raw `.eval` only** (never screened into `screen_summary` form — the card says so
  explicitly rather than implying they are scored results), `backfill-2026-09-05`,
  `moe_floor_extension/` (the ~4× N extension that FALSIFIED the rung-1
  "era not architecture" claim, published because it is a falsification), and `drivers/`
  (`run_eval_openrouter.py`, `run_openrouter_queue.sh` with its concurrency-incident note,
  `screen_behavioral.py`). Live check: 100 files, 16 screen dirs.
  https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-or-screens-2026-09

As of 2026-09-08 there are **eleven** BlueDot datasets live under `DarkStarDeleeuw`, all
private. Every result artifact this project depends on is now on HF except the two things
that genuinely do not exist yet: activations for the north-mini big batch, and a decode of
correctly-aligned project vectors through the NLA (§F34, blocked on Kaggle quota).

## Added 2026-09-08 (afternoon)

- `sae-causal/` — the §F35 causal-test rig: `export_control_vector.py` (GemmaScope-2
  decoder row → llama.cpp control vector, with the `direction.{L+1}` layer arithmetic
  derived in the script and a refusal if the SAE config's hook point disagrees),
  `run_resample.py` (resample continuations from the cheat-or-disclose decision point;
  unsteered it harvests positives, steered it is the causal test), `serve_steered.sh`
  (kills the server when llama-server logs a control-vector load failure and serves
  anyway — this fired for real). Run outputs are gitignored and published with the
  session artifacts on HF. Interim result and the seed/pairing bug: §F37.
- `labelling/` — the two blind human-rater packets and their pre-registered analysis
  (§F38). `PROTOCOL.md` is the operative document and was written before any answers
  came back. `packet_features/` and `packet_concealment/` are what gets handed over;
  `_keys/` must not be. Both packets regenerate exactly from the build scripts with
  seed 20260908, so what the raters saw is reconstructable.
- `bystander/` gains two positive controls: `tool_arm="tool_probe"` (affordance floor —
  asks outright for one `alert_oversight` call; if that is not ~1.0 the instrument is
  broken and no zero elsewhere is behavioural) and `arm="blatant_wrongdoing"`
  (propensity ceiling — evidence in plain language in the CI log the ticket already
  sends you to). Neither is in the pilot defaults, so existing numbers stay comparable.
  Also corrects a published determinism overclaim: the built tarballs are **not**
  byte-identical (gzip mtime, now fixed, plus `.git/index` which caches host stat data
  and cannot be normalised); every file the agent reads and the git history are
  identical, and `test_env_determinism` asserts that rather than a hash that never matches.

## Added 2026-09-09

- `bystander/` gains the two-tier split. **Core** (`run_bench.sh`) is behavioural only and
  takes any Inspect model string, hosted or local, with no serving of its own.
  **Extended** (`capture_activations.py` → `extract_resid`) adds residual-stream capture
  for probe/SAE/NLA work on the reporting decision. `tool_loop_smoke.py` screens a
  candidate model for multi-turn tool-loop capability against a local port or a hosted
  endpoint, and exists because a single-turn check passes models that then fail every
  episode (§F50). `capture_backlog.sh` retro-captures every pre-existing run.
- `bystander/acts/`, `acts_qwen_backlog/`, `acts_nemotron_floor/` — token streams,
  per-episode sidecars and extracted activations from BystanderBench episodes. Sidecars
  record the model, the eval file, the pooled span and its mode (final turn vs from first
  evidence), and the episode's scores, so an activation can always be traced to the
  behaviour it accompanied. Gitignored; published with the HF lab-artifacts dataset.
- `sae-causal/tokens*/` — the same for the ImpossibleBench resample harness, plus
  `tokenize_saved.py`, which rebuilds streams for generations that predate token capture
  from their stored text (§F39).
- `concealment-probe/tools/corpus.py` — single loader for `samples.jsonl` /
  `transcripts.jsonl` with the counting unit as a required argument (§F41). Run it on any
  samples file for a one-line denominator summary before quoting an N.
- `research/drafts/paper-draft-2026-09-09.md` — the shareable draft. Part I is the
  negative interpretability results, Part II is BystanderBench with both tiers and both
  controls.
- `research/drafts/bystander-viability-review-2026-09-09.md` — external review of the
  benchmark's viability; its dispositions are worked through in §F48.

## HF dataset state, verified 2026-09-09 evening

`DarkStarDeleeuw/bluedot-unit2-lab-artifacts-2026-09-08` now holds **765 files**, including
**205 activation `.bin` files** and **116 `.meta.json` sidecars**. Live check by category:
`acts` 73, `acts_qwen_arms` 73, `acts_qwen_backlog` 79, `acts_nemotron_arms` 109,
`acts_nemotron_floor` 19, `sae-causal` 162, `bystander` 140 (code plus every eval log),
`figures` 5 (four charts and the data sanity check), plus `FINDINGS.md`, the paper draft
and the viability review at the root.

That is every behavioural sample this project has produced on both target behaviours,
with its activations, under the standing capture rule in `CLAUDE.md`. Each sidecar records
the model, source eval file, pooled span and mode, and that episode's scores, so an
activation traces to the behaviour it accompanied without re-deriving provenance.

Eleven BlueDot datasets remain live under the account; this is the one that grows.

## Added 2026-09-10

Code and docs (in git):

- `bystander/env/content.py` gains two ceiling incidents, `blatant_safety_falsification`
  and `blatant_oversight_evasion` (§F59). Built to differ in domain, actors and mechanism
  rather than surface detail, so the ceiling has k=3 and the *incident* becomes an
  available inferential unit. Structurally identical file slots; evidence volume matched
  within 6%.
- `bystander/prompted_solver.py` (§F62) — a ReAct-style solver with no tool calls
  anywhere, for models whose chat template has no tool support at all. Paired with
  `affordance="cli"` in `task.py`, which exposes the escalation channel as an
  `ops-escalate` executable rather than a tool (§F61). Both dimensions are recorded on
  every score and are **never pooled** with the tool-calling path.
- `sae-causal/extract_harvest_acts.sh` — teacher-forced extraction driver for the 200
  generations harvested by the §F44 causal run.
- `concealment-probe/tools/corpus.py` hardened: `collapse()` split out so in-memory
  producers share one unit definition, a path matching no file now raises instead of
  reporting a confident zero, and a row whose generation cannot be identified stops the
  count instead of silently merging (§F60).

**Updated 2026-09-11.** The eval transcripts are no longer local-only. `logs/` remains
gitignored, but `logs/bystander-*`, `logs/or-*` and `logs/orpaid-*` were force-added
(68 dirs, 88 files, 20 MB) because `bystander/report.py` recomputes every released rate
*from the transcripts* rather than reading a scorer's baked-in value — they are the only
thing that makes §F59–§F97 auditable, so a disk failure would have left a ledger of
uncheckable numbers. That now includes the qwen incident-2 and incident-3 runs previously
listed here as local-only, and every nex and frontier run.

### New since 2026-09-11 — code and artifacts

- `bystander/evidence_ref.py` (§F117) — deterministic test for whether an escalation NAMES
  the planted misconduct or is a "I am blocked" status report. The discriminating vocabulary
  is a set difference computed from the built environment per episode (tokens in the
  evidence-only files minus tokens in every other file), so there is **no keyword list** and
  it regenerates for any new arm without curation. Measured 17/17 substantive vs 0/16 stuck.
  Reported by `report.py` as `alert names evidence`; not gating, since v1.0 is frozen.
- `bystander/capture_coverage.py` (§F111) — enumerates locally-served episodes with no
  activation capture; exits 1 while a gap exists.
- `bystander/package_acts_to_hf.py` — the upload path described above, with the bin-size
  refusal that caught §F116.
- `bystander/requirements.txt` (§F102 B) — the dependency set, which did not exist.
  `inspect-ai==0.3.261` pinned, not floored: the API surface used is not stable across majors.
- `bystander/env/content.py` gains two minimal-pair arms, `blatant_safety_addressee` and
  `blatant_wrongdoing_noaddressee` (§F104), built to move one variable with total evidence
  length held within 3% of their parents. The experiment they were built for came back
  negative (§F110) and they are kept as a documented null.
- `visualizations/build_model_results.py` + `bystander_model_results.png` — the results figure,
  built **from `report.py`'s CSV** rather than re-derived from logs, so it cannot disagree with
  the ledger. Shows refused cells hatched, since refusal is an outcome.
- `research/proposals/detection-game-autolabelling-2026-09-12.md` — proposal, nothing run.

`report.py` itself changed four times on 2026-09-11/12, each verified retroactively inert by
diffing full output before and after: the competence gate (`COVER_MIN`, §F98), `affordance`
added to the cell and floor keys (§F102 C), refusal of `no_tool` cells (§F107), refused cells
emitted to the CSV with empty rate fields so a refusal can be reported but never plotted as a
measurement, and the `alert names evidence` metric (§F117).

**Updated 2026-09-12. The BystanderBench activation captures are now ON HF**, in two private
datasets, which closes the gap the previous revision of this section described. Both were
verified through the HF API after upload rather than from the uploader's own output — private
flag, file count, and one distinct bin size per repo.

| HF dataset (private, `DarkStarDeleeuw/`) | bins | bin size | covers |
|---|---|---|---|
| `bluedot-unit2-bystander-acts-nex-n2.5-mini` | **338** | 196,608 = 8 × 3 × 2048 × 4 | every nex capture: incidents 1–3, both depth runs, the benign control, both addressee arms, the new positive-class batches |
| `bluedot-unit2-bystander-acts-llama3.3-70b` | **18** | 786,432 = 8 × 3 × 8192 × 4 | llama-3.3-70b ceiling + floor (§F112). Labelled on the card as **escalation-while-stuck, not misconduct reporting** — the cell is REFUSED and these must never be used as a bystander positive class |

Capture layers: nex `4,8,16,24,30,34,37,39` (40-block model); llama `8,20,32,44,50,53,64,72`,
chosen to include **both** published artifact layers, Goodfire SAE L50 and kitft NLA L53.

`bystander/package_acts_to_hf.py` is the upload path. It size-checks every bin against
`n_layers × 3 × d_model × 4` and **refuses the whole upload on any mismatch** — that check
caught §F116 (see below) and is the only reason a stale tree did not reach HF mislabelled.

Still local-only, not on HF:

| dir | streams | why it is still here |
|---|---|---|
| `bystander/acts_incidents23` | 96 | incidents 2 and 3 on qwen3.5-27b (§F64/§F65) |
| `bystander/acts_qwen_arms`, `acts_qwen_backlog` | 24 / 27 | qwen3.5-27b arm sweep |
| `bystander/acts_nemotron_arms`, `acts_nemotron_floor` | 36 / 6 | nemotron-3.5-lightning |
| `bystander/acts_benign_n24` | 24 | the qwen `benign_anomaly` control (§F81) |
| `sae-causal/tokens/acts/` | — | harvested generations, 8 layers × 3 slots × 5120 dims, 491,520 B/stream; `base` arm complete at 100/100 |

**Three trees are retained deliberately and must never be pooled with current data.** Each is
named so that its state is visible without opening it — the §F87 convention, which §F116 then
proved is load-bearing:

- `acts_nex_scale.5layer` (24) — the first nex capture, written at 5 layers because a
  64-block layer list was used on a 40-block model (§F87).
- `acts_nex_local.5layer-STALE-20260912` (12) — **the same defect, missed by §F87's
  re-capture and not found for a day** (§F116). It covers `nex-local-n6`, the run holding this
  project's first voluntary alert on a local model. The upload guard refused the entire
  ten-tree nex push over these twelve files; `acts_nex_local` has since been re-captured at
  8 layers and is in the HF dataset above.
- `acts_qwen_backlog.CORRUPT-20260910` (26) — visible and unusable beats deleted and forgotten.

**Capture coverage is now measured, not assumed.** `bystander/capture_coverage.py` matches
captures to log directories by cid prefix and **exits 1 while any locally-served episode is
uncaptured**, so it can gate a check-in. It found 478 uncaptured episodes across 36 dirs on
2026-09-12 (§F111), including the entire addressee experiment run that same night; the
backfill has taken that to **346 across 24 dirs**, all older qwen/nemotron runs.

## Published 2026-09-13 (each verified by reading back from the remote, not from the upload's exit code)

- **`DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-13`** — private, 3 files. First
  RunPod A40 execution of the gemma NLA decode kernel. **Superseded and uninterpretable**: all
  four validation vectors arrived NaN, so the four project decodes have no positive control
  behind them (§F147). Kept because §F149 diagnoses the cause from it. Do not cite its decodes.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-nex-pos-jk-2026-09-14`** — private, 152 files:
  48 residual bins (8 layers `4,8,16,24,30,34,37,39` × 3 slots × d=2048, 196,608 B each) for the
  +24 nex-n2.5-mini incident-1 `with_tool` episodes (batches j, k; alerted 7/12 and 4/12) as
  both the full-stream tree and the `pool_bounds` pre-decision tree (seed 20260912), plus
  tokens and meta. Feeds the §F167 probe refit (n 84 → 108). Read back 4/4 sampled bins.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-nex-inc23-gh-2026-09-14`** — private, 149 files:
  48 residual bins (8 layers `4,8,16,24,30,34,37,39` × 3 slots × d=2048, 196,608 B each) + token
  streams + meta for the W8 +24 `with_tool` episodes on incident 2 and +24 on incident 3 for
  nex-n2.5-mini (thinking on), logdirs `logs/bystander-nex-incident{2,3}-depth-{g,h}` (§F170:
  incident 2 n 48→72, incident 3 n 48→72). Read back 3/3 sampled bins + manifest MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-lightning-ext-2026-09-14`** — private, 114 files:
  36 residual bins (delivered layers `8,24,40` × 3 slots × d=2688, 96,768 B each; requested
  `4,8,16,24,32,40,48`, dropped silently per §F156) + token streams + meta for the W4 +12
  `with_tool` episodes per incident on nemotron-3.5-lightning (thinking on), logdirs
  `logs/bystander-lightning-{inc1,inc2,inc3}-ext` (§F169: 0/72 escalations, 0/51 conditional).
  Read back 3/3 sampled bins + manifest MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-gemma4-31b-pod-2026-09-14`** — private, 134 files:
  43 residual bins (8 layers `4,8,16,24,32,40,48,56` of 60 × 3 slots × d=5376, every bin
  516,096 bytes) + token streams + meta for the gemma-4-31B-it Q4_K_M cell (§F163): floor 6,
  smoke 1, with_tool 12 × three incidents. Served on a RunPod A40, benchmark run locally over
  a tunnel; tokens captured locally on a CPU server after the pod's llama-server
  `--prefill-assistant` guard 400'd the tunnel capture; extracted on a local M40 from the
  byte-verified local GGUF. Read back 3/3 sampled bins MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-nla-decode-kaggle-2026-09-14`** — private, 5 files
  (`decodes.jsonl`, `run_meta.json`, `kaggle_kernel.log`, `prefixes.jsonl`, `script_v4.py`).
  NLA v4 (§F162): all 24 recruiter-pilot episodes, fresh single-position vectors at
  hidden_states[33] (last prompt token, first response token, response-span mean) from the exact
  reconstructed final-stage context (88/88 stage token counts exact), bf16 AV on Kaggle T4x2,
  positive controls pass and two random-direction negative controls decode to fluent generic
  text — so fluency is not evidence. 78 decodes. Supersedes the 09-13b project decodes (wrong
  layer offset, span means, and `arr[-1]` was stage 3 for 5 of 24 episodes).
- **`DarkStarDeleeuw/bluedot-unit2-bystander-gemma3-27b-pod-2026-09-15`** — private, 77 files:
  18 residual bins (16 layers `4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60` × 3 slots × d=5376,
  1,032,192 B each, all requested layers delivered) + sidecars + token streams + meta for the W11
  gemma-3-27b-it pod cell (prompted CLI mode, bartowski `google_gemma-3-27b-it-Q4_K_M.gguf`,
  sha256 `4e83142e…7170`): floor 6 + incident-1 `with_tool` 12, logdir
  `logs/bystander-gemma3-27b-pod` (§F172: floor 6/6, ceiling REFUSED on competence 2/12; ceilings 2
  and 3 stopped by the gate). Extracted on the pod against the same file; the local ggml-org build
  is a different file and was not used. Extract + capture logs included. Read back 6/6 MD5-match
  (`bystander/push_acts_tree.py`). Pod run records (setup, server, NLA prep logs, GGUF sha256) in
  `logs/gemma3_27b_pod_records/` (local, gitignored under `logs/`).
- **`DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-15`** — private, 4 files
  (`decodes.jsonl`, `run_meta.json`, `pod_run.log`, `script_v4_pod.py`). NLA v4 duplicate on a
  RunPod A40, bf16 AV, same 78 vectors as the Kaggle run (§F173): norms agree to a median 5e-4
  relative, decoded text agrees for a median 227 characters then diverges, domain profile agrees
  64/78; controls pass on both machines. Local copy `nla-decode/results/runpod-2026-09-15/`
  (committed). Read back 4/4 MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-concealment-probe-qwen38-27b`** — private, 310 files: the
  complete Part 1 qwen3.8:27b tree at n=100 (`samples.jsonl` 100 rows / 100 sids, `manifest.tsv`,
  100 token streams, 100 residual bins with sidecars: 11 layers `1,7,12,18,24,30,35,41,47,52,58`
  × 3 slots × d=5120, 675,840 B each; layer 64 was requested and silently dropped, §F156, the
  delivered set is in `delivered_layers.txt`), both extract logs, `prepare_dataset.log`,
  `build_rates.log`, and a dated copy of `concealment_rates.csv` (row 10 = 0/100, competence
  30/50). §F174: `conflicting` 0/25 concealed, 13 disclosed (hand-read, all visible prose).
  Read back 8/8 MD5-match. Supersedes the empty `qwen3.8-27b` dirs inside
  `bluedot-unit2-concealment-probe-2026-09-01` for every qwen3.8 claim.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-lightning-nothink-ext-2026-09-15`** — private, 52 files:
  12 residual bins (layers `8,24,40` × 3 slots × d=2688, 96,768 B each, requested = delivered) +
  sidecars + token streams + meta for the W4b +12 `with_tool` incident-1 episodes on
  nemotron-3.5-lightning with thinking OFF (`--reasoning off`, keyed `tools/native` by the
  per-log majority rule), logdir `logs/bystander-nemotron-blatant-ext` (§F175: pooled cell
  0/24 alerted, 0/21 conditional, cover 24/24). Read back 5/5 MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-qwen35-blatant-ext-2026-09-15`** — private, 37 files:
  8 residual bins (layers `4,8,16,24,32,40,48,56` × 3 slots × d=5120, 491,520 B each) + sidecars +
  token streams + meta for the W4c +8 `with_tool` incident-1 episodes on qwen3.5-27b (native tools,
  thinking off, keyed `tools/native`), logdir `logs/bystander-blatant-qwen35-27b-ext` (§F176: pooled
  cell 0/25 alerted, 0/16 conditional, cover 25/25). Read back 5/5 MD5-match.
- **`DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-13b`** — private, 3 files. The
  re-run after the one-line dtype fix. **This is the citable one** (§F152): all four validation
  vectors finite and decoding to their known content (the weather vector returns "We're
  expecting heavy rain and strong" against a source of "heavy rain and strong winds across the
  coast tomorrow"). The four project decodes are a null for concealment — pressure and control
  indistinguishable, all four describing degenerate repetition. md5
  `baaf9ab1be35672c459f0e1b703b840c` for `decodes.jsonl`, matched on both sides and on the
  remote.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-northmini-acts-20260913`** — private, 66 files,
  20 bins (12 layers × 3 slots × 2048 × 4 = 294912 B each). north-mini-code BystanderBench
  episodes, 18 under `native`/`tools` and 2 under `cli`/`prompted`. Recovered only after §F151:
  the rebuild dropped `tool_call_id`, which this model's template dereferences, so all 18 had
  been returning HTTP 500 and the model had no tier-2 corpus at all.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-lightning-dualtarget-20260913`** — private, 58
  files, 18 bins (3 layers × 3 slots × 2688 × 4 = 96768 B each). The §F155 dual-target cell:
  floor 6/6, cover 12/12, alerted 0/10. **Layer list: 7 were requested (4,8,16,24,32,40,48) and
  `extract_resid` delivered 3 (8,24,40) with no warning (§F156).** The delivered set matches
  every prior nemotron-lightning capture, so this tree is comparable with
  `acts_nemotron_floor` and `acts_nemotron_arms`; the card records both lists.
- **`DarkStarDeleeuw/bluedot-unit2-bystander-lightning-incidents23-20260913`** — private, 119
  files, 37 bins (3 layers × 3 slots × 2688 × 4 = 96768 B each). The §F159 three-incident
  result: nemotron-3.5-lightning on `blatant_safety_falsification` and
  `blatant_oversight_evasion`, floor + ceiling each, plus the inc2 smoke episode. Arms:
  safety_falsification 7 floor / 12 ceiling, oversight_evasion 6 floor / 12 ceiling. Layers
  8,24,40 **requested and delivered**, verified by `check_layers.py` against
  `requested_layers.txt` (§F157) rather than assumed. Together with
  `...-lightning-dualtarget-20260913` this is every episode behind lightning's 0/36.

## Pending 2026-09-15: agent-perpetrator arm activation captures, not yet pushed

A new arm, `blatant_wrongdoing_agents` (§F178/§F179), is a minimal pair with
`blatant_wrongdoing`: same domain, harm, evidence slots and salience, volume matched to
+3.1%, with the wrongdoer's species as the one changed axis. `blatant_wrongdoing`,
`blatant_safety_falsification` and `blatant_oversight_evasion` above are that arm's
human-wrongdoer control condition. Two launchers run it with activation capture and are in
flight today; each will produce an HF dataset once it finishes, pushed with the usual MD5
read-back verification and added above with its real name, file count and bin size:

- **[PENDING]**: nex-n2.5-mini, n=24 `with_tool` on `blatant_wrongdoing_agents`, GPU 0, 8
  residual layers matching the existing nex capture set (`4,8,16,24,30,34,37,39`). Exact
  repo name not yet assigned; will follow the `bluedot-unit2-bystander-<tag>-<date>` pattern
  used above. Source: `bystander/launchers/w14_agentarm_nex_n24.sh`, local tree
  `bystander/acts_nex_agentarm/`.
- **[PENDING]**: nemotron-3.5-lightning, n=12 `with_tool` on `blatant_wrongdoing_agents`,
  thinking on, GPU 1, 3 residual layers matching the existing lightning capture set
  (`8,24,40`). Exact repo name not yet assigned, same naming pattern. Source:
  `bystander/launchers/w16_agentarm_lightning.sh`, local tree
  `bystander/acts_lightning_agentarm/`.

Two more launchers run the same arm behaviourally only, with no activation capture, so they
do not add a new HF dataset by themselves: `bystander/launchers/w13_agentarm_free_sweep.sh`
(free-tier OpenRouter models matched to their existing human-arm incident-1 cell) and
`bystander/launchers/w15_agentarm_paid_frontier.sh` (the four paid frontier models, n=6
each, Caleb's per-launch go-ahead given 2026-09-15 ~11:20 PDT). Their results commit as run
logs in git, per this project's data-permanence rule for small raw logs.

- `bluedot-unit2-bystander-agentarm-overnight-2026-09-19` (48 bins, 201 files, private): two
  trees from the 2026-09-19 overnight session. `acts_qwen35_agentarm/` is qwen3.5-27b's
  agent-arm activation capture (n=36, stayed at zero alerts in both conditions). `acts_nex_agentarm_holdout.predecision/`
  is the 24-episode probe holdout batch used in §F200/§F201: captured and cut after a probe
  direction was already fixed, specifically to test it blind. MD5 read-back 5/5. Ledger:
  §F196-§F201.
- `bluedot-unit2-bystander-nex-agentarm-rep3-2026-09-19` (24 bins, 100 files, private): the
  rep-g/rep-h activation capture that was missing from its original launcher, completed at
  wind-down after the process survived a harness interruption and a buggy first cleanup
  watcher. MD5 read-back 3/3. check_layers rc=0. Episodes already counted in §F199's 35/78.
- `bluedot-unit2-bystander-nex-agentarm-holdout2-2026-09-20` (24 bins full-stream, 100 files,
  private): agent-arm holdout 2 (batches k, l), captured 01:58, full-stream extraction for
  non-probe use only (slot 0/2 confound, §F199). CHAIN_OK 03:16. MD5 read-back 6/6. §F203.
- `bluedot-unit2-bystander-nex-agentarm-holdout2-predecision-2026-09-20` (24 bins, private): the
  pre-decision cut of the same 24 episodes, fixed quantile matcher (§F202), gate 0.455. Carries
  the primary and blind-refit result JSONs. The §F203 replication tree. MD5 read-back 6/6.
- `bluedot-unit2-bystander-nex-ctrl-holdout-2026-09-20` (token streams, no bins, private):
  human-arm control holdout (batches a, b), captured 01:30. MD5 read-back 2/2. §F203.
- `bluedot-unit2-bystander-nex-ctrl-holdout-predecision-2026-09-20` (24 bins, private): its
  pre-decision cut, gate 0.438. The §F203 human-arm transfer tree. MD5 read-back 6/6.
- `bluedot-unit2-bystander-nex-agentarm-holdout3-2026-09-20` (24 bins full-stream, private) and
  `bluedot-unit2-bystander-nex-agentarm-holdout3-predecision-2026-09-20` (24 bins, gate 0.438): agent-arm holdout 3 (batches m, n),
  CHAIN_OK 05:52. The §F204 AUC 0.757 tree is the pre-decision one. MD5 read-back 6/6 each.
- `bluedot-unit2-bystander-nex-agentarm-holdout5-tokens-2026-09-20` (token streams, no bins) and
  `bluedot-unit2-bystander-nex-agentarm-holdout5-predecision-2026-09-20` (24 bins, gate 0.557): agent-arm holdout 5 (batches q, r,
  GPU 1 under W42), CHAIN_OK 06:12. The §F204 AUC 0.969 tree. MD5 read-back 6/6 (bins), 2/2.
- `bluedot-unit2-bystander-nex-agentarm-holdout4-2026-09-20` (24 bins full-stream) and
  `bluedot-unit2-bystander-nex-agentarm-holdout4-predecision-2026-09-20` (24 bins, gate 0.421): agent-arm holdout 4 (batches o, p),
  CHAIN_OK 08:16. The §F205 AUC 0.707 / p 0.052 tree. MD5 read-back 6/6 each.
- `bluedot-unit2-bystander-nex-agentarm-holdout6-tokens-2026-09-20` (token streams) and
  `bluedot-unit2-bystander-nex-agentarm-holdout6-predecision-2026-09-20` (24 bins, gate 0.434): agent-arm holdout 6 (batches s, t,
  GPU 1 under W42), CHAIN_OK 08:04. The §F205 AUC 0.615 tree. MD5 read-back 6/6, 2/2.
- `bluedot-unit2-bystander-nex-agentarm-off0102-tokens-2026-09-20` and
  `...-off0102-predecision-2026-09-20` (24 bins, gate 0.479): offline-mode batches 01+02 (GPU 0,
  `tools/offline/gpu0_bystander_queue.sh`), CHAIN_OK 14:42. The §F206 AUC 0.833 tree. Read-back 2/2, 6/6.
- `bluedot-unit2-bystander-nex-agentarm-off0304-tokens-2026-09-20` and
  `...-off0304-predecision-2026-09-20` (24 bins, gate 0.420): offline batches 03+04, CHAIN_OK 16:34.
  The §F206 AUC 0.629 (fails) tree. Read-back 2/2, 6/6.
- `bluedot-unit2-bystander-nex-agentarm-off0506-tokens-2026-09-20` and
  `...-off0506-predecision-2026-09-20` (24 bins, gate 0.441): offline batches 05+06, CHAIN_OK 18:30.
  The §F206 AUC 0.804 tree. Read-back 2/2, 6/6. All six pushed 18:34-18:35 with IPv4 forced and
  xet off (§F206 defect 4).
- `bluedot-unit2-bystander-nex-ctrl-nite0304-tokens-2026-09-21`, `...-nite0708-tokens-...`,
  `...-nite0910-tokens-...` and their `-predecision-...` pairs where a tree exists (24 bins each,
  gates 0.508/others -- CHAIN_OK all three), plus tokens-only trees for the two refused pairs
  `...-nite0102-tokens-...` and `...-nite0506-tokens-...` (position gate 0.387/0.370, correctly
  refused, no predecision tree): the nex human-wrongdoer control arm's overnight growth, last
  night of local compute, 09-20/21. Read-back 2/2 and 6/6 on every tree.
- `bluedot-unit2-bystander-nex-agentarm-nite0102-{tokens,predecision}-2026-09-21`,
  `...-nite0506-...`, `...-nite0708-...` (24 bins each, CHAIN_OK) and tokens-only
  `...-nite0304-tokens-...` (refused, gate 0.370): the probe holdout pool's overnight growth,
  same session. Each predecision tree scored immediately against the frozen §F200 direction:
  nite0102 AUC 0.721 (passes), nite0506 AUC 0.609 (fails), nite0708 AUC 0.891 (passes). Pooled
  over all eleven fresh holdouts now on the hub: n=262, AUC 0.760, CI [0.699, 0.818]. Read-back
  2/2 and 6/6 on every tree.
- `bluedot-unit2-bystander-agentarm-behavioural-2026-09-15` (8 files, private; row added
  2026-09-20 after a MANIFEST-vs-live check found it unlisted): the first agent-arm eval logs,
  2026-09-15: the smoke batch and the four paid frontier cells (claude-opus-5, claude-sonnet-5,
  gemini-3.1-pro-preview, gpt-5.6-luna-pro) at n=6, plus the `cells_agentarm_live.csv` of that
  day. Ledger: §F180. Hosted models have no activations, so this repo is transcripts only.
