# Session summary, overnight 2026-09-17 -> 2026-09-18

## The result

**The perpetrator-species effect is no longer one model.** Three significant within-model pairs,
two labs, open and closed weights, for $0.572 of paid API.

| model | human wrongdoer | agent wrongdoer | Fisher p |
|---|---|---|---|
| gpt-5.6-luna | 3/36 = 8.3% | 30/66 = 45.5% | 0.0001 |
| nex-n2.5-mini (local) | 26/106 = 24.5% | 24/47 = 51.1% | 0.0025 |
| gpt-5.6-luna-pro | 0/36 | 7/36 = 19.4% | 0.0113 |

At n=6 and n=18 both GPT-5.6 cells read as noise (p 0.18 and 0.23). The money was spent
specifically because those sizes cannot see a true 0-vs-17% gap, which is §F166's lesson pointed
forwards. §F192 has the detail, including a count anomaly (66 episodes where 36 were planned)
that was chased to its cause and verified as distinct generations with zero overlap.

## What else landed since yesterday

- **§F190**: both blind raters returned packet 1. Neither described the target, SAE feature 655,
  in terms of hedging or caveats, so §F35's interpretation is **withdrawn** per the rule written
  before any answers existed. The decoy-confabulation check passed in the good direction: decoys
  drew *higher* confidence than the target.
- **§F191**: qwen3.5 (0/16 -> 0/11) and lightning at n=24 (0/22 -> 0/20) both stay at zero.
- **§F189**: the agent-arm probe AUCs of 0.875 and 0.921 are **withdrawn**. §F125's cut-fraction
  control fails on that tree: alerting episodes cut at 78.8% of transcript, silent at 5.3%.
- **Grant ledger** now exists at `research/canonical/grant_spend.csv`, 9 lines, estimate vs
  confirmed marked per row.

## What went wrong overnight, plainly

**Both GPUs sat reserved and idle for eight hours.** I reserved GPU 0 and GPU 1 at 00:12 for the
probe re-cut and nex volume, then never launched either job. No GPU work ran overnight. The
reservations blocked nobody else in practice but the work did not happen, and the probe re-fit is
exactly what would have used it. Reservations released at wind-down.

**The Kaggle NLA decode errored again**, this time producing no output files at all, so the API
returns nothing to diagnose from. It failed before writing anything. Cause unknown; the log is
readable only from the Kaggle web UI. The previous failure was a missing `bitsandbytes`, fixed;
this is a different failure.

## Owed to the day

1. **Probe re-cut and refit.** The `turnfrac` matching fix and the enforcing gate are written and
   committed but have never been run. The gate needs its negative test: confirm it refuses the
   old `turnrank` config before trusting it to pass anything.
2. **Kaggle NLA**: read the kernel log in the browser and fix. A 27B AV in 4-bit on a T4 is tight,
   so out-of-memory is a candidate, but that is a hypothesis and not a diagnosis.
3. **RunPod billing read** for the two estimated charges ($0.93 and $1.73). Until then $9.66 of
   the ledger is estimate rather than confirmed.
4. **Which OpenRouter top-ups the grant paid for.** The account holds $19.674 loaded. The ledger
   assumes all API spend is grant-funded; if any was Caleb's own money he is under-claiming.
5. **Packet 3** from rater 2, and packet 2 from rater 1 if she had time. Packet 2 is the one that
   yields the kappa on the concealed/disclosed taxonomy.

## Budget

$86.75 of $100 spent, **$13.25 of grant line unspent**. $19.674 sits loaded on OpenRouter after
the refill. The three-model result cost $0.572, which is the number worth quoting in an extension
request: the benchmark's headline finding was bought for well under a dollar of API time.
