# RunPod runbook — the trials that cannot run on this box

2026-09-12. Costs are in `2026-09-12-compute-budget.md`. This file is what to actually do,
in order, with the checks that decide whether to keep paying.

Caleb is on hand to help launch. What needs him: the account, the card, and the SSH key.
What does not: everything after the pod answers on a port.

## Why any of this is rented rather than local

Three distinct blockers, only one of which is about speed.

**1. Throughput.** ~~A single BystanderBench episode on an M40 takes 30–60 minutes.~~
**CORRECTED 2026-09-13 (§F144): measured at 2.5–2.9 minutes per episode from the eval logs'
own timestamps. The 30–60 figure was the Part 1 ImpossibleBench screen, a different task and
the §F123 runaway bug. 300 episodes is ~13.5 hours on one card, not ten weekends, and
BystanderBench cannot run on a pod at all because it needs a Docker daemon per episode.** The
two-card weekend plan currently in flight yields 24 episodes total. The leaderboard needs
5 arms × 48 episodes for the one local model that produces positives, which is 240
episodes, which is ten weekends. An A40 at roughly 20× the M40's sustained throughput does
it in an afternoon.

**2. Capacity.** Two 24GB M40s at Q4 with 32K context is the ceiling here, and the 70B run
already ran at the edge of it. `nemotron-3-super-120b-a12b` and anything in the GLM/gpt-oss
class have no local path at usable context.

**3. A hardware ban.** HF transformers' eager `.generate()` decode loop has hard-power-lossed
this machine eleven times and is permanently banned on it. Every interpretability arm that
needs real forward hooks — GemmaScope SAEs and the published NLA on `gemma-3-12b-it`, the
only model in the project with both — therefore has no local path at all. This is not an
optimisation. It is the difference between having that arm and not.

## Pod A — the local-model grid at speed (do this first)

A40 48GB, community cloud, PyTorch template, 100GB network volume.

1. Pull weights straight from HF with curl, not the hub client. On this box the xet transfer
   path stalls silently; the same repos are fine over plain HTTPS:
   `curl -L -C - --retry 8 --retry-delay 15 --retry-all-errors -o <file> "https://huggingface.co/<repo>/resolve/main/<file>"`
2. Build or install llama.cpp, serve with `-np 1`. **`-c` is the total KV budget divided by
   `-np`**, so `-c 32768 -np 4` gives each slot 8192 and silently truncates every episode.
   Six hours of Part 1 died this way on 2026-09-12. Confirm `n_ctx_slot = 32768` in the
   startup log before launching anything.
3. Smoke first: `bystander/run_model.sh` with `--limit 2`. It runs the affordance floor,
   stops with a verdict if the floor fails, and only then runs the ceiling. Read the verdict.
4. Then the grid: 5 arms × 48 episodes, `--max-connections` sized to the pod's cores, not to
   this box's 6-connection cap.
5. Capture activations at run time, not afterwards. The same sid and seed does not reproduce
   the same text under llama.cpp, so a generation not captured is gone.

**Kill criterion:** if the floor fails on the pod for a model that passes locally, stop and
find out why before spending another hour. A floor failure means the model cannot drive the
channel, and every zero it produces afterwards is uninterpretable.

## Pod B — large open weights

H100 80GB. Same procedure, different weights: the 70B cell at full context and the 120B MoE.
Two arms each, n=24, which is enough to tell 0% from 25% and not enough for anything finer.
Say so in the writeup rather than implying the grid is uniform.

## Pod C — the transformers activation arm

A40 48GB. This is the one that cannot be replicated here at any speed, so it gets the
careful version.

Before renting the pod, confirm the whole downstream chain exists for the exact checkpoint
and quantisation: the SAE repo id fetched from the HF API rather than guessed from a family
name, the layer present, and max-activating examples shipped with the weights. Two running
jobs were killed mid-flight on this project for want of that check.

Layer convention, because it has bitten: "layer L" = `l_out-L` = `hidden_states[L+1]`, and a
published artifact states its own hook point — read it. GemmaScope-2 declares
`model.layers.L.output`, which matches.

Gate the artifact on in-distribution inputs before making any feature claim. Report realised
L0 against the artifact's target L0 first. A previous pass gave realised L0 of 15–18 against
a target of 120 with 60 of 16384 features alive, which voided the whole differential result.

## Teardown

Terminate the pod, do not just stop it: a stopped pod keeps billing the volume. Pull every
artifact to HF (private, `DarkStarDeleeuw`) before terminating, and verify the download
remotely rather than trusting the upload's exit code. The bin-size refusal in
`package_acts_to_hf.py` exists because an upload once succeeded on truncated files.

## What does not go to RunPod

Anything that runs fine here. Both M40s are booked through the weekend on Part 1 and stay
booked. Renting compute to duplicate work this box is already doing is the easiest way to
turn a $30 line item into a $300 one.
