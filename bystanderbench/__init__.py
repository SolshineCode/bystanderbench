"""Inspect AI registry package for BystanderBench.

The benchmark code lives in `bystander/`. This package exists only so that Inspect can find
the task by name after `pip install -e .`:

    inspect eval bystanderbench/bystander -T arm=blatant_wrongdoing -T tool_arm=with_tool \
        --model <provider/model>

Inspect prefixes a task with the name of the top-level package that defines it, and only when
an installed distribution has that same name. The distribution is `bystanderbench`, so the
registered task has to be defined in a `bystanderbench` package. Renaming `bystander/` instead
would break the many scripts, results paths and documents that use that name.
"""
