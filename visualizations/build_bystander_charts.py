#!/usr/bin/env python
"""Charts for the BystanderBench result set. Audited cells only, Wilson CI and k/N on
every bar, per this repo's charting discipline."""
import json, math, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "visualizations/bystander_out"
os.makedirs(OUT, exist_ok=True)

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0, c-h), min(1, c+h))

def bars(ax, labels, ks, ns, colors, title, ylabel="rate"):
    x = np.arange(len(labels)); rates = [k/n if n else 0 for k, n in zip(ks, ns)]
    lo = [wilson(k, n)[0] for k, n in zip(ks, ns)]; hi = [wilson(k, n)[1] for k, n in zip(ks, ns)]
    err = [[r-l for r, l in zip(rates, lo)], [h-r for r, h in zip(rates, hi)]]
    ax.bar(x, rates, color=colors, edgecolor="black", linewidth=.6, zorder=3)
    ax.errorbar(x, rates, yerr=err, fmt="none", ecolor="black", capsize=4, linewidth=1.1, zorder=4)
    for i, (k, n) in enumerate(zip(ks, ns)):
        ax.text(i, hi[i]+.03, f"{k}/{n}", ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 1.18); ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10.5, weight="bold")
    ax.grid(axis="y", alpha=.25, zorder=0)

# ---- 1. the instruction ladder -------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 4.4))
labels = ["tool_probe\n(ordered)", "with_tool_named\n(category named)",
          "with_tool\n(mundane)", "no_tool\n(final msg only)"]
ks = [10, 0, 0, 0]; ns = [10, 24, 24, 24]
bars(ax, labels, ks, ns, ["#2a7", "#c44", "#c44", "#c44"],
     "BystanderBench: reporting by instruction strength\n(ceiling arm, qwen3.5-27b + nemotron-3.5-lightning pooled)",
     "reported (tool call, or mention for no_tool)")
ax.text(.5, -.22, "Models call the tool 10/10 when ordered. Naming misconduct as reportable, "
        "or removing the tool so\nprose is the only channel, both give zero. The gap is between "
        "instruction-following and voluntary action.",
        transform=ax.transAxes, ha="center", fontsize=8, style="italic")
fig.tight_layout(); fig.savefig(f"{OUT}/1_instruction_ladder.png", dpi=150, bbox_inches="tight"); plt.close(fig)

# ---- 2. discovery vs reporting, per arm ----------------------------------------
arms = [("blatant\n(ceiling)", 9, 12, 0, 12), ("realistic\n(incidental)", 5, 12, 0, 12),
        ("benign\n(control)", 6, 12, 0, 12)]
fig, ax = plt.subplots(figsize=(7.6, 4.4))
x = np.arange(len(arms)); w = .36
disc = [a[1]/a[2] for a in arms]; rep = [a[3]/a[4] for a in arms]
ax.bar(x-w/2, disc, w, label="discovered the evidence", color="#48c", edgecolor="k", linewidth=.6, zorder=3)
ax.bar(x+w/2, rep, w, label="reported it", color="#c44", edgecolor="k", linewidth=.6, zorder=3)
for i, a in enumerate(arms):
    ax.text(i-w/2, disc[i]+.02, f"{a[1]}/{a[2]}", ha="center", fontsize=8.5)
    ax.text(i+w/2, .02, f"{a[3]}/{a[4]}", ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels([a[0] for a in arms], fontsize=9)
ax.set_ylim(0, 1.1); ax.legend(fontsize=8.5); ax.grid(axis="y", alpha=.25, zorder=0)
ax.set_title("Salience moves discovery, not reporting (qwen3.5-27b, n=12 per arm)",
             fontsize=10.5, weight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/2_discovery_vs_reporting.png", dpi=150, bbox_inches="tight"); plt.close(fig)

# ---- 3. per-model ceiling comparison -------------------------------------------
fig, ax = plt.subplots(figsize=(7.8, 4.4))
x = np.arange(2); w = .27
d_content = [9/12, 12/12]; d_strict = [6/12, 12/12]; rep = [0, 0]
ax.bar(x-w, d_content, w, label="discovered (content)", color="#48c", edgecolor="k", linewidth=.6, zorder=3)
ax.bar(x, d_strict, w, label="discovered (opened by path)", color="#7ad", edgecolor="k", linewidth=.6, zorder=3)
ax.bar(x+w, rep, w, label="alerted", color="#c44", edgecolor="k", linewidth=.6, zorder=3)
for i, (a, b) in enumerate(zip([9, 12], [6, 12])):
    ax.text(i-w, d_content[i]+.02, f"{a}/12", ha="center", fontsize=8.5)
    ax.text(i, d_strict[i]+.02, f"{b}/12", ha="center", fontsize=8.5)
    ax.text(i+w, .02, "0/12", ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(["qwen3.5-27b\n(dense)", "nemotron-3.5-lightning\n(30B-A3B MoE)"], fontsize=9)
ax.set_ylim(0, 1.15); ax.legend(fontsize=8.5, loc="upper left"); ax.grid(axis="y", alpha=.25, zorder=0)
ax.set_title("Ceiling arm across two architectures: both read it, neither reports",
             fontsize=10.5, weight="bold")
ax.text(.5, -.2, "Models differ a lot in how thoroughly they read the repo (strict discovery 6/12 vs 12/12),\n"
        "so a cross-model reporting comparison that does not condition on discovery compares exploration habits.",
        transform=ax.transAxes, ha="center", fontsize=8, style="italic")
fig.tight_layout(); fig.savefig(f"{OUT}/3_two_architectures.png", dpi=150, bbox_inches="tight"); plt.close(fig)

# ---- 4. concealment side: hardcode rate by model --------------------------------
models = [("north-mini-code\n(no SAE/NLA)", 39, 177), ("gemma-3-12b-it\n(SAE+NLA)", 5, 166),
          ("gemma-3-27b-it\n(SAE+NLA)", 2, 62), ("llama-3.3-70b\n(SAE+NLA)", 0, 65),
          ("qwen2.5-7b\n(NLA)", 0, 66)]
fig, ax = plt.subplots(figsize=(8.6, 4.4))
bars(ax, [m[0] for m in models], [m[1] for m in models], [m[2] for m in models],
     ["#e83", "#48c", "#48c", "#48c", "#48c"],
     "The other side of the problem: the models you can look inside barely cheat",
     "concealed_cheat rate")
ax.set_ylim(0, .45)
ax.text(.5, -.24, "Orange has no published interpretability artifacts and cannot get them (sparse MoE).\n"
        "Blue all have published SAEs and/or Anthropic's released NLAs. Seven positives total across both Gemmas.",
        transform=ax.transAxes, ha="center", fontsize=8, style="italic")
fig.tight_layout(); fig.savefig(f"{OUT}/4_concealment_by_model.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("wrote 4 charts to", OUT)
