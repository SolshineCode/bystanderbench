#!/usr/bin/env python
"""Encode captured residual-stream activations with a published GemmaScope-2 SAE.

Pure linear algebra + JumpReLU -- no HF `generate()`, so this is safe on the
local M40s (see ~/CLAUDE.md failure mode 3).

Layer convention check: GemmaScope-2 config.json says
`hf_hook_point_in = "model.layers.<L>.output"` = output of block L =
hidden_states[L+1] = this project's `l_out-L` capture. They match exactly; the
script asserts the config agrees with the layer it was asked for.

Validity gate: an SAE trained on bf16 HF activations is being applied to
activations captured through llama.cpp on a quantised GGUF. That is a real
basis question, so every run reports fraction-of-variance-unexplained (FVU)
and realised L0 against the SAE's own target L0. A large FVU or a wildly
off-target L0 means the bases do NOT match and the feature analysis below it
is not interpretable -- report the gate, do not bury it.
"""
import argparse, os, sys, json, os, sys
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

def load_acts(rows, layer, slot_i):
    X, keep = [], []
    for r in rows:
        meta = json.load(open(r["prefix"] + ".json"))
        if layer not in meta["layers"]:
            continue
        n_l = len(meta["layers"])
        a = np.fromfile(r["prefix"] + ".bin", dtype=np.float32).reshape(n_l, 3, meta["d_model"])
        X.append(a[meta["layers"].index(layer), slot_i])
        keep.append(r)
    return np.stack(X).astype(np.float32), keep


def load_sae(repo, subdir, layer):
    from huggingface_hub import hf_hub_download
    from safetensors.numpy import load_file
    cfg = json.load(open(hf_hub_download(repo, f"{subdir}/config.json")))
    want = f"model.layers.{layer}.output"
    if cfg.get("hf_hook_point_in") != want:
        sys.exit(f"REFUSING: {repo}/{subdir} hooks {cfg.get('hf_hook_point_in')}, not {want}")
    p = load_file(hf_hub_download(repo, f"{subdir}/params.safetensors"))
    return cfg, p


def jumprelu(x, p):
    pre = x @ p["w_enc"] + p["b_enc"]
    acts = pre * (pre > p["threshold"])
    recon = acts @ p["w_dec"] + p["b_dec"]
    return acts, recon


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def group_perm_p(acts, y, groups, stat_fn, n_perm=2000, seed=0):
    """Permutation p-value that permutes labels at the TASK-GROUP level, so a
    task with several epochs cannot leak its label across the permutation."""
    rng = np.random.default_rng(seed)
    gs = sorted(set(groups))
    g_lab = {}
    for g, yy in zip(groups, y):
        g_lab.setdefault(g, []).append(yy)
    # a group is positive if any of its samples is positive
    base_g = np.array([1 if max(g_lab[g]) else 0 for g in gs])
    gidx = {g: i for i, g in enumerate(gs)}
    memb = np.array([gidx[g] for g in groups])
    obs = stat_fn(acts, y)
    ge = 0
    for _ in range(n_perm):
        pg = rng.permutation(base_g)
        yp = pg[memb]
        if yp.sum() == 0 or yp.sum() == len(yp):
            ge += 1
            continue
        if stat_fn(acts, yp) >= obs:
            ge += 1
    return obs, (ge + 1) / (n_perm + 1)


def max_abs_d(acts, y):
    """Largest per-feature standardised mean difference across all features."""
    p, n = acts[y == 1], acts[y == 0]
    if len(p) < 2 or len(n) < 2:
        return 0.0
    mp, mn = p.mean(0), n.mean(0)
    sd = np.sqrt((p.var(0, ddof=1) * (len(p) - 1) + n.var(0, ddof=1) * (len(n) - 1))
                 / (len(p) + len(n) - 2)) + 1e-9
    return float(np.abs((mp - mn) / sd).max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--sae-repo", required=True)
    ap.add_argument("--sae-family", default="resid_post_all")
    ap.add_argument("--layers", required=True, help="comma-separated")
    ap.add_argument("--width", default="16k")
    ap.add_argument("--l0", default="big")
    ap.add_argument("--slot", default="mean_range", choices=SLOTS)
    ap.add_argument("--pos-cat", default="concealed_cheat")
    ap.add_argument("--neg-cat", default="failed_silent")
    ap.add_argument("--top-k", type=int, default=25)
    ap.add_argument("--n-perm", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = load_model_dir(a.model_dir)
    slot_i = SLOTS.index(a.slot)
    out = {"model_dir": a.model_dir, "sae_repo": a.sae_repo, "family": a.sae_family,
           "width": a.width, "l0": a.l0, "slot": a.slot,
           "pos_cat": a.pos_cat, "neg_cat": a.neg_cat, "layers": {}}

    for layer in [int(x) for x in a.layers.split(",")]:
        subdir = f"{a.sae_family}/layer_{layer}_width_{a.width}_l0_{a.l0}"
        cfg, p = load_sae(a.sae_repo, subdir, layer)
        X, keep = load_acts(rows, layer, slot_i)
        if len(keep) == 0:
            print(f"layer {layer}: no captured activations, skipping")
            continue
        acts, recon = jumprelu(X, p)

        # --- validity gate ---
        resid = X - recon
        fvu = float((resid ** 2).sum() / ((X - X.mean(0)) ** 2).sum())
        l0 = float((acts > 0).sum(1).mean())
        alive = int((acts > 0).any(0).sum())

        cats = np.array([r["category"] for r in keep])
        y = np.where(cats == a.pos_cat, 1, np.where(cats == a.neg_cat, 0, -1))
        m = y >= 0
        groups = [r["task_id"] for r in keep]

        rec = {"n_samples": len(keep), "d_model": int(X.shape[1]),
               "d_sae": int(acts.shape[1]), "target_l0": cfg.get("l0"),
               "fvu": fvu, "realised_l0": l0, "alive_features": alive,
               "n_pos": int((y == 1).sum()), "n_neg": int((y == 0).sum()),
               "cat_counts": {c: int((cats == c).sum()) for c in sorted(set(cats))}}

        if rec["n_pos"] >= 2 and rec["n_neg"] >= 2:
            A, yy = acts[m], y[m]
            gg = [g for g, k in zip(groups, m) if k]
            pos, neg = A[yy == 1], A[yy == 0]
            mp, mn = pos.mean(0), neg.mean(0)
            sd = np.sqrt((pos.var(0, ddof=1) * (len(pos) - 1) + neg.var(0, ddof=1) * (len(neg) - 1))
                         / (len(pos) + len(neg) - 2)) + 1e-9
            d = (mp - mn) / sd
            order = np.argsort(-np.abs(d))[:a.top_k]
            rec["top_features"] = [
                {"feature": int(i), "cohens_d": float(d[i]),
                 "mean_pos": float(mp[i]), "mean_neg": float(mn[i]),
                 "frac_active_pos": float((pos[:, i] > 0).mean()),
                 "frac_active_neg": float((neg[:, i] > 0).mean())}
                for i in order]
            obs, pv = group_perm_p(A, yy, gg, max_abs_d, n_perm=a.n_perm)
            rec["max_abs_d"] = obs
            rec["group_perm_p"] = pv
            rec["n_pos_groups"] = len(set(g for g, k in zip(gg, yy) if k == 1))
        else:
            rec["note"] = "insufficient class counts for differential analysis"

        out["layers"][str(layer)] = rec
        print(f"L{layer:>2} n={rec['n_samples']:>3} FVU={fvu:.3f} L0={l0:.1f}"
              f" (target {cfg.get('l0')}) alive={alive} pos={rec['n_pos']} neg={rec['n_neg']}"
              + (f" max|d|={rec.get('max_abs_d',0):.2f} p={rec.get('group_perm_p','-')}"
                 if "max_abs_d" in rec else ""))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
