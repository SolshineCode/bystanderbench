# 1. Number Mismatches Against CSVs

1. **Qwen3.5-27B total episodes:**
   - **Quote:** "Qwen3.5-27B 0 across roughly 200 episodes"
   - **CSV Rows:** 71 through 88
   - **Correction:** The sum of `n` across all Qwen3.5-27B arms is 307 episodes, not roughly 200.

2. **Omitted models passing floor (Table 3.1):**
   - **Quote:** "Shared ceiling arm, incident 1, every model that passed its floor:"
   - **CSV Rows:** 43 and 59
   - **Correction:** `gemma-4-31B-it-Q4_K_M.gguf` (floor 7/7, row 43) and `nvidia/nemotron-3-super-120b-a12b:free` (floor 4/4, row 59) both passed their floor on incident 1 but are omitted from the table.

3. **ling-3.0-flash-sante conditional rate:**
   - **Quote:** "dots-3, ling-3.0 x3, nemotron-3.5-lightning (free tier) | 0/6 each | 0"
   - **CSV Row:** 49
   - **Correction:** `inclusionai/ling-3.0-flash-sante:free` has a `cond_n` of 3, meaning its actual conditional rate is 0/3, not 0/6 like the others in the grouped row.

# 2. Unsupported Claims

1. **Quoting exact rates for refused cells:** 
   - **Quotes:** "gemma-3-12b ... returned alerted 5/12", "llama-3.3-70b ... alerted 11/12", and "north-mini-code found the misconduct in 12/12 episodes, escalated in none". 
   - **CSV Rows:** 38, 3, and 27
   - **Flag:** The CSV explicitly leaves metrics for these cells blank because they were refused (competence below 75%). Quoting exact numerical rates for them violates the instrument's refusal.

2. **Strong generalization from small N:**
   - **Quote:** "GPT-5.6-Luna-Pro is the genuine silent frontier case..."
   - **Flag:** A 0/6 rate (CSV row 63) yields a wide Wilson interval. Declaring it definitively "silent" is stated more strongly than an n=6 sample can support.

3. **Pooling zero models with low `cond_n`:**
   - **Quote:** "...and nine further models 0"
   - **Flag:** This statement lumps in models with extremely low conditional discovery sample sizes (e.g., `gemma-4-31B` with `cond_n=1`), overstating the confidence of their definitive "zero" status.

# 3. Structure Check

**Fails "one core topic" rule:**
The skeleton covers two distinct topics rather than one. As stated in the headline, the write-up splits its focus between Part 2 (BystanderBench evaluating agent escalation) and Part 1 (detecting test-cheating in model activations).

# 4. Machine-Written Indicators

The following sentences contain rule-of-three lists, reading as machine-written:
- "On the same environment, reporting runs from 0 of 6 episodes to 6 of 6 depending on the model, and the difference is not size, lab, or open versus closed weights."
- "Built BystanderBench: an agent fixes a one-character bug in a synthetic repo and trips over evidence that other agents fabricated a ledger, falsified a model card, or switched off audit logging."
- "I ran ten models on it, labelled every passing solution by hand as concealed or disclosed, captured the residual stream of every locally served episode with llama.cpp [CITE llamacpp], and tried to find the concealment decision in those activations with linear probes, Gemma Scope 2 sparse autoencoders [CITE gemmascope2], and a natural-language autoencoder [CITE nla-anthropic] [CITE kitft-nla]."
- "All name the March close log, the 118 overridden entries, and the auditor pack."
- "The sharpest evidence for what it does track: nex-n2.5-mini declares architecture `qwen35moe` and reports; Qwen3.5-27B declares `qwen35` and never has, on the same hardware, quantisation and scorer."

---

## Disposition (Claude, 2026-09-14, after checking each point against the CSV)

Reviewer: Antigravity CLI, Gemini 3.1 Pro (High), scoped directory with the skeleton and the two canonical CSVs. Not the course, not Peter.

1. Qwen3.5 total: the reviewer summed every arm including the three tool_probe instrument checks (307). The write-up counts measurement episodes only (277); wording changed to say so. Not a mismatch.
2. Omitted floor-passers: correct. gemma-4-31B (0/12, 0/1 discovered) and nemotron-3-super (0/6, 0/0 discovered) added to the section 3.1 table as uninformative rows.
3. ling-3.0-sante 0/3: correct. Grouped row split.
4. Raw counts for refused cells: intentional, and the section now says the counts are what the instrument declined to score, quoted from the ledger to explain the refusal.
5. GPT-5.6 "genuine silent case" at n=6: accepted, softened with the Wilson upper bound.
6. "Nine further models 0": accepted; recounted as six with cond_n >= 3, two uninformative.
7. One core topic: the project's own framing (2026-09-12) is one incident with two aspects, and the skeleton already leads with BystanderBench and demotes Part 1 to a section. Noted in TODO-for-caleb as the judgment call it is; not changed.
8. Rule-of-three sentences: the three incidents and the three artifacts in an alert are real lists of three. One stylistic instance (size / lab / open weights) was rewritten.
