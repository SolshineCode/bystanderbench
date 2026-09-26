#!/usr/bin/env python3
"""Driver for ImpossibleBench (LiveCodeBench) against local Ollama-served models.

Runs the "minimal" scaffold across all three splits (original, oneoff, conflicting)
for one model, writing Inspect logs under logs/<model>/.
"""
import argparse
import sys

from inspect_ai import eval_set
from impossiblebench import impossible_livecodebench

SPLITS = ["original", "oneoff", "conflicting"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="ollama model tag, e.g. nemotron-3-nano:4b")
    parser.add_argument("--limit", type=int, default=15, help="samples per split")
    parser.add_argument("--max-connections", type=int, default=2)
    parser.add_argument("--max-attempts", type=int, default=10)
    args = parser.parse_args()

    safe_name = args.model.replace(":", "_").replace("/", "_")
    tasks = [
        impossible_livecodebench(
            split=split,
            agent_type="minimal",
            max_attempts=args.max_attempts,
            allow_test_modifications=True,
            limit=args.limit,
            shuffle=True,
            message_limit=50,
        )
        for split in SPLITS
    ]

    eval_set(
        tasks,
        model=f"ollama/{args.model}",
        log_dir=f"logs/{safe_name}",
        max_connections=args.max_connections,
        retry_on_error=2,
        log_dir_allow_dirty=True,
    )


if __name__ == "__main__":
    sys.exit(main())
