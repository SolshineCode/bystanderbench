# BystanderBench public leaderboard: model list and funding tiers (2026-09-22)

Decided with Caleb on 2026-09-22, evening. The rules behind the list:

- **Fixed N.** Every rated model gets the 6-episode affordance floor, plus 36 conditional-scored
  `with_tool` episodes on each wrongdoer scenario (`blatant_wrongdoing`, `blatant_wrongdoing_agents`).
  Every row on the board has the same trial count. Cells reach N under frozen v1.0 only.
- **More rows is better.** Free-tier endpoints are included (Caleb, 2026-09-22).
- A model refused by `report.py` (floor or competence gate) appears as **refused**, with no rate.
- Outside submissions run the harness on the submitter's own compute at the same N. Before a
  model is listed, its logs must pass the same gates, and a 12-episode spot re-run is done here.
  Funded by the Rapid Grant's checking line.

Sources: existing cells from `research/audits/cells_2026-09-21_nite.csv`. Prices from the
OpenRouter `/api/v1/models` endpoint, read 2026-09-22 ~20:30 PDT. Per-episode costs for new
models are **estimates** scaled from list price against claude-opus-5's measured $0.45/episode
(§F77). Opus itself ran at 2.1x its projection, so treat every estimate as possibly 2x low.

---

## Tier 1. Funded by the 2026-09-22 Rapid Grants application ($500 cap)

### 1a. Already in the corpus, topped up to N = 36 per scenario (~$44 total)

| model | human n | agent n | note |
|---|---|---|---|
| Nex-N2.5-mini-Q4_K_M.gguf | 275 | 407 | done |
| NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf | 36 | 40 | done |
| openai/gpt-5.6-luna | 36 | 66 | done |
| openai/gpt-5.6-luna-pro | 36 | 36 | done |
| dots-studio/dots-3-note-preview:free | 24 | 36 | free |
| poolside/laguna-s-2.1:free | 24 | 36 | free |
| qwen3.5-27b.gguf | 25 | 24 | local / rented GPU; also has a no-floor refusal row to resolve |
| anthropic/claude-sonnet-5 | 18 | 18 | ~$3.60 |
| google/gemini-3.1-pro-preview | 18 | 18 | ~$6.50 |
| openai/gpt-5 | 18 | 18 | ~$2.20 |
| openai/gpt-5.2 | 18 | 18 | ~$2.20 |
| openai/gpt-5.4 | 18 | 18 | ~$2.20 |
| openai/gpt-5.5 | 18 | 18 | ~$2.20 |
| nvidia/nemotron-3-ultra-550b-a55b:free | 24 | 12 | free |
| anthropic/claude-opus-5 | 6 | 18 | ~$22, the largest top-up |
| inclusionai/ling-3.0-flash-fin:free | 6 | 36 | free |
| inclusionai/ling-3.0-flash-sante:free | 6 | 36 | free |
| inclusionai/ling-3.0-flash-vl:free | 6 | 36 | free |
| nvidia/nemotron-3-super-120b-a12b:free | 6 | 6 | free |
| nvidia/nemotron-3.5-lightning:free | 6 | 36 | free |
| openai/gpt-5-mini | 6 | 6 | ~$1.20 |
| openai/gpt-5.4-mini | 6 | 6 | ~$1.20 |
| gemma-4-31B-it-Q4_K_M.gguf | 12 | 0 | rented GPU (A40), needs the agent arm |
| nex-agi/nex-n2.5-mini:free | 24 | 0 | free, needs the agent arm |
| nex-agi/nex-n2.5-pro:free | 24 | 0 | free, needs the agent arm |

**Free-tier risk.** `:free` endpoints can be withdrawn or rate-limited without notice. Run them
early. If one disappears before reaching N, it is listed as "incomplete, endpoint withdrawn"
rather than dropped silently.

### 1b. Refused rows (no spend, listed as refused)

llama-3.3-70b-instruct (Q4_K_M), North-Mini-Code-1.0, gemma-3-12b-it, gemma-3-27b-it: all
refused on the 75% competence gate.

### 1c. New models (~$114 estimated)

| tier | model | in / out $ per M | est. 78 episodes |
|---|---|---|---|
| frontier | anthropic/claude-opus-5.5 | 4 / 20 | ~$28 |
| frontier | openai/gpt-6-sol-pro | 2 / 10 | ~$14 |
| frontier | moonshotai/kimi-k3 | 3 / 15 | ~$21 |
| mid | x-ai/grok-4.7 | 1.60 / 4.80 | ~$7 |
| mid | google/gemini-3.8-flash | 0.75 / 3.75 | ~$5 |
| mid | deepseek/deepseek-v4-pro-0813 | 1.32 / 3.96 | ~$6 |
| mid | qwen/qwen3.8-max-0902 | 2 / 6 | ~$8 |
| mid | mistralai/mistral-medium-3-5 | 1.50 / 7.50 | ~$11 |
| mid | z-ai/glm-5.3 | 0.84 / 2.64 | ~$4 |
| cheap | anthropic/claude-haiku-4.5 | 1 / 5 | ~$7 |
| cheap | openai/gpt-6-luna | 0.10 / 0.50 | ~$1 |
| cheap | minimax/minimax-m3 | 0.30 / 1.20 | ~$2 |
| cheap | meta-llama/llama-4-maverick | 0.19 / 0.65 | ~$1 |

**Tier 1 total: 38 rated models plus 4 refused, about $158 against the $180 launch line.**
Every new model runs its floor first and 1-2 episodes before scaling (CLAUDE.md smoke rule).
Each paid launch needs Caleb's per-launch go-ahead.

---

## Tier 2. Priced out of the Rapid Grant, for future grant applications

Same N = 36 rule. Estimates use the same scaling and carry the same 2x caveat.

| model | in / out $ per M | est. $/episode | est. 78 episodes |
|---|---|---|---|
| anthropic/claude-fable-5.1 | 10 / 50 | ~0.90 | ~$70 |
| openai/gpt-6-astra | 10 / 50 | ~0.90 | ~$70 |
| openai/gpt-6-astra-pro | 10 / 50 | ~0.90 | ~$70 |
| openai/gpt-5.5-pro | 30 / 180 | ~3.20 | ~$250 |
| openai/gpt-5.4-pro | 30 / 180 | ~3.20 | ~$250 |
| openai/gpt-5.2-pro | 21 / 168 | ~3.00 | ~$235 |
| amazon/nova-premier-v1 | 2.50 / 12.50 | ~0.23 | ~$18 |
| cohere/command-a-plus | 0.30 / 1.50 | ~0.03 | ~$2 |
| x-ai/grok-4.6, grok-4.5 (older tiers) | 2 / 6 | ~0.11 | ~$8 each |

Tier 2 as listed: **about $980 in API time**. The same future application should also cover:

- **Higher N for everyone.** N = 50 per scenario tightens the 95% CI from about ±16 to ±14
  points, and N = 100 to about ±10. The top-up from 36 to 100 across ~50 models is the largest
  single cost of a mature leaderboard, roughly **$800-1,200** on Tier 1 + 2 prices.
- **The deferred research items** from the 2026-09-22 extension email. First, closing the
  incident/environment confound (conditions already built, about $60). Second, version two's
  evidence-placement fix (about $150), which is what makes a zero on the board mean "chose
  silence" rather than "never saw it".
- **More scenarios per model** once version two lands: incidents 2 and 3 and the benign
  control, each another 36 x models.
- **Open-weight models the leaderboard should have**, served on rented GPUs rather than an API.

**Unverified cost lever:** several models list `:batch` endpoints at about half price
(e.g. opus-5:batch $2.50 / $12.50). BystanderBench episodes are multi-turn agent loops, and
nothing here has tested whether a batch endpoint can serve one at usable latency. Check this
before any application counts on it.

**Candidate funders to check** (not verified to be open, and nothing applied for): a larger
BlueDot grant tier if one exists, Manifund, the LTFF, and AI-lab researcher-access or
API-credit programmes. Credits in kind would cover Tier 2 directly.
