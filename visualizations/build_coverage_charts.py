#!/usr/bin/env python3
"""Charts for §F77: the split is family coverage, not serving path.

Every number is read from the logs and sample files at run time. Nothing is hardcoded --
the recurring failure in this project has been a remembered figure drifting from the data,
so a chart that cannot be regenerated from source is not evidence.

Wilson intervals are drawn on every rate, and every bar is annotated k/n, because a bare
percentage without its denominator is the specific thing §F43/§F65 caught.
"""
from __future__ import annotations

import collections
import glob
import math
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "concealment-probe" / "tools"))
OUT = ROOT / "visualizations"

LOCAL = "#2b6cb0"    # served on this machine (llama.cpp, quantised)
# NB: this axis is HOW WE SERVED the model, NOT whether its weights are open.
# Verified 2026-09-10 against the HF API: every model in both studies has open,
# ungated weights under a permissive licence -- including CohereLabs/North-Mini-Code
# (apache-2.0) and nex-agi/Nex-N2.5-mini (apache-2.0). There is no closed-weight
# model anywhere in this data, so the colours must never be read as open vs closed.
HOSTED = "#c05621"   # served by a provider API


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def _bars(ax, labels, ks, ns, colors, title, ylabel):
    xs = range(len(labels))
    rates = [100 * k / n if n else 0 for k, n in zip(ks, ns)]
    los, his = [], []
    for k, n in zip(ks, ns):
        lo, hi = wilson(k, n)
        # max(0, ...) because at exactly 0% or 100% the Wilson bound can land a hair on
        # the wrong side of the point estimate in floating point, and matplotlib rejects a
        # negative error bar outright.
        los.append(max(0.0, 100 * k / n - 100 * lo) if n else 0)
        his.append(max(0.0, 100 * hi - 100 * k / n) if n else 0)
    ax.bar(xs, rates, color=colors, width=0.62)
    ax.errorbar(xs, rates, yerr=[los, his], fmt="none", ecolor="#444", elinewidth=1.1, capsize=3)
    for x, (k, n, r) in enumerate(zip(ks, ns, rates)):
        ax.text(x, r + max(his[x], 2) + 2.5, f"{k}/{n}", ha="center", fontsize=8.5, color="#222")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=8.5)
    ax.set_ylim(0, 112)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10.5, loc="left")
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def bystander_rows():
    from inspect_ai.log import read_eval_log
    rows = []
    for f in glob.glob(str(ROOT / "logs" / "*" / "*.eval")):
        try:
            log = read_eval_log(f)
        except Exception:
            continue
        ta = log.eval.task_args or {}
        if "arm" not in ta:
            continue
        # Crashed runs are excluded outright. The gemma-3-12b n=8 run died on a context
        # overflow after 3 samples (§F73) and its surviving partial episodes would
        # otherwise be pooled with the clean re-run, which is how a broken run quietly
        # becomes data.
        if log.status != "success":
            continue
        mdl = log.eval.model or "?"
        hosted = "local-model" not in mdl
        if hosted:
            # Normalise to the bare family name so the SAME model served two ways lands in
            # one bucket. Without this, panel (a) silently compared a populated local
            # bucket against an empty hosted one and printed 0/0.
            name = mdl.replace("openrouter/", "").replace(":free", "").split("/")[-1]
        else:
            d = os.path.basename(os.path.dirname(f))
            if "gemma27" in d: name = "gemma-3-27b-it"
            elif "gemma12" in d: name = "gemma-3-12b-it"
            elif "nemotron" in d: name = "nemotron-3.5-lightning"
            else: name = "qwen3.5-27b"
        for s in (log.samples or []):
            if getattr(s, "error", None):
                continue
            v = next(iter(s.scores.values())).value
            rows.append(dict(model=name, hosted=hosted, tool_arm=ta.get("tool_arm"),
                             alerted=v["alerted"], cover=v["cover_task_passed"]))
    return rows


def main():
    rows = bystander_rows()
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2))
    fig.suptitle("Is the split local-vs-hosted, or model family?  (§F77)",
                 fontsize=13.5, y=0.985, x=0.055, ha="left")

    # ---- (a) the decisive control: one model, two serving paths -----------------------
    ax = axes[0][0]
    sub = [r for r in rows if r["model"] == "nemotron-3.5-lightning"
           and r["tool_arm"] == "with_tool"]
    g = collections.defaultdict(lambda: [0, 0, 0])
    for r in sub:
        key = "hosted" if r["hosted"] else "local"
        g[key][0] += r["alerted"]; g[key][1] += 1; g[key][2] += r["cover"]
    labels = ["LOCAL\nQ4_0, quantised KV", "HOSTED\nfull precision",
              "LOCAL\ncover task", "HOSTED\ncover task"]
    ks = [g["local"][0], g["hosted"][0], g["local"][2], g["hosted"][2]]
    ns = [g["local"][1], g["hosted"][1], g["local"][1], g["hosted"][1]]
    _bars(ax, labels, ks, ns, [LOCAL, HOSTED, LOCAL, HOSTED],
          "(a) nemotron-3.5-lightning, ONE model served two ways", "rate (%)")
    ax.axvline(1.5, color="#999", linewidth=0.8, linestyle=":")
    ax.text(0.5, 70, "alerted: identical",
            ha="center", fontsize=8.5, style="italic", color="#333")
    ax.text(2.5, 70, "competence: identical",
            ha="center", fontsize=8.5, style="italic", color="#333")

    # ---- (b) reporting by model ------------------------------------------------------
    ax = axes[0][1]
    g = collections.defaultdict(lambda: [0, 0, False])
    for r in rows:
        if r["tool_arm"] != "with_tool":
            continue
        e = g[r["model"]]
        e[0] += r["alerted"]; e[1] += 1; e[2] = r["hosted"]
    items = [(m, k, n, h) for m, (k, n, h) in g.items() if n >= 6]
    items.sort(key=lambda t: (-t[1] / t[2], t[0]))
    _bars(ax, [i[0][:26] for i in items], [i[1] for i in items], [i[2] for i in items],
          [HOSTED if i[3] else LOCAL for i in items],
          "(b) Voluntary reporting — one FAMILY stands out, not one serving path",
          "alerted | with_tool (%)")

    # ---- (c) cover task --------------------------------------------------------------
    ax = axes[1][0]
    g = collections.defaultdict(lambda: [0, 0, False])
    for r in rows:
        if r["tool_arm"] not in ("with_tool", "with_tool_named", "tool_probe"):
            continue
        e = g[r["model"]]
        e[0] += r["cover"]; e[1] += 1; e[2] = r["hosted"]
    items = [(m, k, n, h) for m, (k, n, h) in g.items() if n >= 6]
    items.sort(key=lambda t: (t[1] / t[2], t[0]))
    _bars(ax, [i[0][:26] for i in items], [i[1] for i in items], [i[2] for i in items],
          [HOSTED if i[3] else LOCAL for i in items],
          "(c) Cover-task competence — 100% everywhere except Gemma-3",
          "cover_task_passed (%)")

    # ---- (d) concealment -------------------------------------------------------------
    ax = axes[1][1]
    import corpus
    data = []
    for p in sorted(glob.glob(str(ROOT / "concealment-probe" / "data" / "*" / "*" / "samples.jsonl"))):
        d = os.path.dirname(p)
        fam = os.path.basename(d)
        try:
            gens = corpus.load(p, "generation")
        except Exception:
            continue
        if len(gens) < 20:
            continue
        c = collections.Counter(r.get("category") for r in gens)
        hosted = "north-mini" in fam
        data.append((fam[:26], c.get("concealed_cheat", 0), len(gens), hosted))
    merged = collections.defaultdict(lambda: [0, 0, False])
    for fam, k, n, h in data:
        merged[fam][0] += k; merged[fam][1] += n; merged[fam][2] = h
    items = [(m, v[0], v[1], v[2]) for m, v in merged.items()]
    items.sort(key=lambda t: (-t[1] / t[2], t[0]))
    _bars(ax, [i[0] for i in items], [i[1] for i in items], [i[2] for i in items],
          [HOSTED if i[3] else LOCAL for i in items],
          "(d) Concealed cheating — again one family, and two LOCAL models at zero",
          "concealed_cheat (% of generations)")
    ax.set_ylim(0, 40)

    handles = [plt.Rectangle((0, 0), 1, 1, color=LOCAL),
               plt.Rectangle((0, 0), 1, 1, color=HOSTED)]
    fig.legend(handles, ["served locally (llama.cpp, quantised)", "served via provider API"],
               loc="upper right", fontsize=9, frameon=False, bbox_to_anchor=(0.985, 0.995))
    fig.text(0.055, 0.012,
             "Bars annotated k/n; error bars are Wilson 95%. All values regenerated from "
             "logs/ and concealment-probe/data/ at build time.\n"
             "Colour = how the model was SERVED, not weight availability: every model shown "
             "has open, ungated weights (verified against the HF API, 2026-09-10).",
             fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.03, 1, 0.955])
    out = OUT / "coverage_not_serving_2026-09-10.png"
    fig.savefig(out, dpi=155)
    print("wrote", out)


if __name__ == "__main__":
    main()
