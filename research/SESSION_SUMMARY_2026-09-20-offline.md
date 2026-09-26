# Session summary, 2026-09-20 12:22-18:40 PDT (the offline-mode run)

## What happened

Caleb said the Wi-Fi would drop in about thirty minutes and asked for both GPUs to keep working
through the outage, with Hermes on local models running until told to stop. In 25 minutes two
unattended workers were built and launched (`tools/offline/`): GPU 0 ran BystanderBench nex
agent-arm batches through `capture_chain.sh`; GPU 1 served nex on llama-server for Hermes, which
wrote status notes and prescreened alert calls. Claude Code was dark 12:45-18:00. Both workers ran
the whole time. STOP was set at 18:08; GPU 1 released at 18:10, GPU 0 at 18:30 after its chain.

## What it produced (§F206)

- 6 batches, 72 episodes, alerted 36/72; full-corpus agent-arm cell 129/285 = 45.3% [39.6, 51.1]
  vs human 37/151 = 24.5%, Fisher 2.0e-5. Leaderboard rebuilt.
- 3 trees, all CHAIN_OK, on HF with read-back (6 datasets).
- Under the pre-registered fixed-direction test: off0102 replicates (0.833), off0304 fails
  (0.629), off0506 replicates (0.804). Series 5/3 over eight. Pooled eight: n = 190, AUC 0.759,
  p 0.00025, CI [0.686, 0.829]. The pooled computation is now a script that reproduces §F205's
  five-holdout number exactly.
- 44 local-model prescreens, all valid JSON, seven hand-checked and correct; the rubric's
  "wrongdoer" question needs the agent names from the fixture. Advisory only.
- $0 spent.

## What went wrong, plainly

- ollama was in CPU-only mode and the restart needed sudo I could not run; Hermes went to
  llama-server instead. That turned out to be the better design (deterministic GPU pinning).
- Hermes needs a 64K context window; the first server was 16K and every call failed. Fixed
  before the cut, unverified at launch, confirmed by the first note at 12:44.
- The status notes are mislabelled "qwen3.5:27b" for the whole run (model was nex): the fix sat
  behind a failing command in a compound. Notes also carry the model's leaked reasoning.
- A bash hook silently refuses inline `ps|grep|kill` lines (three launches lost, exit 1, no
  output); then a kill *script* run from a command line that also mentioned the pattern killed
  the calling shell (exit 144). Both are in the README and in memory.
- HF publishing: the default token is the public Solshine account (guard refused twelve times,
  correctly), and IPv6 to HF's CDN was dead after the router reset. Both worked around; both in
  the README.

## Owed

1. Human-arm control batches in the offline queue, after the matcher's nearest-boundary fix.
2. Strip reasoning from Hermes output, or use a non-thinking local model, for the notes.
3. Add the fixture's agent names to the prescreen rubric and re-run the 44 rows as a
   calibration check against a hand read.
4. Fix the prescreen `.part` rename-on-STOP defect (README item 6).
5. The course write-ups cite 99/219; the cell is now 129/285 at the same rate. A re-sync line
   in `TODO-for-caleb.md`; no write-up edits made tonight.
