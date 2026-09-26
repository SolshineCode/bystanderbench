# Question for Peter: arXiv before Inspect Evals?

Drafted 2026-09-12 for Caleb to send. **Not sent.** Slack or the next meeting, his call.

## Why this is a question at all

BystanderBench is worth more to other people as a thing they can run than as a paper. The
natural home is UK AISI's `inspect_evals`, since the benchmark is already an Inspect task and
the porting work is mostly packaging: `__init__.py`, the task module, the scorer, a README,
`eval.yaml`, and a `_registry.py` entry.

The snag is their `register/` submission process, which asks for a paper URL. arXiv is the
expected form. So the order of operations is forced: arXiv first, port second. That makes
"should this go on arXiv" a question about distribution rather than about publication, and
it is the kind of question a mentor should weigh in on before I spend the effort.

## The message

> Hi Peter, a question about where BystanderBench should end up.
>
> The benchmark is an Inspect task already, and the obvious home for it is UK AISI's
> inspect_evals repo, so people can run it against their own models without talking to me.
> Their submission process wants a paper URL, and in practice that means arXiv. So arXiv
> would come first, and the port second.
>
> Does that seem appropriate for a BlueDot project at this stage? I'm conscious it's a
> preprint on a benchmark with three incidents and a clustering caveat that bounds the
> design-level claim at k=3, not a finished paper, and I don't want to put something on
> arXiv that would read as overclaiming.
>
> The result I'd lead with is that reporting rates on an identical environment run from
> 0/6 to 6/6 across models, and that within one model the rate moves by incident (9/48,
> 1/48, 0/48) with five pre-registered explanations tested and all five rejected. The
> unexplained part is the interesting part, and putting it somewhere citable is partly an
> invitation for someone else to explain it.
>
> Happy either way, including "not yet, do X first."

## What the answer changes

**Yes:** arXiv goes on the critical path, which means the write-up has to become a paper, the
Opus benign control has to run (about $2.67, the one gap the README leads with), and the repo
has to go public before submission.

**No, or not yet:** the port is blocked, and the benchmark ships as a repo plus HF datasets.
Everything else in the plan is unchanged, which is why this is not urgent enough to chase.

## Scheduling

I could not find Peter's scheduling link anywhere in the repo or the transcripts. The
shortlist doc says to use whatever link is on Caleb's BlueDot profile or mentor page, notes
it was never captured, and notes that Peter books ahead rather than same-day. Caleb needs to
pull that from his BlueDot account.
