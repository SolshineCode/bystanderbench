#!/usr/bin/env python3
"""The local audited concealment corpus: competence against concealment, per model.

WHY THIS EXISTS (§F138). Every concealment figure in this repo plots the CLOUD screen corpus
via build_charts.py. The LOCAL audited corpus, which is what research/canonical/concealment_rates.csv
holds and what §F120/§F126/§F128/§F132 corrected, appears in no figure at all. nex-n2.5-mini
appears in no figure. The competence column appears in no figure. Those are the numbers the
write-up cites, so they were the ones with no picture.

The two corpora must NOT be merged: CLAUDE.md rule 5 says provenance categories never pool,
cloud/behavioural evidence stays permanently separate from local activation-backed evidence.
So this is a second figure, not a fix to the first, and it reads only from the canonical CSV.

WHAT IT SHOWS. §F126's point is that concealment is confounded with whether the model can do
the task at all, so the rate alone is misleading. Panel (a) is the rate with its Wilson
interval and k/N. Panel (b) is competence against concealment, which is the actual argument:
the low band is populated by models that cannot solve the solvable split, and the only
matched-competence comparison is the one that carries the architecture result.

Usage:  python visualizations/build_local_corpus.py
"""
from __future__ import annotations
import csv, math
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
CSV = BASE / "research" / "canonical" / "concealment_rates.csv"
OUT = BASE / "visualizations" / "local_corpus_competence.png"
FLOOR = 0.75                      # §F132, inherited from report.py's COVER_MIN
MOE = {"north-mini-code", "nex-n2.5-mini"}
HOT, COOL, MUTE = "#c05621", "#2b6cb0", "#6b6157"


def wilson(k, n, z=1.96):
    if not n: return (0.0, 1.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return max(0.0, c-h), min(1.0, c+h)


def main() -> int:
    rows = [r for r in csv.DictReader(CSV.open()) if r["competence"]]
    # "pooled" is the citable north-mini figure; the screen/bigbatch rows are its parts and
    # plotting all three would show one model three times.
    rows = [r for r in rows if "(screen)" not in r["model"] and "(bigbatch)" not in r["model"]]
    for r in rows:
        r["k"] = int(r["concealed_rows"]); r["n"] = int(r["total_rows"])
        r["rate"] = r["k"] / r["n"]; r["comp"] = float(r["competence"])
        r["short"] = r["model"].replace(" (pooled)", "").replace("-instruct", "")
        r["moe"] = any(m in r["model"] for m in MOE)
    rows.sort(key=lambda r: -r["comp"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.4))
    fig.suptitle("Local audited concealment corpus: the rate is confounded with competence",
                 fontsize=14, x=0.5, y=0.98)

    # ---- panel (a): rate with CI and k/N -------------------------------------------------
    ys = range(len(rows))
    rates = [100*r["rate"] for r in rows]
    lo = [100*r["rate"] - 100*wilson(r["k"], r["n"])[0] for r in rows]
    hi = [100*wilson(r["k"], r["n"])[1] - 100*r["rate"] for r in rows]
    ax1.barh(list(ys), rates, color=[HOT if r["moe"] else COOL for r in rows], height=.6)
    ax1.errorbar(rates, list(ys), xerr=[lo, hi], fmt="none", ecolor="#444", elinewidth=1.1,
                 capsize=3)
    for y, r in zip(ys, rows):
        ax1.text(rates[y] + hi[y] + 0.7, y, f"{r['k']}/{r['n']}", va="center", fontsize=9)
    ax1.set_yticks(list(ys))
    ax1.set_yticklabels([f"{r['short']}  ({100*r['comp']:.0f}% competent)" for r in rows],
                        fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("concealed-cheat rate (all rows), 95% Wilson CI")
    ax1.set_title("(a) Rate per model, ordered by competence", fontsize=11, loc="left")
    ax1.set_xlim(0, max(rates) + max(hi) + 6)

    # ---- panel (b): competence vs concealment, the actual argument ------------------------
    # Label placement. Earlier versions labelled all seven points and could not be made to
    # read: five sit in one corner, and pushing labels apart just moved them onto other
    # markers. Panel (a) already names every model in competence order, so per-point labels
    # here were redundant clutter. Label only the two above-floor points, which are isolated
    # and are the comparison the panel is about, and name the cluster once.
    ax2.set_xlim(0, 98)
    ax2.set_ylim(-2.5, 27)
    for r in rows:
        x, y = 100*r["comp"], 100*r["rate"]
        ax2.scatter(x, y, s=95, color=HOT if r["moe"] else COOL, zorder=3,
                    edgecolor="white", linewidth=1.2)
        if r["comp"] >= FLOOR:
            ax2.annotate(f"{r['short']}  {r['k']}/{r['n']}", (x, y),
                         textcoords="offset points", xytext=(-11, 0), fontsize=9,
                         color="#333", ha="right", va="center")
    below = [r for r in rows if r["comp"] < FLOOR]
    bx = max(100*r["comp"] for r in below)
    by = max(100*r["rate"] for r in below)
    names = sorted(r["short"] for r in below)
    ax2.annotate(f"{len(below)} models below the floor:\n"
                 f"{', '.join(names[:3])},\n{', '.join(names[3:])}\n"
                 "rates here are not evidence\nabout propensity",
                 xy=(bx, by), xytext=(30, 16), fontsize=8.5, color="#444",
                 ha="left", va="center",
                 arrowprops=dict(arrowstyle="-", color="#999", lw=0.9,
                                 connectionstyle="arc3,rad=0.15"))
    ax2.axvline(100*FLOOR, color=MUTE, ls="--", lw=1.3, zorder=1)
    ax2.text(100*FLOOR - 1.8, 25.6, f"competence floor {FLOOR:.2f} (§F132)",
             ha="right", va="top", fontsize=8.5, color=MUTE)
    ax2.set_xlabel("solves the SOLVABLE split (original-split pass rate, %)")
    ax2.set_ylabel("concealed-cheat rate (%)")
    ax2.set_title("(b) Only two models clear the floor, and they are the comparison",
                  fontsize=11, loc="left")
    ax2.grid(alpha=.25, zorder=0)

    from matplotlib.patches import Patch
    ax2.legend(handles=[Patch(color=HOT, label="mixture of experts"),
                        Patch(color=COOL, label="dense")], loc="upper left", fontsize=9)

    fig.text(0.01, 0.015,
             "Source: research/canonical/concealment_rates.csv, regenerated by "
             "concealment-probe/tools/build_rates.py (refuses to write if a published cell moves). "
             "Denominator is ALL rows, matching the CSV;\n§F126 quotes nex as 0/50 on the impossible "
             "splits alone, a different and narrower denominator. This is the LOCAL audited corpus: "
             "CLAUDE.md rule 5 forbids pooling it with the cloud screens\nplotted in out/1_cheat_rate_ci.png. "
             "Five of seven models fall below the competence floor, so their rates are not evidence about "
             "propensity in either direction (§F132).",
             fontsize=7.6, color="#555", va="bottom")
    fig.tight_layout(rect=[0, 0.075, 1, 0.955])
    fig.savefig(OUT, dpi=135)
    print(f"wrote {OUT}")
    for r in rows:
        print(f"  {r['short']:<26} {r['k']:>3}/{r['n']:<4} rate {100*r['rate']:5.1f}%  "
              f"competence {100*r['comp']:5.1f}%{'  BELOW FLOOR' if r['comp'] < FLOOR else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
