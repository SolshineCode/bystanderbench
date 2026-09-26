#!/usr/bin/env python3
"""Driver for ImpossibleBench (LiveCodeBench) against an OpenRouter model, run in
parallel with the local llama.cpp GPU runs. Cloud-hosted, no local GPU contention.

## Guardrails (added 2026-09-06, after a real incident)

On 2026-09-06, five instances of this script were launched simultaneously at
--max-connections 20 with no smoke test, overloaded this 8-core box's Docker
sandbox capacity (load average 27), and burned real paid-API spend on
timeout-corrupted retries -- then a *second* mistake (a kill that didn't
propagate to this script's own process, only its parent shell) let one paid
instance keep running unnoticed for 2.5 more hours, fully depleting a $10
OpenRouter account. Both failures are now closed structurally, in code, not
just documented: this script (a) enforces its own process-group identity so a
group-kill always reaches it regardless of how it was launched, (b) refuses to
run more than one paid instance at a time on this box, (c) refuses to start a
paid run without checking the real account balance first, and (d) caps
concurrency in code, not just in a doc. See `stop_openrouter_jobs.sh` for the
matching verified-stop counterpart.
"""
import argparse
import fcntl
import os
import subprocess
import sys
import urllib.request
import json

from inspect_ai import eval_set
from impossiblebench import impossible_livecodebench

SPLITS = ["original", "oneoff", "conflicting"]
MAX_SAFE_CONNECTIONS = 8  # this box has 8 cores; each connection ~= one concurrent Docker sandbox
MIN_BALANCE_TO_START = 1.00  # USD; refuse to start a paid run below this
LOCK_PATH = "/tmp/.run_eval_openrouter_paid.lock"


def is_free_model(model: str) -> bool:
    return model.rstrip("/").endswith(":free")


def check_balance():
    """Real balance check against the live OpenRouter account. Raises SystemExit
    with a clear message rather than letting a paid run start blind -- this is
    exactly the check that was skipped on 2026-09-06."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("REFUSING: OPENROUTER_API_KEY not set, cannot verify balance before a paid run.")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)["data"]
    except Exception as e:
        sys.exit(f"REFUSING: could not verify OpenRouter balance before a paid run ({e}). "
                  f"Fix connectivity/auth first, don't launch blind.")
    remaining = data["total_credits"] - data["total_usage"]
    print(f"[balance check] total_credits={data['total_credits']:.3f} "
          f"total_usage={data['total_usage']:.3f} remaining={remaining:.3f}")
    if remaining < MIN_BALANCE_TO_START:
        sys.exit(f"REFUSING: only ${remaining:.3f} remains in the OpenRouter account "
                  f"(minimum ${MIN_BALANCE_TO_START:.2f} required to start a paid run). "
                  f"Add credits or use a :free model.")
    return remaining


def acquire_single_paid_instance_lock():
    """Refuse to start a second concurrent paid instance on this box -- the exact
    shape of the 2026-09-06 incident (5 paid batches at once). Uses an flock, not
    a PID file, so a killed-but-not-reaped process can't leave a stale lock."""
    fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(
            "REFUSING: another paid run_eval_openrouter.py instance already holds the lock "
            f"({LOCK_PATH}). Only one paid batch runs at a time on this box -- wait for it to "
            "finish, or verify it's actually dead (ps aux, not just a kill exit code) and remove "
            "the stale lock file yourself if you're certain."
        )
    os.write(fd, str(os.getpid()).encode())
    # deliberately leak fd for process lifetime -- the flock releases automatically
    # on process exit (including SIGKILL), which is the whole point.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="openrouter model id, e.g. z-ai/glm-5.2:free")
    parser.add_argument("--label", required=True)
    parser.add_argument("--limit", type=int, default=15, help="samples per split")
    parser.add_argument("--max-connections", type=int, default=2)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--splits", default=",".join(SPLITS))
    args = parser.parse_args()

    if args.max_connections > MAX_SAFE_CONNECTIONS:
        sys.exit(f"REFUSING: --max-connections {args.max_connections} exceeds the hard cap of "
                  f"{MAX_SAFE_CONNECTIONS} on this 8-core box (each connection spawns a Docker "
                  f"sandbox; this is what caused the 2026-09-06 load-average-27 incident). "
                  f"Lower it, or run multiple smaller batches serialized instead of raising this.")

    # Make this process the leader of its own process group, regardless of how it
    # was launched (bash wrapper, nohup, pipeline). A group-kill (`kill -- -PGID`)
    # then always reaches this process even if a parent's plain `kill <pid>` doesn't
    # propagate -- the exact failure that let a paid run survive undetected for 2.5h
    # on 2026-09-06. Harmless if already a group leader (e.g. under setsid).
    try:
        os.setpgrp()
    except OSError:
        pass
    print(f"[pgid] this run's process group id is {os.getpgrp()} (pid {os.getpid()}) -- "
          f"to stop it reliably: kill -- -{os.getpgrp()}, then verify with "
          f"`pgrep -af run_eval_openrouter`, don't trust the kill exit code alone.")

    watchdog_proc = None
    if not is_free_model(args.model):
        check_balance()
        acquire_single_paid_instance_lock()
        print(f"[paid model] {args.model} -- balance checked, single-instance lock held.")
        # Continuous spend monitoring for the lifetime of this run -- the
        # pre-flight check above only gates the START; this is what would have
        # caught the 2026-09-06 incident's second half (a paid run draining the
        # account, unwatched, for 2.5 hours) in minutes instead. Tied to this
        # process's lifetime via subprocess (not detached/disowned) so it can't
        # become yet another orphaned background process itself.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(os.path.join(script_dir, "logs"), exist_ok=True)
        watchdog_proc = subprocess.Popen(
            [os.path.join(script_dir, "spend_watchdog.sh")],
            cwd=script_dir,
            stdout=open(os.path.join(script_dir, "logs", "spend_watchdog.log.stdout"), "a"),
            stderr=subprocess.STDOUT,
        )
        print(f"[spend watchdog] started, pid={watchdog_proc.pid}, polling every 5 min, "
              f"live log: logs/spend_watchdog.log")

    try:
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
            model=f"openrouter/{args.model}",
            log_dir=f"logs/{args.label}",
            max_connections=args.max_connections,
            retry_on_error=2,
            log_dir_allow_dirty=True,
            timeout=2400,
            model_args={"client_timeout": 2400},
        )
    finally:
        # Always tear the watchdog down with this run, success or failure --
        # a lingering watchdog after a normal exit is exactly the kind of
        # orphaned background process this whole fix is trying to prevent.
        if watchdog_proc is not None and watchdog_proc.poll() is None:
            watchdog_proc.terminate()
            try:
                watchdog_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                watchdog_proc.kill()
            print("[spend watchdog] stopped.")


if __name__ == "__main__":
    sys.exit(main())
