#!/usr/bin/env python3
"""Paired control-vs-treatment figure for the agent-perpetrator arm.

Control  = `blatant_wrongdoing`        (the wrongdoer is a named human employee)
Treatment= `blatant_wrongdoing_agents` (the wrongdoer is an autonomous agent pool)

Everything else about the two arms is held constant (domain, harm, evidence slots,
salience, volume to +3.1%), so a per-model pair is a within-model minimal pair.

Plots the conditional rate alerted/discovered_content with Wilson 95% intervals, one
row per model, control and treatment side by side. Models whose treatment cell has not
landed yet are drawn with the control bar and an explicit PENDING marker, never with a
guessed value. Refused cells are drawn as refusals, never as zeros.

Usage:  python visualizations/build_agentarm_figure.py <cells.csv> [-o out.png]
where cells.csv is produced by `python -m bystander.report <logdirs...> --csv <file>`.
"""
import csv, sys, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONTROL = "blatant_wrongdoing"
TREAT = "blatant_wrongdoing_agents"

def wilson(k, n, z=1.959963985):
    if not n:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))

def load(path):
    cells = {}
    for r in csv.DictReader(open(path)):
        if r["tool_arm"] != "with_tool" or r["arm"] not in (CONTROL, TREAT):
            continue
        key = (r["model"], r["mode"], r["arm"])
        cells[key] = r
    return cells

def short(model):
    m = model.replace(".gguf", "").replace("-Q4_K_M", "").replace("-Q4_0", "")
    m = m.split("/")[-1]
    return m[:28]

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    out = Path(sys.argv[sys.argv.index("-o") + 1]) if "-o" in sys.argv else Path(
        "visualizations/course/fig8_agent_vs_human_wrongdoer.png")
    cells = load(src)
    models = []
    for (model, mode, arm) in cells:
        if (model, mode) not in models:
            models.append((model, mode))
    rows = []
    for (model, mode) in models:
        c = cells.get((model, mode, CONTROL))
        t = cells.get((model, mode, TREAT))
        if not c and not t:
            continue
        rows.append((model, mode, c, t))
    # order: biggest control rate first, so the models that talk sit at the top
    def ckey(row):
        c = row[2]
        if c and c.get("cond_n") and int(c["cond_n"]) > 0 and not c.get("refused"):
            return -int(c["cond_k"]) / int(c["cond_n"])
        return 1.0
    rows.sort(key=ckey)

    fig, ax = plt.subplots(figsize=(10, 0.62 * max(6, len(rows)) + 2.2))
    ypos, ylabels = [], []
    for i, (model, mode, c, t) in enumerate(rows):
        y = len(rows) - i
        ypos.append(y); ylabels.append(f"{short(model)}\n{mode}")
        for arm_row, off, color, label in ((c, 0.18, "#4a6fa5", "human wrongdoer (control)"),
                                           (t, -0.18, "#c1544a", "agent wrongdoer")):
            if arm_row is None:
                ax.text(0.01, y - 0.18, "PENDING", va="center", fontsize=7.5,
                        color="#888", style="italic")
                continue
            if arm_row.get("refused"):
                ax.text(0.01, y + off, f"refused: {arm_row['refused']}", va="center",
                        fontsize=7.5, color="#999", style="italic")
                continue
            k, n = int(arm_row["cond_k"] or 0), int(arm_row["cond_n"] or 0)
            if not n:
                ax.text(0.01, y + off, "no discovering episode", va="center",
                        fontsize=7.5, color="#999", style="italic")
                continue
            p, lo, hi = wilson(k, n)
            ax.barh(y + off, p, height=0.32, color=color, alpha=0.85,
                    label=label if i == 0 else None)
            ax.plot([lo, hi], [y + off, y + off], color="black", lw=1.1)
            ax.text(min(hi + 0.015, 0.97), y + off, f"{k}/{n}", va="center",
                    fontsize=8, color="#333")
    ax.set_yticks(ypos); ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_xlim(0, 1.06); ax.set_xlabel(
        "reported to a human, conditional on having the evidence in context (Wilson 95%)")
    ax.set_title("Does the wrongdoer's species change whether an agent reports it?\n"
                 "Same incident, same evidence, same salience; only the perpetrator differs",
                 fontsize=11)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"wrote {out}  ({len(rows)} model rows)")
    for model, mode, c, t in rows:
        def fmt(r):
            if r is None: return "PENDING"
            if r.get("refused"): return f"refused({r['refused']})"
            return f"{r['cond_k']}/{r['cond_n']}"
        print(f"  {short(model):30s} {mode:20s} control={fmt(c):12s} agents={fmt(t)}")

if __name__ == "__main__":
    main()
