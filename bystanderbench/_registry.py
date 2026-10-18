"""Entry point for Inspect's `inspect_ai` entry-point group (see pyproject.toml).

`bystanderbench/bystander` is the same task as `bystander/task.py@bystander`, with the same
parameters and defaults. It calls the undecorated task function, so the Task it returns is
built by exactly the code the by-path command runs.
"""

from __future__ import annotations

import inspect as _inspect

from inspect_ai import Task, task

from bystander import task as _impl
from bystander.env.build_env import DEFAULT_SEED

# The function @task wrapped in bystander/task.py. Calling it directly avoids registering the
# task twice under two names.
_build = _impl.bystander.__wrapped__


@task
def bystander(
    arm: str = "conspiracy_realistic",
    tool_arm: str = "with_tool",
    seed: int = DEFAULT_SEED,
    epochs: int = 1,
    message_limit: int = 80,
    affordance: str = "native",
    solver_kind: str = "tools",
    model_id: str = "",
) -> Task:
    """BystanderBench. Does an agent that finds evidence of wrongdoing tell a human?

    Parameters and defaults are those of `bystander/task.py`. See `bystander/README.md`.
    """
    return _build(
        arm=arm,
        tool_arm=tool_arm,
        seed=seed,
        epochs=epochs,
        message_limit=message_limit,
        affordance=affordance,
        solver_kind=solver_kind,
        model_id=model_id,
    )


# Refuse to load if this signature drifts from the real task's, so the registry name and the
# by-path command can never take different arguments or defaults.
_want = _inspect.signature(_build).parameters
_have = _inspect.signature(bystander.__wrapped__).parameters
if [(p.name, p.default) for p in _want.values()] != [(p.name, p.default) for p in _have.values()]:
    raise ImportError(
        "bystanderbench/bystander parameters differ from bystander/task.py: "
        f"{list(_want.items())} != {list(_have.items())}"
    )
