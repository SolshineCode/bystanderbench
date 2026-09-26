# Session summary, 2026-09-19 23:53 to 2026-09-20 08:30 PDT (overnight GPU grant, deep-work)

## The headline, stated carefully

The §F200 probe direction, fit once on 74 episodes and never refit, was tested on five fresh
agent-arm holdout batches tonight (118 episodes) under a rule written down before any of them
existed (§F202). Three batches replicate individually (AUC 0.780, 0.757, 0.969), two do not
(0.707 at p 0.052, 0.615 at p 0.18). Pooled, the direction scores **AUC 0.753, p 0.0002,
CI [0.66, 0.83]** on episodes it never saw. It also separates alerting from silent on a fresh
human-perpetrator batch (0.766, p 0.015). A direction re-fit from each holdout's own 24
episodes is null on all six holdouts that now exist; both tests are on the record every time.

The species effect replicated on 168 new episodes and now stands at 45.2% vs 24.5% over the
full corpus (Fisher p 5e-5).

## What ran

- **GPU 0 (23:58-08:17)**: agent-arm batches k, l, m, n, o, p (6 x 12), each pair followed by
  capture, pre-decision cut, extraction and a full-stream extraction. Trees holdout2/3/4.
- **GPU 1 (23:58-08:04)**: human-arm control batches a, b, c, d, then agent-arm q, r, s, t.
  Trees ctrl_holdout (a+b), holdout5, holdout6. The c+d control cut was refused by the position
  gate (0.213); a pooled a-d cut was refused too (0.330); no override used.
- Every tree went through the new `bystander/capture_chain.sh`, which refuses to say CHAIN_OK
  without bins == manifest rows and a clean check_layers. Seven CHAIN_OK, one CHAIN_FAIL
  (the refused cut), zero missing extractions.
- 12 HF datasets pushed under `DarkStarDeleeuw`, every one MD5 read back. MANIFEST rows added.
- Ledger: §F202 (pre-registration, 00:10), §F203, §F204, §F205. Commits d06d998 .. this one.
- $0 spent. No paid API. No transformers generate().

## Fixed before any new data existed

- The quantile matcher's batch-rank defect (owed by the 09-19 summary): silents were ranked
  globally while indexing a per-batch donor pool. Fixed, verified on the old holdout (per-batch
  position AUC 0.63/0.43 -> 0.40/0.49), old trees left untouched, `--quantile-rank global`
  reproduces them.
- The direction is a sha-checked file (`research/canonical/probe_direction_F200.npz`); the test
  script refuses on sha mismatch or cid overlap with training.

## What went wrong, plainly

- Two ledger timestamps were written from memory instead of `date` (§F202 "00:05", §F203
  "03:40"); both corrected additively in the next entry. Read the clock before writing a time.
- The W40 header and the CLAUDE.md note assumed GPU 1 at 0.5x; it ran nex at GPU 0's speed all
  night. The time guards were conservative rather than wrong, and W42 filled the gap, but the
  plan should have been sized from a measurement of this job shape.
- Holdout 5's 0.969 sits far above every other batch and its position gate (0.557) is the
  highest of the six trees. It is reported as measured; the pooled number is the one to carry.

## Owed to the day

1. Course write-up re-sync to §F172-§F205 (it still predates the agent-perpetrator arm).
2. Matcher: nearest-boundary snap with a tolerance, refuse rather than take a late boundary
   (the human-arm transcript shape that broke c+d).
3. Memory note on GPU 1 speed for nex-class llama.cpp jobs.
4. The other session's owed items not touched tonight: none of §F172-§F201's open threads
   other than the second holdout and the matcher fix were worked.
