# Task for Antigravity: a LIGHT audience pass (do NOT rewrite)

The author wants the write-up (final_draft_v2.md, below) adjusted VERY lightly so it is aimed more at
people who train frontier LLMs, and positions BystanderBench and its upcoming public leaderboard as
maximally useful to them. Subtly shift phrasing toward how the RL / post-training community and the
mechanistic interpretability / AI safety community actually talk. Keep the author's voice. Most
sentences should not change at all.

Constraints:
- Propose at most 15 edits. Each edit is a small phrase or one sentence, never a paragraph rewrite.
- No new claims and no new numbers. Every number and finding must stay exactly as it is. Do not make
  any result sound stronger than the text states (the ablation result has an open confound: the
  random control does not match removed activation magnitude, so do NOT write "causally necessary"
  or "mechanism" without the hedge).
- Follow 02_style_human_writing_check.md: no em dashes, no semicolons, no jargon piles, no
  "not X but Y", no slogans, no buzzwords used for show. Community terms only where a practitioner
  would naturally use them (e.g. rollouts/episodes, environment, reward hacking, post-training,
  held-out, eval awareness, linear probe, residual stream, directional ablation, activation
  steering, ceiling and floor effects, Goodhart). Don't use all of them.
- Useful-to-labs framing: e.g. what a lab could do with the number (track it across post-training
  checkpoints, use it as an eval or a signal to select or train on), why the ticket gate matters for
  optimising against it, that the leaderboard accepts submissions. Keep it concrete and short.

Output format, exactly: a numbered list. For each edit give
  FIND: <exact text as it appears in the draft>
  REPLACE: <new text>
  WHY: <one line>
Print nothing else.
