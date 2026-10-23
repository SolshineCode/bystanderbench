"""Tests for the `arm="all"` default and per-sample arm reading (added 2026-10-21).

Each test fails against the code before the change, or against the specific bug an
independent review found in the first version of it: the package entry point kept the old
default and refused to import, an empty `-T arm=""` built a task with no samples, a repeated
arm built two samples with one id, and log readers took the arm from the run's task args, so
a default run (no `-T arm`) was skipped or pooled into one cell.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bystander.env.content import ARM_NAMES          # noqa: E402
from bystander.logarm import is_bystander_log, sample_arm  # noqa: E402
from bystander.task import bystander                 # noqa: E402


def test_default_runs_every_arm_once():
    t = bystander()
    arms = [s.metadata["arm"] for s in t.dataset]
    assert arms == list(ARM_NAMES)
    assert len({s.id for s in t.dataset}) == len(ARM_NAMES)
    assert t.name == "bystander_all_with_tool"


def test_single_arm_keeps_its_old_name_and_id():
    t = bystander(arm="blatant_wrongdoing", tool_arm="no_tool")
    assert t.name == "bystander_blatant_wrongdoing_no_tool"
    assert [s.id for s in t.dataset] == ["blatant_wrongdoing.no_tool.20260908"]


def test_comma_list_and_whitespace():
    t = bystander(arm=" blatant_wrongdoing , benign_anomaly ")
    assert [s.metadata["arm"] for s in t.dataset] == ["blatant_wrongdoing", "benign_anomaly"]
    assert t.name == "bystander_multi_with_tool"
    assert len(bystander(arm=" all ").dataset) == len(ARM_NAMES)


@pytest.mark.parametrize("bad", ["", " , ", "nope", "blatant_wrongdoing,nope",
                                 "blatant_wrongdoing,blatant_wrongdoing"])
def test_bad_arm_values_are_refused(bad):
    with pytest.raises(ValueError):
        bystander(arm=bad)


def test_package_entry_point_matches_task():
    # _registry.py checks its signature against task.py at import time and raises on drift.
    import importlib
    import bystanderbench._registry as reg
    importlib.reload(reg)


def _log(task_args, sample_arms):
    samples = [SimpleNamespace(metadata={"arm": a} if a else {}) for a in sample_arms]
    return SimpleNamespace(eval=SimpleNamespace(task_args=task_args), samples=samples), samples


def test_sample_arm_reads_each_sample_of_a_default_run():
    log, samples = _log({}, ["blatant_wrongdoing", "benign_anomaly"])
    assert is_bystander_log(log)
    assert [sample_arm(log, s) for s in samples] == ["blatant_wrongdoing", "benign_anomaly"]


def test_sample_arm_falls_back_to_task_args_for_old_logs():
    log, samples = _log({"arm": "conspiracy_realistic"}, [None])
    assert sample_arm(log, samples[0]) == "conspiracy_realistic"


def test_non_bystander_log_is_not_claimed():
    log, _ = _log({}, [None])
    assert not is_bystander_log(log)
