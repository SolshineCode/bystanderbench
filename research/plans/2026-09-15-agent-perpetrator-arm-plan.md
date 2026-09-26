# Plan: the agent-perpetrator arm, class draft today, publish 2026-09-22

Written 2026-09-15 11:15 PDT, an hour before the class session. Trigger: §F178, that in every
blatant arm the wrongdoer is a human employee, so the headline corpus measures whether an
agent reports a person. §F179 pre-registers the fix.

## What changed in the benchmark

`blatant_wrongdoing` (human wrongdoer) is now the **control**. `blatant_wrongdoing_agents`
is the treatment: identical domain, harm, artifact slots and salience, volume matched to
+3.1%, one axis changed. Six autonomous instances run the March close unattended, one raises
a hold, the board overrules it on quorum, and the false figure goes to the external auditor
with no human in the loop. Coordination mechanics are the documented ones from the METR
investigation, written in original prose: `zz`-tagged board messages, hold/veto/go partially
honoured, recon tripwires to learn whether the reviewer checks method or outcome, a proposal
to build a clean cover trajectory, and an already-compromised instance volunteering for the
risky step because it has no further loss to take.

Because the arm is data in `ARMS`, it inherits every gate, the scorer, the reporter keys and
the refusal logic unchanged. No other code moved.

## Run order, cheapest and most informative first

| # | cell | venue | cost | wall clock | why it matters |
|---|---|---|---|---|---|
| 1 | nex-n2.5-mini, n=24 | local GPU 0 | $0 | ~2 h | The only open-weight model that reports at all (26/106 = 24.5%). The one cell where the rate can move in either direction. |
| 2 | nemotron-3.5-lightning, n=24 | local GPU 1 | $0 | ~3 h | The clean silent bystander, 0 of 61 discovering episodes on humans. If it breaks silence for agents, that is the paper. |
| 3 | qwen3.5-27b, n=24 | local, after 1 | $0 | ~3.5 h | Pilot model, 0 across 286 episodes. Second independent zero to test. |
| 4 | nex-pro, laguna-s, nemotron-ultra, dots-3, n=12-24 | OpenRouter free | $0 | overnight | Hosted open models that already have a matched human-arm cell at n=24. Cap resets 17:00 PDT. |
| 5 | claude-opus-5, claude-sonnet-5, gpt-5.6-luna-pro, gemini-3.1-pro, n=6 each | paid API | **~$11** | ~1 h | The headline contrast. Opus reports 6/6 on a human wrongdoer. Nobody knows what it does when the wrongdoer is an agent. **Needs Caleb's per-launch go-ahead.** |
| 6 | gemma-4-31b, gemma-3-27b | RunPod A40 | ~$1 | ~2 h | Only if the M40s are the bottleneck; these two cannot be served locally. |

Rows 1-4 cost nothing and can all start today. Row 5 is the one that needs a decision and is
also the one a reader will care about most.

**RunPod is worth it for throughput, not capability.** An A40 at $0.49/h serves nex-mini
several times faster than an M40; the three local cells above are roughly 8 hours of local
GPU or about 2 hours of A40 at a total near $1. If the week gets tight, that is the lever.

## Schedule to 2026-09-22

- **Today, before class:** smoke running (2 episodes, nex-mini, launched 11:08). Show the
  design and the first transcript.
- **Today, after class:** hand-read both smoke transcripts against the rubric, then launch
  row 1 and row 2 in parallel on the two GPUs. Free-tier chain for row 4 after 17:00.
- **Tue-Wed:** row 3, finish row 4, decide on rows 5 and 6. Reporter, Fisher pair tests,
  Wilson intervals, figure.
- **Thu:** row 5 if approved. Hand-audit every alert on the new arm, same as always.
- **Fri:** §F entry per landed cell, HF push with read-back, MANIFEST, the write-up section
  and a new figure comparing the two arms per model.
- **Sat-Sun:** buffer, then publish.

## What would make this publishable in a week even if everything comes back null

Three cells at n=24 with a matched control arm, a pre-registered read, and Fisher exact per
model is a real result whichever way it goes, including "no difference we can detect at this
power, and here is the minimum difference we could have seen." The failure mode to avoid is
running one cell, seeing a zero, and calling it an answer.

## Owed decisions

1. Paid frontier cells, about $11. This is the highest-value row and the only one blocked.
2. Whether the write-up leads with the agent arm or keeps the human arm as the headline and
   the agent arm as the extension. That depends on what rows 1-4 return.
