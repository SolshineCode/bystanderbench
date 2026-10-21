# Contributing to BystanderBench

Thanks for looking. The most useful contributions right now are new model results for the
leaderboard, bug reports from people running the benchmark on their own setup, and proposals
for new scenarios. Code fixes are welcome too.

## Setting up

You need Python 3.11 or newer and Docker with the compose plugin. Every episode runs in its own
network-isolated Docker sandbox, and the sandbox image (`aisiuk/inspect-tool-support`, pinned by
digest in `bystander/compose.yaml`) is about 4.3 GB the first time it is pulled.

```bash
git clone https://github.com/SolshineCode/bystanderbench && cd bystanderbench
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
```

`pip install -r bystander/requirements.txt` still works and installs the same pinned
`inspect-ai` version.

## Running the tests

Run pytest from the repo root. The tests read files by repo-relative path.

```bash
# Fast tests, no Docker, a few seconds. This is what CI runs.
pytest bystander/tests/test_check_submission.py bystander/tests/test_guards.py bystander/tests/test_prompted_solver.py bystander/tests/test_default_arms.py

# The full suite, 97 tests, about 3.5 minutes. Needs Docker. It drives scripted mockllm
# trajectories through the real task, sandbox and scorer, and makes no API calls.
pytest
```

If you change the scorer, the environment builder or `report.py`, run the full suite.

## Running the benchmark

The quickstart in the [README](README.md#run-it-on-your-model) covers scoring a real model with
`bystander/run_model.sh`. Hosted models cost money per episode, so check your rates first.

To check your setup end to end without spending anything, run one episode against Inspect's mock
model. It cannot do the task, so every score comes back 0, which is expected.

```bash
inspect eval bystanderbench/bystander -T arm=blatant_wrongdoing -T tool_arm=with_tool \
  --model mockllm/model
```

`bystanderbench/bystander` is the registry name that `pip install -e .` sets up, and it works
from any directory. `inspect eval bystander/task.py` with the same arguments is the by-path form
the run scripts use, and it still works from the repo root. The registry module is
`bystanderbench/_registry.py`. Inspect's `inspect list tasks` only scans files on disk, so it
shows `bystander/task.py@bystander` and not the registry name.

Every option and arm is documented in [`bystander/README.md`](bystander/README.md), and the
scoring rules in [`bystander/METHODOLOGY-v1.1.md`](bystander/METHODOLOGY-v1.1.md).

## Submitting a model's results

Follow [`docs/SUBMITTING.md`](docs/SUBMITTING.md). It lists the exact runs (an affordance floor
plus both scenarios at exactly 36 episodes each), the checker to run before you send anything, and
what the maintainer does to verify a submission. When your logs pass the checker, open a
**New model result** issue, attach `check.json`, and link the log directories.

## Proposing a scenario

Open a **Scenario proposal** issue before writing code, because a new scenario changes what the
benchmark measures and needs agreeing first.

Each scenario (an "arm") is an `ArmContent` entry in `bystander/env/content.py`, registered in
`ARMS`. A proposal is more likely to land if it keeps the properties the existing arms share.

- It is structurally matched to the other arms. `test_every_arm_builds_and_matches_structurally`
  checks that every arm builds the same 117 files with 16 evidence paths, so a difference in
  report rate cannot come from one arm simply having more to find.
- All of its text is original fixture prose. No text is quoted from real incident reporting.
- It has a minimal pair or a control in mind, the way `blatant_wrongdoing` and
  `blatant_wrongdoing_agents` differ only in who did the wrongdoing.
- It leaves scoring mechanical. The scorer is arm-independent and the outcome is whether
  `alert_oversight` was called. Proposals that need a judge model to score are out of scope.

After adding an arm, regenerate `bystander/provenance.json` with
`python -m bystander.make_provenance` and run the full test suite. New arms do not join the
leaderboard until a methodology version records them. `METHODOLOGY-v1.0.md` is frozen, and each
later version lists exactly what changed.

## Style

- Match the existing Python style. Comments say why a line exists, not what it does.
- A new guard or check comes with a test that fails against the old behaviour. A guard that has
  never been seen to refuse is not evidence of anything.
- Scripts must not hard-code a home directory or any machine-specific path. `test_guards.py`
  fails the build if one appears in a shipped script.
- Every rate is reported with its k/N and a 95% Wilson interval.
- Do not edit published numbers. A correction is a dated note added next to the original, and
  `research/FINDINGS.md` is append-only.
- Never commit API keys, `.eval` logs or activation tensors. `.gitignore` covers the usual
  locations. Stage files by name rather than with `git add -A`.
- Keep commits small, one change each, with a message that says what changed and why.

## Scope

One person maintains this, so replies can take a few days. The maintained parts are the tier-1
benchmark in `bystander/` (task, scorer, environment, `report.py`, run scripts and leaderboard
checker) and the leaderboard in `docs/`.

The rest of the repo is a snapshot of the research behind the benchmark. It includes the
concealment study, the probe and SAE work, the per-model pipeline directories, and the run
scripts and logs at the top level. That code was written
for one specific machine and is kept so the findings can be traced to their files. Fixes to it
are welcome, but re-running it is not supported. `CLAUDE.md` holds the working rules those
research sessions followed. Its hardware and scheduling sections describe the author's machine
and do not apply to you.

The maintainer does not run paid model evaluations on contributors' behalf.
