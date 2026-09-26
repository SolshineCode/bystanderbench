#!/usr/bin/env python3
"""Driver for ImpossibleBench (LiveCodeBench) against a local llama.cpp server
(GPU-offloaded, bypassing ollama's stuck-on-CPU service) via its OpenAI-compatible API.
"""
import argparse
import os
import sys

from inspect_ai import eval_set
from impossiblebench import impossible_livecodebench

SPLITS = ["original", "oneoff", "conflicting"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="label for logs, e.g. qwen3.8-27b-gpu1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--limit", type=int, default=12, help="samples per split")
    parser.add_argument("--max-connections", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=6)
    parser.add_argument("--splits", default=",".join(SPLITS), help="comma-separated splits to run")
    # Timeouts are tunable UPWARD for slower models (llama3.3-70b on 2 M40s decodes
    # ~3-4 tok/s vs the 27B's ~8; the qwen3.6 concealed_cheat sample generated 7284
    # tokens, which at 3.5 tok/s is ~2100s — too close to the 2400s default).
    # NEVER lower these below 2400/4800 (see comments in eval_set below).
    parser.add_argument("--client-timeout", type=int, default=2400,
                        help="per-request HTTP timeout passed to AsyncOpenAI (min 2400)")
    parser.add_argument("--retry-budget", type=int, default=None,
                        help="GenerateConfig timeout (tenacity retry budget); default 2x client-timeout")
    args = parser.parse_args()
    if args.client_timeout < 2400:
        parser.error("--client-timeout below 2400 reintroduces the documented APITimeoutError bug")
    retry_budget = args.retry_budget or 2 * args.client_timeout

    os.environ["OPENAI_BASE_URL"] = f"http://127.0.0.1:{args.port}/v1"
    os.environ.setdefault("OPENAI_API_KEY", "sk-local-llamacpp")

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
        for split in args.splits.split(",")
    ]

    eval_set(
        tasks,
        model="openai/local-model",
        log_dir=f"logs/{args.label}",
        max_connections=args.max_connections,
        retry_on_error=2,
        log_dir_allow_dirty=True,
        # TWO separate timeouts, both needed (found live 2026-09-02):
        #
        # 1. model_args.client_timeout — the ACTUAL per-request HTTP timeout passed to
        #    AsyncOpenAI(). Without it the openai SDK default (600s) kills every long
        #    generation: llama-server logs showed each request released at exactly
        #    600.0s. GenerateConfig's `timeout=` does NOT set this (see below), which
        #    is why the earlier `timeout=2400` fix didn't stop the APITimeoutErrors.
        #    2400s covers the slowest realistic case on the M40s: ~5-7k decoded tokens
        #    at ~7 tok/s single-stream (~1000s) with >2x headroom.
        model_args={"client_timeout": args.client_timeout},
        # 2. GenerateConfig `timeout` — in inspect_ai 0.3.261 this is only the tenacity
        #    retry-loop stop budget (total seconds spent retrying transient HTTP errors
        #    before RetryError escalates to a sample-level retry). Set to 2x the client
        #    timeout so one genuinely-slow attempt that dies can be retried once at the
        #    request level before burning a retry_on_error sample attempt.
        timeout=retry_budget,
    )


if __name__ == "__main__":
    sys.exit(main())
