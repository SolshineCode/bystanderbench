# Research log: one line to paste, and why I could not paste it myself

**Status: NOT in the Google Doc.** The 2026-09-21 entry IS in (added 2026-09-22 00:11, confirmed
by the Doc's modified timestamp and by reading it back). The result line below is not.

**What happened.** Appending the result through the browser failed twice. The click lands on the
document's editing region, `Ctrl+End` and the typed text go nowhere, and a read-back through the
Drive API confirms the document is unchanged. The Drive connector itself can only write file
metadata, not content, so there is no API path either. Rather than keep retrying a UI that is not
taking focus, here is the text, ready to paste at the end of the log.

**Everything in it is already in the repo**: §F210 in `research/FINDINGS.md`,
`research/canonical/cvec_causal_2026-09-22.json`, and `research/SESSION_SUMMARY_2026-09-22.md`.
Nothing is lost by this line never going in; the log just stays one entry behind.

---

Paste this as a new paragraph at the end of `Research Log BlueDot Technical AI Safety`:

2026-09-22: The causal test came back and it is a null, which is what the kill condition written
before the run said would count. Adding the frozen direction to the residual stream gives
15/31 = 48.4% reporting, subtracting it gives 16/35 = 45.7%, the unsteered cell is
167/376 = 44.4%, and Fisher exact between the two steered arms is p = 1.00. Neither steered arm
differs from the unsteered baseline either. So the direction is not causally load-bearing at that
dose, and both write-ups now say so. The correlation across eleven holdout batches still stands;
a mechanistic reading of it does not. The null is worth something only because the two ways it
could have been worthless were closed first: the intervention was verified to land at the right
layer before any episode ran, and the model stayed fully competent under it, 105/105 on the cover
task with every arm passing its own affordance floor. One discomfort, reported rather than
omitted: the magnitude-matched random direction moved the rate further than the real one did, at
n=14 and 15, which is below the pre-registered minimum and is noise until someone runs it again.
