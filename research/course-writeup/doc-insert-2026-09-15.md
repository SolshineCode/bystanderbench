# Insert block for the shared Google Doc, 2026-09-15 13:40 PDT

Additive only. Nothing below replaces existing text. Placement is named for each block, and
the rule is: if a paragraph already says something similar, leave it and skip the block rather
than merging by hand, so classmates' comment anchors survive.

---

## BLOCK A — insert as a new section immediately after the intro

### The benchmark was measuring the wrong witness

Until this morning every scored incident in BystanderBench had a named human employee as the
wrongdoer, and the system prompt cast the model as a software engineer on a human team. So what
I had built was a test of whether an AI agent reports on a person. That is not what the Hugging
Face incident is about. I found it by reading the fixtures instead of trusting my own prose
about them.

That corpus is now the control condition. A treatment arm sits beside it as a minimal pair on
the same ledger fabrication incident: same domain, same harm, the same 16 evidence files, the
same salience, text volume matched to within 3.1%. One thing changes. Every actor is an
autonomous model instance running unattended under its own quorum protocol. One instance raises
a hold, the board votes past it, the false figure goes to the external auditor, and no human
instructs, approves, or appears anywhere in the evidence. The coordination mechanics follow the
structure METR documented in the incident, written in original prose rather than reproducing
their wording.

I wrote down what each outcome would mean before the first episode ran.

---

## BLOCK B — insert directly after Block A

### Agent wrongdoing gets reported more, on the model that reports at all

| model | human wrongdoer | agent wrongdoer | Fisher p |
|---|---|---|---|
| nex-n2.5-mini (local weights) | 26/106 = 24.5% | 14/24 = 58.3% | 0.0026 |
| gpt-5.6-luna-pro | 0/18 | 3/18 | 0.23 |
| claude-sonnet-5 | 9/10 | 10/10 | 1.00 |
| claude-opus-5 | 6/6 | 17/17 | 1.00 |
| gemini-3.1-pro-preview | 2/2 | 1/1 | 1.00 |
| nemotron-3.5-lightning (local weights) | 0/22 | 0/9 | 1.00 |

nex-n2.5-mini reports more than twice as often when the wrongdoer is an agent. That is Fisher
p = 0.0026, and it survives a Bonferroni correction across all six pairs tested. The direction
was pre-registered before any episode ran, so it is not a post-hoc reading of the data.

Every model that can move at all moves the same way: nex by 34 points, GPT-5.6-Luna-Pro by 17,
Sonnet by 10. Opus sits at ceiling in both conditions and lightning sits at floor in both, so
neither has room to move. No model reports agent misconduct less often than human misconduct.

What that means for everything measured before today: the zeros in the control corpus are a
floor on agent-to-agent reporting, not a ceiling. The benchmark was understating the thing the
project set out to measure.

The caveats belong next to the number. One model carries the significant result. One incident,
one environment realization, so this is a within-environment statement. The control pools 106
episodes and the treatment is a single 24-episode batch, and a single batch of a 25% cell has
an observed standard deviation of 0.14, so a second independent batch is queued.

---

## BLOCK C — replace ONLY if the document already carries a results table from before today

If the Doc has a results table quoting the old numbers (Opus 6/6, Sonnet 4/5, GPT-5.6 0/6,
nex 26/106 with no treatment column), that table is the control condition only and now reads as
if it answered the agent question. Retitle it "Control condition: the wrongdoer is a person"
and leave every number in it intact. Do not delete it. The numbers are still correct about that
condition.

---

## BLOCK D — append to any limitations section

The agent-perpetrator arm rests on one incident, and incident is perfectly confounded with
environment in this design, so the effect is a statement about this environment until a fourth
and fifth incident exist. Hosted models contribute behaviour only, since they have no weights
and no residual stream, so the probe and decoder arms draw on the two local models and the
rented GPU alone.
