#!/usr/bin/env python3
"""fig12: the frozen agent-arm probe direction (F200) on every independent holdout batch.
Reads research/canonical/probe_holdout2_*.json (written by bystander/scripts/probe_holdout2.py,
one per holdout, AUC + bootstrap CI + per-batch) and the F200 numbers for holdout 1 from
probe_holdout2_F200_replay.json. Pooled values are passed on the command line because they are
computed inline in F205 from the same direction file (n=118, AUC 0.753, CI [0.663, 0.832]).
Usage: python visualizations/build_probe_holdout_figure.py [-o out.png]
"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "research/canonical"
rows = [("holdout 1 (i+j), §F200", "probe_holdout2_F200_replay.json"),
        ("holdout 2 (k+l)", "probe_holdout2_holdout2.json"),
        ("holdout 3 (m+n)", "probe_holdout2_holdout3.json"),
        ("holdout 4 (o+p)", "probe_holdout2_holdout4.json"),
        ("holdout 5 (q+r)", "probe_holdout2_holdout5.json"),
        ("holdout 6 (s+t)", "probe_holdout2_holdout6.json"),
        ("offline holdout (01+02)", "probe_holdout2_off0102.json"),
        ("offline holdout (03+04)", "probe_holdout2_off0304.json"),
        ("offline holdout (05+06)", "probe_holdout2_off0506.json"),
        ("nite holdout (01+02)", "probe_holdout2_nite0102.json"),
        ("nite holdout (05+06)", "probe_holdout2_nite0506.json"),
        ("nite holdout (07+08)", "probe_holdout2_nite0708.json"),
        ("human-wrongdoer batch (a+b)", "probe_holdout2_ctrl_holdout.json")]
POOLED = ("pooled fresh agent-arm holdouts, 11 batches", 262, 117, 0.7598, (0.699, 0.818), 0.00025)
out = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else str(ROOT / "visualizations/course/fig12_probe_holdouts.png")
fig, ax = plt.subplots(figsize=(9.6, 5.6))
labels, ys = [], []
items = []
for lab, f in rows:
    d = json.load(open(C / f))
    items.append((lab, d["n"], d["alerted"], d["auc"], tuple(d["bootstrap_ci95"]), d["perm_p_holdout_labels"], "ctrl" in f))
items.append((*POOLED, False))
for i, (lab, n, k, auc, (lo, hi), p, is_ctrl) in enumerate(items):
    y = len(items) - i
    color = "#c0504d" if lab.startswith("pooled") else ("#4f81bd" if is_ctrl else "#7f7f7f")
    ax.barh(y, auc, height=.6, color=color, alpha=.9)
    ax.plot([lo, hi], [y, y], color="black", lw=1.2)
    ax.text(hi + .012, y, f"AUC {auc:.2f}, n={n} ({k} alerted), p={p:.3g}", va="center", fontsize=8.8, color="#333")
    labels.append(lab); ys.append(y)
ax.axvline(.5, color="black", ls=":", lw=1)
ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=9.5)
ax.set_xlim(0.3, 1.45); ax.set_xticks([.3, .5, .7, .9, 1.0])
ax.set_xlabel("AUC of the frozen direction, transcripts cut before the decision (bootstrap 95%)")
ax.set_title("One direction, fit once on 74 episodes and never refit, on every batch captured afterwards\n"
             "nex-n2.5-mini, layer 37, mean over the pre-decision window; §F200 to §F206 (nite batches added post-wind-down 09-21)", fontsize=11.5)
ax.grid(axis="x", alpha=.25); fig.tight_layout(); fig.savefig(out, dpi=150); print("wrote", out)
