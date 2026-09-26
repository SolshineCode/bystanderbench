# Resume note — 2026-09-05 wind-down (written while 3 jobs in flight)

If the session cuts before the final consolidated report, here is the exact state
and next commands. Everything below is also committed/pushed as of this note.

## In flight right now

1. **Splice-continuation trial (workstream B)** — `splice/run_trial.sh` running
   detached (launched ~13:38 PT; reservation `ad25ef29` + self-reserve fallback now
   built in). Sequence: 70B server on :8091 (up, full offload) → 7 continuations x 2
   arms (`splice/run_continuation.py`, writes `splice/continuations.jsonl`
   incrementally) → server stop → L49/53/57 extraction of continuations into
   `splice/acts/`. Log: `run_splice_trial.log`. If it died mid-way: re-run
   `nohup bash splice/run_trial.sh > run_splice_trial.log 2>&1 &` — it re-reserves
   itself, and continuations.jsonl rows already written are evidence (append mode;
   dedup by cid before analysis).
   **Analysis when done**: doctored-arm vs control-arm concealed_cheat/hardcode-
   completion rates from `continuations.jsonl` (framing discipline: continuation/
   consistency pressure, NOT spontaneous propensity — see `splice/provenance.json`).

2. **NLA decode kernel v3** — `calebdeleeuw/nla-decode-gemma12b-20260905` on Kaggle.
   v1 = prompt-ids nesting bug, v2 = ran but EMPTY decodes (root cause found: double
   sqrt(d) embedding scaling — model's Gemma3TextScaledWordEmbedding already scales;
   fixed in v3). Collect: `kaggle kernels output calebdeleeuw/nla-decode-gemma12b-20260905`
   → `decodes.jsonl`. Validation vectors decode first; pilot vectors carry off-by-one
   + span-mean caveats (documented in the script header + published pilot card).

3. **Free-model screen queue** — `moe-floor/run_free_screens.sh` detached;
   north-mini DONE (audited: 12/49 cheats, taxonomy v2 — see
   `research/model-testing-audit-2026-09-05.md`), nemotron-3.5-lightning RUNNING
   (started 10:28 PT; north-mini took ~11.5h on free-tier rate limits), laguna-xs
   queued. On each SCREEN DONE: run
   `python3 concealment-probe/tools/screen_behavioral.py --logdir logs/moe-free-<tag>-or --out .../screen_summary_v2.jsonl`
   then hand-audit cheat/disclosed rows (v2 taxonomy: only visible-prose flags =
   disclosed).

## Next queued (not started)

- **gemma-12b local capture** (`gemma12b/run_full_pipeline.sh`, needs its own
  gpusched reservation with "gemma12b" in the session name) — FIRST after splice
  frees the GPUs; then gemma-27b (`gemma27b/`). Both GGUFs on disk + verified.
  These feed workstream A's first CLEAN organic NLA decode (l_out-32 convention
  is correct in the local pipeline).
- Rung 2 triplet (Kaggle, Monday quota reset): `moe-floor/kernels/moe-floor-qwen15-*`.
- north-mini's 7 `unclassified_audit_needed` cheat mechanisms need hand audit.
- A ~30B-total dense screen as north-mini's param-matched comparator (not run).

## Published tonight (all with MANIFEST entries)

- `DarkStarDeleeuw/bluedot-unit2-moe-floor-rung1` (+ layer-convention correction)
- `DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b` (+ correction)
- `DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b`

## Standing decisions/rules encoded tonight

- Raw log ≠ result (MANIFEST top; backfill of the three 09-02 runs done).
- Taxonomy v2: flag LOCATION decides disclosure (audit doc + screen_behavioral.py).
- Layer convention: "layer L" = l_out-L = hidden_states[L+1]; Kaggle templates fixed;
  pre-fix datasets carry corrections on their cards.
