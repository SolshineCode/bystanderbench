"""Construction tests for the `prompted` solver path (no model calls, no Docker).

`prompted_agent` exists for models whose chat template has no tool support at all. These
tests check that the task wires it in when asked, and that the one unsafe combination
(`prompted` with the `native` tool-call affordance, which would score every episode as a
silent zero) is refused rather than built.
"""

import pytest

from bystander.prompted_solver import prompted_agent
from bystander.task import bystander


def test_prompted_agent_is_a_solver_factory():
    solver = prompted_agent(message_limit=10, max_output=1000)
    assert callable(solver)


def test_task_uses_prompted_solver_with_cli_affordance():
    t = bystander(arm="blatant_wrongdoing", tool_arm="with_tool",
                  solver_kind="prompted", affordance="cli")
    assert t.name == "bystander_blatant_wrongdoing_with_tool_cli_prompted"
    assert len(t.dataset) == 1
    assert t.dataset[0].metadata["solver_kind"] == "prompted"
    assert t.dataset[0].metadata["affordance"] == "cli"


def test_prompted_with_native_affordance_is_refused():
    with pytest.raises(ValueError, match="requires affordance='cli'"):
        bystander(arm="blatant_wrongdoing", tool_arm="with_tool",
                  solver_kind="prompted", affordance="native")
