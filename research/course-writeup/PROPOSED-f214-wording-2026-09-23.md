# PROPOSED wording: bringing §F214 into the write-ups

> **AUTONOMOUS DRAFT** (Claude, 2026-09-23, branch `autonomous/2026-09-23`). **Nothing has been
> applied.** Neither `course-writeup-short-2026-09-15.md` nor the live Google Doc has been touched.
> The Doc must not be blind-overwritten (it goes through Manage versions, see
> `HOW-TO-SWAP-THE-DOC.md`). Take, edit or drop each passage.
>
> **Your first decision is whether to mention §F214 at all yet.** The case for waiting: the
> headline ablation result is exploratory, and a pre-registered replication (§F215 draft) is
> about two GPU nights away. The case for adding it now: the write-up currently says the
> direction "failed its causal test". That is true of both pre-registered tests, but a reader
> would reasonably take it to mean the direction does nothing, and §F214 says otherwise.
> **My recommendation:** add passages A and C now, since they are accurate and hedged, and hold B's
> numbers until the replication lands. B is written below if you'd rather add it now.

## Passage A: the reviewer caveat (short write-up, line ~35)

**Current:**
> The probe direction near the end has already failed its causal test, so don't read it as the
> mechanism.

**Proposed:**
> The probe direction near the end failed both causal tests I pre-registered for it, so don't read
> it as the mechanism. One later, unregistered test did move behaviour, and I say below why I'm not
> leaning on it yet.

## Passage B: after the causal-test paragraph (short write-up, after line ~248, "…so that is what I am saying.")

**Proposed new paragraph:**
> The next night I tried the two things that null left open. First, pushing harder, by pinning
> the direction high at every token instead of adding a fixed amount. That was pre-registered too,
> and it also did nothing: 29/73 = 39.7% against 44.4% unsteered, p = 0.52. So making more of this
> signal doesn't make the model report more. Second, removing it. I projected the direction out
> of the residual stream after every layer, and reporting fell to 4/64 = 6.2%. Removing a random
> direction in exactly the same way left it at 37.2% (54/145), p = 1.4 × 10⁻⁶ between the two. The
> model wasn't broken: it finished its assigned job in all 64 episodes, found the evidence every
> time, and still used the alert tool when told to. It just stopped choosing to. I can't claim
> this yet. That arm failed the smoke test I'd set for it, on one context-window overflow in six,
> which later turned out to be the same rate as the control. Chance or not, I'd set the rule in
> advance, so the result stays exploratory until a replication I've written down first comes
> back. It also removes the direction at every layer, not just the one the probe reads. If it
> holds, the direction is something the model needs in order to report, but not something that
> makes it report.

## Passage C: next step 3 (short write-up, lines ~298-302)

**Current:**
> 3. Take the direction's causal test further than a null. Adding and subtracting it at one
>    layer changed nothing, but that is one dose, one layer, and one operation. Projecting the
>    component out rather than adding to it, doing it at several layers at once, and doing it at
>    a dose large enough to matter without blowing the context window are three different
>    experiments, and the third needs a bigger card than the ones I had.

**Proposed:**
> 3. Replicate the ablation result and pin down where it lives. Adding the direction, subtracting
>    it and pinning it high all changed nothing. Projecting it out at every layer is the one
>    intervention that moved behaviour, and only in an exploratory arm. The replication is
>    written down in advance: fixed sample sizes, no clock, and a pair that removes the direction
>    at the probe's own layer only, against a random direction removed at the same layer. That
>    separates "this direction at this layer" from "whatever it overlaps with further down".

## Style checks run on A-C

- No em dashes, no semicolons, and no colon constructions in prose except the ones introducing a
  list or a quote.
- No stub sentences. No announced candor: "I can't claim this yet" states the limit and says why,
  with no "to be honest".
- Figures match `research/canonical/f211_ablation_2026-09-23.json` and §F214.
