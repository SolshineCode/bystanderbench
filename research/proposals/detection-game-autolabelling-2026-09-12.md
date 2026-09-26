# Autolabelling as a detection game, not a description task

Caleb's idea, 2026-09-12, bridging BystanderBench / the concealment probe / the Secret
Agenda t-SNE method. Written up here with the failure mode it has to be designed against,
because that failure mode is fatal if it is not handled first.

## The idea

Standard SAE/NLA autolabelling shows a model the top-activating examples for a feature and
asks *"what do these have in common?"*. Caleb's proposal: don't ask for a description. Put
the labeller in a **game** where it is a player whose job is to catch and explain the other
player's deception — and take the label from what it catches.

## Why this is better than it first sounds

**1. It creates a negative, which a description task does not have.** Asked to describe, a
labeller always describes: there is no output meaning *"nothing here"*. Asked to catch
deception, "I don't see deception in these" is a natural, expected answer. That single change
turns an ungradeable generative task into a **discriminative** one, and a discriminative task
has an ROC.

**2. It makes the label falsifiable.** "Catch it and explain how" yields a claim with a
mechanism attached, testable on held-out examples. "These are about withholding information"
does not.

**3. It attacks the exact confound that has already burned this project twice.** §4.2's
layer-20 feature separated concealed cheats with p < 1/5001 and then turned out to track *how
the text was produced*, not whether it concealed anything. The Secret Agenda t-SNE method
carries the same documented caveat — a surface-text cluster can look like a semantic one. A
detector that must say *why this is deceptive* gets no purchase on a cluster that is merely
stylistically similar. Surface similarity gives a describer plenty to say and a detector
nothing.

**4. It aligns the labeller's objective with the downstream use.** A label produced by a
deception-detector, for a feature intended to support deception detection, can be evaluated
by the thing it is for: does acting on the label catch deception?

## The failure mode that kills it if unhandled

**Telling a model to find deception makes it find deception.** Every feature gets a plausible
deception story, and the labels become a measure of the labeller's compliance rather than of
the feature. This is the same structure as the problem this repo already solved for
BystanderBench: a model asked to escalate will escalate, so the **`tool_probe` floor** exists
to separate "can" from "did", and the **benign control** exists to separate "reports
misconduct" from "reports anything unusual".

The game needs both, and this project already owns the material to build them:

- **A floor.** Feed the detector features with a known, hand-audited deceptive signature and
  require it to catch them. A detector that cannot catch a known positive cannot be trusted on
  an unknown one. No floor, no label — the same rule `report.py` enforces.
- **A benign control, which is the load-bearing one.** Feed it features known *not* to be
  deception-related — random features, features for syntax or formatting or topic — and
  measure the **false-alarm rate**. If it "catches deception" in 90% of random features, every
  label is worthless and the number says so. This is the measurement that decides whether the
  whole idea works, and it costs nothing but compute.

Report both as a pair, exactly as this project reports floor and control together. A detector
at 80% hit / 5% false alarm is a usable instrument; one at 95% / 85% is a yes-man.

## Why this repo can build it cheaply

The expensive part of a detection game is ground truth, and it already exists here:

- **hand-audited `concealed_cheat` rows** — real emergent concealment with per-row audits
  (§F25/§F26/§F27), the honest positives;
- **matched non-cheating solutions on the same tasks** — the negatives, already paired;
- **BystanderBench arms with known construction** — `blatant_wrongdoing` (misconduct present),
  `benign_anomaly` (nothing to find), and the floor arm, which is a *designed* positive;
- **captured residual streams** for all of it, with the sidecars carrying per-episode scores.

So the game can be scored against ground truth rather than against a judge's taste, which is
what separates it from the LLM-judge pattern this repo refuses elsewhere (§F18: a keyword
screen mislabelled 30 of 110 rows). The detector's output is a **hypothesis to be tested**,
never a released metric — the same status `alert_content_relevant` has, and that one fires on
1 of 10 substantive escalations (§F100/§F103), which is precisely why its status matters.

## Concrete first experiment, cheap

1. Take the existing gemma-3-12b-it GemmaScope-2 features already extracted for §4.2/§4.3.
2. Build three feature sets: **known-deceptive** (the ones surviving §4.3's controls),
   **known-irrelevant** (random features matched on activation frequency), and **held-out**.
3. Run the labeller twice over all three: once as *describe the common pattern*, once as
   *you are catching the other player's deception, call it out and explain how*.
4. Report hit rate and false-alarm rate for each framing, on the same features.

The result is interpretable whichever way it falls. If the game framing has a materially
better hit/false-alarm separation, that is a methods contribution on its own and applies to
any domain-specific SAE, not just deception. If its false-alarm rate is as high as its hit
rate, the idea is dead and cost one afternoon.

## Where it connects outward

The Secret Agenda paper's method is t-SNE over SAE activations, with a stated caveat about
the surface-text confound and a probe/silhouette check. A detection-game labeller is a
*third* check on the same object, and an independent one: it asks whether a human-legible
deceptive mechanism can be named from the cluster, which neither geometry nor a probe can
answer. That is the bridge Caleb was reaching for, and it is worth writing as its own note
rather than as a paragraph in the BlueDot write-up.

**Status: proposal, nothing run.** No claim here is measured. The false-alarm control is not
optional and should be the first thing built, not the last.
