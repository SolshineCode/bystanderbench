#!/usr/bin/env python3
"""H5: does incident 1 get reported because its evidence arrives EARLIER in the episode?

§F110 rejected four explanations for the within-model incident effect (9/48 on incident 1,
1/48 on incident 2, 0/48 on incident 3) and named this as the next axis, chosen because it
is the remaining STRUCTURAL difference rather than a fifth content hypothesis guessed from
the text: incident 1's evidence sits in a file the ticket sends the agent to read, so it
arrives in the course of the assigned work, while incidents 2 and 3 place it adjacent to
that path. It needs no new episodes.

PREDICTION AND KILL CONDITION, recorded here before the numbers were read, in the §F104
template. H5 is supported only if BOTH hold:
  (a) between incidents: first-evidence turn is EARLIER in incident 1 than in incidents
      2 and 3, by a margin that is not a coin flip; and
  (b) within incident 1: episodes that alert met the evidence EARLIER than episodes that
      did not.
Either one failing kills it. (b) is the load-bearing half. A between-incident difference on
its own is confounded with everything else that differs between incidents, which is the
error §F110 exists to avoid; only the within-incident gradient tests the mechanism.

Usage:  python bystander/turn_index.py logs/bystander-nex-* --cache /tmp/bb-env
"""
from __future__ import annotations
import argparse, glob, os, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inspect_ai.log import read_eval_log                              # noqa: E402
from inspect_ai.model import ChatMessageTool, ChatMessageUser         # noqa: E402
from bystander.env.build_env import build_env                      # noqa: E402
from bystander.report import MIN_EVIDENCE_LINE, SHARED_PATHS      # noqa: E402


def first_evidence_turn(sample, root: Path, man: dict):
    """Index of the first observation message carrying a verbatim evidence-only line.

    Counts the SAME message kinds report.py's discovery counts (tool results, or exit=
    user turns in the prompted CLI loop), so an episode discovered here iff it is
    discovered there. Returns (turn, n_turns) or (None, n_turns) if never discovered.
    """
    lines = []
    for rel in (man.get("evidence_paths") or []):
        if rel in SHARED_PATHS:
            continue
        f = root / rel
        if f.is_file():
            lines += [ln.strip() for ln in f.read_text().splitlines()
                      if len(ln.strip()) >= MIN_EVIDENCE_LINE]
    msgs = sample.messages or []
    obs = [m for m in msgs if isinstance(m, ChatMessageTool)]
    if not obs:
        obs = [m for m in msgs
               if isinstance(m, ChatMessageUser) and (m.text or "").startswith("exit=")]
    for i, m in enumerate(obs):
        t = m.text or ""
        if any(ln in t for ln in lines):
            return i, len(obs)
    return None, len(obs)


def mwu(a, b):
    """Mann-Whitney U as a normal approximation, with the tie correction. Small enough to
    read; scipy is not a dependency of this repo's reporting path."""
    import math
    n1, n2 = len(a), len(b)
    if not n1 or not n2:
        return float("nan"), float("nan")
    allv = sorted(a + b)
    ranks = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2 + 1
        ranks[allv[i]] = r
        i = j + 1
    r1 = sum(ranks[v] for v in a)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    ties = {}
    for v in allv:
        ties[v] = ties.get(v, 0) + 1
    tc = sum(t**3 - t for t in ties.values())
    n = n1 + n2
    sd = math.sqrt(n1 * n2 / 12 * ((n + 1) - tc / (n * (n - 1)))) if n > 1 else 0.0
    if sd == 0:
        return u1, float("nan")
    z = (u1 - mu) / sd
    p = math.erfc(abs(z) / math.sqrt(2))
    return u1, p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/bb-env")
    ap.add_argument("--tool-arm", default="with_tool")
    ap.add_argument("logs", nargs="+")
    a = ap.parse_args()

    envs, rows = {}, []
    for d in a.logs:
        for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
            try:
                log = read_eval_log(p)
            except Exception:
                continue
            ta = log.eval.task_args or {}
            if "arm" not in ta or log.status != "success":
                continue
            if ta.get("tool_arm") != a.tool_arm:
                continue
            for s in (log.samples or []):
                if getattr(s, "error", None):
                    continue
                sc = next(iter(s.scores.values()))
                md = s.metadata or {}
                arm, seed, man = md.get("arm"), md.get("seed"), md.get("manifest") or {}
                key = (arm, seed)
                if key not in envs:
                    out = Path(a.cache) / f"{arm}-{seed}"
                    if not out.exists():
                        build_env(arm, seed, out)
                    envs[key] = out
                turn, nturns = first_evidence_turn(s, envs[key], man)
                rows.append(dict(arm=arm, alerted=int(bool(sc.value.get("alerted"))),
                                 turn=turn, nturns=nturns))

    arms = sorted({r["arm"] for r in rows})
    print(f"{len(rows)} episodes, tool_arm={a.tool_arm}\n")
    print(f"{'arm':<34}{'n':>4}{'disc':>6}{'alert':>7}{'median turn':>13}{'IQR':>14}")
    per = {}
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        d = [r["turn"] for r in rs if r["turn"] is not None]
        per[arm] = d
        q = (f"{sorted(d)[len(d)//4]}-{sorted(d)[3*len(d)//4]}" if len(d) >= 4 else "-")
        med = f"{statistics.median(d):.1f}" if d else "-"
        print(f"{arm:<34}{len(rs):>4}{len(d):>6}{sum(r['alerted'] for r in rs):>7}"
              f"{med:>13}{q:>14}")

    # (a) BETWEEN incidents.
    print("\n(a) between incidents: is incident 1's evidence met earlier?")
    base = "blatant_wrongdoing"
    if base in per:
        for arm in arms:
            if arm == base or not per[arm]:
                continue
            u, p = mwu(per[base], per[arm])
            print(f"    {base} vs {arm}: median {statistics.median(per[base]):.1f} vs "
                  f"{statistics.median(per[arm]):.1f}, Mann-Whitney p = {p:.3f}")

    # (b) WITHIN incident 1 -- the load-bearing half.
    print("\n(b) within an arm: do alerting episodes meet the evidence earlier?")
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm and r["turn"] is not None]
        al = [r["turn"] for r in rs if r["alerted"]]
        no = [r["turn"] for r in rs if not r["alerted"]]
        if not al or not no:
            print(f"    {arm}: {len(al)} alerted / {len(no)} not -- no contrast available")
            continue
        u, p = mwu(al, no)
        print(f"    {arm}: alerted median {statistics.median(al):.1f} (n={len(al)}) vs "
              f"silent median {statistics.median(no):.1f} (n={len(no)}), "
              f"Mann-Whitney p = {p:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
