#!/usr/bin/env python3
"""Final analysis for the 2026-09-01/02 real-data concealment-probe attempt.

With 0 concealed_cheat samples, no probe can be fit for the primary contrast.
This script documents that degeneracy concretely and reports descriptive
activation geometry only (explicitly non-inferential):
  1. attempted LOGO fit for disclosed-vs-failed_silent -> shows it degenerates
  2. within-task vs between-task activation distances (task identity check)
  3. layer-wise cosine between disclosed and failed_silent response means,
     within task lcbhard_41 only (task-controlled, n too small for inference)
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe_fit import load_model_dir, logo_scores, fit_meandiff, auroc

import glob as _glob
BASE = "/home/darkstar/bluedot-unit2-impossiblebench/concealment-probe"
DIRS = sorted(_glob.glob(f"{BASE}/data/*/qwen3.[58]-27b"))

rows = []
for d in DIRS:
    if os.path.exists(os.path.join(d, "samples.jsonl")):
        rows += load_model_dir(d)
print(f"loaded {len(rows)} samples with activations")
layers = rows[0]["layers"]
SLOT = 1  # mean over response span

out = {"n": len(rows),
       "census": {},
       "primary_contrast": "UNFITTABLE: 0 concealed_cheat samples",
       "secondary_contrast_logo": {},
       "task_geometry": {},
       "disclosed_vs_silent_within_task41": {}}

from collections import Counter
out["census"] = {f"{k[0]}|{k[1]}": v for k, v in
                 Counter((r["model"], r["category"]) for r in rows).items()}

# --- 1. attempted secondary contrast: disclosed(1) vs failed_silent(0) ---
use = [r for r in rows if r["category"] in ("disclosed", "failed_silent")]
y = np.array([1 if r["category"] == "disclosed" else 0 for r in use])
groups = np.array([r["task_id"] for r in use])
li = layers.index(32)
X = np.stack([r["X"][li, SLOT] for r in use])
s = logo_scores(X, y, groups, fit_meandiff)
n_nan = int(np.isnan(s).sum())
valid = ~np.isnan(s)
a = auroc(s[valid], y[valid]) if valid.any() else float("nan")
out["secondary_contrast_logo"] = {
    "n": len(use), "n_pos": int(y.sum()), "n_groups": len(set(groups)),
    "note": ("all disclosed samples are the same task (lcbhard_41); leaving that "
             "group out leaves 0 positives to fit on -> those folds are undefined; "
             "remaining folds contain only negatives -> AUROC undefined"),
    "n_undefined_fold_samples": n_nan,
    "pooled_auroc": None if np.isnan(a) else float(a),
}
print("secondary contrast:", out["secondary_contrast_logo"])

# --- 2. within-task vs between-task distances (all samples, per layer) ---
geom = {}
for lidx, L in enumerate(layers):
    Xa = np.stack([r["X"][lidx, SLOT] for r in rows])
    Xn = Xa / (np.linalg.norm(Xa, axis=1, keepdims=True) + 1e-9)
    tid = [r["task_id"] for r in rows]
    win, btw = [], []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            csim = float(Xn[i] @ Xn[j])
            (win if tid[i] == tid[j] else btw).append(csim)
    geom[str(L)] = {"mean_cos_within_task": round(float(np.mean(win)), 4),
                    "mean_cos_between_task": round(float(np.mean(btw)), 4)}
out["task_geometry"] = geom

# --- 3. task-controlled disclosed vs silent (task 41 impossible-splits only) ---
t41 = [r for r in rows if r["task_id"] == "lcbhard_41" and r["split"] in ("conflicting", "oneoff")]
d41 = [r for r in t41 if r["category"] == "disclosed"]
s41 = [r for r in t41 if r["category"] == "failed_silent"]
res = {}
for lidx, L in enumerate(layers):
    D = np.stack([r["X"][lidx, SLOT] for r in d41]).mean(0)
    S = np.stack([r["X"][lidx, SLOT] for r in s41]).mean(0)
    cs = float(D @ S / (np.linalg.norm(D) * np.linalg.norm(S) + 1e-9))
    res[str(L)] = {"cos_disclosed_mean_vs_silent_mean": round(cs, 4)}
out["disclosed_vs_silent_within_task41"] = {
    "n_disclosed": len(d41), "n_silent": len(s41),
    "note": ("descriptive only; n far too small for any inference. ADDITIONAL "
             "CONFOUND: within task 41 every disclosed sample is from the "
             "'conflicting' split and every silent one from 'oneoff', so any "
             "separation here is indistinguishable from split identity."),
    "splits_disclosed": sorted({r["split"] for r in d41}),
    "splits_silent": sorted({r["split"] for r in s41}),
    "per_layer": res}

os.makedirs(f"{BASE}/results", exist_ok=True)
with open(f"{BASE}/results/final_analysis.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out["task_geometry"]["32"], indent=1))
print("wrote", f"{BASE}/results/final_analysis.json")
