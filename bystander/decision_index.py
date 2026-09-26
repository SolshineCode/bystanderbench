#!/usr/bin/env python3
"""Locate each episode's DECISION INDEX and emit a pooling manifest that stops before it.

WHY. `bystander/probe_alert.py` fits a linear probe on pooled residual vectors and its own
docstring says the result is not a result: every pooling slot covers positions that include
the `alert_oversight` escalation, so a direction separating alerting from silent episodes may
be reading the decision or may be reading the presence of the alert. The fix it names is to
re-extract with the pooled window ending BEFORE the decision is emitted. This script computes
that end point and writes a tree `extract_resid` can consume.

RELATION TO `bystander/pool_bounds.py` (§F125). That script solves the same confound by
TRUNCATING the token stream at the decision point. This one keeps the full stream and moves
only the pool range. The two are not interchangeable:

  * `pool_bounds.py` is stricter. `extract_resid` computes slot 0 over ALL positions and
    slot 2 at the LAST position regardless of POOL_START/POOL_END, so in a full-stream tree
    those two slots stay contaminated. Truncation fixes all three at once.
  * This tree is therefore a **slot-1-only artifact**. Any analysis reading slot 0 or slot 2
    out of `acts_nex_predecision/` is reading the confounded quantity §F124 already rejected.
    That is a limitation of the approach, not an oversight; it is stated here so a later
    reader cannot miss it.
  * In exchange it keeps the teacher-forced stream byte-identical to the capture, so the
    pre-decision window and the original final-turn window are measured on the same forward
    pass and are directly comparable.

WHAT THE DECISION INDEX IS. The number of tokens in the rendered prefix up to and EXCLUDING
the first assistant message that carries an `alert_oversight` tool call -- i.e. exactly the
prompt the model had in front of it at the moment it began the turn in which it escalated.
Not one token of the escalation turn is inside it.

  Cut rule = "first alert CALL", which is what this script was asked for. §F125 found that
  the permissive rule leaves a lexical cue in one window of 28: an episode deliberated about
  escalating several turns before it acted, so the literal string `alert_oversight` sits
  inside its pre-decision window while no silent episode has anything of the kind. A probe
  can read that string. `pool_bounds.py --cut-at mention` exists for that reason. This script
  does NOT implement the mention rule; if a probe fit on this tree separates the classes, the
  lexical cue is a live alternative explanation and must be ruled out before any claim.

THE MATCHED-INDEX RULE FOR SILENT EPISODES, stated in full because it is load-bearing and
because the rule as originally specified was measured to LEAK and had to be changed.

A silent episode has no decision point. Giving it the end of the episode would hand the probe
a cue -- window position -- that tracks the label perfectly, trading one leaking artifact for
a quieter one. So each silent episode gets a SYNTHETIC index drawn, with a fixed seed
(default 20260914), from the alerting episodes of a donor pool.

  THE TEST THAT DECIDES WHETHER THE RULE WORKED, printed on every run: the AUC of
  (decision_index / n_tokens) ALONE at separating alerting from silent. If position alone
  separates the classes, a probe fit on this tree can read position instead of internal state
  and the confound has merely been moved. 0.5 is the target. §F125's equivalent was 0.481.
  Every silent episode here is `with_tool`, so the `with_tool` row is the meaningful one; the
  all-arms row is dragged by the six `tool_probe` floor episodes, which alert at 2-4% of the
  episode by instruction and have no silent counterparts.

  Three rules were implemented and measured on this corpus (98 episodes, 24 alerting):

    --match ratio --snap at_or_before   with_tool AUC 0.689   THE LITERAL BRIEF. LEAKS.
        Draw decision_index/n_tokens, multiply by this episode's length, snap back to the
        nearest assistant-turn boundary at or before the target. The DRAW is unbiased (AUC
        0.473 against the raw targets) but the backwards snap is not: turns get long late in
        an episode, so snapping strictly backwards loses a median 0.114 and a mean 0.163 of
        fraction, pushing every silent window systematically earlier than the alerting ones.
    --match ratio --snap nearest        with_tool AUC 0.387   LEAKS THE OTHER WAY.
        Removes the snap bias (median loss -0.007) but silent windows now land later than
        alerting ones, because the 74 silent episodes' boundary grids do not cover the same
        fractional positions as the 18 with_tool alerting decision points.
    --match turnrank                    with_tool AUC 0.513   DEFAULT.
        Draw the alerting turn's RANK counted back from the last turn, and take that turn.
        Matching the discrete structure a boundary snap has to land on removes the problem at
        source: there is no continuous target to round, so there is no rounding bias.

  `--match ratio --snap at_or_before` reproduces the literal brief exactly and is kept so the
  0.689 figure can be re-derived rather than taken on trust.

  Donor pool, all three rules. The episode's own capture batch, RESTRICTED TO THE SAME
  `tool_arm`. The restriction is not cosmetic: §F125 found that floor (`tool_probe`) episodes
  INSTRUCT an immediate escalation, so their decision points sit at 2-4% of the episode, and
  mixing them into the pool dragged the median matched fraction from 0.81 to 0.05 and cut
  every silent episode to a stub. `bystander-nex-local-n6` holds both arms, so an unrestricted
  per-batch pool would hit exactly that trap. When a batch has fewer than `--min-donors`
  alerting episodes of the right arm the pool falls back to every alerting episode of that arm
  across all processed batches, and the episode records `matched_pool: "global"`. On this
  corpus 52 of 74 silent episodes take the global fallback, because six of the eight batches
  have only 1-2 alerters.

  LIMITATIONS THAT REMAIN EVEN AT AUC 0.513, all real:
   - The rule makes index position uninformative about the label BY CONSTRUCTION. It does not
     make it CORRECT. There is no fact of the matter about when a silent episode "decided", so
     the silent class's windows are arbitrary in a way the alerting class's are not, and a
     probe that separates them is not thereby reading "the decision".
   - The donor pool is 18 `with_tool` alerting episodes for 74 silent ones, and 52 of those
     draws come from the pooled global set rather than the episode's own batch. The silent
     windows inherit that small pool's idiosyncrasies. Small-N applies to the MATCHING, not
     only to whatever probe is fit afterwards.
   - AUC 0.513 is a point estimate on n=18 vs n=74. It is consistent with chance; it is not
     proof of chance. Re-check it at the seed actually used before quoting it.

VERIFICATION, which is the point of the script. The rebuilt prefix's token ids must be an
EXACT PREFIX of the already-captured `<cid>.txt`. Two things make that non-trivial:

  * These captures predate the §F151 fix, so `capture_activations.py` as it runs TODAY does
    not reproduce them -- today's version carries `tool_call_id` / `tool_calls` through to the
    template and the older captures did not. `--selftest` renders ep5 of `nex-pos-g` the
    modern way and gets 10381 tokens against the captured 10192. This script therefore
    rebuilds messages as bare `{role, content}`, matching the code at capture time, and
    re-derives the FULL stream first to confirm it reproduces `n_tokens` before trusting any
    prefix of it. `--selftest` is the reproducible demonstration that both prefix guards
    actually refuse: it checks a positive control and the two constructed negatives.
  * The chat template appends an assistant generation prompt to whatever it is handed, so
    `msgs[:j]` is an exact token prefix only when `msgs[j]` is itself an assistant message
    (the appended header then coincides with the real one). Measured on nex-pos-g ep5:
    prefixes before an assistant turn match exactly; prefixes before a tool turn diverge six
    tokens from the end. Only boundaries that pass a byte-level prefix check are eligible.

  A side effect worth recording: `capture_activations.py` computes `pool_start` by rendering
  `msgs[:-1]`, and in these episodes the LAST message is often a `tool` result rather than an
  assistant turn, so that render appends a generation prompt the real stream does not have
  and `pool_start` overshoots the true start of the final message (nex-pos-g ep5: recorded
  10128, true boundary 10082). Small, pre-existing, and not fixed here -- this script does not
  modify the original trees -- but it means the published "final assistant turn" slot is
  really "the last ~60 tokens", and for a tool-terminated episode it is not an assistant turn
  at all.

WHY `pool_start` IS 0 AND NOT THE CAPTURED VALUE. The brief asked for `pool_end = decision
index` with `pool_start` unchanged. That range is INVERTED on this corpus and cannot be used:
the captured `pool_start` is the start of the final turn, which lands near the very end of the
episode, while the escalation happens earlier -- in all four alerting episodes of the smoke
batch the decision index is 46 to 5928 tokens BEFORE `pool_start`, so `[pool_start,
decision_index)` is empty and `extract_resid` would divide by zero. `--pool-start orig`
reproduces the literal request and REFUSES on any episode where the range inverts, so the
claim is checkable rather than asserted. The default `--pool-start zero` pools over
`[0, decision_index)`, which is the slot-1 semantics §F125's truncated trees already have and
is the only version that is comparable to them. The captured value is preserved per episode as
`orig_pool_start` in `decision_index.json` either way.

`manifest_lastwindow.tsv` is written alongside as an optional second view: the same streams
pooled over `[decision_index - W, decision_index)`, W = `--window`. The `[0, decision_index)`
mean is roughly 90% shared system prompt and evidence documents, identical across episodes in
a batch, so it dilutes whatever signal exists; the trailing window is what the model was
processing immediately before it committed. It writes to `acts_lastwindow/` so it cannot
collide with the primary extraction. Running it is optional and costs a second GPU pass.

KNOWN INTEGRATION HAZARD. `probe_alert.py` selects `bystander/acts_nex_*.predecision` under
`--predecision` and every other `bystander/acts_nex_*` otherwise. The output directory name
`acts_nex_predecision` (no dot) matches NEITHER intent: it is swept into the default branch
alongside the original trees, where the §F127 duplicate-cid guard drops it because
`acts_nex_cd` sorts first. So once the bins exist, probe_alert's default mode will silently
ignore this tree and its `--predecision` mode will not see it. Point probe_alert at the
directory explicitly, or rename it to end in `.predecision`, before reading anything from it.

Usage:
    # smoke, one batch
    .venv/bin/python bystander/decision_index.py --port 8098 --batch bystander-nex-pos-g
    # full run, all batches
    .venv/bin/python bystander/decision_index.py --port 8098

Requires a llama-server on the SAME model and template as the capture, used only for
/apply-template, /tokenize and /detokenize. None of those touch a GPU slot; a CPU-only server
(`-ngl 0 --no-warmup -c 512`) is enough and is what this was developed against.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bystander.capture_activations import flatten, post, tpl  # noqa: E402

ALERT = "alert_oversight"
BASE = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = ["bystander/acts_nex_local", "bystander/acts_nex_pos",
                "bystander/acts_nex_scale", "bystander/acts_nex_cd"]


# --------------------------------------------------------------------------- rebuild

def rebuild(sample, schema="pre_f151"):
    """Rebuild the message list as `capture_activations.py` did AT CAPTURE TIME.

    Two capture schemas exist and the difference is ~10% of rendered length, which is fatal
    to the prefix assertion this whole module rests on.

    `schema="pre_f151"` (default) rebuilds bare `{role, content}`, mirroring the capture code
    as it stood before 2026-09-13. Every tree written on or before 2026-09-12 needs this, and
    it stays the default so earlier fits reproduce byte for byte.

    `schema="f151"` also forwards `tool_call_id` on tool turns and normalised `tool_calls` on
    assistant turns, exactly as `capture_activations.py` does after the §F151 fix. Trees
    captured from 2026-09-13 onward need this; with the default they fail the prefix check by
    roughly 10-14% of tokens, which is how the agent-perpetrator trees announced themselves on
    2026-09-15. The `.meta.json` `n_tokens` check in `episode_plan()` is what makes the claim
    testable rather than assumed, and it is doing its job either way: a wrong schema refuses
    rather than cutting at a plausible but wrong index.

    Returns (msgs, alert_at) where `alert_at` is the index of the first assistant message
    carrying an `alert_oversight` tool call, or None.
    """
    msgs, alert_at = [], None
    for m in (sample.messages or []):
        role = getattr(m, "role", None)
        if role not in ("system", "user", "assistant", "tool"):
            continue
        txt = flatten(getattr(m, "content", ""))
        tcs = getattr(m, "tool_calls", None)
        if role == "assistant" and not txt.strip() and tcs:
            txt = "[tool call]"
        if not txt.strip():
            continue
        if schema == "f151":
            tcid = getattr(m, "tool_call_id", None)
            if role == "tool" and tcid:
                _extra = {"tool_call_id": tcid}
            else:
                _extra = {}
            if role == "assistant" and tcs:
                rebuilt = []
                for tc in tcs:
                    fn = getattr(tc, "function", None)
                    name = getattr(fn, "name", None) or getattr(tc, "function", None) or "tool"
                    args = getattr(fn, "arguments", None) if fn is not None else None
                    if args is None:
                        args = getattr(tc, "arguments", None)
                    if not isinstance(args, str):
                        try:
                            args = json.dumps(args if args is not None else {})
                        except Exception:
                            args = "{}"
                    rebuilt.append({"id": getattr(tc, "id", None) or name,
                                    "type": "function",
                                    "function": {"name": name if isinstance(name, str) else "tool",
                                                 "arguments": args}})
                if rebuilt:
                    _extra["tool_calls"] = rebuilt
        else:
            _extra = {}
        if role == "assistant" and tcs and alert_at is None:
            if any(ALERT in str(getattr(tc, "function", tc)) for tc in tcs):
                alert_at = len(msgs)
        msgs.append({"role": role, "content": txt, **_extra})

    # The trailing-assistant merge the capture applies. If the alerting turn is swallowed by
    # the merge, the decision point moves to the start of the merged turn -- which is the
    # honest answer, since after the merge there is no earlier boundary that excludes it.
    tail = 0
    while tail < len(msgs) and msgs[len(msgs) - 1 - tail]["role"] == "assistant":
        tail += 1
    if tail >= 2:
        n_before = len(msgs)
        merged = "\n\n".join(m["content"] for m in msgs[-tail:])
        msgs = msgs[:-tail] + [{"role": "assistant", "content": merged}]
        if alert_at is not None and alert_at >= n_before - tail:
            alert_at = len(msgs) - 1
    return msgs, alert_at


def toks(port, msgs):
    prompt = tpl(port, msgs)
    return post(port, "/tokenize", {"content": prompt,
                                    "add_special": False, "parse_special": True})["tokens"]


def detok(port, ids):
    return post(port, "/detokenize", {"tokens": list(ids)})["content"]


# --------------------------------------------------------------------------- pass 1

def episode_plan(port, meta, stored, sample, schema="pre_f151"):
    """Locate the decision point and every VERIFIED assistant-turn boundary for one episode.

    "Verified" means the prefix's token ids are byte-identical to `stored[:len]`. A boundary
    that fails is dropped rather than repaired: an unverified index would put the pool window
    somewhere the model never was, which is the exact class of error this script exists to
    remove.
    """
    msgs, alert_at = rebuild(sample, schema)
    full = toks(port, msgs)
    if full != stored:
        return dict(ok=False, why=f"full rebuild differs from capture "
                                  f"({len(full)} vs {len(stored)} tokens)")

    bounds = {}          # message index -> token index, verified prefixes only
    bad = []
    for j in range(2, len(msgs)):
        if msgs[j]["role"] != "assistant":
            continue
        t = toks(port, msgs[:j])
        if stored[:len(t)] == t:
            bounds[j] = len(t)
        else:
            bad.append(j)

    dec = bounds.get(alert_at) if alert_at is not None else None
    if alert_at is not None and dec is None:
        why = (f"alert turn at message {alert_at} has no verified boundary "
               f"({'too early to render' if alert_at < 2 else 'prefix check failed'})")
        return dict(ok=False, why=why, alert_at=alert_at)
    return dict(ok=True, msgs=len(msgs), alert_at=alert_at, decision_index=dec,
                bounds=bounds, unverified=bad, n_tokens=len(stored))


# --------------------------------------------------------------------------- self-test

def selftest(port, ep_dir, cid):
    """Prove the two guards say NO on the failures they exist to catch.

    A guard never seen to refuse is not evidence of anything, and neither of these refuses
    during a normal run: the full-stream check passes on every episode, and the prefix check
    is only ever offered boundaries that satisfy it by construction. So construct the
    negatives explicitly.

      NEGATIVE 1 -- modern rendering. Rebuild the SAME episode the way `capture_activations.py`
      runs today (forwarding `tool_call_id` / `tool_calls`, the §F151 fix). These trees were
      written before that fix, so the render must NOT reproduce the captured stream. If this
      ever passes, the bare rebuild is no longer what made the captures and every decision
      index in the tree is measured against the wrong text.

      NEGATIVE 2 -- boundary before a non-assistant message. The template appends an assistant
      generation prompt to whatever it renders, so a prefix ending before a `tool` or `user`
      turn must diverge from the captured stream. If this ever passes, the snap-back rule may
      silently place a pool window at a position the model never occupied.
    """
    from inspect_ai.log import read_eval_log
    dp = BASE / ep_dir
    md = json.loads((dp / (cid + ".meta.json")).read_text())
    stored = [int(x) for x in (dp / (cid + ".txt")).read_text().split()]
    log = read_eval_log(str(list((BASE / "logs").glob(f"*/{md['eval_file']}"))[0]))
    sample = log.samples[md["episode"] - 1]
    ok = True

    # positive control first: the bare rebuild MUST reproduce the capture, or the negatives
    # below prove nothing.
    msgs, _ = rebuild(sample)
    if toks(port, msgs) == stored:
        print(f"  PASS positive control: bare rebuild reproduces {len(stored)} captured tokens")
    else:
        print("  FAIL positive control: bare rebuild does not reproduce the capture"); ok = False

    modern = []
    for m in (sample.messages or []):
        role = getattr(m, "role", None)
        if role not in ("system", "user", "assistant", "tool"):
            continue
        txt = flatten(getattr(m, "content", ""))
        tcs = getattr(m, "tool_calls", None)
        if role == "assistant" and not txt.strip() and tcs:
            txt = "[tool call]"
        if not txt.strip():
            continue
        out = {"role": role, "content": txt}
        tcid = getattr(m, "tool_call_id", None)
        if role == "tool" and tcid:
            out["tool_call_id"] = tcid
        if role == "assistant" and tcs:
            rb = []
            for tc in tcs:
                fn = getattr(tc, "function", None)
                name = getattr(fn, "name", None) or "tool"
                args = getattr(fn, "arguments", None) if fn is not None else None
                if not isinstance(args, str):
                    args = json.dumps(args if args is not None else {})
                rb.append({"id": getattr(tc, "id", None) or name, "type": "function",
                           "function": {"name": name, "arguments": args}})
            if rb:
                out["tool_calls"] = rb
        modern.append(out)
    t = toks(port, modern)
    if t == stored:
        print(f"  FAIL negative 1: modern rendering reproduced the capture ({len(t)} tokens); "
              "the bare-rebuild premise no longer holds"); ok = False
    else:
        print(f"  PASS negative 1: modern rendering rejected ({len(t)} tokens vs "
              f"{len(stored)} captured)")

    tried = 0
    for j in range(2, len(msgs)):
        if msgs[j]["role"] == "assistant":
            continue
        tried += 1
        tj = toks(port, msgs[:j])
        if stored[:len(tj)] == tj:
            print(f"  FAIL negative 2: prefix before a {msgs[j]['role']!r} turn at message "
                  f"{j} passed the prefix check"); ok = False
        if tried >= 3:
            break
    if tried and ok:
        print(f"  PASS negative 2: {tried} prefixes before non-assistant turns all rejected")
    return ok


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8098)
    ap.add_argument("--dirs", nargs="*", default=DEFAULT_DIRS)
    ap.add_argument("--position-auc-band", nargs=2, type=float, default=(0.40, 0.60),
                    metavar=("LO", "HI"),
                    help="refuse to write the tree unless cut position alone separates alerting "
                         "from silent within this AUC band. F125's good tree measured 0.481; the "
                         "F189 failure measured 0.705.")
    ap.add_argument("--allow-unmatched-cut", action="store_true",
                    help="write the tree even if the position gate fails. For deliberately "
                         "studying the confound, never for getting a number out.")
    ap.add_argument("--capture-schema", choices=["pre_f151", "f151"], default="pre_f151",
                    help="message schema the tree was captured with. pre_f151 (default) for "
                         "trees written on or before 2026-09-12; f151 for 2026-09-13 onward, "
                         "which forward tool_call_id and tool_calls and render ~10%% longer.")
    ap.add_argument("--out", default="bystander/acts_nex_predecision")
    ap.add_argument("--batch", default=None,
                    help="only episodes whose cid starts with this (smoke runs)")
    ap.add_argument("--seed", type=int, default=20260914)
    ap.add_argument("--min-donors", type=int, default=3,
                    help="alerting episodes needed in a batch+tool_arm before its own ratios "
                         "are used; below this the global same-arm pool is used instead")
    ap.add_argument("--pool-start", choices=["zero", "orig"], default="zero",
                    help="'zero' pools [0, decision_index). 'orig' reproduces the literal "
                         "brief, [captured pool_start, decision_index), and REFUSES when that "
                         "range inverts -- which it does on this corpus.")
    ap.add_argument("--window", type=int, default=256,
                    help="width of the auxiliary trailing-window manifest")
    ap.add_argument("--quantile-rank", choices=["pool", "global"], default="pool",
                    help="quantile mode only. 'pool' (default since 2026-09-20) ranks each silent "
                         "episode among the silents of the same donor pool (its batch, or the "
                         "global pool on fallback). 'global' is the 2026-09-19 behaviour that "
                         "ranked across all batches and skewed per-batch cuts; kept for re-derivation.")
    ap.add_argument("--match", choices=["ratio", "turnrank", "turnfrac", "quantile"], default="turnrank",
                    help="'ratio' draws decision_index/n_tokens (the brief). 'turnrank' draws "
                         "the alerting turn's rank counted back from the last turn, which "
                         "matches the DISCRETE structure a boundary snap has to land on.")
    ap.add_argument("--snap", choices=["at_or_before", "nearest"], default="nearest",
                    help="where a silent episode's drawn target is snapped to a real "
                         "assistant-turn boundary. See the matched-rule section of the module "
                         "docstring: 'at_or_before' is the literal brief and MEASURABLY LEAKS "
                         "on this corpus; 'nearest' is the default for that reason.")
    ap.add_argument("--link", choices=["symlink", "copy"], default="symlink")
    ap.add_argument("--show", type=int, default=0,
                    help="detokenise the cut for this many alerting episodes")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="prove both prefix guards refuse on constructed negatives, then exit")
    a = ap.parse_args()

    if a.selftest:
        print("self-test on bystander/acts_nex_pos ep5 (nex-pos-g):")
        return 0 if selftest(
            a.port, "bystander/acts_nex_pos",
            "bystander-nex-pos-g__blatant_wrongdoing_with_tool_native_tools_ep5") else 1

    from inspect_ai.log import read_eval_log

    # ---- gather episodes
    eps = []
    for d in a.dirs:
        dp = BASE / d
        for mp in sorted(dp.glob("*.meta.json")):
            md = json.loads(mp.read_text())
            cid = md["cid"]
            if a.batch and not cid.startswith(a.batch):
                continue
            tf = dp / (cid + ".txt")
            if not tf.is_file():
                print(f"skip {cid}: no token file")
                continue
            hits = list((BASE / "logs").glob(f"*/{md['eval_file']}"))
            if not hits:
                print(f"skip {cid}: eval log {md['eval_file']} not found")
                continue
            eps.append(dict(cid=cid, dir=dp, tf=tf, meta=md, eval_path=hits[0],
                            batch=cid.split("__")[0],
                            tool_arm=md.get("tool_arm"),
                            episode=md["episode"],
                            alerted=(md.get("scores", {}).get("bystander_scorer", {})
                                     or {}).get("alerted")))
    if not eps:
        print("no episodes matched")
        return 1
    print(f"{len(eps)} episodes from {len(a.dirs)} trees"
          + (f" (batch filter {a.batch})" if a.batch else ""))

    # ---- pass 1: decision points + verified boundaries
    by_eval = {}
    for e in eps:
        by_eval.setdefault(e["eval_path"], []).append(e)
    fails = []
    for p, its in sorted(by_eval.items()):
        log = read_eval_log(str(p))
        samples = log.samples or []
        for e in sorted(its, key=lambda x: x["episode"]):
            i = e["episode"]
            if i < 1 or i > len(samples):
                fails.append((e["cid"], f"episode {i} absent from {p.name}")); continue
            stored = [int(x) for x in e["tf"].read_text().split()]
            if len(stored) != e["meta"]["n_tokens"]:
                fails.append((e["cid"], "token file length disagrees with meta n_tokens"))
                continue
            plan = episode_plan(a.port, e["meta"], stored, samples[i - 1], a.capture_schema)
            if not plan["ok"]:
                fails.append((e["cid"], plan["why"])); continue
            e.update(plan); e["stored"] = stored
        print(f"  {p.name}: {len([e for e in its if e.get('ok')])}/{len(its)} planned",
              flush=True)

    if fails:
        print("\nREFUSING TO WRITE -- prefix/plan failures:")
        for cid, why in fails:
            print(f"  {cid}: {why}")
        return 2
    ok = [e for e in eps if e.get("ok")]

    # ---- pass 2: matched draws for silent episodes
    rng = np.random.default_rng(a.seed)
    alerting = [e for e in ok if e["decision_index"] is not None]
    silent = [e for e in ok if e["decision_index"] is None]
    n_bounds = sum(len(e["bounds"]) for e in ok)
    n_bad = sum(len(e["unverified"]) for e in ok)
    print(f"\n{len(alerting)} alerting (decision point located), {len(silent)} silent")
    print(f"assistant-turn boundaries: {n_bounds} verified as exact token prefixes, "
          f"{n_bad} rejected by the prefix check and dropped")
    if not alerting:
        print("no alerting episodes: there is no distribution to match against")
        return 3

    def ratios(pool):
        return np.array([e["decision_index"] / e["n_tokens"] for e in pool], dtype=float)

    global_pool = {}
    for e in alerting:
        global_pool.setdefault(e["tool_arm"], []).append(e)
    batch_pool = {}
    for e in alerting:
        batch_pool.setdefault((e["batch"], e["tool_arm"]), []).append(e)

    for e in alerting:
        e["rule"] = "first_alert"
        e["matched_pool"] = None
        keys = sorted(e["bounds"])
        e["turnrank"] = (len(keys) - keys.index(e["alert_at"])) if e["alert_at"] in keys else None
        e["turnfrac"] = (keys.index(e["alert_at"]) / max(1, len(keys) - 1)) if e["alert_at"] in keys else None
    # 2026-09-20 (batch-rank fix, owed by the 09-19 session summary). The quantile rule ranked
    # every silent episode GLOBALLY by cid and used len(silent) as the denominator, while the
    # donor distribution it indexed into was the episode's OWN batch pool. cids sort by batch
    # prefix, so in a two-batch tree the first batch's silents took the low quantiles and the
    # second batch's the high ones: the pooled position-AUC still passed the gate (0.507 on the
    # 09-19 holdout) but per batch it sat at 0.63-0.86. Ranking is now done inside the same
    # group the donors come from (the batch+tool_arm pool, or the global tool_arm pool when the
    # batch fell back). `--quantile-rank global` reproduces the 09-19 trees exactly.
    silent_rank_batch, silent_rank_global = {}, {}
    for key in {(e["batch"], e["tool_arm"]) for e in silent}:
        grp = sorted((e for e in silent if (e["batch"], e["tool_arm"]) == key), key=lambda x: x["cid"])
        for i, e in enumerate(grp):
            silent_rank_batch[e["cid"]] = (i, len(grp))
    for ta in {e["tool_arm"] for e in silent}:
        grp = sorted((e for e in silent if e["tool_arm"] == ta), key=lambda x: x["cid"])
        for i, e in enumerate(grp):
            silent_rank_global[e["cid"]] = (i, len(grp))
    silent_order = {e["cid"]: i for i, e in enumerate(sorted(silent, key=lambda x: x["cid"]))}
    for e in sorted(silent, key=lambda x: x["cid"]):        # sorted => seed is reproducible
        key = (e["batch"], e["tool_arm"])
        pool, which = batch_pool.get(key, []), "batch"
        if len(pool) < a.min_donors:
            pool, which = global_pool.get(e["tool_arm"], []), "global"
        if not pool:
            fails.append((e["cid"], f"no alerting donor for tool_arm={e['tool_arm']}"))
            continue
        if a.match == "quantile":
            # 2026-09-19. turnrank gave position-AUC 0.705 (alerting cut far later) and turnfrac
            # gave 0.388 (alerting cut earlier); both were refused by the gate. Both draw a value
            # at random per episode, so the silent DISTRIBUTION only matches the alerting one in
            # expectation, and at n=24 it does not. This mode matches the distributions by
            # construction: the silent episodes are ranked by cid (stable, seed-free), and the
            # i-th of m gets the (i+0.5)/m quantile of the alerting cut fractions, then snaps to
            # the nearest available turn boundary. Quantile matching is what the gate is actually
            # asking for, and random draws were never going to satisfy it reliably.
            donors = sorted(ratios(pool))
            if donors:
                if a.quantile_rank == "global":
                    idx_s, m = silent_order[e["cid"]], len(silent)          # 09-19 behaviour
                elif which == "batch":
                    idx_s, m = silent_rank_batch[e["cid"]]
                else:
                    idx_s, m = silent_rank_global[e["cid"]]
                e["quantile_rank"] = f"{a.quantile_rank}:{idx_s}/{m}"
                q = (idx_s + 0.5) / max(1, m)
                pos = min(len(donors) - 1, max(0, int(round(q * (len(donors) - 1)))))
                target_ratio = donors[pos]
            else:
                target_ratio = 0.5
            target = target_ratio * e["n_tokens"]
            vals = list(e["bounds"].values())
            e["decision_index"] = min(vals, key=lambda v: abs(v - target)) if vals else 0
            e["snap"] = "quantile_nearest"
            e["rule"] = "matched"; e["matched_pool"] = which
            e["drawn_ratio"] = target_ratio
            continue
        if a.match == "turnfrac":
            # 2026-09-17 (F189). `turnrank` draws the donor's rank COUNTED FROM THE END and
            # applies it to a different episode: idx = len(keys) - rk. Alerting episodes run
            # longer, so rk routinely exceeds a silent episode's whole turn count, idx goes
            # negative, max(0, ...) pins the cut to turn zero, and the episode is represented
            # by its system prompt. On the agent-arm tree that hit 14 of 24 silent episodes and
            # produced a meaningless AUC of 0.921. This mode draws the donor's RELATIVE turn
            # position and applies it to the silent episode's own turn count, so a short
            # transcript gets a proportionally early cut instead of a degenerate one.
            donors = [d["turnfrac"] for d in pool if d.get("turnfrac") is not None]
            keys = sorted(e["bounds"])
            fr = float(rng.choice(donors)) if donors else 0.5
            idx = int(round(fr * (len(keys) - 1)))
            e["drawn_turnfrac"] = fr
            e["decision_index"] = e["bounds"][keys[max(0, min(idx, len(keys) - 1))]]
            e["snap"] = "turnfrac"
            e["rule"] = "matched"; e["matched_pool"] = which
            e["drawn_ratio"] = e["decision_index"] / e["n_tokens"]
            continue
        if a.match == "turnrank":
            donors = [d["turnrank"] for d in pool if d["turnrank"]]
            keys = sorted(e["bounds"])
            rk = int(rng.choice(donors)) if donors else 1
            e["drawn_turnrank"] = rk
            idx = max(0, len(keys) - rk)
            e["decision_index"] = e["bounds"][keys[min(idx, len(keys) - 1)]]
            e["snap"] = "turnrank"
            e["rule"] = "matched"; e["matched_pool"] = which
            e["drawn_ratio"] = e["decision_index"] / e["n_tokens"]
            continue
        r = float(rng.choice(ratios(pool)))
        target = int(round(r * e["n_tokens"]))
        vals = list(e["bounds"].values())
        cand = [v for v in vals if v <= target]
        if a.snap == "nearest" and vals:
            e["decision_index"] = min(vals, key=lambda v: (abs(v - target), v))
            e["snap"] = "nearest"
        elif cand:
            e["decision_index"] = max(cand)
            e["snap"] = "at_or_before"
        else:
            e["decision_index"] = min(vals) if vals else None
            e["snap"] = "snap_fallback"
        if e["decision_index"] is None:
            fails.append((e["cid"], "no verified assistant-turn boundary to snap to"))
            continue
        e["rule"] = "matched"
        e["matched_pool"] = which
        e["drawn_ratio"] = r
        e["drawn_target"] = target

    if fails:
        print("\nREFUSING TO WRITE -- matching failures:")
        for cid, why in fails:
            print(f"  {cid}: {why}")
        return 2

    # ---- inverted-range check for the literal-brief mode
    if a.pool_start == "orig":
        bad = [(e["cid"], e["meta"]["pool_start"], e["decision_index"])
               for e in ok if e["meta"]["pool_start"] >= e["decision_index"]]
        if bad:
            print(f"\nREFUSING TO WRITE -- --pool-start orig inverts the pool range on "
                  f"{len(bad)}/{len(ok)} episodes (pool_start >= decision_index). "
                  f"extract_resid would pool an empty span. Use --pool-start zero.")
            for cid, ps, di in bad[:10]:
                print(f"  {cid}: pool_start={ps} decision_index={di}")
            return 2

    # ---- report the distribution
    fr_a = np.array([e["decision_index"] / e["n_tokens"] for e in alerting])
    fr_s = np.array([e["decision_index"] / e["n_tokens"] for e in silent])
    def summ(name, v):
        if not len(v):
            return f"  {name}: (none)"
        return (f"  {name}: n={len(v)} min {v.min():.3f} q25 {np.percentile(v,25):.3f} "
                f"median {np.median(v):.3f} q75 {np.percentile(v,75):.3f} max {v.max():.3f}")
    print("\ndecision_index / n_tokens")
    print(summ("alerting (first_alert)", fr_a))
    print(summ("silent   (matched)    ", fr_s))

    # THE number that says whether the matched rule did its job. If window position alone
    # separates the classes, a probe fit on this tree can read position instead of state and
    # the confound has only been moved. §F125's equivalent was 0.481.
    def auc(score, lab):
        order = np.argsort(score); rank = np.empty(len(score)); rank[order] = np.arange(1, len(score) + 1)
        n1, n0 = lab.sum(), (1 - lab).sum()
        return float("nan") if n1 == 0 or n0 == 0 else (rank[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    fr = np.concatenate([fr_a, fr_s]); lab = np.concatenate([np.ones(len(fr_a)), np.zeros(len(fr_s))])
    print(f"  AUC of position alone, all arms : {auc(fr, lab):.3f}")
    wt_a = np.array([e["decision_index"] / e["n_tokens"] for e in alerting if e["tool_arm"] == "with_tool"])
    wt_s = np.array([e["decision_index"] / e["n_tokens"] for e in silent if e["tool_arm"] == "with_tool"])
    if len(wt_a) and len(wt_s):
        print(f"  AUC of position alone, with_tool: "
              f"{auc(np.concatenate([wt_a, wt_s]), np.concatenate([np.ones(len(wt_a)), np.zeros(len(wt_s))])):.3f}"
              "   <- the one that matters; 0.5 is the target")
    # ---- THE GATE (F189, added 2026-09-17) ------------------------------------------
    # The AUC above was printed by this script on 2026-09-16 and was 0.705, and the run
    # carried on and wrote a tree anyway. A probe was then fitted on it and returned 0.921,
    # which was reported, and only a later hand analysis found that alerting episodes were cut
    # at 78.8% of their transcript and silent ones at 5.3%. A diagnostic nobody is forced to
    # read is not a control. Refuse instead of printing.
    _gate_a, _gate_s = (wt_a, wt_s) if (len(wt_a) and len(wt_s)) else (fr_a, fr_s)
    if len(_gate_a) and len(_gate_s):
        _g = auc(np.concatenate([_gate_a, _gate_s]),
                 np.concatenate([np.ones(len(_gate_a)), np.zeros(len(_gate_s))]))
        _lo, _hi = a.position_auc_band
        if not (_lo <= _g <= _hi):
            print(f"\n!! REFUSING TO WRITE THE TREE: cut position alone separates alerting from "
                  f"silent at AUC {_g:.3f}, outside the required band [{_lo}, {_hi}].")
            print(f"   alerting cut fraction median {np.median(_gate_a):.3f}, "
                  f"silent {np.median(_gate_s):.3f}.")
            print("   A probe fitted on this tree would be reading window position, not state.")
            print("   Try --match turnfrac (preserves relative turn position; --match turnrank "
                  "pins short transcripts to turn zero, which is what caused F189).")
            print("   Override with --allow-unmatched-cut only if you intend to report position "
                  "as a confound rather than control for it.")
            if not a.allow_unmatched_cut:
                return 2
            print("   --allow-unmatched-cut given: continuing with a KNOWN confounded tree.")
        else:
            print(f"  GATE PASS: position-alone AUC {_g:.3f} inside [{_lo}, {_hi}]")
    if a.match == "ratio" and silent:
        lost = np.array([e["drawn_ratio"] - e["decision_index"] / e["n_tokens"] for e in silent])
        print(f"  snap loss (drawn ratio - realised): median {np.median(lost):+.3f} "
              f"mean {lost.mean():+.3f}")

    # ---- optional hand-check excerpts
    for e in sorted(alerting, key=lambda x: x["cid"])[:a.show]:
        k = e["decision_index"]
        print(f"\n--- {e['cid']}  decision_index={k} / {e['n_tokens']}")
        print("  BEFORE (last ~30 tokens of the pooled window):")
        print("    " + repr(detok(a.port, e["stored"][max(0, k - 30):k])))
        print("  AFTER (first ~15 tokens, excluded from the window):")
        print("    " + repr(detok(a.port, e["stored"][k:k + 15])))

    if a.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    # ---- write the tree
    out = BASE / a.out
    (out / "acts").mkdir(parents=True, exist_ok=True)
    (out / "acts_lastwindow").mkdir(parents=True, exist_ok=True)
    rows, rows_w, index = [], [], {}
    for e in sorted(ok, key=lambda x: x["cid"]):
        cid, k = e["cid"], e["decision_index"]
        tf = out / (cid + ".txt")
        if tf.is_symlink() or tf.exists():
            tf.unlink()
        if a.link == "symlink":
            tf.symlink_to(e["tf"].resolve())
        else:
            shutil.copy2(e["tf"], tf)
        ps = 0 if a.pool_start == "zero" else e["meta"]["pool_start"]
        rows.append(f"{tf}\t{out/'acts'/cid}\t{ps}\t{k}")
        rows_w.append(f"{tf}\t{out/'acts_lastwindow'/cid}\t{max(0, k - a.window)}\t{k}")
        (out / (cid + ".meta.json")).write_text(json.dumps(dict(
            e["meta"], decision_index=k, orig_pool_start=e["meta"]["pool_start"],
            pool_start=ps, pool_end=k, rule=e["rule"], matched_pool=e["matched_pool"],
            snap=e.get("snap"), drawn_ratio=e.get("drawn_ratio"),
            cut_mode="call", source_dir=str(e["dir"]),
        ), indent=1))
        index[cid] = dict(decision_index=k, n_tokens=e["n_tokens"],
                          pool_start=e["meta"]["pool_start"], rule=e["rule"],
                          alerted=e["alerted"], batch=e["batch"], tool_arm=e["tool_arm"],
                          matched_pool=e["matched_pool"], snap=e.get("snap"),
                          drawn_ratio=e.get("drawn_ratio"),
                          manifest_pool_start=ps,
                          fraction=k / e["n_tokens"])
    (out / "manifest.tsv").write_text("\n".join(rows) + "\n")
    (out / "manifest_lastwindow.tsv").write_text("\n".join(rows_w) + "\n")
    (out / "decision_index.json").write_text(json.dumps(dict(
        _meta=dict(
            script="bystander/decision_index.py", seed=a.seed, cut_mode="call",
            pool_start_mode=a.pool_start, window=a.window, min_donors=a.min_donors,
            snap=a.snap, match=a.match,
            dirs=a.dirs, batch_filter=a.batch,
            note=("slot 1 only: extract_resid computes slot 0 over all positions and slot 2 "
                  "at the last position regardless of the pool range, so in this full-stream "
                  "tree those two slots remain confounded exactly as in the originals."),
        ), episodes=index), indent=1))
    print(f"\nwrote {len(rows)} rows -> {out}/manifest.tsv")
    print(f"      {len(rows_w)} rows -> {out}/manifest_lastwindow.tsv (pool width {a.window})")
    print(f"      {out}/decision_index.json")
    print("next: RESID_MANIFEST=<manifest> extract_resid over the new manifest (GPU), "
          "then probe_alert.py pointed AT THIS DIRECTORY -- see the integration hazard in "
          "the module docstring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
