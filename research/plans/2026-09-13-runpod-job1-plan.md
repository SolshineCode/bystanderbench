# RunPod Job 1, exact plan, for review before anything spends

Written 2026-09-13. Balance verified in the console: **$55.39**. A40 48GB listed at
**$0.49/hr** (the budget doc said $0.44, so costs below are recomputed at the real price).

## Goal

Take the §F134 pre-decision probe from **16 positives to roughly 73**. It is currently a null
(pooled AUC 0.586, p = 0.14, n = 84 with 16 alerts) and does not survive "would this have been
significant at 60?". 300 more `blatant_wrongdoing` ceiling episodes on `nex-n2.5-mini` at its
measured 19% rate gives about 57 more alerts.

**Decision rule, fixed before the run:** if the pooled-slot AUC at ~73 positives is still below
0.62 with permutation p above 0.05, the null is reportable as a null. If it crosses, §F134 gets
a dated correction and the probe becomes a finding.

## The activation question, and why I propose two passes

The standing rule (§F111) is capture at run time, because a re-run does not reproduce the same
text (§F37: same sid and seed give different output under llama.cpp).

But the project's capture path is `concealment-probe/tools/extract_resid`, a llama.cpp-based
binary, plus `capture_activations.py` which **teacher-force replays persisted text**. That
replay is not a re-run: it feeds back the exact token stream the episode produced. It is how
all 342 episodes were captured this weekend.

So the proposal is:

1. **Pod generates episodes.** Serve `Nex-N2.5-mini-Q4_K_M.gguf` with llama.cpp, run
   BystanderBench, persist the `.eval` logs. No extract_resid build needed on the pod.
2. **Download the `.eval` logs before teardown**, verify them locally, push to HF.
3. **Capture activations locally** on the idle M40s by teacher-forced replay of that text,
   through the same binary and same GGUF that produced every other capture in the corpus.

This keeps the corpus in one convention, avoids building CUDA llama.cpp on a rented box, and
means the irreplaceable artifact (the text) is what gets downloaded and published.

**The risk it accepts:** if the `.eval` logs are lost before download, the episodes are gone
and the money is wasted. Mitigated by downloading after each arm rather than at the end.

**The alternative** is building llama.cpp + extract_resid on the pod and capturing there.
Costs an hour of build time, adds a second capture convention, and still requires downloading
the `.bin` files. I do not think it is worth it, but it is the reviewer's call to disagree.

## Pod config

| | |
|---|---|
| GPU | A40 48GB, Secure Cloud, $0.49/hr |
| template | PyTorch (CUDA, python, git present) |
| container disk | 40GB |
| network volume | 100GB, for the GGUF and logs |
| ports | SSH |
| est. runtime | 8h generation |
| est. cost | **$3.92 GPU + ~$5 storage for a week** |

## Run sequence on the pod

1. `curl -L -C - --retry 8 --retry-delay 15 --retry-all-errors` the GGUF from HF. **Not**
   `hf_hub_download`: the xet path stalls silently on this project's downloads and the standing
   recipe is single-stream resumable curl.
2. Build or install llama.cpp, serve with `-np 1` and **`--reasoning-budget 0`** (§F123:
   `--reasoning off` does not stop a hybrid model thinking; one generation ran to 27,153 tokens).
3. **Confirm `n_ctx_slot = 32768` in the startup log** (§F121: `-c` is the TOTAL KV budget
   divided by `-np`, so `-c 32768 -np 4` silently gives 8192 per slot and truncates every
   episode; six hours were lost to this).
4. **Smoke: `--limit 2`, read the output**, confirm episodes complete and score, before the
   300-episode run.
5. Run in arms of 50 episodes, downloading each arm's `.eval` before starting the next.

## Teardown

**Terminate, not stop.** A stopped pod still bills the volume. Before terminating: every
`.eval` downloaded, `report.py` run locally over them to confirm they parse and produce cells,
and the HF push **verified by reading the files back from the remote**, not by trusting the
upload's exit code (`package_acts_to_hf.py`'s bin-size refusal exists because an upload once
succeeded on truncated files, §F116).

## Cost ceiling

Three jobs at the real price: 8h + 6h + 8h = 22h x $0.49 = **$10.78**, plus ~$5 storage.
Against a $55.39 balance. Job 1 alone is $3.92.
