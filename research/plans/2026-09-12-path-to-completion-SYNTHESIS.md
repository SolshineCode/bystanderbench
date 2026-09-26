# Path to completion — synthesis, 2026-09-12

Two plans were written independently: mine (`...-path-to-completion.md`) and a Fable 5.1
agent's (`...-path-to-completion-fable.md`). This reconciles them. **Where they disagree, the
Fable plan was right on three points and I have corrected mine rather than split the
difference.** All four of its load-bearing claims were verified against the tree before being
adopted.

## Where the Fable plan corrected mine — verified, not accepted on trust

**1. The Inspect Evals sequencing. arXiv is a hard prerequisite, not a follow-on.**
My plan had "restructure as a package → PR upstream" on the critical path. That ordering is
wrong and the repo already knew it. `research/bluedot-research-positioning-and-trial-design-
2026-09-03.md` §16 (lines 843–860, decided 2026-09-04) records a direct check:
`register/README.md` **hard-requires an arXiv URL per submission** because their metadata bot
derives title/description/tags from the paper, and `CONTRIBUTING.md` says native merge is not
the route. The decided sequence is **paper → arXiv → external `register/` submission**. So the
packaging work does not gate the PR; **the paper does**. I had this backwards and would have
spent six hours on a restructure that cannot be submitted yet.

**2. `run_bench.sh` is still broken — I fixed the documentation, not the script.**
Yesterday I rewrote the README quickstart to say "run `tool_probe` first" and "read numbers
with `report.py`". The script itself is unchanged: line 44 still defaults
`TOOL_ARMS="with_tool no_tool"`, line 73 still calls `summarize.py`, and there is still no
`set -e` (`grep -c` returns 0). Documenting around a defect is not fixing it, and an outsider
runs the script, not the README.

**3. The leaderboard grid is nearly empty, and that is the real cost of the feature Caleb
asked for.** Only `nex` and `qwen` have incidents 2/3 and a benign control. Every hosted model
has **incident 1 only, at n=6**. A models × conditions leaderboard with one populated column is
not a leaderboard. Filling it is a paid batch (~$15 at §F80 rates) against a $0.66 balance —
so it needs a top-up and one blanket approval of a pre-registered cell list, per §F104's
practice of fixing the list before running.

**4. No `LICENSE` file exists.** Verified: none at root. Nothing can be released openly
without one, and it is a five-minute fix that blocks an entire category of work.

## Where my plan holds

- **Part 1's decisive experiment is the `nex-n2.5-mini` concealment screen**, running now. It
  decides whether the 0–5% dense / 22% MoE split means "rare behaviour" or "wrong architecture
  class screened". Fable independently reached the same conclusion and added the better
  framing: §F109's discovery that gemma hardcodes the *cover task* in 4 of 12 BystanderBench
  episodes is the strongest Part 1 ↔ Part 2 bridge available, and should become a
  `tampered_cover_task` column rather than staying in scorer metadata.
- **Ruthless cutting.** Both plans cut the same things; the union is below.

## The merged critical path

```
M1 ledger corrections  ──┐
M2 script + LICENSE      ├──→ M4 paper rewrite ──→ arXiv ──→ M7 Inspect register/ submission
M3 leaderboard batch  ───┘           ↑
M5 Part 1 screen + audit ────────────┘
```

**The binding constraint is the paper, and the paper is gated on numbers being settled.** Not
packaging, which was my error. M2 and M5 run in parallel now; M3 needs a human for money; M7
cannot start before arXiv exists.

## Must-do, merged and ordered

1. **One correcting ledger entry** for the five §F102 A contradictions (north-mini 39/177 vs
   41/176 vs 53/237; gemma's denominator 166/122/156; the paid-balance chain; the qwen `0/40`
   that is actually nex's incident-3 conditional). Gates every external number. ~3h.
2. **Fix `run_bench.sh` itself** (`tool_probe` default, call `report.py`, `set -e` +
   `PIPESTATUS`), add `LICENSE` and `pyproject.toml`, finish the hardcoded-path sweep (five
   files, the guard covers one). ~4h.
3. **Leaderboard batch** — pre-registered cell list, one approval, one top-up. ~$15 + Opus
   benign control $2.67.
4. **Paper rewritten against the current ledger.** The draft is ~20 entries stale: it still
   says "every model shown has open, ungated weights" at line 434 under a table containing
   Opus, and still carries 5/30 beside 9/48. Every number in the rewrite comes from a CSV cell,
   not from memory. ~12h, written last.
5. **Part 1 landed as a result** whichever way the screen falls, with the killed results
   (§F35/§F40/§F44/§F47) kept in full — the negative results are a contribution.
6. **Visibility decision** — repo private, 11 HF datasets private. Caleb's explicit yes/no.

## Cut, union of both plans

The fifth mechanism hypothesis (§F110's "next axis"); the reasoning-on rerun and the offline
replay probe (superseded by §F108); the 346-episode capture backlog; the gemma prompted-loop
rescue (task #24); more nex incident-1 episodes; k=35 incidents; the detection-game proposal
(good idea, different paper); further llama-70b/north-mini/splice/moe-floor runs; and — after
M3 lands — a declared freeze on the ledger, which has taken 117 entries in six days.

## Risks, merged

1. **Number drift across documents.** Mitigation: two committed canonical CSVs, tables
   generated from them by script, never typed. This has already bitten four times.
2. **Money gates the headline control.** Mitigation: one top-up plus blanket approval of a
   pre-registered list; fallback is to make Sonnet the headline, since it has a benign control.
3. **The ledger's own gravity.** 117 entries in six days is a research process that generates
   work faster than it closes it. Mitigation: the cut list above is a commitment.
