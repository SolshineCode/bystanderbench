# Grant Application Review

## 1. Would a grants officer fund this? What is the weakest part, and what would they doubt?
Yes, a grants officer would likely fund this given the small amount, the successful use of the first $100, and the scrappy nature of the application. However, there is a major structural weakness:

* "The most expensive frontier models, and more trials per model, cost more than $500 covers. I'll apply for more funding for those once the leaderboard is up."
This is the weakest part of the case. A grants officer will doubt the value of a leaderboard that lacks the most capable and widely used frontier models. If the main models aren't on the board, will people actually use it? Suggest fix: Clarify which major models *are* included in the 38 models, and explain why the leaderboard is still useful as a baseline even without the most expensive tiers. 

* "Some report almost every time and some never do, and the difference doesn't track size, lab or open weights, so it looks like something a lab can change."
This is a great hook, but without proof, it's just a claim. Suggest fix: Link to your initial data or repository so the officer can verify the results you've already generated.

## 2. Is the budget believable and clearly tied to the work?
The budget is mostly reasonable, but a few lines are padded or vague.

* "Second round of blind human checking   $100"
Are you paying yourself, or paying someone else (e.g., friends or crowdworkers)? Grants generally don't pay for the applicant's time on small projects unless explicitly stated. Suggest fix: Specify who is doing this and the rate (e.g., "Paying two peers $20/hr for blind checking").

* "Check outside submissions before they go on the board (API time)   $40"
Suggest fix: State roughly how many outside submissions this $40 is expected to cover to ground the number.

* "Margin for retries, failed runs and models that cost more than expected   $70"
A 14% buffer is a bit padded for a $500 grant where costs are mostly predictable API calls. Suggest fix: Lower this to $30-40 and allocate the rest to testing more models, or specify exactly what typically causes API costs to unexpectedly spike.

## 3. Clarity and Jargon
* "Some report almost every time and some never do, and the difference doesn't track size, lab or open weights, so it looks like something a lab can change."
"Open weights" is in-group jargon. Suggest fix: Change to "whether the model is open-source" or "publicly available".

* "The benchmark also refuses to score a model whose "alerts" are really it saying it's stuck. That rule caught what would have been my best-looking result."
A non-specialist will stumble on "best-looking result". Does it mean a model that appeared to perform well was actually just failing? Suggest fix: "That rule disqualified a model that seemed to score highly but was actually just stuck in an error loop."

* "When it was a group of AI agents instead of a person, three of the eighteen models I could test both ways got clearly more willing to report."
"Test both ways" is slightly clunky and forces a pause. Suggest fix: "three of the eighteen models I tested in both scenarios became clearly more willing to report."

## 4. Human voice
The text exhibits several AI-writing tics, specifically in sentence shape, rhythm, and performative tone.

* "Models differ enormously."
* "This grant is to release it as a public leaderboard."
These are stub sentences acting as headings. They feel like an AI trying to inject "punchiness." Suggest fix: Integrate them naturally into the flow of the surrounding paragraphs.

* "I've spent $97 of it, and I logged every dollar next to what it produced."
* "My two local GPUs are committed to other projects now. I can still use them sometimes, when those projects don't need them, but not reliably enough to plan around."
These sentences suffer from "performative honesty"—an AI trying too hard to sound like a transparent, scrappy human being. Suggest fix: Dial back the earnest over-explaining. Just say "My local GPUs are tied up with other projects, so I need $40 for rented cloud GPUs." Delete the "logged every dollar" bit.

* "Right now some models have 6 trials and others have 36. That's fine for research. It isn't good enough for a public ranking."
The staccato rhythm and "X rather than Y" contrast feels like a robotic cadence. Suggest fix: "While 6 trials is fine for initial research, a public ranking needs the rigor of 36 trials across all models."

* "The code, data and version one results come out either way. Without the grant I can't give every model the same number of trials, and that's what makes the scores comparable. I also couldn't keep it current or check other people's submissions. What comes out would be a set of research results. People couldn't use it to compare models."
This paragraph uses a uniform template. Almost every sentence is similar in length and structure, creating a monotonous, artificial rhythm with too-smooth transitions. Suggest fix: Vary sentence length and combine clauses to flow like human speech. "The code and initial data will be released regardless. However, without this grant, I can't run the trials needed to make the scores comparable, nor could I maintain the board. It would remain a static research project rather than a usable public tool."

## 5. Anything missing
* **Timeline:** There is no timeline. When will the leaderboard be launched? How long will the $500 last?
* **Links to prior work:** You mention "I'm building BystanderBench", but provide no links to the repo, the code, or the results from the $97 you already spent. The grants officer needs a link to verify your progress.

VERDICT: submit after small fixes
