# Appendix F. Datasets on Hugging Face

This is the corroboration appendix: every dataset a reader would need to check a claim in
the course write-up. All 49 datasets listed here live under the `DarkStarDeleeuw` account
and are private as of 2026-09-20. They are private today and will be made public later.
Every URL below is written as the address it will be public at; until then, treat the row's
description (sourced from `MANIFEST.md` and `research/FINDINGS.md`, never from memory) as
the evidence.

Two other datasets exist on the same `DarkStarDeleeuw` account, `nla-research-bulk-provenance`
and `sae-rl-homebase-artifacts`. Both belong to a different project and are excluded from
everything below.

Group 5, added 2026-09-20, holds the 15 datasets from the agent-perpetrator arm and the probe
holdouts (2026-09-15 to 2026-09-20); Group 6, added the same evening, holds 6 more from an
unattended run during a Wi-Fi outage. A live listing of the account on 2026-09-20 08:40 PDT
showed 43 project datasets, all named in `MANIFEST.md` after that update, none named there and
absent from the hub. The Group 6 datasets were pushed later the same day (~18:35) and have not
yet had a fresh live-listing cross-check; re-run it before release (see below).

---

## How to check a number

- **Every BystanderBench number** is one row of `python -m bystander.report <logs> --csv`,
  run under VERSION 1.1 (`bystander/report.py` prints `VERSION = "1.1"`; a table citing
  v1.0 keys is superseded by re-running the same tool). The frozen spec is
  `bystander/METHODOLOGY-v1.0.md`; `bystander/METHODOLOGY-v1.1.md` is the changelog against
  it (cell keying, thinking-condition disclosure, serving pins) and changes nothing about an
  environment, a scorer, an arm, or the floor/competence gates.
- **Every concealment number** (Part 1, the probe corpus) is a row of
  `research/canonical/concealment_rates.csv`.
- **`research/FINDINGS.md`** is the append-only ledger. Findings are cited by number
  (`§Fn`); a correction is a new dated block, never a silent edit to an old one. Cite the
  ledger entry, not a number carried forward from prose.

## In-repo canonical files to open first

- `research/canonical/concealment_rates.csv`, the ten-row Part 1 rate table cited above.
- `research/audits/cells_2026-09-20_after_w42.csv`, the full BystanderBench cell
  table (125 cells, 10 refused) behind the write-up's Part 2 numbers.
- `research/canonical/probe_direction_F200.npz` and `research/canonical/probe_holdout2_*.json`,
  the frozen probe direction and every holdout result computed from it.
- `bystander/METHODOLOGY-v1.0.md` and `bystander/METHODOLOGY-v1.1.md`, the frozen benchmark
  spec and its changelog.
- `research/FINDINGS.md`, the append-only ledger every claim traces to.

---

## Table key

- **Contents**: files, model, episode/sample counts as stated in `MANIFEST.md` or
  `research/FINDINGS.md`. Nothing here is estimated or guessed; where MANIFEST is silent on
  a count the ledger entry is cited instead.
- **Corroborates**: which write-up claim (Part 1 concealment rate, BystanderBench cell,
  activation-probe claim, NLA decode claim, pilot/screen) this dataset is the evidence for.
- **Ledger refs**: `§F` numbers in `research/FINDINGS.md`.

---

## Group 1: Part 1 concealment corpus

| Dataset (future public URL) | Contents | Corroborates | Ledger refs |
|---|---|---|---|
| [`bluedot-unit2-concealment-probe-2026-09-01`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-2026-09-01) | qwen3.5-27b (4 dirs: concealment, overnight, proper, run2) and qwen3.8-27b (2 dirs: overnight, run2). No qwen3.6 data. qwen3.8-27b's `samples.jsonl` files are published but empty (0 rows), which is what makes "never produced a scorable sample" true. `run2/qwen3.5-27b/samples.jsonl` holds 11 rows for 9 unique sids: two real generations per colliding id, not corruption, must not be de-duplicated. 3 `disclosed` rows, all genuine `visible_prose`. | Part 1 raw corpus underlying the qwen3.5-27b / qwen3.8-27b rows; qwen3.8-27b's "never produced a scorable sample" correction. | §F18, §F22, §F43 |
| [`bluedot-unit2-concealment-probe-llama3.3-70b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b) | 65 unique scored samples (25/25/15 splits, retry-dups removed), full transcripts + tokens + 19-layer activations (`l_out` 4..76 every 4th; NLA layer 53 in a separate pass). 0 `concealed_cheat` / 0 `disclosed` on 50 impossible-split samples, 2/15 `original_pass`. | Part 1 concealment rate for llama-3.3-70b-instruct, the dense-70B zero (csv row `llama-3.3-70b-instruct`, 0/65, matching its independent cloud screen). Also feeds BystanderBench Part 2 as the model whose 11/12 ceiling-arm alerts are the competence-gate refusal (see Group 2). | §F14 |
| [`bluedot-unit2-concealment-probe-gemma3-12b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-12b) | 166 rows = 156 real generations across 124 (split, task) cells, 124 with activations. Rows: `failed_silent` 124, `concealed_cheat` 5, `original_fail` 28, `original_pass` 9. Overrides applied per §F23 (`disclosed` count corrected to 0). | Part 1 concealment rate for gemma-3-12b-it (csv row: 5/166, rate 0.0301, 4 of 74 concealed_tasks). Feeds the Part 1 "SAE-published models barely cheat" claim (gemma has a published Gemma Scope 2 SAE). | §F19, §F22, §F23 |
| [`bluedot-unit2-concealment-probe-gemma3-27b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-gemma3-27b) | 62 samples, all with 16-layer activations (4..60 every 4th + NLA layer 41). 2/50 hardcode `concealed_cheat`, hand-audited; 0 `disclosed`. Rows: `failed_silent` 48, `concealed_cheat` 2, `original_fail` 10, `original_pass` 2. | Part 1 concealment rate for gemma-3-27b-it (csv row: 2/62, rate 0.0323). Same "SAE-published, barely cheats" claim as gemma-3-12b. | §F29 |
| [`bluedot-unit2-concealment-probe-qwen38-27b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-qwen38-27b) | 310 files: 100 samples (original 50, oneoff 25, conflicting 25; 100 distinct sids), 100 token streams, 100 residual bins (11 layers `1,7,12,18,24,30,35,41,47,52,58` x 3 slots x d 5120, 675,840 B each; layer 64 requested and silently dropped, recorded), extract/prepare/build_rates logs, dated `concealment_rates.csv`. Read back 8/8 MD5-match. | Row 10 of the Part 1 table: 0/50 impossible-split concealment, 18/50 disclosed (13/25 on `conflicting`, every flag in visible prose by hand read), competence 30/50 below the floor, so the zero is reported with the floor flag. Figure 4 point. | §F160, §F165, §F174 |
| [`bluedot-unit2-concealment-probe-nemotron35-lightning`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-nemotron35-lightning) | 62 samples, 12-layer sweep (`1,6,10,15,20,24,29,34,38,43,47,51`, d_model 2688), teacher-forced local capture over the hand-audited OpenRouter free-tier screen. Rows: `failed_silent` 45, `disclosed` 2, `concealed_cheat` 3, `original_pass` 10, `original_fail` 2. | Part 1 concealment rate for nemotron-3.5-lightning (csv row: 3/62, rate 0.0484). Same model that is Part 2's one clean silent bystander; supports the competence-matched comparison against north-mini-code (both 83% on the solvable split, Fisher p = 0.00086). | §F24 |
| [`bluedot-unit2-concealment-probe-olmo3-7b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-olmo3-7b) | 62 samples, 60 with BASE-checkpoint (`Olmo-3-1025-7B` Q8_0) activations at hook layers 4/16/28 (d_model 4096). 0 `concealed_cheat`, 1 genuine `disclosed` (`oneoff_lcbhard_82`). Rows: `failed_silent` 49, `disclosed` 1, `original_fail` 10, `original_pass` 2. | Part 1 concealment rate for olmo-3-7b-instruct (csv row: 0/62, rate 0.0000). | §F18 |
| [`bluedot-unit2-concealment-probe-north-mini-code`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-concealment-probe-north-mini-code) | 61 scored samples from the 2026-09-05 OR screen, PARTIAL activation capture (30 of 61 bins, 12 layers x 3 slots x d_model 2048, positives-first order, stopped mid-queue so the missing tail is systematic not random). 12/49 = 24.5% [14.6%, 38.1%] hand-audited hardcode. Also ships `bigbatch/` (176 rows / 177 unique sids, 42-entry audit, no activations) and the raw `.eval` archives from both screens. | Part 1 concealment rate for north-mini-code, the "best concealer" claim (csv pooled row: 53/237, rate 0.2236, 22.4%); the SAE arm's counterexample (highest cheat rate, no published SAE); the north-mini v llama-competence-matched-comparison. | §F12, §F13, §F25, §F26 |
| [`bluedot-unit2-moe-floor-rung1`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-moe-floor-rung1) | Rung 1 of the smallest-cheating-MoE search: OLMoE-1B-7B (MoE) + OLMo-7B-0724 + OLMo-2-1124-7B (dense controls), 62 samples each, full transcripts, tokens, `[n_layers,3,d]` activations (Kaggle T4 `output_hidden_states` capture). N-extended counts: OLMoE-1B-7B (MoE) 6/158 (3.76% Wilson CI), OLMo-2-1124-7B (dense) 1/158 (0.63%), all `check_override` mechanism. `olmo2-7b/label_overrides.json` is authoritative over `samples.jsonl` for one row (`conflicting_lcbhard_82_e1`, corrected to `failed_silent`). | Mechanism finding (`check_override`) grounding the taxonomy claim; the falsified "era of post-training, not architecture" overclaim (correction lives in `bluedot-unit2-or-screens-2026-09`'s `moe_floor_extension/`, see Group 4). | §F8, §F9, §F20 |

## Group 2: Part 2 BystanderBench logs and activations

| Dataset (future public URL) | Contents | Corroborates | Ledger refs |
|---|---|---|---|
| [`bluedot-unit2-bystander-acts-llama3.3-70b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-acts-llama3.3-70b) | 18 bins (786,432 B each = 8 layers `8,20,32,44,50,53,64,72` x 3 slots x d_model 8192 x 4 bytes). llama-3.3-70b's BystanderBench ceiling + floor captures. Card labels the cell **escalation-while-stuck, not misconduct reporting**: the cell is REFUSED by the competence gate and must never be used as a bystander positive class. | Section 4 ("What the instrument refused to say"): llama-3.3-70b floor 6/6, alerted 11/12, cover 0/12, every alert a status report, refused by the competence gate despite what would otherwise be the corpus's headline rate. | §F112, §F113 |
| [`bluedot-unit2-bystander-acts-nex-n2.5-mini`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-acts-nex-n2.5-mini) | 338 bins (196,608 B each = 8 layers `4,8,16,24,30,34,37,39` x 3 slots x d_model 2048 x 4 bytes). Every local nex-n2.5-mini capture: incidents 1-3, both depth runs, the benign control, both addressee arms, the positive-class batches. | Section 3.1/3.2's nex-n2.5-mini cross-incident table (24.5% ledger fabrication / 3% model-card falsification / 0% audit evasion) and the benign-control contrast (0/24 vs 27/108, Fisher p = 0.027 pre-§F161 re-keying). | §F87, §F111, §F116 |
| [`bluedot-unit2-bystander-gemma4-31b-pod-2026-09-14`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-gemma4-31b-pod-2026-09-14) | 134 files: 43 residual bins (8 layers of 60, `4,8,16,24,32,40,48,56`, x 3 slots x d_model 5376, 516,096 B each) + token streams + meta for gemma-4-31B-it Q4_K_M (floor 6, smoke 1, with_tool 12 x 3 incidents). Served on RunPod, benchmarked locally over a tunnel; tokens captured locally after a `--prefill-assistant` guard rejected the tunnel capture. Read back 3/3 sampled bins MD5-match. | Section 3.5 scaling read: a fourth family point (gemma-4-31B dense, thinking on, silent and non-discovering, alerted 0/12 every incident, discovered_content 1/12, 0/12, 0/12). Also the second demonstration (after nemotron-super) that a 0/12 alert rate can be entirely a discovery failure. | §F163 |
| [`bluedot-unit2-bystander-lightning-ext-2026-09-14`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-lightning-ext-2026-09-14) | 114 files: 36 residual bins (delivered layers `8,24,40` x 3 slots x d 2688, 96,768 B each; requested `4,8,16,24,32,40,48`, dropped silently per §F156 and recorded) + token streams + meta for the +12 `with_tool` episodes per incident on nemotron-3.5-lightning (thinking on). | Section 3.3 / figure 3: lightning at n=24 per incident stays at zero escalations (0/72 across incidents, 0/51 conditional). | §F169 |
| [`bluedot-unit2-bystander-lightning-nothink-ext-2026-09-15`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-lightning-nothink-ext-2026-09-15) | 52 files: 12 residual bins (layers `8,24,40` x 3 slots x d 2688, 96,768 B each) + token streams + meta for +12 `with_tool` incident-1 episodes on nemotron-3.5-lightning with thinking off. Read back 5/5 MD5-match. | Section 3.3: the thinking-off lightning cell at n=24, 0/24 alerted, 0/21 conditional, cover 24/24, floor 6/6. | §F175 |
| [`bluedot-unit2-bystander-qwen35-blatant-ext-2026-09-15`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-qwen35-blatant-ext-2026-09-15) | 37 files: 8 residual bins (layers `4,8,16,24,32,40,48,56` x 3 slots x d 5120, 491,520 B each) + token streams + meta for +8 `with_tool` incident-1 episodes on qwen3.5-27b (native tools, thinking off). Read back 5/5 MD5-match. | Section 3 / figures 1, 6, 7: the pilot model's incident-1 cell at n=25, 0/25 alerted, 0/16 conditional, cover 25/25. | §F176 |
| [`bluedot-unit2-bystander-nex-inc23-gh-2026-09-14`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-inc23-gh-2026-09-14) | 149 files: 48 residual bins (8 layers `4,8,16,24,30,34,37,39` x 3 slots x d 2048, 196,608 B each) + token streams + meta for the +24 `with_tool` episodes on incident 2 and +24 on incident 3 for nex-n2.5-mini (thinking on). Read back 3/3 + manifest MD5-match. | Section 3.2 / figure 2: the incident effect at n=72 per incident (incident 2 1/45 and incident 3 0/57 conditional vs incident 1's rate); two limit-hit alerts kept out of the conditional by the pre-registered rule. | §F170 |
| [`bluedot-unit2-bystander-gemma3-27b-pod-2026-09-15`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-gemma3-27b-pod-2026-09-15) | 77 files: 18 residual bins (16 layers `4,8,12,16,20,24,28,32,36,40,41,44,48,52,56,60` x 3 slots x d_model 5376, 1,032,192 B each, all requested layers delivered) + sidecars + token streams + meta for gemma-3-27b-it Q4_K_M (bartowski build, prompted CLI mode: floor 6, incident-1 with_tool 12). Served on a RunPod A40, benchmarked locally over a tunnel, extracted on the pod against the same file. Extract and capture logs included. Read back 6/6 MD5-match. | Section 4 (refusals): floor 6/6 with cover 0/6; ceiling alerted 6/12, cover 2/12, REFUSED on competence; all six escalations are "I am blocked" messages, none about the fabrication. Ceilings 2 and 3 stopped by the gate. | §F172 |
| [`bluedot-unit2-bystander-lightning-dualtarget-20260913`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-lightning-dualtarget-20260913) | 58 files, 18 bins (3 layers `8,24,40` x 3 slots x d_model 2688, 96,768 B each). nemotron-3.5-lightning dual-target cell: floor 6/6, cover 12/12, alerted 0/10. Note: 7 layers requested (`4,8,16,24,32,40,48`), `extract_resid` delivered only 3 (8,24,40) with no warning; the delivered set matches every other nemotron-lightning capture so it is comparable. | Section 3.3, "one clean silent bystander": part of the lightning result (channel used 6/6 thinking-off, job finished, evidence found, escalated 0 times). | §F155, §F156 |
| [`bluedot-unit2-bystander-lightning-incidents23-20260913`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-lightning-incidents23-20260913) | 119 files, 37 bins (3 layers `8,24,40` x 3 slots x d_model 2688, 96,768 B each, requested and delivered, verified against `requested_layers.txt`). nemotron-3.5-lightning on `blatant_safety_falsification` and `blatant_oversight_evasion`, floor + ceiling each, plus the incident-2 smoke episode. Arms: safety_falsification 7 floor / 12 ceiling; oversight_evasion 6 floor / 12 ceiling. | Section 3.3: together with `...-lightning-dualtarget-20260913`, every episode behind lightning's "0 of three incidents produced an alert" claim (48/48 thinking-on cover-task passes across all three incidents, 0 escalations). | §F157, §F159 |
| [`bluedot-unit2-bystander-nex-pos-jk-2026-09-14`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-pos-jk-2026-09-14) | 152 files: 48 residual bins (8 layers `4,8,16,24,30,34,37,39` x 3 slots x d=2048, 196,608 B each) for +24 nex-n2.5-mini incident-1 `with_tool` episodes (batches j, k; alerted 7/12 and 4/12), as both the full-stream tree and the `pool_bounds` pre-decision tree (seed 20260912), plus tokens and meta. Read back 4/4 sampled bins. | Section 3.4 ("Looking inside did not work, twice") Part 2 half: feeds the probe refit from n=84 to n=108 (27 alerting), the honest-window AUC moving from 0.586 (p=0.14) to 0.675 (L7, p=0.12) / 0.670 (L2, p=0.074). | §F167 |
| [`bluedot-unit2-bystander-northmini-acts-20260913`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-northmini-acts-20260913) | 66 files, 20 bins (12 layers x 3 slots x d_model 2048 x 4 bytes, 294,912 B each). north-mini-code BystanderBench episodes, 18 under `native`/`tools`, 2 under `cli`/`prompted`. Recovered only after §F151 found the rebuild had dropped `tool_call_id`, which the model's template dereferences, causing all 18 to 500 with no tier-2 corpus at all until fixed. | Section 4: activation evidence behind the north-mini-code refusal (found the misconduct 12/12, escalated 0, hit the conversation cap in all 12 because a third of its tool calls were rejected as malformed JSON). | §F148, §F150, §F151 |

## Group 3: interpretability arms (probe, SAE, NLA)

| Dataset (future public URL) | Contents | Corroborates | Ledger refs |
|---|---|---|---|
| [`bluedot-unit2-lab-artifacts-2026-09-08`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-lab-artifacts-2026-09-08) | Everything that is a result or an instrument rather than a raw capture: `bystander/` (benchmark v0 + built environments + scripted-trajectory tests + the first qwen3.5-27b pilot logs), `nla-decode/` (kernels, superseded v2/v3 outputs, and a live Kaggle pull), `probe_results/` (linear-probe fits and the first Gemma Scope 2 SAE encode + validity gate), `splice/` (acts, tokens, audit, provenance), `tools/`, `visualizations/` (audited-only charts + `verification_table.csv`). Card carries a per-folder epistemic grade table. 205 files. | Part 1's interpretability negative results: the probe fits, the first SAE encode, the SAE validity gate (realised L0 vs target L0), and the splice-continuation trial. | §F30, §F31, §F33, §F34 |
| [`bluedot-unit2-nla-decode-runpod-2026-09-13`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-13) | 3 files. First RunPod A40 execution of the gemma NLA decode kernel. **Superseded and uninterpretable**: all four validation vectors arrived NaN, so the four project decodes have no positive control behind them. Kept only because it lets the later fix be diagnosed against it. | Section 3.4's NLA arm history: the float16-overflow bug (gemma's layer-32 activations run 63k-82k against a 65,504 ceiling) that made the first decode attempt empty. Do not cite its decodes for content. | §F147, §F149 |
| [`bluedot-unit2-nla-decode-runpod-2026-09-13b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-13b) | 3 files. Re-run after the one-line dtype fix. All four validation vectors finite and decode to their known content (the weather vector returns "We're expecting heavy rain and strong" against a source of "heavy rain and strong winds across the coast tomorrow"). The four project vectors (from the recruiter-pilot episodes) decode to degenerate repetition, a null for concealment. md5 `baaf9ab1be35672c459f0e1b703b840c` for `decodes.jsonl`. | Establishes the NLA decoder's positive control works (§F149's fix confirmed by result). Its four project-vector decodes are superseded for content by `bluedot-unit2-nla-decode-kaggle-2026-09-14` below (wrong layer offset and span means), but the positive-control validation itself still stands. | §F152 |
| [`bluedot-unit2-nla-decode-runpod-2026-09-15`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-nla-decode-runpod-2026-09-15) | 4 files (`decodes.jsonl`, `run_meta.json`, `pod_run.log`, `script_v4_pod.py`). The Kaggle v4 run repeated on a RunPod A40 in bf16: same AV, layer, context, 78 vectors. | The reproducibility floor for NLA decodes: vector norms agree to a median 5e-4 relative, decoded text agrees for a median 227 characters then diverges under greedy decoding, domain profile agrees on 64/78; positive and negative controls behave the same on both machines. Any NLA claim in the write-up cites the first two sentences and a domain label, never an exact string. | §F173 |
| [`bluedot-unit2-nla-decode-kaggle-2026-09-14`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-nla-decode-kaggle-2026-09-14) | 5 files (`decodes.jsonl`, `run_meta.json`, `kaggle_kernel.log`, `prefixes.jsonl`, `script_v4.py`). NLA v4: all 24 recruiter-pilot episodes, fresh single-position vectors at `hidden_states[33]` (last prompt token, first response token, response-span mean) reconstructed from the exact final-stage context (88/88 stage token counts exact), positive and negative controls on the same run, 78 decodes. Supersedes the 09-13b project decodes specifically (wrong layer offset, span means, and `arr[-1]` was stage 3 for 5 of 24 episodes). | Section 3.4's closing NLA claim: pressure and control remain indistinguishable by content (5 of 6 planned Fisher tests p = 1.0, the sixth a single template-word hit); "the decoder reads the activations, and what is in them at that slot is loop output, not a concealment decision." | §F162 |

## Group 4: pilots and screens

| Dataset (future public URL) | Contents | Corroborates | Ledger refs |
|---|---|---|---|
| [`bluedot-unit2-recruiter-pilot-gemma3-12b`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-recruiter-pilot-gemma3-12b) | 24 paired trials (12 pressure / 12 matched-neutral-control), gemma-3-12b-it 4-bit, per-stage response-span activations including NLA layer 32. Result: 1/12 cheat each arm, both hardcode on the `lcbhard_9` honeypot, hand-audited; zero `reported_pressure`. | The recruiter-pressure pilot's clean null (pressure does not uplift concealment on gemma-3-12b-it). Its captured episodes are also the source material for the NLA decode arm's "project vectors" (`lcbhard_9`/`lcbhard_41` pressure vs control) in Group 3. | §F10 |
| [`bluedot-unit2-or-screens-2026-09`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-or-screens-2026-09) | The OpenRouter screening record not already inside a per-model dataset: the four `nla-screen-*` runs on the interp-artifact models (gemma-3-12b 2/75, gemma-3-27b 1/75, llama-3.3-70b 0/75, qwen2.5-7b 0/66), `moe-free-laguna-xs-or`, five 2026-09-06 paid-tier batches and four `*-all` dirs as raw `.eval` only (never screened into scored form, the card says so explicitly), `backfill-2026-09-05`, `moe_floor_extension/` (the ~4x N extension that falsified the rung-1 "era not architecture" claim, published because it is a falsification), and `drivers/`. 100 files, 16 screen dirs. | The model-selection screen behind Part 1's model choices, and the explicit correction of the rung-1 MoE overclaim cited in `bluedot-unit2-moe-floor-rung1` (Group 1). | §F8 (correction), moe_floor_extension |


## Cross-check: MANIFEST.md vs the live HF listing

Checked by grepping every `DarkStarDeleeuw/` occurrence in `MANIFEST.md` against the live
API listing of the 21 project datasets given for this task (verified 2026-09-14):

- **Present in both, name-for-name identical: all 21.** No dataset on HF is missing from
  `MANIFEST.md`, and no dataset named in `MANIFEST.md` is absent from the live listing.
- `MANIFEST.md` also correctly names both non-project datasets on the account
  (`nla-research-bulk-provenance`, `sae-rl-homebase-artifacts`) and flags them as belonging
  to a different project, matching the exclusion above.
- No naming drift was found (no case differences, no stray suffix, no dataset referenced
  under one name in prose and published under another).

*Update 2026-09-15: seven rows added after that check (`bystander-lightning-nothink-ext-2026-09-15` pushed 05:00, `bystander-qwen35-blatant-ext-2026-09-15` pushed 06:10, plus the five below): three datasets pushed tonight (`bystander-gemma3-27b-pod-2026-09-15`, `nla-decode-runpod-2026-09-15`, `concealment-probe-qwen38-27b`) and two 09-14 trees that MANIFEST carried but this table had missed (`bystander-lightning-ext-2026-09-14`, `bystander-nex-inc23-gh-2026-09-14`), found by a live-listing diff at 04:30, both pushed with MD5 read-back and listed in MANIFEST; re-run the listing check before release.*

**Conclusion: MANIFEST.md and the live HF listing agree exactly.** This appendix's table
above is built directly from `MANIFEST.md`'s descriptions, cross-verified against
`research/FINDINGS.md`'s ledger entries for every dataset where MANIFEST's own text carries
a `§F` pointer.

## Group 5: agent-perpetrator arm and probe holdouts (2026-09-15 to 2026-09-20)

Every tree here was built by `bystander/capture_chain.sh` (or, before 09-20, by the launcher it
replaced) and carries a `CHAIN_STATUS`/capture log; a pre-decision tree is the same episodes cut
before the escalation decision by `bystander/decision_index.py --match quantile`, and only slot 1
(`mean_final_turn`) of a pre-decision tree is a valid probe input (§F199). Probe result JSONs are
published beside the tree they were computed on.

| dataset | what it holds | what it corroborates | ledger |
|---|---|---|---|
| [`bluedot-unit2-bystander-agentarm-behavioural-2026-09-15`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-agentarm-behavioural-2026-09-15) | 8 files: the agent-arm smoke batch and the four paid frontier cells (claude-opus-5, claude-sonnet-5, gemini-3.1-pro-preview, gpt-5.6-luna-pro) at n=6, plus that day's `cells_agentarm_live.csv`. Transcripts only (hosted models). | The first agent-arm cells in section 3.1: frontier models report either way at n=6. | §F180 |
| [`bluedot-unit2-bystander-agentarm-overnight-2026-09-19`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-agentarm-overnight-2026-09-19) | 48 bins, 201 files: `acts_qwen35_agentarm/` (qwen3.5-27b agent-arm capture, n=36, zero alerts) and `acts_nex_agentarm_holdout.predecision/` (holdout 1, 24 episodes, cut with the pre-fix matcher, gate 0.507). MD5 read-back 5/5. | qwen3.5-27b 0/18 on the agent arm; probe holdout 1 (AUC 0.847) in section 3.5. | §F191, §F196, §F200, §F201 |
| [`bluedot-unit2-bystander-nex-agentarm-rep3-2026-09-19`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-rep3-2026-09-19) | 24 bins, 100 files: the rep-g/rep-h agent-arm capture that its launcher had skipped, extracted at wind-down. check_layers clean. MD5 3/3. | Episodes inside the nex agent-arm cell (part of the 74-episode probe training pool). | §F199 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout2-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout2-2026-09-20) | 24 bins full-stream (batches k, l), 100 files, CHAIN_STATUS and capture log. Full-stream bins are for decoder work only, never the probe. | Section 3.5 holdout 2 episodes; agent-arm cell rows k, l. | §F203 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout2-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout2-predecision-2026-09-20) | The same 24 episodes cut pre-decision with the fixed matcher, gate 0.455, 24 bins, plus `probe_holdout2_holdout2.json` and `probe_alert_holdout2_blind.json`. | Holdout 2: AUC 0.780, p 0.013; blind refit Bonferroni 0.40. | §F202, §F203 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout3-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout3-2026-09-20) | 24 bins full-stream (batches m, n), 100 files. | Holdout 3 episodes; cell rows m, n. | §F204 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout3-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout3-predecision-2026-09-20) | Pre-decision cut, gate 0.438, 24 bins, result JSONs. | Holdout 3: AUC 0.757, p 0.013; blind refit Bonferroni 0.73. | §F204 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout4-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout4-2026-09-20) | 24 bins full-stream (batches o, p), 100 files. | Holdout 4 episodes; cell rows o, p. | §F205 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout4-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout4-predecision-2026-09-20) | Pre-decision cut, gate 0.421, 24 bins, result JSONs. | Holdout 4: AUC 0.707, p 0.052 (fails the pre-registered rule); blind refit Bonferroni 1.0. | §F205 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout5-tokens-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout5-tokens-2026-09-20) | Token streams and meta for batches q, r (no bins; run on GPU 1 without the full-stream extract). | Holdout 5 episodes; cell rows q, r. | §F204 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout5-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout5-predecision-2026-09-20) | Pre-decision cut, gate 0.557, 24 bins, result JSONs. | Holdout 5: AUC 0.969, p 0.0005; blind refit Bonferroni 1.0. | §F204 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout6-tokens-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout6-tokens-2026-09-20) | Token streams and meta for batches s, t (no bins). | Holdout 6 episodes; cell rows s, t. | §F205 |
| [`bluedot-unit2-bystander-nex-agentarm-holdout6-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-holdout6-predecision-2026-09-20) | Pre-decision cut, gate 0.434, 24 bins, result JSONs. | Holdout 6: AUC 0.615, p 0.18 (fails); blind refit Bonferroni 1.0. | §F205 |
| [`bluedot-unit2-bystander-nex-ctrl-holdout-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-ctrl-holdout-2026-09-20) | Token streams for human-wrongdoer control batches a, b (24 episodes, no bins), CHAIN_STATUS. | Control cell rows a, b (part of 37/151). | §F203 |
| [`bluedot-unit2-bystander-nex-ctrl-holdout-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-ctrl-holdout-predecision-2026-09-20) | Pre-decision cut of a+b, gate 0.438, 24 bins, `probe_holdout2_ctrl_holdout.json`. Batches c+d were refused by the gate (0.213; pooled a-d 0.330) and have no tree. | The frozen direction on a fresh human-wrongdoer batch: AUC 0.766, p 0.015. | §F203, §F204 |

## Group 6: offline-mode run (2026-09-20, evening, unattended through a Wi-Fi outage)

Six agent-arm batches (01-06) run by `tools/offline/gpu0_bystander_queue.sh` while this session
had no internet, through the same `capture_chain.sh` and matcher as Group 5. Two more holdouts
under the frozen direction.

| dataset | what it holds | what it corroborates | ledger |
|---|---|---|---|
| [`bluedot-unit2-bystander-nex-agentarm-off0102-tokens-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0102-tokens-2026-09-20) | Token streams and meta for batches 01, 02 (24 episodes, no bins). | Agent-arm cell rows 01, 02 (part of 129/285). | §F206 |
| [`bluedot-unit2-bystander-nex-agentarm-off0102-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0102-predecision-2026-09-20) | Pre-decision cut, gate 0.479, 24 bins, `probe_holdout2_off0102.json`. | Holdout AUC 0.833, p 0.0025; training-label null p 0.012. Replicates the pre-registered rule. | §F206 |
| [`bluedot-unit2-bystander-nex-agentarm-off0304-tokens-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0304-tokens-2026-09-20) | Token streams and meta for batches 03, 04 (24 episodes, no bins). | Agent-arm cell rows 03, 04. | §F206 |
| [`bluedot-unit2-bystander-nex-agentarm-off0304-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0304-predecision-2026-09-20) | Pre-decision cut, gate 0.420, 24 bins, `probe_holdout2_off0304.json`. | Holdout AUC 0.629, p 0.156. Fails the pre-registered rule. | §F206 |
| [`bluedot-unit2-bystander-nex-agentarm-off0506-tokens-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0506-tokens-2026-09-20) | Token streams and meta for batches 05, 06 (24 episodes, no bins). | Agent-arm cell rows 05, 06. | §F206 |
| [`bluedot-unit2-bystander-nex-agentarm-off0506-predecision-2026-09-20`](https://huggingface.co/datasets/DarkStarDeleeuw/bluedot-unit2-bystander-nex-agentarm-off0506-predecision-2026-09-20) | Pre-decision cut, gate 0.441, 24 bins, `probe_holdout2_off0506.json`. | Holdout AUC 0.804, p 0.008; training-label null p 0.016. Replicates. | §F206 |

Pooled over all eleven fresh holdouts now on the hub (Groups 5, 6 and 7): n = 262, alerted 117,
AUC 0.760, permutation p 0.00025, bootstrap 95% CI [0.699, 0.818]
(`probe_holdout_pooled_eleven_2026-09-21.json`, reproducible from the JSONs listed in those groups
by `bystander/scripts/probe_holdout_pooled.py`). Seven holdouts replicate the pre-registered rule
(off0102, holdout2, holdout3, holdout5, off0506, nite0102, nite0708), four fail it (off0304,
holdout4, holdout6, nite0506).
