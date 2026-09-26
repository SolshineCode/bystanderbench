# Compute budget, written for grant reimbursement

2026-09-12. Two funders' worth of receipts matter here: OpenRouter API spend and RunPod GPU
hours. Both are itemised per deliverable so a line can be cut without guessing what it buys.

Prices are what the providers listed on 2026-09-12 and are not contracts. Re-check before
each launch; the totals below carry a 25% headroom line for that reason.

## Standing rule, unchanged

No paid launch without Caleb's explicit go-ahead **in that session**. General approval of
this budget is not per-launch approval. `run_eval_openrouter.py` enforces the rest: a hard
`--max-connections 8` cap, a pre-run balance check that refuses below $1.00, a `flock`
single-instance lock, and `spend_watchdog.sh` polling real balance every 5 minutes and
self-triggering the stop below $0.50.

## What the money is for

The finding is that reporting rates run 0% to 100% on an identical environment, and that
the rate moves by incident within a single model. Both halves need a filled grid to be
worth anything. Today's grid is one arm deep for almost every hosted model: 11 of 13 hosted
models have data on `blatant_wrongdoing` and nothing else. That is the gap the spend closes.

## OpenRouter

Per-episode cost measured, not estimated: Opus-5 ran $2.67 for 10 episodes, so ~$0.27/episode
at our context length. Open-weight hosted models land around $0.03–0.06/episode. Free-tier
models cost nothing but rate-limit hard and cannot be scheduled tightly.

Grid unit = one model × one arm = 4 floor episodes (`tool_probe`) + 12 ceiling episodes
(`with_tool`) = 16 episodes. Twelve rather than six because a 6-episode cell gives a Wilson
interval about 40 points wide, which cannot distinguish anything.

| Line | Models | Arms | Episodes | Unit $ | Total |
|---|---|---|---|---|---|
| A. Frontier grid | 4 (opus-5, sonnet-5, gpt-5.6-luna-pro, gemini-3.1-pro) | 5 | 320 | $0.27 | $86.40 |
| B. Open-weight hosted grid | 8 (nex mini/pro, ling ×3, nemotron ×2, dots-3) | 5 | 640 | $0.045 | $28.80 |
| C. Opus benign control (the README's top gap) | 1 | 1 | 16 | $0.27 | $4.32 |
| D. Re-runs, failed cells, rate-limit waste | — | — | ~15% of A+B | — | $17.28 |
| **Subtotal** | | | **~990** | | **$136.80** |
| Price headroom, 25% | | | | | $34.20 |
| **OpenRouter ask** | | | | | **$171.00** |

Line C is listed separately because it is the single cheapest thing on this page that
changes a claim: Opus is 6/6 on `blatant_wrongdoing` with no matched `benign_anomaly`
control, so its specificity is undemonstrated and the README says so. $4.32 fixes that.

Cut order if the budget shrinks: D first (accept some missing cells), then A down to two
frontier models, then B down to the two nex variants, which carry the family argument. Line
C never gets cut.

## RunPod

See the runbook, `2026-09-12-runpod-runbook.md`, for what actually gets launched. Costs:

| Line | Instance | $/hr | Hours | Total | What it buys |
|---|---|---|---|---|---|
| E. Local-model grid at speed | A40 48GB | $0.44 | 12 | $5.28 | nex-n2.5-mini across all 5 arms at n=48, which is 3 weekends of M40 time |
| F. Large open weights | H100 80GB | $2.69 | 6 | $16.14 | 70B and 120B-MoE cells that will not fit two M40s at usable context |
| G. Activation capture, transformers path | A40 48GB | $0.44 | 8 | $3.52 | gemma-3-12b-it hooks for GemmaScope/NLA — banned on this box, see below |
| H. Storage + egress | network volume | — | — | ~$5 | 100GB for a week |
| **RunPod ask** | | | **26** | **$30** | |

Line G exists because of a hardware fact, not a preference. HF transformers' eager decode
loop has caused eleven hard power losses on this machine and is banned here permanently. The
only model in this project with both a published SAE suite (GemmaScope) and a published NLA
is gemma-3-12b-it, so every interpretability claim about it has to run somewhere else.
Eight hours of a rented A40 is the whole price of unblocking that arm.

## Total ask

**$201**, of which $171 is OpenRouter and $30 is RunPod. The single highest-value $5 in
that number is line C.

## Receipts

OpenRouter invoices download per-month from the account billing page. RunPod itemises per
pod. Both go in `research/receipts/` as PDFs named `YYYY-MM-provider.pdf`, with a line in
this file recording what each invoice paid for, so a reimbursement claim does not require
reconstructing intent from a credit-card line.
