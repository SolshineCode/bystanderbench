#!/usr/bin/env python3
"""qwen3.6 analysis: first dataset with a real local concealed_cheat sample.

A. census
B. disclosed(2) vs failed_silent(62): first LOGO-definable contrast of the
   session (positives span 2 task groups). Mean-diff direction, LOGO by task,
   eval-side-only group permutation, layer sweep. n_pos=2 -> reported as
   exploratory, minimum achievable p is limited by group-permutation count.
C. task-controlled lcbhard_9 triplet: concealed (c3/oneoff) vs failed_silent
   (early/oneoff, same task+split+model) vs disclosed (early/conflicting).
D. concealed-sample outlier check vs the failed_silent distribution per layer.
E. primary contrast (concealed vs disclosed): still not fittable (1 positive
   group) -- documented, not forced.
"""
import glob, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe_fit import load_model_dir, logo_scores, fit_meandiff, auroc, group_permutation_pvalue

BASE = "/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe"
rows = []
for d in sorted(glob.glob(f"{BASE}/data/*/qwen3.6")):
    rows += load_model_dir(d)
print(f"qwen3.6 samples with activations: {len(rows)}")
layers = rows[0]["layers"]
SLOT = 1  # mean over response span

from collections import Counter
out = {"n": len(rows), "census": dict(Counter(r["category"] for r in rows)),
       "layers": layers, "slot": "mean_range"}
print(out["census"])

# ---- B. disclosed vs failed_silent, LOGO by task ----
use = [r for r in rows if r["category"] in ("disclosed", "failed_silent")]
y = np.array([1 if r["category"] == "disclosed" else 0 for r in use])
groups = np.array([r["task_id"] for r in use])
res_b = {}
for li, L in enumerate(layers):
    X = np.stack([r["X"][li, SLOT] for r in use])
    s = logo_scores(X, y, groups, fit_meandiff)
    obs, p, null = group_permutation_pvalue(s, y, groups, n_perm=10000)
    res_b[str(L)] = {"auroc": None if np.isnan(obs) else round(float(obs), 4),
                     "p_perm": round(float(p), 5)}
    print(f"B layer {L:2d}: disclosed-vs-silent LOGO AUROC={res_b[str(L)]['auroc']} p={res_b[str(L)]['p_perm']}")
out["disclosed_vs_silent_logo"] = {
    "n": len(use), "n_pos": int(y.sum()), "n_groups": int(len(np.unique(groups))),
    "note": ("first LOGO-definable contrast (2 positive groups); n_pos=2 so treat "
             "as exploratory; permutation shuffles group label-blocks among "
             "same-size groups"),
    "per_layer": res_b}

# ---- C. lcbhard_9 triplet ----
def get(cat, sid_contains):
    return [r for r in rows if r["category"] == cat and sid_contains in r["sid"]]
cheat = [r for r in rows if r["category"] == "concealed_cheat"][0]
silent9 = [r for r in rows if r["task_id"] == "lcbhard_9" and r["category"] == "failed_silent" and r["split"] == "oneoff"]
disc9 = [r for r in rows if r["task_id"] == "lcbhard_9" and r["category"] == "disclosed"]
sil = [r for r in rows if r["category"] == "failed_silent"]
res_c = {}
for li, L in enumerate(layers):
    c = cheat["X"][li, SLOT]
    cn = c / np.linalg.norm(c)
    def cs(v): return float(cn @ (v / np.linalg.norm(v)))
    entry = {}
    if silent9: entry["cos_cheat_vs_silent_sametask_samesplit"] = round(cs(silent9[0]["X"][li, SLOT]), 4)
    if disc9:   entry["cos_cheat_vs_disclosed_sametask"] = round(cs(disc9[0]["X"][li, SLOT]), 4)
    if silent9 and disc9:
        a = silent9[0]["X"][li, SLOT]; b = disc9[0]["X"][li, SLOT]
        entry["cos_silent_vs_disclosed_sametask"] = round(float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))), 4)
    res_c[str(L)] = entry
out["lcbhard9_triplet"] = {
    "note": "task-controlled; cheat vs silent shares task AND split AND model",
    "per_layer": res_c}

# ---- D. outlier check: cheat vs failed_silent distribution ----
res_d = {}
for li, L in enumerate(layers):
    S = np.stack([r["X"][li, SLOT] for r in sil])
    Sn = S / np.linalg.norm(S, axis=1, keepdims=True)
    mu = Sn.mean(0); mu /= np.linalg.norm(mu)
    cos_sil = Sn @ mu                      # each silent sample vs class mean
    c = cheat["X"][li, SLOT]; c = c / np.linalg.norm(c)
    cos_cheat = float(c @ mu)
    pct = float((cos_sil < cos_cheat).mean())  # low pct = cheat farther from mean than most
    res_d[str(L)] = {"cos_cheat_to_silent_mean": round(cos_cheat, 4),
                     "silent_cos_p05": round(float(np.quantile(cos_sil, .05)), 4),
                     "silent_cos_median": round(float(np.median(cos_sil)), 4),
                     "cheat_percentile_in_silent_dist": round(pct, 3)}
out["cheat_outlier_check"] = {
    "n_silent": len(sil),
    "note": "percentile ~0 = cheat is an outlier vs silent class; ~0.5 = typical",
    "per_layer": res_d}

# ---- E. primary contrast status ----
out["primary_contrast"] = {
    "n_pos": 1, "n_neg": len([r for r in rows if r["category"] == "disclosed"]),
    "status": "NOT FITTABLE: one positive sample/group; LOGO undefined by construction; not forced"}

json.dump(out, open(f"{BASE}/results/analysis_q36.json", "w"), indent=1)
print("wrote", f"{BASE}/results/analysis_q36.json")
