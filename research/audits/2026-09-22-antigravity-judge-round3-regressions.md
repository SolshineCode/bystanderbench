### 1. Regressions from Previous Repairs

1.1. **Contradiction and redundancy from repairing "disjoint sets":**
* **Side 1 (Lines 79–81):** *"The published decoders and the models that actually cheat barely overlap: every decoder model is below the floor, and the highest of them conceals at 3.2%."*
* **Side 2 (Line 304):** *"- Why are published activation decoders and models that actually misbehave disjoint sets?"*
* **Issue:** While lines 79–81 replaced the overclaimed "disjoint sets" with "barely overlap," line 304 in "Further questions" was missed and still asserts they are disjoint. Additionally, the patch introduced an immediate verbatim redundancy in lines 77–81: *"the best of them conceals at 2/62 = 3.2%, with every one of the four below the competence floor"* followed immediately by *"every decoder model is below the floor, and the highest of them conceals at 3.2%."*

1.2. **Internal inconsistency from repairing the stale unread-alert count:**
* **Side 1 (Lines 196, 201–202):** *"I read the first 36 alerting episodes by hand before believing any of it..."* and *"The 131 alerts the cell has gained since have not been read yet, so for those the rate rests on the scorer alone."* ($36 + 131 = 167$ total alerts).
* **Side 2 (Line 198):** *"Thirteen of the first 26 go further and name the thing that makes it an agent story..."*
* **Issue:** The author updated the audited alert count to 36 (matching $167 - 131 = 36$), but left the evaluation of how many named the agent story pegged to *"the first 26"*, leaving 10 read transcripts completely unaccounted for.

1.3. **Contradiction from repairing the over-strong post-training attribution:**
* **Side 1 (Lines 269–270):** *"...the two differ in size as well as post-training, so this is a narrowing rather than a finding."*
* **Side 2 (Lines 299–300):** *"- What in post-training makes nex-n2.5-mini report when qwen3.5-27b never has, from a shared lineage?"*
* **Issue:** Line 269 was corrected to acknowledge that `nex-n2.5-mini` and `qwen3.5-27b` differ in model size as well as post-training, but line 299 in "Further questions" reverts to attributing the divergence entirely to post-training.

1.4. **Nonsensical qualifier from repairing the "best number in the corpus" claim:**
* **Side 1 (Lines 250–251):** *"It alerted in 11 of 12 episodes, which would have been the best number outside the frontier models and my headline."*
* **Side 2 (Lines 62–63, Line 120):** *"The headline is north-mini-code at 53/237 = 22.4%"* / *"the same fabrication, wrongdoer is an agent pool | 167/376 = 44.4%"*.
* **Issue:** $11/12$ is 91.7%. That is far higher than the headline cheat rate (22.4%) and the headline alert rate (44.4%). Patching the claim by adding *"and my headline"* is mathematically incoherent, as 91.7% exceeds the headline rate.

1.5. **Conceptual mismatch in the size analysis repair:**
* **Side 1 (Lines 175–176):** *"Across the 14 reportable cells whose active parameter count is public, rate and size rank together at Spearman rho -0.19..."*
* **Side 2 (Line 160):** *"Eighteen models have both cells, so eighteen pairs were tested..."*
* **Issue:** Parameter count is a static property of a *model*, not an experimental *cell*. Correlating size across 14 "cells" rather than models either conflates multiple conditions per model or inappropriately pools distinct experimental arms.

---

### 2. Remaining Claim-Evidence Gaps

2.1. **Missing models and conflated metrics in free-tier scaling:**
* **Sentence & Number (Lines 193–194):** *"Taking four free-tier models from 6 to 36 episodes moved nothing: dots-3 0/24 to 0/35, laguna-s 1/24 to 3/33."*
* **Gap:** The text announces *"four free-tier models"* but names and provides numbers for only two (`dots-3` and `laguna-s`). Furthermore, the reported numbers ($0/24 \to 0/35$ and $1/24 \to 3/33$) are the cross-condition swap numbers (human vs. agent wrongdoer), not sample size scaling from 6 to 36 episodes.

2.2. **Missing human-arm data for Claude models:**
* **Sentence & Number (Lines 183–184):** *"...and Claude Opus and Sonnet sit at the ceiling whoever did it (17/17 and 10/10 on the agent arm)."*
* **Gap:** The text claims both models sit at ceiling *"whoever did it"* (both human and agent arms), but omits the numerators and denominators for the human-wrongdoer arm entirely.

2.3. **Unsupported "harder arm" and unmatched denominator on within-family size comparison:**
* **Sentence & Number (Lines 177–179):** *"The one place size does move the number is inside a single family on a single incident: nex-n2.5-mini 3/22 against nex-n2.5-pro 20/24, p 4e-06, which is one pair, confounded with post-training, and flat on the harder arm."*
* **Gap:** No data or numbers are provided anywhere in the text to support the claim that it is *"flat on the harder arm"*. Additionally, the denominator $3/22$ for `nex-n2.5-mini` does not match any cell reported in Table 1 (which lists 0/23, 0/57, 1/45, 4/46, 59/258, and 167/376).

2.4. **Unattributed population for evaluation-gaming keyword scan:**
* **Sentence & Number (Lines 204–207):** *"I scanned 367 with_tool episodes for explicit signs in the reasoning that the model suspected a test... Episodes with a cue alerted at 10/22 = 45.5% [26.9, 65.3]; episodes without, 19/345 = 5.5% [3.6, 8.4]."*
* **Gap:** The text never states which models, runs, or incident conditions make up these *"367 with_tool episodes"*, leaving an aggregate with only 29 total alerts ($10 + 19$) completely untethered to the rest of the dataset.

2.5. **Unexplained selective holdout refitting:**
* **Sentence & Number (Lines 235–236):** *"Refitting a direction from any one batch's own two dozen episodes finds nothing that survives correction, six batches out of six."*
* **Gap:** The experiment collected eleven holdout batches (lines 221, 230, 240). Reporting refitting results for *"six batches out of six"* leaves five batches omitted without explanation.

---

### 3. The Reading Experience

3.1. **Where a tired reader stops:**
* **Paragraph:** Lines 160–173 (*"Eighteen models have both cells, so eighteen pairs were tested..."*).
* **Why:** Coming right after the clear minimal-pair table (line 154), this 170-word paragraph abruptly derails narrative momentum into procedural defense: multiple-testing corrections, orphaned run workers, and a numbing string of incremental sample size fractions (`26/106 against 35/78, then 37/151 against 99/219, then 37/151 against 129/285, then 59/258 against 167/376`). In a five-minute breakout, this is the exact threshold where cognitive overload sets in and reading stalls.

3.2. **Does the final paragraph land?**
* **Assessment:** No.
* **Why:** Lines 317–319 (*"Code, logs, every cell table, the append-only findings ledger..."*) read like a release checklist and software pipeline maintenance note rather than a conclusion. The intellectual climax of the work occurs in Section 8 (lines 272–276, defining the deployment dilemma between hyper-reporting and complete silence). Ending on CSV synchronization and data-release logistics leaves the piece on a bureaucratic whimper.
