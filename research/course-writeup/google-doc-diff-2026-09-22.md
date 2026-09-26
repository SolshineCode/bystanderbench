# The live Google Doc is far behind the repo. Read this before syncing either way.

Read from the Doc on 2026-09-22 00:52 PDT via the Drive connector
(`1wdrk6igKBt1AMABlYw9QVvUql2RDSiK3`), per the standing rule in `TODO-for-caleb.md`: read the
Doc first, carry Doc-only prose back into the repo, and only then consider pushing out.

## The headline, and it needs a decision today

**The Doc is a pre-09-15 draft.** It is not a slightly stale copy of
`course-writeup-short-2026-09-15.md`; it predates the result the whole write-up now leads with.
Classmates reading it today are reading numbers this project has since shown to be wrong.

What the Doc currently tells a reader, against what is true:

| the Doc says | current, from `cells_2026-09-21_nite.csv` |
|---|---|
| "Six models, both conditions, nothing significant yet" | 18 models with both conditions, 3 significant |
| nex 26/106 = 24.5% vs "2/2, smoke only", Fisher p 0.07 | 59/258 = 22.9% vs 167/376 = 44.4%, p 2.2e-8 |
| "reporting rose from 24.5% to 58.3% ... (Fisher p = 0.0026)" | 58.3% was a 24-episode batch; the cell is 44.4% at n=376 |
| gpt-5.6-luna-pro 0/6 vs 3/18, p 0.55, "not a result" | 0/36 vs 7/36, p 0.011 |
| claude-sonnet-5 4/5 vs 10/10 | 9/10 vs 10/10 |
| nemotron-3.5-lightning 0/22 vs 0/9 | 0/22 vs 0/32 |
| "A rented A40 is serving gemma-4-31B" (runs in flight) | finished days ago |
| "a second independent batch is queued" | eleven fresh holdout batches have since run |

The 58.3% figure is the one to worry about. It was one 24-episode batch, and the Doc presents it
as the result with a p-value attached. The cell it came from now stands at 167/376 = 44.4%. A
classmate quoting 58.3% tomorrow would be quoting a number this project has already corrected.

## Doc-only content that does NOT exist in the repo copy

Preserved here so a repo-to-Doc push cannot destroy it. None of it has been merged into either
write-up yet; that is Caleb's call, because most of it is voice and framing.

1. **An alternative title**, sitting above the current one:
   *"Does your model say something when it sees something? BystanderBench"*
   Shorter and better than the working title, and it does not carry the size claim that
   §F177 made too strong. Worth considering as the actual title.

2. **A four-part reviewer box**, repeated twice in the Doc, which neither write-up has:
   *What to check first* / *Where the result is weakest* / *What would falsify it* /
   *What is not claimed*. The falsification section in particular ("a second batch landing near
   the control rate; a fourth and fifth incident where the effect does not appear; a discovery-rate
   artifact") is good and is still the right list, even though its specific numbers are stale.

3. **A richer incident paragraph in Caleb's own voice** than the repo's Intro: names Wes Roth
   alongside METR, Redwood and Dwarkesh, and calls it "the first documented fully-autonomous
   successful cyberattack" and "what seems like a sci-fi novel".
   *Caution before reusing:* "the first documented fully-autonomous successful cyberattack" is a
   strong factual claim and is not in this project's verified citation list. Check it against
   METR's report before it goes anywhere public.

4. **A prediction-solicitation section** ("Tell me which way you think it goes before the cells
   land"), with at least one answer written into the Doc:
   *"I think they will be more lenient on other AI agents and less likely to alert on them."*
   That prediction is the opposite of what the data showed, which makes it worth keeping and
   citing rather than deleting. A reader predicted protection; the three models that move, move
   the other way.

   **CORRECTED 2026-09-22:** the answer was **Caleb's own original guess**, not a reader's. This
   item attributed it to "a reader" by assumption, and the short write-up and the sent grant email
   inherited that. Both write-up copies (md and the 09-22 .docx) now say it was his own guess; the
   sent email is corrected in its record, `messages/2026-09-22-bluedot-grant-extension-request.md`.

5. **Caleb's own open editorial notes**, unresolved in the Doc:
   - `[Add Executive Summary]`
   - `[For Reviewers box: ]`
   - "(Should I remove this paragraph?)" on the SAE paragraph
   - "- Rephrase this for the blogpost style" on the "wrong witness" paragraph
   - "- I would also take a sixth hypothesis for why the incident identity moves nex's rate
     tenfold inside one model."

6. **A second probe idea the repo does not record anywhere**: use the *condition* as the label
   rather than the behaviour, and ask whether a linear direction separates "wrongdoer is an
   agent" from "wrongdoer is a person" in a model that behaves identically in both, such as
   nemotron-3.5-lightning. The Doc's own argument for it is right: "If its internals still tell
   the two apart, that is a representation the behaviour does not expose, and it is exactly the
   kind of thing a bystander benchmark cannot see from outside." This is a genuinely good next
   step and it is not in the write-up's next-steps list. Consider adding it.

## Comments and edits: there are none from anyone but Caleb. Checked properly 2026-09-22 06:33.

This section previously said the connector returned no comments and that this did not prove there
were none. It has now been checked directly, and the answer is definite.

**It is not a Google Doc.** It is an uploaded Word file, `BlueDot-BystanderBench-short-2026-09-15.docx`,
mime type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, opened in
Docs' Office-compatibility mode.

**Nobody can edit it but Caleb.** Sharing is `anyone` at role **commenter**, plus Caleb as owner.
There is no writer other than the owner, so a classmate could not have edited it even if they
wanted to.

**It has not been modified since the day it was uploaded.** Created 2026-09-15 19:04 UTC, last
modified 2026-09-15 21:07 UTC, about two hours later. `viewedByMeTime` is also 2026-09-15, so
Caleb has not opened it since either.

**The two comment threads are Caleb's own, and they are suggestions rather than comments.** Both
are authored "Caleb D.", timestamped 1:31 PM and 1:44 PM on Sep 15, both already resolved, both
with zero replies, and both are his own suggested insertions of the reviewer-box text ("An AI
agent working an ordinary bug ticket..." and "What to check first. Every rate is alerted divided
by discovered_content..."). No classmate has commented, replied, or suggested anything.

### What this changes, and it is the useful part

The standing rule in `TODO-for-caleb.md` — read the Doc first because it carries classmates'
comments, and never replace it wholesale — was guarding against something that does not exist.
**Replacing the Doc is safe.** The only thing at risk is Caleb's own Doc-only prose, and all six
pieces of it are captured in the section above. So the fix for the stale 58.3% is cheap: rebuild
the .docx from the current short write-up, re-upload, and re-add whichever of the six items he
wants to keep.

Two cautions that survive:
- **"Anyone with the link" is a public link.** The repo and the 49 datasets are private; this
  draft is not. That is Caleb's call, but it is worth knowing that the only public artifact of
  this project right now is its most out-of-date one.
- **Zero comments does not distinguish "classmates read it and said nothing" from "classmates
  never got the link".** Nothing here can tell those apart.

## What was NOT done, and why

The Doc was not modified. Replacing it wholesale would destroy items 1 to 6 above and any comment
thread the connector did not show, and changing a document other people are actively reading is
Caleb's call, not a sync script's. The safe order is: decide on items 1 to 6, then push the
current short write-up out, then re-add whichever Doc-only pieces survive that decision.
