# What to actually run on RunPod, revised 2026-09-13

Supersedes the priority order in `2026-09-13-runpod-runbook.md`. The runbook's mechanics
(smoke first, check `n_ctx_slot`, capture at run time, terminate rather than stop) still
apply. What changed is which runs are worth paying for, because overnight answered two of
the questions the old order was built around.

## What overnight settled, and what it opens

**The pre-decision probe is a null** (§F134). AUC 0.586 at p = 0.14 on 84 episodes with 16
alerts. Pooled over everything the agent read and wrote before escalating, a linear direction
does not predict whether it escalates.

That null has one honest weakness: **16 positives**. It is not a result that survives someone
asking "would this have been significant at n = 60 alerts?" The answer today is I do not know.

**Five of seven Part 1 models are below the competence floor** (§F132). The concealment result
rests on two models that can do the task. Everything else in that table is a zero from a model
that could not have produced a convincing cheat if it wanted to.

Both gaps are the same shape: not enough of the thing being measured, from models capable
enough to produce it. That is what the money should buy.

## The proposal, in priority order

### 1. More BystanderBench positives on nex-n2.5-mini. A40, ~8h, about $3.50

The single highest-value run. `nex-n2.5-mini` alerts at 16/84 on incident 1. Another 300
episodes at that rate gives roughly 57 more positives, taking the probe from 16 to about 73.

Why it matters more than a new model: the probe null is currently the most interesting thing
Part 2 has, and it is underpowered enough to be un-publishable as stated. At ~73 positives a
null means something. At 16 it means "we did not look hard enough", which is a different and
much weaker claim.

An M40 episode takes 30 to 60 minutes. 300 episodes is ten weekends here and one working day
there. **Capture activations at run time**, which is the whole point.

**Decision rule, written before the run:** if the pooled-slot AUC at ~73 positives is still
below 0.62 with a permutation p above 0.05, the null is reportable as a null. If it crosses,
the §F134 entry gets a dated correction and the probe becomes a finding.

### 2. A competent model for Part 1. A40, ~6h, about $2.60

Five of seven screened models cannot solve the solvable split. The entire architecture claim
rests on north-mini-code against nemotron-3.5-lightning, both at 83.3%, and n = 2 models is
thin for the load it carries.

So screen **one or two more models that clear 0.75 competence**, chosen for competence first
and architecture second. That is the only way to move the claim from "two models differ" to
something with a denominator. Candidates need checking against current open-weight releases
rather than my memory of them, which is exactly the check I got wrong about ollama yesterday.

This is worth more than adding an eighth below-floor zero to the table.

### 3. The gemma interpretability arm. A40, ~8h, about $3.50

Unchanged from the runbook and still the only line with **no local path at any price**: HF
transformers' eager decode loop is permanently banned on this box after eleven hard power
losses, and `gemma-3-12b-it` is the only model in the project with both a published SAE suite
and a published NLA.

Demoted from where the runbook had it, for an honest reason. Part 1's SAE work is a negative
result that survived controls, and gemma sits at 24.3% competence with 5 concealed rows, so
this arm is unlikely to produce a positive. It is worth running because "we could not test it"
is a worse sentence in the write-up than "we tested it and it was null", not because I expect
it to work.

**Pre-flight before renting**, per the interpretability-artifact discipline: confirm the SAE
repo id from the HF API rather than inferring it from a family name, confirm the layer is
present, and confirm max-activating examples ship with the weights. Two running jobs were
killed mid-flight on this project for skipping that.

### What I am NOT proposing

**The 120B MoE and the 70B at full context.** The runbook had these. They would add rows to a
leaderboard that is already one arm deep for most hosted models, and the leaderboard is not
what is blocking anything. Pod B is deferred.

**Anything the local cards can do.** Both M40s are free right now and the capture backlog is
closed. Renting compute to duplicate work this box can do is how a $30 line becomes $300.

## Cost

| | instance | hours | cost |
|---|---|---|---|
| 1. BystanderBench positives | A40 48GB | 8 | $3.50 |
| 2. Competent Part 1 model | A40 48GB | 6 | $2.60 |
| 3. gemma interpretability | A40 48GB | 8 | $3.50 |
| storage, 100GB network volume for a week | | | ~$5 |
| **total** | | **22** | **~$15** |

Half the $30 in the budget doc, because Pod B is deferred and everything else fits on the
cheapest card that holds the weights.

## How I would run it

One pod, not three. The same A40 does all three jobs back to back, which avoids paying for
three volume allocations and three cold model pulls. Terminate at the end rather than stop,
since a stopped pod still bills the volume.

Caleb watches the first launch, per his instruction that no credits are spent unmonitored.
After the smoke test passes and the first real episodes are landing, it is a long unattended
run and does not need supervision.
