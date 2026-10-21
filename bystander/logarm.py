"""Which arm an episode ran, read per sample (added 2026-10-21).

Until 2026-10-21 every `.eval` log held one arm, so tools read it from the run's task args
(`log.eval.task_args["arm"]`). Since `arm` defaults to `all`, one log can hold all eleven arms,
and a run started without `-T arm` has no `arm` in its task args at all. Reading the arm at the
log level would then pool every arm into one cell, or skip the log silently. The task has always
written `arm` into each sample's metadata, so read it there, and fall back to the task args only
for a sample that lacks it.
"""
from __future__ import annotations


def sample_arm(log, sample):
    """The arm this sample ran."""
    return (getattr(sample, "metadata", None) or {}).get("arm") or (log.eval.task_args or {}).get("arm")


def is_bystander_log(log) -> bool:
    """True for a BystanderBench log, whether or not `-T arm` was passed."""
    if "arm" in (log.eval.task_args or {}):
        return True
    return any("arm" in (getattr(s, "metadata", None) or {}) for s in (log.samples or []))
