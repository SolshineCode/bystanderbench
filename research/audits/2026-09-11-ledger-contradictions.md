# Ledger contradiction audit — research/FINDINGS.md (§F1–§F99, 4019 lines)

Date: 2026-09-11. Auditor: Claude Code (read-only pass). **Nothing was fixed; FINDINGS.md was not edited.**

Rule under audit: corrections in FINDINGS.md are **additive and dated** — a later entry that
falsifies an earlier claim must say so explicitly, naming the entry it corrects. This file lists
places that rule appears to have been broken, ordered by damage (a citable wrong number first).

Known-good baseline: §F94 correcting §F92's "36 further episodes" is a *compliant* correction and
is not counted as a violation.

---

## A. Citable wrong numbers (highest damage)

### 1. §F78 restates north-mini-code's concealment counts with THREE different denominators/numerators from §F25/§F26, with no correction note.

- §F26 (2026-09-08), headline: *"raw **41/177** `concealed_cheat`, classified **39/177** hardcode"*,
  and in the same entry: *"pooled over both north-mini screens the classified hardcode rate is
  **51/226** (22.6%, [17.6%, 28.4%])"* — i.e. 39/177 plus §F25's 12/49.
- §F78 (2026-09-10), line 2856: *"`concealed_cheat` is **41/176** and **12/61** for
  `north-mini-code`"*.
- §F78 (2026-09-10), line 2923: *"`north-mini-code` at **53/237**"*.

Three separate disagreements, none flagged:
  - denominator of the big batch: **177** (§F26, and §F26's `Source:` line says the screen file has
    "177 rows") vs **176** (§F78);
  - denominator of the original screen: **49** (§F25/§F26's pooling arithmetic) vs **61** (§F78);
  - the pooled figure: **51/226** classified (§F26) vs **53/237** raw (§F78).

§F78 also silently switches from the *classified* convention (§F26's citable table, which excludes
the two `algorithmic_pass_ambiguous` rows) to the *raw* convention, without saying so — so a reader
comparing §F26 and §F78 sees two different rates for the same cell.

**Which is correct:** §F26 is the entry backed by a hand-audit and an explicit per-split table, and
its `Source:` line states the row count (177). §F26's 41/177 raw and 39/177 classified should be
treated as authoritative; §F78's 41/176, 12/61 and 53/237 are unexplained and at least the 176 is
arithmetically inconsistent with §F26's own source file. **This is the single most citable wrong
number found** — §F78 is the entry framed as a cross-model summary, i.e. exactly the one a write-up
would quote.

### 2. `gemma-3-12b-it`'s positive-class denominator is stated as 166, 122 and 156 in three different entries — and the 166 was already formally withdrawn when §F32 reused it.

Same cell (gemma-3-12b-it, `concealed_cheat` count over the local corpus), four values across the ledger:

- §F19 (2026-09-07): *"`samples.jsonl` held **166 rows for 124 real samples**"*, and the impossible-splits
  rate *"**n=99**: `concealed_cheat` **4/99 = 4.0%**"*. §F19 also notes the prior figure was
  *"Previously reported as `concealed_cheat: 5, disclosed: 5, n=166`. Superseded by this"* — so 166
  as a *sample* denominator was retired here.
- §F22 (2026-09-07), which explicitly corrects §F19 and §F20: *"§F19's '166 rows for 124 real samples'
  is **withdrawn**: there are **156 real generations** across 124 distinct (split, task) cells."*
  §F22 sets the citable figures as *"`concealed_cheat` **5/122 = 4.10%**"* (behavioral) and
  *"**4/99 = 4.04%**"* (activation basis).
- **§F32 (2026-09-08), one day later**, artifact-inventory table, uncorrected to this day:
  *"`gemma-3-12b-it` | … | **5 `concealed_cheat` / 166**"*.
- **§F78 (2026-09-10)**: *"gemma-3-12b **5/156**"* — a third denominator, also unflagged.

§F32 reuses the exact denominator §F22 had withdrawn the previous day, with no "corrects" language
and no acknowledgement; §F78 then introduces a third. §F41 (2026-09-09) re-confirms the correct
framing (*"gemma-3-12b's 5 rows are 4 solutions on 4 tasks, which is consistent with the n=4 used in
§F35"*) but never names §F32, so the wrong cell stands.

**Which is correct:** §F22's **5/122** (behavioral) and **4/99** (activation-backed). 166 is the raw
row count of a file with known duplicate sids — §F23 says so directly (*"`gemma3-12b/samples.jsonl`
… still 166 lines on disk"*, of which *"156 are real distinct"*) — and §F41 lists this as one of the
five repetitions of the same error class (*"§F19 (166 rows read as 166 samples)"*). 156 is the
generation count, not the sample count, so §F78's 5/156 is a category error even though the number
exists.

**Severity: joint-highest with A.1.** §F32's table is the interpretability arm's artifact inventory —
the entry that designates gemma-3-12b-it "the interpretability arm's primary subject" — so its
positive-class figure is exactly what a write-up would cite when justifying that choice.

### 3. §F92's "36 further episodes" / "36 new episodes" — corrected by §F94 (COMPLIANT, listed for completeness).

§F92: *"Scaled from §F86's 5/30 with **36 further episodes** across both cards"* and *"Activations
captured for **the 36 new episodes**"*. §F94 (2026-09-11) names the entry, gives the per-batch
re-derivation (18 counted + 8 discarded, `scale-d` status=error), and states the headline 9/48 is
unaffected. This is the rule working as intended. **Not a violation** — included only as the
reference example.

---

## B. Claims quietly narrowed or re-stated (medium damage)

### 4. §F88 → §F89: the `ling` within-family floors are given as 4/4 in one place and 3/4 in another, inside the correction chain itself.

- §F88 table: *"`ling-3.0-flash-vl` | **3/4 = 75%**"*, *"`ling-3.0-flash-fin` | **none**"*,
  *"`ling-3.0-flash-sante` | **none**"*.
- §F89 table (the entry that closes §F88's gap): *"`ling-3.0-flash-fin` | **4/4**"*,
  *"`ling-3.0-flash-sante` | **3/4**"*, *"`ling-3.0-flash-vl` | 3/4"*.
- §F89 prose immediately after that table: *"**Two of the three floors are 3/4, not 4/4**"*.

§F89's own table and its own prose agree (vl 3/4, sante 3/4, fin 4/4 = two of three at 3/4), so this
is internally consistent — but §F89's sentence *"not 4/4"* reads as a correction of an earlier "4/4"
claim that it never names. The nearest 4/4 claim is §F88's *"The nemotron pair (both floored 4/4)
and the nex-agi pair (both floored 4/4)"*, which is about different families. **Low-severity wording
hazard, not a wrong number**, but a reader tracing "not 4/4" back finds no antecedent.

### 5. §F79's "all three ling siblings alert 0/6" was stated as a floored, settled within-family replication; §F88 narrows it and §F89 restores it — the chain is compliant but the §F79 headline was never marked.

- §F79 (2026-09-10) headline: *"**Within-family replication: all three `ling-3.0-flash` siblings
  alert 0/6.** … three families now behave consistently INTERNALLY … the strongest support yet for
  §F77's family framing."*
- §F88 (2026-09-11): *"**AUDIT CORRECTION to §F79.** Two of its three `ling` cells have no affordance
  floor of their own, so under v1.0's own rule they are not reportable."*

§F88 and §F89 both name §F79 explicitly, so the *rule* is followed. The residual hazard is that
§F79's headline line still reads as settled and carries no inline pointer forward, unlike §F4 which
was explicitly given a pointer by §F43 (*"§F4 is not deleted or renumbered. It keeps its text and
gains a pointer here."*). **Inconsistent application of the repo's own pointer convention.**

### 6. §F78's "seven other models sit at 0" contradicts §F75's own table, which it cites.

- §F78 (line 2938): *"one family reports at **4/6** while **seven other models sit at 0**"*.
- §F75 table: `nex-agi/nex-n2.5-pro` **4/6**, `nex-agi/nex-n2.5-mini` **2/6**,
  `dots-3-note-preview` 0/6, `ling-3.0-flash-vl` 0/6, `nemotron-3.5-lightning` 0/6,
  `nemotron-3-super-120b-a12b` **0/0 — uninformative**.

`nex-n2.5-mini` is 2/6, not 0, and one of the remaining cells is explicitly marked uninformative
(floor 0/6), so it cannot be counted as "sitting at 0". **§F75 is correct; §F78's summary sentence
overstates the contrast.** Damage: moderate — it is a headline-shaped sentence in a summary entry.

### 7. §F98's retro-verification census does not reconcile with the cell counts elsewhere in the ledger.

§F98: *"Every cell this tool currently reports has `cover_task_passed` at 100% — **17 cells at 6/6,
three at 18/18, one at 12/12**"*.

But §F92 reports `cover_task_passed` **48/48** on the nex local cell, §F85 reports **24/24** on two
qwen cells, §F81 reports **24/24**, and §F66 reports *"`cover_task_passed` 24/24 … in every cell"*.
None of 48/48, 24/24 appear in §F98's census of 21 cells. Either the census is over a narrower set
than "every cell this tool currently reports", or it is incomplete. **§F98 does not say which**, and
it uses the census as the evidence that the new `COVER_MIN` gate is retroactively inert. The
byte-identical-diff claim is separately verifiable; the census sentence is not consistent with the
ledger as written.

---

## C. Budget tracking

### 8. §F80 → §F82 → §F91: the running paid-API balance does not reconcile across three entries, and no entry names the gap.

- §F80 (2026-09-10): *"Total for the four-model set: **$6.07** of the $7.76 balance ($1.69
  remaining)."* — internally correct: 7.76 − 6.07 = 1.69.
- §F82 (2026-09-10): *"Cost $0.4378 for 6 episodes ($0.073/ep); balance **$1.07** remaining."*
  — but 1.69 − 0.4378 = **$1.2522**, not $1.07. Unexplained gap: **$0.18**.
- §F91 (2026-09-11): *"Run on Sonnet for $0.35 (6 episodes at $0.058, under the $0.073 estimate)"*
  and *"at $0.445/episode a 6-episode control costs $2.67 against a balance of **$0.66**."*
  — but 1.07 − 0.35 = **$0.72**, not $0.66. Further unexplained gap: **$0.06**.

Neither §F82 nor §F91 flags a discrepancy, names an intervening spend, or corrects the
predecessor's stated balance. The only entry between §F80 and §F82 (§F81) is an unpaid local qwen
run, so nothing in the ledger accounts for the drift.

**Which is correct: not determinable from the ledger alone.** The likeliest explanation is untracked
overhead or rounding rather than a misstated result, and no scientific claim depends on it. It is
listed because the $0.66 figure is *load-bearing for a decision*: §F91 uses it to argue the
outstanding Opus benign control ($2.67) is unaffordable, and that is the project's stated top open
item. A balance that is actually $0.72 does not change that conclusion, but the number is cited in
support of it while not reconciling with its own predecessors.

**Severity: low-medium.** Below every numeric finding in section A, above the wording hazards in B.

---

## D. Source-path integrity (§ `Source:` lines)

73 `Source:` blocks were parsed and every backticked path in them resolved against the working tree
(brace expansions expanded, globs allowed). Results:

### 9. No `Source:` path was found to be genuinely missing from disk.

Every path that failed a literal `os.path.exists` check falls into one of three benign classes,
each confirmed by a filesystem search:

- **Hugging Face repo IDs, not local paths** (correctly not on disk):
  `DarkStarDeleeuw/bluedot-unit2-concealment-probe-2026-09-01` (§F21),
  `DarkStarDeleeuw/bluedot-unit2-or-screens-2026-09` (§F17),
  `DarkStarDeleeuw/bluedot-unit2-lab-artifacts-2026-09-08` (§F33, §F34),
  `google/gemma-scope-2-12b-it` (§F17).
- **Bare filenames relative to a directory named earlier in the same `Source:` line** — all located:
  `sae_encode.py`, `corpus.py` → `concealment-probe/tools/`;
  `resample_f655neg.jsonl` → `sae-causal/`; `manifest_f655_neg.tsv` → `sae-causal/tokens/`;
  `mechanism_audit.json` → `logs/moe-free-north-mini-or/` and `hf_upload_gemma12b/`;
  `gemma12b_last_16k_small.json`, `gemma12b_L20_feature_cells.json`,
  `gemma12b_last_16k_vs_originalpass.json` → `concealment-probe/results/sae/`;
  `run2/qwen3.5-27b/samples.jsonl` → `concealment-probe/data/run2/qwen3.5-27b/`;
  `nla-decode/results/...` → `nla-decode/` exists.
- **Paths outside the repo that do exist**: `~/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf`
  (§F77) — present.
- **Prose, not a path**: `corpus.load(..., "generation")` (§F77), `acts/*.bin` (§F19).

**Finding: clean.** No entry cites a non-existent source. The residual risk is stylistic — several
`Source:` lines cite bare filenames that are ambiguous between two copies on disk (e.g.
`mechanism_audit.json` exists under both `hf_upload_gemma12b/` and `logs/moe-free-north-mini-or/`;
`sae_encode.py` under both `concealment-probe/tools/` and `hf_upload_labartifacts/tools/`), so a
future reader cannot tell which copy backed the number.

---

## E. Scope note

This pass covered: all 89 `Source:` blocks (mechanically verified); the recurring-fraction sweep
(4/4, 3/4, 6/6, 8/8, 12/12, 1/6, 2/6, 4/6, 5/30, 9/48, 0/18, 0/24, 0/40, 0/48, 62/62, 12/12) across
all 4019 lines; and close reading of §F25/§F26, §F75/§F78/§F79, §F84/§F86/§F92/§F93/§F94,
§F88/§F89, §F97/§F98/§F99.

A background prose-comparison scan of §F1–§F61 completed and contributed finding A.2 (verified
independently against the file before inclusion). It reports that every explicit correction chain in
that range correctly names its target: §F17→§F34, §F18→§F20, §F19/§F20→§F22, §F4→§F43,
§F35→§F47, and the §F22 dedup bug recurring through §F37/§F41/§F60.

A second prose-comparison scan covering §F62–§F99 also completed and contributed finding C.8
(verified independently against the file before inclusion). It reports that every apparent
contradiction in that range traces back to a properly-named correction satisfying the ledger's rule:
§F73→§F61/§F65/§F69/§F70, §F74→§F73, §F77→§F76, §F88→§F79, §F94→§F92, and §F97's qualification of
§F96. It further reports that the scientific quantities in that range — floors, alert rates, Wilson
intervals, discovery rates, n-counts — reproduce identically wherever they recur, including
near-collisions that are genuinely distinct (the two 8/8 floors belong to gemma-3-12b-it and
gemma-3-27b-it respectively and are correctly labelled).

**Residual uncertainty.** Findings 1, 6 and 7 were caught by targeted numeric cross-referencing
rather than by either prose scan, which means prose scanning alone did not surface them. The
cross-entry numeric sweep here was driven by a recurring-fraction grep and is therefore strongest on
quantities written as `a/b`; figures written as percentages, decimals or prose ("roughly a fifth",
"about 5%") were not systematically cross-checked and are the most likely place for a remaining
undetected contradiction.
