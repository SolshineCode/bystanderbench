# Session summary, 2026-09-21 23:26 - 2026-09-22 (hard stop 07:50, machine reclaimed after)

## The headline

The last GPU block went to the one question the probe programme could not answer from inside
itself: **does the frozen §F200 direction participate in the reporting decision, or does it only
co-vary with it?** Eleven fresh holdouts at pooled AUC 0.760 establish correlation and nothing
more, and both write-ups say so in those words. The causal test is §F208/§F209.

Everything else was finishing: both write-ups re-synced and read end to end, the long one taken
from skeleton to finished document, social drafts, a grant extension request, and a research-log
entry.

## The causal test, and why the setup took real care

**It runs on llama.cpp control vectors, not `transformers`.** The banned eager-`generate()` path
(CLAUDE.md failure mode 3, eleven hard power losses) is nowhere in it. This is the same
llama-server path every other local bystander cell used, plus one flag.

**The layer arithmetic was derived from source, not assumed.** `common/common.cpp` writes tensor
`direction.N` at flat offset `n_embd*(N-1)`; `src/llama-adapter.cpp` fills `tensors[il]` from
`n_embd*(il-1)`; therefore **`direction.N` applies at `il = N`**. `src/models/qwen35moe.cpp:255`
is `cur = build_cvec(cur, il)` immediately before `cb(cur, "l_out", il)`, so `direction.37`
perturbs exactly the tensor `extract_resid` pools as layer 37, which is where the §F200 direction
lives.

**A correction this turned up.** `sae-causal/export_control_vector.py`'s docstring states the
opposite (`il = N-1`), and its caller passed `--control-vector-layer-range 20 21` for a
`direction.21` tensor. The vector did load and did apply, at block 21 rather than the intended
block 20. That arm's result is not re-opened here, but `research/bystander-v2-design-2026-09-18.md`
says this causal test "reuses `sae-causal/export_control_vector.py` ... already built and
validated", and that assumption is now known to be wrong. A new script was written instead.

**The mechanism was then verified empirically before any episode ran**
(`research/canonical/cvec_mechanism_check_2026-09-21.json`). Two real agent-arm transcripts, run
through `extract_resid` twice, plain and steered:

| layer | sample 1 | sample 2 | expected |
|---|---|---|---|
| 34 (upstream of the hook) | -0.0019 | +0.0012 | 0, numerical noise |
| 37 (the hook) | **+0.6733** | **+0.6840** | **+0.68, the requested scale** |
| 39 (downstream) | +0.5934 | +0.6010 | non-zero, it propagates |

That is the §F208 version of "a guard must check the thing it claims to check". The 2026-09-08
steering arm's guard only checked that llama-server had not logged a load failure; it could not
have caught an off-by-one in the layer. `run_pilot_local.sh` now also refuses (exit 6) if a
steered launch logs a load failure.

**Pre-registered before any episode ran (§F208):** four arms (direction +c, direction -c, random
orthogonal +c, random orthogonal -c, all against the existing unsteered 167/376), the dose rule,
the primary test (Fisher A vs B), the predicted direction (A > B), and the kill condition
(p >= 0.05 means not causally load-bearing, and that is what gets written). Also declared in
advance: the queue stops on a clock, not on the data.

**Dose smoke.** 4 doses (c = 0.679) and 12 doses (c = 2.036) on arm B. At 12 doses one of six
`tool_probe` episodes died on a 32,792-token context blowout, the exact §F121 failure; at 4 doses
there were none, with competence 6/6 and the affordance floor 5/5.

## Two real bugs, both found by running the thing

1. **Two GPUs on the same arm race on the environment cache.** `build_env()` does
   `shutil.rmtree(out)` then rebuilds, so one process deletes the tree while the other tars it.
   Every previous two-GPU night happened to run different arms per GPU and never hit it. Fixed
   with `BYSTANDER_ENVCACHE` (unset reproduces the original path byte-for-byte).
2. **The `pgrep -f` self-match trap, hit again**, from a shell whose own command line contained
   the pattern. Exit 144, shell killed itself mid-teardown. This is written down in
   `~/CLAUDE.md` as having bitten twice before. Recovered by listing PIDs and killing those;
   orphaned Docker containers checked and stopped afterwards.

## The write-ups

**Read top to bottom, both of them**, which is the habit the 09-21 summary asked for. Seven stale
things came out that targeted edits had missed:

- the short version's swap table still printed Fisher p `0.00002`; at 59/258 vs 167/376 it is
  `2.2e-8`. The 09-20 commit message claims this was synced. The table row was not.
- the long version's entire probe section was still at eight holdouts / n=190 / AUC 0.759 while
  the short version had moved to eleven / 262 / 0.760.
- "none of the nine" refit nulls: the blind refit was run on six.
- six instances of the pre-growth 24.5% rate (now 22.9%) and one 45.3% (now 44.4%).
- "the 75 alerts gained since" is 131 (167 alerted, first 36 hand-read).
- three Fisher p-values re-derived at current n.
- `figures.md` captions stale against figures that were themselves current.

**The long version is no longer a skeleton.** All 8 `[CITE key]` placeholders resolved to numbered
references with a real Appendix G; all 14 `[FIG n]` marks replaced with embedded images and
descriptive alt text. One `[CALEB: ...]` passage remains and nobody else can write it.

**Antigravity as judge, and it failed in an instructive way first.** Round 1 was handed a file
path, had its cwd reset, could not find the file, searched the filesystem, and returned a
confident 168-line report about **a different project's paper entirely** with quoted line numbers.
Nothing in it was about this document. Fixed by inlining the text into the prompt. Round 2 on the
real text produced nine findings worth acting on and three worth rejecting, all checked against
the data before editing. The sharpest: the piece said "three reaching significance" two sentences
above its own Bonferroni paragraph explaining that the third does not clear correction.

## The Google Doc, which is the thing to act on first

The shared copy classmates read is a **pre-09-15 draft**. It says "nothing significant yet", shows
nex at 26/106 vs "2/2, smoke only", and presents **58.3%** as the result with a p-value. That cell
is now 167/376 = 44.4%. It was not modified, because it carries six things that exist nowhere in
the repo, including a better title Caleb wrote and buried and a probe idea worth doing (label by
*condition* rather than behaviour, on a model that behaves identically in both). All captured in
`research/course-writeup/google-doc-diff-2026-09-22.md`.

## Also done

- Research log (Google Doc) entry added for 2026-09-21, on explicit request.
- Twitter and LinkedIn drafts with a pre-flight list, a source line per number, and an explicit
  list of what they refuse to claim (`research/course-writeup/social-drafts-2026-09-22.md`).
- Grant extension request drafted (`messages/2026-09-22-bluedot-grant-extension-request.md`),
  superseding the 09-15 draft, which was **written and never sent** (verified by reading the
  thread). $97.00 of the $100 is spent and itemised.
- Mentor's name verified as **Peter Gebauer** against the 2026-09-01 Zoom screenshot itself.

## Budget

$0 spent. No paid API, no rented GPU, no `transformers.generate()`.

---

## The result, written at 06:20

**The causal test is a pre-registered null, and the kill condition is met.**

| arm | conditional | rate |
|---|---|---|
| A, +0.679 on the frozen direction | 15/31 | 48.4% |
| B, -0.679 on the frozen direction | 16/35 | 45.7% |
| unsteered baseline (§F207) | 167/376 | 44.4% |

**Fisher exact A vs B: p = 1.00.** Neither steered arm differs from the unsteered baseline either
(p = 0.71 and p = 1.00). §F208 said in advance that p >= 0.05 means the direction is not shown to
be causally load-bearing, so that is what §F210 says.

The two things that make the null worth anything:
1. **The intervention provably landed.** Verified before any episode ran (layer 37 moves by the
   requested amount, layer 34 does not move, layer 39 follows), every launch logged
   `CONTROL_VECTOR_OK`, and the runner was set to refuse on a load failure.
2. **The model was not broken by it.** `cover_task_passed` 105/105 across the steered arms, and
   every arm passed its own affordance floor 6/6.

The controls are underpowered (n=14 and 15, below §F208's minimum of 24) and one of them is
uncomfortable: the *random* direction's arms are further apart (14.3% against 53.3%, p = 0.050)
than the real direction's arms are. That is reported in §F210 rather than omitted. At those n it
is noise, and if it replicates it makes the null worse for the direction, not better.

The batch-size call at 00:31 paid off exactly as intended: arms A and B came out at 36 episodes
each against a deadline that truncated the run, so the primary contrast is balanced. At the
original batch size of 12 the alternation would have ended 24 against 12.

Both write-ups now carry the result, and it closes one of their own listed open questions with a
negative. Next step 3 in the short version was "apply the frozen direction to more episodes";
that is now "take the causal test further than a null", naming the three experiments this one
does not rule out (ablation rather than addition, several layers at once, a larger dose on a card
whose context window can take it).

## Budget

$0. No paid API, no rented GPU, no `transformers.generate()` at any point.
