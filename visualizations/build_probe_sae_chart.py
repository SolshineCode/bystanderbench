#!/usr/bin/env python3
"""Ad-hoc chart for the probe + SAE trials (not part of build_charts.py's audited
behavioral pipeline). Source: concealment-probe/results/sae/gemma12b_L20_feature_cells.json
and concealment-probe/results/final_analysis.json. n=4 positives -- exactly at the
project's volume gate, not above it (see CLAUDE.md, FINDINGS.md SS F35).
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "visualizations", "out")

with open(os.path.join(BASE, "concealment-probe", "results", "sae", "gemma12b_L20_feature_cells.json")) as f:
    sae = json.load(f)

cells = sae["cells"]["655"]
order = [
    ("oneoff|concealed_cheat", "concealed_cheat\n(oneoff)", "#A50021"),
    ("oneoff|failed_silent", "failed_silent\n(oneoff)", "#7A7A7A"),
    ("conflicting|failed_silent", "failed_silent\n(conflicting)", "#7A7A7A"),
    ("original|original_fail", "original_fail", "#0072CE"),
    ("original|original_pass", "original_pass", "#00856E"),
]

fig, ax = plt.subplots(figsize=(9, 5.5))
labels = [o[1] for o in order]
means = [cells[o[0]]["mean"] for o in order]
colors = [o[2] for o in order]
ns = [cells[o[0]]["n"] for o in order]
n_active = [cells[o[0]]["n_active"] for o in order]

bars = ax.bar(labels, means, color=colors)
for bar, n, na in zip(bars, ns, n_active):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 8,
            f"n={n}\nactive={na}", ha="center", va="bottom", fontsize=9)

ax.set_ylabel("mean SAE feature activation (feature 655, layer 20)")
ax.set_title(
    "gemma-3-12b-it, GemmaScope-2 SAE feature 655 (caveat/limitation-flagging)\n"
    "PRELIMINARY -- n=4 concealed_cheat, exactly at volume gate, not above it\n"
    "silent hardcoded cheats fire this feature 0/4 times; every other class fires it near-universally"
)
plt.tight_layout()
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "6_sae_feature655.png")
plt.savefig(outpath, dpi=150)
print("wrote", outpath)

# ---- second panel: probe task-geometry (why group-level validation is required) ----
with open(os.path.join(BASE, "concealment-probe", "results", "final_analysis.json")) as f:
    fa = json.load(f)

geo = fa["task_geometry"]
layers = sorted(int(k) for k in geo.keys())
within = [geo[str(l)]["mean_cos_within_task"] for l in layers]
between = [geo[str(l)]["mean_cos_between_task"] for l in layers]

fig2, ax2 = plt.subplots(figsize=(9, 5.5))
ax2.plot(layers, within, marker="o", label="mean cos, within task", color="#0072CE")
ax2.plot(layers, between, marker="o", label="mean cos, between task", color="#C1541C")
ax2.set_xlabel("layer")
ax2.set_ylabel("mean cosine similarity of residual-stream activations")
ax2.set_title(
    "qwen3.5-27b probe geometry -- why leave-one-group-out validation is required\n"
    f"n={fa['n']} samples; primary contrast UNFITTABLE (0 concealed_cheat samples this run)\n"
    "within-task and between-task similarity track closely -> task identity dominates the geometry"
)
ax2.legend()
plt.tight_layout()
outpath2 = os.path.join(OUT, "7_probe_task_geometry.png")
plt.savefig(outpath2, dpi=150)
print("wrote", outpath2)
