#!/usr/bin/env python3
"""Does an episode's residual stream predict whether the agent will report the misconduct?

THE POINT. Part 1 built a probe for concealment and got a negative result. Part 2 has
measured the bystander behaviour across nine models but has never looked inside one. This is
the missing half: a linear probe for the reporting decision, on the one open-weight model
that produces both classes.

DESIGN, and why it is shaped this way.

Unit: one episode, one pooled residual vector per (layer, slot). The capture writes
[n_layers][3][d_model] float32, slot 0 = mean over all positions, slot 1 = mean over the
final assistant turn, slot 2 = last position.

Held-out unit: the CAPTURE BATCH (the source log directory), never the episode. Every episode
in one arm shares a single deterministic environment, so held-out episodes are not independent
of trained ones, and an episode-level split would report a number that means nothing (§F101 is
the entry about exactly this error at the reporting layer). Batches are separate runs on
separate days, which is the weakest honest grouping available.

Direction: difference of class means. Logistic regression is reported but never used for
selection, following the Part 1 discipline.

Null: permute labels WITHIN batch and refit, so the null preserves the batch structure. A
permutation that ignores batch would be testing whether batches differ, not whether alerting
does.

Transfer: the incident-1 direction is applied unchanged to `blatant_wrongdoing_noaddressee`,
which is a different environment with its own alerts. That is the only test here that is not
within-environment, so it is the one worth believing.

⛔ READ THIS BEFORE QUOTING ANY NUMBER THIS PRINTS. The probe is confounded by
construction and the AUC is not a result. All three pooling slots cover positions that
INCLUDE the escalation itself: slot 0 is the mean over every position in the episode, slot 1
the mean over the final assistant turn, slot 2 the last position. An episode that alerted
contains the `alert_oversight` call and its summary text inside the pooled window; an episode
that stayed silent does not. So a direction separating them may be reading the decision, or
it may be reading the presence of the alert, and nothing here distinguishes those. That the
best cell is layer 1 of 8 points the wrong way: an early layer separating the classes is what
you would expect from surface token statistics rather than from a decision represented
mid-stack. This is the same shape as Part 1's feature 655, which separated 4 cheats from 120
non-cheats at p < 1/5001 and turned out to be a generic function-word component.

THE FIX, which needs one GPU pass and no new episodes. `extract_resid` already takes a pool
range, and `capture_activations.py` already records `pool_start` per episode. Re-extract with
POOL_END set to the token index of the first `alert_oversight` call (or, for silent episodes,
a matched index drawn from the alerting distribution) so the pooled window ends BEFORE the
decision is emitted. Only then is "does the residual stream predict reporting" a question this
script can answer. Until that run exists, what follows is a scaffold with a known-fatal
confound, kept because the scaffold is the slow part.

Usage:  python bystander/probe_alert.py --out research/canonical/probe_alert.json
"""
from __future__ import annotations
import argparse, glob, json, os, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SLOTS = ["mean_all", "mean_final_turn", "last"]


def labels_for(logdirs):
    """cid -> (alerted, arm, src). Reproduces capture_activations.py's cid exactly,
    including `enumerate(samples, 1)`, so a mismatch here is a real inconsistency and not a
    naming drift."""
    from inspect_ai.log import read_eval_log
    out = {}
    for d in logdirs:
        for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
            try:
                log = read_eval_log(p)
            except Exception:
                continue
            ta = log.eval.task_args or {}
            if log.status != "success":
                continue
            arm, tool_arm = ta.get("arm"), ta.get("tool_arm")
            aff = ta.get("affordance", "native")
            solver = ta.get("solver_kind", "tools")
            src = os.path.basename(os.path.normpath(d))
            for i, s in enumerate(log.samples or [], 1):
                cid = f"{src}__{arm}_{tool_arm}_{aff}_{solver}_ep{i}"
                if getattr(s, "error", None):
                    continue
                sc = next(iter(s.scores.values()))
                v = sc.value if isinstance(sc.value, dict) else {}
                out[cid] = (int(bool(v.get("alerted"))), arm, tool_arm, src)
    return out


def load(actdirs, lab, explicit=()):
    """DEDUPES BY CID, loudly. Two capture directories can point at the same bins: on
    2026-09-12 `acts_nex_scale.5layer/manifest.tsv` was found pointing at
    `acts_nex_scale/acts/...`, so 24 episodes were loaded twice and the first run of this
    probe reported n = 114 for 90 unique episodes (§F127). That is the CLAUDE.md rule about
    activation-backed analyses having to dedupe, and an exclusion list keyed on directory
    names would not have caught it — the directory name said `.5layer` while the bins were
    the 8-layer ones. Dedupe on the cid, which is what actually identifies an episode.

    2026-09-19 (checkpoint-2 review of §F198). Dropping a duplicate is only correct when the
    two copies are the SAME activations. A re-cut tree (`acts_nex_agentarm.predecision3`,
    quantile-matched, gate 0.447) holds the same cids as the withdrawn §F189 trees
    (`acts_nex_agentarm.predecision`, gate 0.713) that `--predecision` still globs, and the
    old tree sorted first, so the §F198 fit silently kept 8 silent episodes at the withdrawn
    cuts, 5 of them at 316 tokens (the system prompt), while the ledger said the fit ran on
    the gated tree. Two rules now: (1) trees named explicitly with `--extra-actdir` are loaded
    FIRST and win the dedupe over globbed defaults, and the count of overridden copies is
    printed; (2) a duplicate cid whose activations differ between two trees of the SAME
    standing (both globbed, or both explicit) is a conflict, and the load refuses, because
    which copy wins would otherwise be decided by sort order. Identical copies still dedupe
    silently as before."""
    X, y, arm, src, cids, tree, fs = [], [], [], [], [], [], []
    seen: dict[str, tuple[str, str]] = {}      # cid -> (bin path, actdir)
    n_dup = n_overridden = 0
    conflicts: list[tuple[str, str, str]] = []
    explicit = {str(Path(d).resolve()) for d in explicit}
    ordered = ([d for d in actdirs if str(Path(d).resolve()) in explicit]
               + [d for d in actdirs if str(Path(d).resolve()) not in explicit])
    for d in ordered:
        man = Path(d) / "manifest.tsv"
        if not man.is_file():
            continue
        is_explicit = str(Path(d).resolve()) in explicit
        for line in man.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            binp = parts[1] + ".bin"
            cid = os.path.basename(parts[1])
            if cid not in lab or not os.path.isfile(binp):
                continue
            # 2026-09-19 (checkpoint-2 review of §F198). A tree written by decision_index.py
            # keeps the FULL token stream and sets only the manifest's pool range, and
            # extract_resid honours that range for slot 1 alone: slot 0 is the mean over ALL
            # positions and slot 2 the last position of the whole stream (extract_resid.cpp
            # lines 24-26; decision_index.py's own _meta.note says the same). On such a tree
            # `mean_all` and `last` are the §F124 full-episode pooling, escalation included,
            # whatever the cut says. Verified: predecision3's slot-0 vectors are cos 1.0000
            # with the raw acts_nex_agentarm capture for every episode. §F183, §F188 and §F198
            # all reported a `mean_all` cell from such trees. Record per episode whether the
            # stream is longer than its pool_end, so main() can refuse to search those slots.
            try:
                n_txt = sum(1 for _ in open(parts[0]).read().split())
                full_stream = len(parts) >= 4 and n_txt > int(parts[3])
            except (OSError, ValueError):
                full_stream = True      # unknown is treated as unsafe
            if cid in seen:
                n_dup += 1
                kept_bin, kept_dir = seen[cid]
                same = (os.path.getsize(kept_bin) == os.path.getsize(binp)
                        and np.array_equal(np.fromfile(kept_bin, dtype=np.float32),
                                           np.fromfile(binp, dtype=np.float32)))
                if same:
                    continue
                kept_explicit = str(Path(kept_dir).resolve()) in explicit
                if kept_explicit and not is_explicit:
                    n_overridden += 1          # explicit tree already won; fine, counted
                else:
                    conflicts.append((cid, kept_dir, d))
                continue
            seen[cid] = (binp, d)
            a = np.fromfile(binp, dtype=np.float32)
            if a.size % (3 * 2048):
                continue
            nl = a.size // (3 * 2048)
            X.append(a.reshape(nl, 3, 2048))
            al, ar, ta, sr = lab[cid]
            y.append(al); arm.append(ar); src.append(sr); cids.append(cid)
            tree.append(os.path.basename(os.path.normpath(d))); fs.append(bool(full_stream))
    if n_dup:
        print(f"!! dropped {n_dup} duplicate cid(s): two manifests referenced the same "
              f"episode. Counted once each. See §F127.")
    if n_overridden:
        print(f"!! {n_overridden} of those carried DIFFERENT activations in a globbed tree; "
              f"the copy from the explicitly passed --extra-actdir tree was kept.")
    if conflicts:
        dirs = sorted({os.path.basename(os.path.normpath(x)) for _, a_, b_ in conflicts
                       for x in (a_, b_)})
        print(f"!! REFUSING TO LOAD: {len(conflicts)} cid(s) have DIFFERENT activations in "
              f"two trees of the same standing ({', '.join(dirs)}). Which copy wins would be "
              f"decided by sort order, which is how §F198's fit kept 8 silent episodes at the "
              f"withdrawn §F189 cuts. Pass the tree that should win as --extra-actdir, or "
              f"rename the superseded tree so the --predecision glob no longer matches it.")
        for cid, a_, b_ in conflicts[:5]:
            print(f"     {cid}\n        {a_}\n        {b_}")
        return None
    if not X:
        return None
    nl = min(x.shape[0] for x in X)
    return (np.stack([x[:nl] for x in X]), np.array(y), np.array(arm),
            np.array(src), np.array(cids), np.array(tree), np.array(fs))


def auc(scores, y):
    pos, neg = scores[y == 1], scores[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float((pos[:, None] > neg[None, :]).mean()
                 + 0.5 * (pos[:, None] == neg[None, :]).mean())


def loo_scores(X, y, grp):
    """Leave-one-batch-out held-out scores from a difference-of-means direction."""
    s = np.full(len(y), np.nan)
    for g in np.unique(grp):
        tr, te = grp != g, grp == g
        if y[tr].sum() == 0 or (1 - y[tr]).sum() == 0:
            continue
        w = X[tr][y[tr] == 1].mean(0) - X[tr][y[tr] == 0].mean(0)
        n = np.linalg.norm(w)
        if n == 0:
            continue
        s[te] = X[te] @ (w / n)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="blatant_wrongdoing")
    ap.add_argument("--transfer-arm", default="blatant_wrongdoing_noaddressee")
    ap.add_argument("--perms", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--predecision", action="store_true",
                    help="use the §F125 pre-decision truncated captures instead of the full "
                         "episodes. This is the only version whose AUC means anything.")
    ap.add_argument("--out")
    # 2026-09-15: the agent-perpetrator arm lives in logs/bystander-agentarm-nex-* and
    # bystander/acts_nex_agentarm, which the default globs below do not match (they are keyed
    # to the `bystander-nex-*` naming used before that arm existed). These two flags ADD to the
    # default sets rather than replacing them, so every earlier fit reproduces byte for byte
    # when they are not passed.
    ap.add_argument("--extra-logdir", action="append", default=[],
                    help="additional eval logdir to read labels from (repeatable)")
    ap.add_argument("--extra-actdir", action="append", default=[],
                    help="additional activation tree to load (repeatable)")
    a = ap.parse_args()

    base = Path(__file__).resolve().parent.parent
    logdirs = sorted(str(p) for p in (base / "logs").glob("bystander-nex-*") if p.is_dir())
    if a.predecision:
        actdirs = sorted(str(p) for p in base.glob("bystander/acts_nex_*.predecision")
                         if p.is_dir())
    else:
        actdirs = sorted(str(p) for p in base.glob("bystander/acts_nex_*")
                         if p.is_dir() and "STALE" not in p.name
                         and "CORRUPT" not in p.name and "DUPMANIFEST" not in p.name
                         and not p.name.endswith(".predecision"))
    logdirs = sorted(set(logdirs) | {str(Path(d).resolve()) for d in a.extra_logdir})
    actdirs = sorted(set(actdirs) | {str(Path(d).resolve()) for d in a.extra_actdir})
    lab = labels_for(logdirs)
    got = load(actdirs, lab, explicit=a.extra_actdir)
    if got is None:
        print("no captured episodes matched a label, or the load refused; nothing to fit")
        return 1
    X, y, arm, src, cids, tree, fs = got
    nl = X.shape[1]
    print(f"{len(y)} captured episodes with labels, {nl} layers, "
          f"{len(np.unique(arm))} arms, {len(np.unique(src))} capture batches\n")

    m = arm == a.arm
    Xa, ya, ga, ta_ = X[m], y[m], src[m], tree[m]
    print(f"{a.arm}: n={len(ya)}, alerted={ya.sum()}, batches={len(np.unique(ga))}")
    # Provenance from inside the artifact (METHODOLOGY-v1.1 §1): which activation tree each
    # fitted episode actually came from. §F198's JSON listed batches only, which is how a
    # fit over two trees of the same cids read as "the gated tree".
    _per_tree = {str(t): int((ta_ == t).sum()) for t in np.unique(ta_)}
    print(f"  activation trees: {_per_tree}")
    # Which slots are honest for THIS set. On a full-stream (decision_index.py) tree only
    # slot 1 is pooled inside the pre-decision window; slots 0 and 2 are the whole episode.
    # Searching them and calling the result "pre-decision" is what §F183/§F188/§F198 did.
    n_full = int(fs[m].sum())
    slots_ok = [1] if (a.predecision and n_full) else [0, 1, 2]
    if a.predecision and n_full:
        print(f"!! {n_full} of {len(ya)} fitted episodes come from FULL-STREAM trees (the .txt is "
              f"longer than its pool_end). extract_resid pools slot 0 over ALL positions and "
              f"slot 2 at the LAST position regardless of the range, so `mean_all` and `last` "
              f"include the escalation itself. Searching `mean_final_turn` (the [pool_start, "
              f"pool_end) mean) ONLY.")
    if ya.sum() < 3 or (1 - ya).sum() < 3 or len(np.unique(ga)) < 2:
        print("refusing to fit: needs >=3 per class across >=2 capture batches")
        return 1

    rng = np.random.default_rng(a.seed)
    # 2026-09-15: this key used to be written unconditionally, so a --predecision fit, whose
    # whole purpose is to remove the leak, still carried a CONFOUNDED label in its artifact.
    # A provenance field that does not track what was actually run is worse than none: it
    # either gets ignored (and then the real confounded runs slip through) or believed (and
    # then a clean number is thrown away). It now states the window mode that ran.
    _window = ("pre-decision: transcripts cut at the commit-to-escalate index, matched cut "
               "positions for silent episodes (F134/F167 leak fix)" if a.predecision else
               "CONFOUNDED: pooling window includes the escalation; see module docstring")
    res = {"window": _window,
           "confounded": (not a.predecision),
           "arm": a.arm, "n": int(len(ya)), "alerted": int(ya.sum()),
           "batches": sorted(set(map(str, np.unique(ga)))),
           "episodes_per_actdir": _per_tree,
           "full_stream_episodes": n_full,
           "slots_searched": [SLOTS[i] for i in slots_ok],
           "actdirs_explicit": sorted(os.path.basename(os.path.normpath(d))
                                      for d in a.extra_actdir),
           "layers": int(nl),
           "perms": a.perms, "cells": []}
    best = None
    for L in range(nl):
        for si, sname in enumerate(SLOTS):
            if si not in slots_ok:
                continue
            V = Xa[:, L, si, :]
            s = loo_scores(V, ya, ga)
            ok = ~np.isnan(s)
            if ok.sum() < 10 or ya[ok].sum() == 0:
                continue
            A = auc(s[ok], ya[ok])
            # Null: permute labels WITHIN batch, refit, recompute held-out AUC.
            null = []
            for _ in range(a.perms):
                yp = ya.copy()
                for g in np.unique(ga):
                    idx = np.flatnonzero(ga == g)
                    yp[idx] = rng.permutation(yp[idx])
                sp = loo_scores(V, yp, ga)
                o2 = ~np.isnan(sp)
                if o2.sum() and yp[o2].sum():
                    null.append(auc(sp[o2], yp[o2]))
            p = (1 + sum(v >= A for v in null)) / (1 + len(null)) if null else float("nan")
            cell = dict(layer=L, slot=sname, auc=round(A, 4), p=round(p, 4),
                        n_scored=int(ok.sum()))
            res["cells"].append(cell)
            if best is None or A > best["auc"]:
                best = cell

    res["cells"].sort(key=lambda c: -c["auc"])
    if not a.predecision:
        # This banner used to print unconditionally, including on --predecision runs,
        # which made it noise; it now tracks the mode, like the `window` field (§F183 #2).
        print("\n!! CONFOUNDED BY CONSTRUCTION: every pooling slot includes the escalation "
              "itself.\n!! These AUCs may be reading the presence of the alert, not the "
              "decision to send it.\n!! Do not quote them. See the module docstring for the "
              "re-extraction that fixes it.")
    print(f"\n{'layer':>6}{'slot':>18}{'AUC':>8}{'p':>9}{'n':>6}")
    for c in res["cells"][:8]:
        print(f"{c['layer']:>6}{c['slot']:>18}{c['auc']:>8.3f}{c['p']:>9.4f}{c['n_scored']:>6}")
    # Multiplicity is not a footnote: nl*3 cells were searched.
    ncells = len(res["cells"])
    res["n_cells_searched"] = ncells
    if best:
        res["best"] = dict(best, p_bonferroni=round(min(1.0, best["p"] * ncells), 4))
        print(f"\nbest: layer {best['layer']} / {best['slot']}, AUC {best['auc']:.3f}, "
              f"p = {best['p']:.4f}, Bonferroni over {ncells} cells = "
              f"{res['best']['p_bonferroni']:.4f}")

    # TRANSFER: the only test here that crosses environments.
    t = arm == a.transfer_arm
    if best and t.sum() and y[t].sum():
        L, si = best["layer"], SLOTS.index(best["slot"])
        w = Xa[ya == 1][:, L, si, :].mean(0) - Xa[ya == 0][:, L, si, :].mean(0)
        w = w / (np.linalg.norm(w) or 1.0)
        st = X[t][:, L, si, :] @ w
        At = auc(st, y[t])
        res["transfer"] = dict(arm=a.transfer_arm, n=int(t.sum()),
                               alerted=int(y[t].sum()), auc=round(At, 4))
        print(f"\ntransfer to {a.transfer_arm}: n={t.sum()}, alerted={y[t].sum()}, "
              f"AUC {At:.3f}  <- the only cross-environment number here")
    else:
        res["transfer"] = None
        print(f"\ntransfer to {a.transfer_arm}: not available "
              f"(n={int(t.sum())}, alerted={int(y[t].sum()) if t.sum() else 0})")

    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=2) + "\n")
        print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
