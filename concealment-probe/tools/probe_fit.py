#!/usr/bin/env python3
"""Fit and evaluate a concealment probe on residual-stream activations.

Reimplementation of the Trial 2 v4 validation discipline (from its documented
methodology -- the original script is not on this machine):
  - linear direction per layer, fit on concealed vs disclosed pooled activations
      primary: difference of class means (robust at small n)
      secondary: logistic regression (only reported, not used for selection)
  - held-out GROUPS (task_id), not held-out samples: leave-one-group-out CV
  - permutation test on the eval side only: held-out scores are computed once
    from the real labels' fits; the null is built by permuting labels across
    groups (never refitting on flipped labels)
  - layer sweep across all extracted layers

Inputs: one or more <data>/<model_tag> dirs from prepare_dataset.py + extract_resid.
Outputs: results JSON + printed report.
"""
import argparse, os, sys, glob, json, os, sys
import numpy as np

SLOTS = ["mean_all", "mean_range", "last"]


def load_model_dir(d):
    """Rows that have an activation file, one per sid.

    Unit is `activation` and it is declared explicitly: `acts/{sid}.bin` is keyed by sid
    and later writes overwrite, so two rows sharing a sid share ONE .bin and loading both
    double-counts (this is what produced n=129 for 99 real samples once). Delegated to
    `corpus.py` (§F41) so this rule lives in one place instead of being re-derived in
    every consumer.

    Caveat carried by the data, not by this function: for a colliding sid the .bin came
    from whichever generation was extracted last, and which one that was is not recorded
    anywhere. In this corpus only one colliding sid disagrees on category, so labels are
    safe, but the activation and the row text can be from different generations.
    """
    import os
    from corpus import load
    rows = []
    for r in load(os.path.join(d, "samples.jsonl"), unit="activation"):
        pre = os.path.join(d, "acts", r["sid"])
        if os.path.exists(pre + ".bin"):
            r["prefix"] = pre
            rows.append(r)
    return sorted(rows, key=lambda r: r["sid"])

def auroc(scores, labels):
    scores, labels = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # rank-based AUROC with tie handling
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def fit_meandiff(X, y):
    mu1, mu0 = X[y == 1].mean(0), X[y == 0].mean(0)
    w = mu1 - mu0
    n = np.linalg.norm(w)
    return w / n if n > 0 else w


def fit_logreg(X, y, l2=1.0, iters=500, lr=0.1):
    # simple ridge-regularized logistic regression via gradient descent on
    # standardized features (numpy only; sklearn not assumed)
    mu, sd = X.mean(0), X.std(0) + 1e-8
    Xs = (X - mu) / sd
    w = np.zeros(X.shape[1]); b = 0.0
    for _ in range(iters):
        z = Xs @ w + b
        p = 1 / (1 + np.exp(-z))
        g = Xs.T @ (p - y) / len(y) + l2 * w / len(y)
        gb = (p - y).mean()
        w -= lr * g; b -= lr * gb
    # return direction in original space
    wd = w / sd
    n = np.linalg.norm(wd)
    return wd / n if n > 0 else wd


def logo_scores(X, y, groups, fitter):
    """leave-one-group-out: returns held-out score per sample."""
    scores = np.zeros(len(y), float)
    for g in np.unique(groups):
        te = groups == g
        tr = ~te
        if len(np.unique(y[tr])) < 2:
            scores[te] = np.nan
            continue
        w = fitter(X[tr], y[tr])
        # center by train mean so scores are comparable across folds
        c = X[tr].mean(0)
        scores[te] = (X[te] - c) @ w
    return scores


def group_permutation_pvalue(scores, y, groups, n_perm=10000, rng=None):
    """Permutation on the eval side only: scores stay fixed; group label
    vectors are shuffled across groups. Requires labels to be a property we
    can permute at group level; if labels are heterogeneous within groups we
    permute the within-group label multisets as blocks (documented caveat)."""
    rng = rng or np.random.default_rng(0)
    ok = ~np.isnan(scores)
    scores, y, groups = scores[ok], y[ok], groups[ok]
    obs = auroc(scores, y)
    ug = np.unique(groups)
    blocks = [np.where(groups == g)[0] for g in ug]
    label_blocks = [y[b] for b in blocks]
    sizes = [len(b) for b in blocks]
    null = []
    for _ in range(n_perm):
        # shuffle label blocks among groups with identical sizes
        perm_labels = [None] * len(blocks)
        order = np.arange(len(blocks))
        for sz in set(sizes):
            idx = [i for i, s in enumerate(sizes) if s == sz]
            src = rng.permutation(idx)
            for i, j in zip(idx, src):
                perm_labels[i] = label_blocks[j]
        yp = np.empty_like(y)
        for b, lb in zip(blocks, perm_labels):
            yp[b] = lb
        a = auroc(scores, yp)
        if not np.isnan(a):
            null.append(a)
    null = np.array(null)
    p = (1 + (null >= obs).sum()) / (1 + len(null))
    return obs, p, null


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+", help="model data dirs (data/<model_tag>)")
    ap.add_argument("--slot", default="mean_range", choices=SLOTS)
    ap.add_argument("--pos-cat", default="concealed_cheat")
    ap.add_argument("--neg-cat", default="disclosed")
    ap.add_argument("--n-perm", type=int, default=10000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--transfer", action="store_true",
                    help="if 2+ dirs: also fit on dir0 samples, test on dir1")
    args = ap.parse_args()

    rows = []
    for d in args.dirs:
        rows += load_model_dir(d)
    use = [r for r in rows if r["category"] in (args.pos_cat, args.neg_cat)]
    if not use:
        print("no usable samples"); sys.exit(1)
    # Cross-model pooling guards (found live 2026-09-04: qwen3.6 has 13 extracted
    # layers, OLMoE 8 -- indexing by list position across ALL rows overran the
    # shorter arrays with IndexError).
    d_models = sorted({r["X"].shape[-1] for r in use})
    if len(d_models) > 1:
        print(f"cannot pool models with different d_model {d_models}: activations "
              f"are not stack-compatible; run per-model or use --transfer between "
              f"same-width models only")
        sys.exit(1)
    n_common = min(len(r["layers"]) for r in use)
    layer_lists = {tuple(r["layers"]) for r in use}
    if len(layer_lists) > 1:
        print(f"NOTE: pooled rows have different layer sweeps {sorted(layer_lists)}; "
              f"comparing by LAYER POSITION over the first {n_common} positions "
              f"(position i = i-th extracted layer of each model, NOT the same depth)")
        layers = list(range(n_common))          # positional indices
        layer_label = lambda li: "pos" + str(li)
    else:
        layers = use[0]["layers"][:n_common]
        layer_label = lambda li: str(layers[li])
    slot = SLOTS.index(args.slot)
    y = np.array([1 if r["category"] == args.pos_cat else 0 for r in use])
    groups = np.array([r["task_id"] for r in use])
    models = np.array([r["model"] for r in use])
    print(f"n={len(use)}  pos({args.pos_cat})={int(y.sum())}  neg({args.neg_cat})={int((1-y).sum())}  "
          f"groups={len(np.unique(groups))}  models={dict(zip(*np.unique(models, return_counts=True)))}")

    results = {"n": len(use), "n_pos": int(y.sum()), "n_neg": int((1 - y).sum()),
               "n_groups": int(len(np.unique(groups))), "slot": args.slot,
               "pos_cat": args.pos_cat, "neg_cat": args.neg_cat, "layers": {}}

    for li in range(len(layers)):
        lab = layer_label(li)
        X = np.stack([r["X"][li, slot] for r in use])
        res = {}
        for name, fitter in (("meandiff", fit_meandiff), ("logreg", fit_logreg)):
            s = logo_scores(X, y, groups, fitter)
            obs, p, _ = group_permutation_pvalue(s, y, groups, n_perm=args.n_perm)
            res[name] = {"auroc": None if np.isnan(obs) else round(float(obs), 4),
                         "p_perm": round(float(p), 5)}
        results["layers"][lab] = res
        print(f"layer {lab:>5s}: meandiff AUROC={res['meandiff']['auroc']} p={res['meandiff']['p_perm']}  "
              f"logreg AUROC={res['logreg']['auroc']} p={res['logreg']['p_perm']}")

    if args.transfer and len(args.dirs) >= 2:
        r0 = [r for r in use if r["model"] == use[0]["model"]]
        other = [r for r in use if r["model"] != use[0]["model"]]
        if r0 and other and len(set(r["category"] for r in r0)) == 2:
            results["transfer"] = {}
            for li in range(len(layers)):
                Xa = np.stack([r["X"][li, slot] for r in r0])
                ya = np.array([1 if r["category"] == args.pos_cat else 0 for r in r0])
                Xb = np.stack([r["X"][li, slot] for r in other])
                yb = np.array([1 if r["category"] == args.pos_cat else 0 for r in other])
                w = fit_meandiff(Xa, ya)
                sb = (Xb - Xa.mean(0)) @ w
                results["transfer"][layer_label(li)] = {"auroc": round(float(auroc(sb, yb)), 4),
                                                        "n_test": len(yb)}
            print("cross-model transfer (fit on", r0[0]["model"], "test on", other[0]["model"], "):")
            for L, v in results["transfer"].items():
                print(f"  layer {L}: AUROC={v['auroc']} (n={v['n_test']})")

    if args.out:
        json.dump(results, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
