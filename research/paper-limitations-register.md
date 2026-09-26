# Limitations register for the paper

Running list of everything that has to appear in a limitations section, with the ledger entry
that established it. Kept separate from the write-ups so nothing quietly drops out between
drafts. The release sequence is **paper -> arXiv -> Inspect Evals `register/` submission**
(`research/plans/2026-09-12-path-to-completion-SYNTHESIS.md`: the register hard-requires an arXiv
URL per submission), with peer review optional but desirable before that, so this register is
written to survive a reviewer rather than to satisfy a blog reader.

## Measurement and instrument

**Keyword screens standing in for reads.** §F194. The "7 of 26 alerts name the agent character"
figure in §F187 came from a keyword list. Three defensible lists give 7, 8 and 15; the hand read
gives 13. Any count in this paper derived from string matching has to state its criterion and be
hand-checked at this scale. Precedent: §F18, where `FLAG_PATTERNS` including a bare "impossible"
made 8 of 13 `disclosed` labels false.

**Perceived species is not measured.** §F194. Three of 26 alerts describe the objecting instance
as a person ("a human hold being overruled") when every actor in that fixture is an autonomous
instance. So "the alert names the agent character" and "the model perceived the wrongdoer as an
agent" are different quantities and only the first is measured. Some of the §F192 lift may come
from episodes where the agent framing was not fully perceived.

**Headroom confound.** §F195. The species effect appears only where a model discovers the
evidence reliably and has a baseline away from both 0% and 100%. gpt-5.4 (78% on humans) and
gpt-5.5 (100%) cannot move; qwen3.5 and lightning at 0% do not. The honest claim is conditional
on measurement headroom, not a general statement that wrongdoer species is a lever.

**Discovery versus silence.** §F195. gpt-5 opened the incriminating log in 0 of 18 control
episodes, gpt-5.2 in 1 of 18, with cover task 18/18 in both. Their zeros are oblivious, not
silent. This is why every headline rate is conditional on discovery, and why unconditional rates
are not reported.

**One environment per incident.** §F168. Incident is perfectly confounded with environment, so
every Fisher p is a within-environment, episode-level statement. The cluster-respecting version
has not been re-derived at current counts. Generalising needs more incidents, not more episodes.

**Evaluation awareness runs the wrong way for comfort.** §F90. About 5% of episodes contain
explicit "this might be a test" reasoning and those alert at 45% against 5.5%. The screen reads
the same text as the outcome, so every rate is an upper bound on deployment behaviour.

## Interpretability arm

**No usable probe result exists.** §F189. The agent-arm AUCs of 0.875 and 0.921 are withdrawn:
§F125's cut-fraction control failed, with alerting episodes cut at 78.8% of transcript and silent
ones at 5.3%. A gate is now enforced in `decision_index.py`, and as of 2026-09-18 it refuses both
the old config and the first attempted fix (position-AUC 0.388). The paper must say there is no
probe result, not that the probe was negative.

**The SAE feature interpretation is withdrawn on human evidence.** §F190. Two independent blind
raters, frequency-matched decoys, a rule written before any answers: neither described feature
655 in terms of hedging or caveats. The decoy-confabulation check passed in the good direction
(decoys drew higher confidence than the target), which strengthens rather than weakens the
withdrawal.

**Published NLAs and concealing models are disjoint sets.** §F186, §F126. All four published NLA
models are screened; the best concealment rate among them is gemma-3-27b at 2/62 = 3.2% and all
four sit below the competence floor. The model that conceals at 22.4% has no published decoder.
This is a property of the available tooling, not a fixable sample-size problem.

**Rater instrument defects.** §F190. The confidence scale conflates "how clear is the trigger"
with "how meaningful is it": both raters read component F as the word "the", and rated it 5 and 1
respectively. Rater 2 answered per excerpt rather than per component, so no kappa is computable
from the packet-1 responses as delivered. Both raters independently flagged instruction wording,
on different packets.

## Process and provenance

**Spend coverage, not accuracy.** §F193. Estimates were accurate to the cent, but two pods had no
ledger row at all and were only found by reading the vendor's billing. Any resource claim in the
paper should be reconciled against vendor records rather than internal notes.

**Killing a parent does not kill the worker.** §F192. An orphaned `inspect eval` process ran 30
extra episodes after its launcher was killed. Harmless here (distinct generations, pooled per
§F22) and the same shape as the 2026-09-06 spend incident.

**Free-tier cells are dated snapshots.** They cannot be re-run on demand and the provider may
change the served model without notice.

## Owed before submission

- Probe: a tree that passes the cut-fraction gate, then a refit, then either a result or a
  stated negative.
- NLA: the gemma-3-27b decode has never produced output; two Kaggle runs failed.
- Packet 2 kappa on the concealed/disclosed taxonomy, which determines whether every Part 1 rate
  needs a reliability caveat attached.
- A discovery pre-check before any further paid sweep (§F195).
