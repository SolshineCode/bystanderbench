# Session commitments — 2026-09-08 small group (Peter's cohort)

Committed to before the next session (one week out).

1. Draft of the paper, shareable for feedback (Peter's #1 ask in this session). Covers
   motivation, method, results so far, limitations, and next steps.
2. Finish the SAE causal test (`sae-causal/`). The rig already exists and is validated
   end to end (§F36); it just needs the run completed past the 5-cell pilot.
3. Broader empirical push to strengthen the draft:
   - Run Qwen3.5-27b at real N (~150-300 samples) on OpenRouter to settle the grant's
     named-model question (currently 0/33, underpowered).
   - Capture activations on the highest-rate uncaptured cheaters (north-mini-code,
     nemotron-3.5-lightning) to start feeding the pooled cross-model probe (§18).
4. Complete BystanderBench construction, including the positive-control arm, so the
   pilot (zero alerts in every arm, including the benign control) has an interpretable
   result to cite.
