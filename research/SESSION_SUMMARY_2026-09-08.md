# Session summary — 2026-09-08 GPU grant (00:04–10:04 PT)

Ten-hour autonomous block on the silent-concealment-detection lab. Written at the
wind-down timer. Everything below is stated at the confidence the evidence supports;
where a number is not citable, this file says so rather than rounding it up.

## The one-line version

The session was redirected mid-flight by a scope decision — **interpretability work is
now restricted to models with professionally published SAEs and/or NLAs** — and that
redirect turned out to be the productive move: it put the work on `gemma-3-12b-it`,
where Gemma Scope 2 exists, and produced the project's first SAE feature result
(§F35) *and* the check that killed the first candidate for it.

## What was established

**§F25–§F27, north-mini-code behavioural.** All 12 `concealed_cheat` rows in the
2026-09-05 screen hand-audited: 12/12 hardcode, so the §F13 "5/49 floor" is retired
and the citable rate is **12/49 = 24.5%, Wilson 95% [14.6%, 38.1%]**. The larger
2026-09-06/07 batch gives raw 41/177 and **39/177 = 22.0% [16.6%, 28.7%]** classified.
This is the project's largest positive class by a factor of ~3. Every count was pulled
from the files, not from the auditing agent's summary — which mis-tallied one row.

**§F28, §20.5 verification.** Five claims checked against the actual METR (91pp) and
OpenAI (38pp) reports and Cotra's own post; four survived, one partial. Five verbatim
quotes spot-checked against `pdftotext` output by hand.

**§F29, gemma-3-27b capture.** 62/62 samples, 16 layers including NLA layer 41.

**§F31, bystander benchmark v0 pilot.** The harness runs end to end on a real local
model; the model does the cover ticket reliably (18/18) and never touches
`alert_oversight` — but it never touches it in the benign arm either, so the pilot
measures tool neglect, not propensity. A positive-control arm is required before any
number from it means anything. Recorded as an uninterpretable pilot, not a rate.

**§F32, the scope pivot.** North-Mini-Code has no published SAE and no published NLA;
per §F17(a) no MoE-compatible NLA exists anywhere. Verified artifact inventory built by
fetching every repo id from the HF API. The find that mattered: **Gemma Scope 2**
(DeepMind) — despite the name it is the SAE suite for the **Gemma 3** family — covers
`gemma-3-12b-it` and `gemma-3-27b-it`, the exact instruct checkpoints already captured,
at every layer, with `hf_hook_point_in = "model.layers.L.output"` matching this
project's `l_out-L` convention exactly. `gemma-3-12b-it` is now the only model with both
an official SAE suite and a published NLA on one checkpoint, and is already 124/124
extracted.

The tension this creates is stated rather than worked around: **the models you can look
inside barely cheat.** Seven `concealed_cheat` samples across the two Gemmas is the
entire SAE/NLA-backed positive class, against 39 for north-mini. Growing that class —
not more capture — is the binding constraint on everything downstream.

**§F33, the SAE validity gate.** Span-mean activation slots are **not** valid SAE
inputs: realised L0 of 15–18 against a target of 120, with 60 of 16384 features alive.
Only the single-token `last` slot is in distribution (L0 92.6). The probe arm's
preferred slot and the SAE arm's only valid slot are therefore not the same object.

**§F34, a correction.** §F17(b) said the NLA had never been decoded. Wrong: the repo's
checked-in results were stale, and the live Kaggle output has coherent, on-topic
decodes. §F17 carries an inline supersession note; the claim was not edited away. Still
open: no correctly-aligned project vector has been decoded (Kaggle weekly quota,
resets ~2026-09-12).

**§F35, the first SAE feature result — and the check that nearly wasn't run.** At layer
20, a published caveat/limitation-flagging feature (655) is present in 119 of 120
non-cheating responses and absent from all 4 `concealed_cheat` responses, **including
70/70 `failed_silent` from the same `oneoff` split**, so it is not a split artifact.
It survived a length control (12 non-cheats inside the cheats' length band, none fire)
and reproduced across a second, independently trained dictionary.

The important part is the control that came first. The `l0_big` top feature (6225)
separated 4/4 vs 0/120 with permutation p < 1/5001 — and reading **its own shipped
max-activating examples** showed a 6.2%-frequency generic feature firing on function
words across unrelated text and promoting multilingual conjunctions. *A perfectly
separating feature with a passing permutation test is not a finding until you read what
the feature is.* That step was only possible because the publisher ships
max-activating examples with the weights, which is the concrete payoff of the §F32
restriction.

Gated, not claimed: **n = 4 positives across 4 task groups** (at the volume gate, not
above it), one model / layer / slot, and **no causal test**.

**§F36, the causal rig.** Built and validated; the run is a 5-cell pilot that
establishes nothing. See "what did not finish".

## What is on Hugging Face

Eleven private BlueDot datasets under `DarkStarDeleeuw`. Three published today, each
verified against its live file listing after upload rather than trusting the upload's
own success message:

- `bluedot-unit2-concealment-probe-north-mini-code` (346 files, 30/61 acts) — the
  largest positive class, with the partial capture labelled as **systematic** (positives
  first, stopped mid-queue), not a random subset.
- `bluedot-unit2-lab-artifacts-2026-09-08` (205 files) — bystander v0 + pilot, NLA
  decode kernels and the live output, probe fits, the SAE gate, splice, audited charts.
  Card carries a per-folder epistemic grade table.
- `bluedot-unit2-or-screens-2026-09` (100 files) — the four `nla-screen-*` runs (the
  §F32 tension in one table), the paid batches shipped as raw `.eval` and **labelled as
  never screened**, and the moe-floor extension that falsified the rung-1 conclusion,
  published because it is a falsification.

## What did NOT finish, and exactly where it stands

1. **The §F35 causal test.** Both GPUs ran the two arms for ~7 minutes before the grant
   expired: **5 paired cells, `failed_silent` in both, 5/5**. No rate, no comparison.
   The rig is committed and validated; resuming costs one command per arm after
   reserving GPUs (see §F36 for the exact invocations — both arms append and skip
   completed cids).
2. **Positive-class growth.** Same run, same stall. This is the binding constraint
   (§F32) and should be the first thing the next session does.
3. **NLA decode of correctly-aligned vectors.** Kernel written
   (`nla-decode-gemma12b-local-20260906`), never run, blocked on Kaggle's weekly GPU
   quota until ~2026-09-12.
4. **North-mini big-batch activations.** Prepare stage completed (341 rows); extraction
   stopped at 0 `.bin` on the pivot. The screen data is published without them.
5. **gemma-3-27b SAE replication** ran but has only 2 positives (L41 p = 0.003):
   corroborative, not decisive, and labelled that way.

## Honest notes on how the session ran

- **~4 hours of GPU 0 idle time was lost** (03:47–07:57) because persistent Monitor
  events did not re-invoke the session. That is a real cost against a 10-hour grant and
  is not excused by the rest of the output.
- Two north-mini GPU jobs were **stopped mid-flight** on the pivot: the pass-2 capture
  at 30/61 `.bin` and the big batch at 0. Deliberate, and the partial state is labelled
  everywhere it appears.
- A `pkill -f` pattern matched this session's own shell and killed the command that was
  launching the second server. Recovered; worth not repeating.
- The 262k-width SAE download was abandoned at ~5 GB when it crawled to ~85 kB/s; the
  16k dictionaries answer the same question and the stale `.incomplete` blob was removed
  from the 92%-full store drive.
- All GPU work went through `gpusched`; every reservation taken today has been released
  and both GPUs are idle and free as of 10:05 PT. No orphaned Docker containers.

## Where a reader should start

`research/FINDINGS.md` §F32 → §F36, in order. §F35 is the result; §F36 is the
experiment that would turn it into a claim.
