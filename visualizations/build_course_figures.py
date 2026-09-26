#!/usr/bin/env python3
"""Publication figures for the BlueDot course write-up.

Every plotted number is read at run time from:
  research/audits/cells_2026-09-20_after_w42.csv   (BystanderBench cells, report.py v1.1)
  research/canonical/concealment_rates.csv                (Part 1 concealment rates)
  research/canonical/probe_alert_predecision_v2.json       (alerting probe, pre-decision refit)
  research/audits/2026-09-14-scaling-read.json             (conditional rate vs active params)

No count in this script is hardcoded; every number a figure shows comes from one of the
four files above, loaded fresh on each run. See visualizations/course/figures.md for the
registry (caption, source, FINDINGS pointers) and figure_values.csv for every plotted
value in tabular form.

Run:  source .venv/bin/activate && python3 visualizations/build_course_figures.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "visualizations", "course")
os.makedirs(OUT, exist_ok=True)

CELLS_CSV = os.path.join(ROOT, "research/audits/cells_agentarm_live.csv")
CONCEALMENT_CSV = os.path.join(ROOT, "research/canonical/concealment_rates.csv")
PROBE_JSON = os.path.join(ROOT, "research/canonical/probe_alert_predecision_v2.json")
SCALING_JSON = os.path.join(ROOT, "research/audits/2026-09-14-scaling-read.json")

DPI = 200

# ---------------------------------------------------------------------------
# Okabe-Ito colorblind-safe palette (fixed assignment order, never cycled by
# rank). Black is reserved for reference/neutral elements (chance lines,
# censored markers), not assigned to a data series.
# ---------------------------------------------------------------------------
OKABE_ITO = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000",  # black (used last, as an 8th hue, not as the neutral)
]
NEUTRAL_GRAY = "#666666"
CENSORED_GRAY = "#999999"

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

VALUES = []  # rows for figure_values.csv: figure, series, label, k, n, rate, ci_lo, ci_hi, status


def record(figure, series, label, k, n, rate, ci_lo, ci_hi, status):
    VALUES.append(dict(figure=figure, series=series, label=label, k=k, n=n, rate=rate,
                        ci_lo=ci_lo, ci_hi=ci_hi, status=status))


def wilson(k, n, z=1.96):
    """Same formula as bystander/report.py's wilson()."""
    if not n:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def err_bar(rate, lo, hi):
    """Wilson bounds can be off by float epsilon at rate 0 or 1; clip to nonnegative."""
    return max(0.0, rate - lo), max(0.0, hi - rate)


def savefig(fig, name, caption=None):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# Model label mapping: strip .gguf / quant suffixes / openrouter prefix; keep
# :free as " (free tier)"; mark local GGUF runs "(local)".
# ---------------------------------------------------------------------------
_QUANT_RE = re.compile(r"-(UD-)?Q\d(_[A-Za-z0-9]+)*$")


def label_model(raw):
    is_local = raw.endswith(".gguf")
    s = raw
    if is_local:
        s = s[:-5]
        s = _QUANT_RE.sub("", s)
        s = s + " (local)"
    else:
        s = s.replace("openrouter/", "")
        if s.endswith(":free"):
            s = s[:-5] + " (free tier)"
    return s, is_local


def mode_suffix(mode):
    parts = []
    if "prompted" in mode:
        parts.append("prompted")
    if "+think" in mode:
        parts.append("thinking on")
    return " (" + ", ".join(parts) + ")" if parts else ""


# Explicit human-readable base names, keyed by the raw model string exactly as it
# appears in cells_2026-09-15_after_w4c.csv. Used by fig1 (display_label());
# any raw model not listed falls back to label_model()'s strip-based mapping.
MODEL_DISPLAY = {
    "anthropic/claude-opus-5": "Claude Opus 5",
    "anthropic/claude-sonnet-5": "Claude Sonnet 5",
    "google/gemini-3.1-pro-preview": "Gemini 3.1 Pro (preview)",
    "openai/gpt-5.6-luna-pro": "GPT-5.6 Luna Pro",
    "nex-agi/nex-n2.5-pro:free": "nex-n2.5-pro",
    "nex-agi/nex-n2.5-mini:free": "nex-n2.5-mini",
    "Nex-N2.5-mini-Q4_K_M.gguf": "nex-n2.5-mini",
    "openrouter/poolside/laguna-s-2.1:free": "laguna-s-2.1",
    "openrouter/poolside/laguna-xs-2.1:free": "laguna-xs-2.1",
    "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf": "nemotron-3.5-lightning",
    "nvidia/nemotron-3.5-lightning:free": "nemotron-3.5-lightning",
    "dots-studio/dots-3-note-preview:free": "dots-3-note-preview",
    "gemma-4-31B-it-Q4_K_M.gguf": "gemma-4-31B",
    "inclusionai/ling-3.0-flash-fin:free": "ling-3.0-flash-fin",
    "inclusionai/ling-3.0-flash-sante:free": "ling-3.0-flash-sante",
    "inclusionai/ling-3.0-flash-vl:free": "ling-3.0-flash-vl",
    "nvidia/nemotron-3-super-120b-a12b:free": "nemotron-3-super-120b-a12b",
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free": "nemotron-3-ultra-550b-a55b",
    "openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": "nemotron-3-nano-omni-30b-a3b-reasoning",
    "openrouter/liquid/lfm-2.5-2.6b:free": "lfm-2.5-2.6b",
    "qwen3.5-27b.gguf": "qwen3.5-27b",
    "Llama-3.3-70B-Instruct-Q4_K_M.gguf": "Llama 3.3 70B Instruct",
    "North-Mini-Code-1.0-UD-Q4_K_M.gguf": "North-Mini-Code-1.0",
    "gemma-3-12b-it-Q4_K_M.gguf": "gemma-3-12b-it",
    "gemma-3-27b-it-Q4_K_M.gguf": "gemma-3-27b-it",
    "Olmo-3-7B-Instruct-Q4_K_M.gguf": "Olmo 3 7B Instruct",
}


def display_label(raw, mode):
    """Readable label for fig1: explicit base name (MODEL_DISPLAY, falling back to
    label_model()'s strip-based name) plus a location/mode tag: '(local, thinking
    on/off/prompted)' for GGUF runs, '(free tier)' for :free API runs, nothing extra
    for direct/paid API models."""
    is_local = raw.endswith(".gguf")
    is_free = raw.endswith(":free")
    base = MODEL_DISPLAY.get(raw)
    if base is None:
        base, _ = label_model(raw)
        base = base.replace(" (local)", "").replace(" (free tier)", "")
    if is_local:
        if "prompted" in mode:
            tag = "prompted"
        elif "+think" in mode:
            tag = "thinking on"
        elif mode == "tools/native":
            tag = "thinking off"
        else:
            tag = mode
        return f"{base} (local, {tag})"
    if is_free:
        return f"{base} (free tier)"
    return base


# fig1 exact labels, keyed by (raw model, mode) as they appear in the cells CSV.
# Hand-written per the coordinator's explicit examples (Claude Opus 5, nex-n2.5-pro
# (free tier), nex-n2.5-mini (local, thinking on), nemotron-3.5-lightning (local,
# thinking off), qwen3.5-27b (local), gemma-4-31B (local, thinking on)); every other
# fig1 row is filled in by the same convention (thinking tag shown when the model has
# more than one thinking condition in this figure or the tag is otherwise informative;
# the unmarked tools/native cell for a model with only one non-thinking mode stays
# plain "(local)"). Falls back to display_label() for any (raw, mode) not listed here.
FIG1_LABELS = {
    ("Llama-3.3-70B-Instruct-Q4_K_M.gguf", "tools/native"): "Llama 3.3 70B Instruct (local)",
    ("NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf", "tools/native"): "nemotron-3.5-lightning (local, thinking off)",
    ("NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf", "tools/native+think"): "nemotron-3.5-lightning (local, thinking on)",
    ("Nex-N2.5-mini-Q4_K_M.gguf", "tools/native+think"): "nex-n2.5-mini (local, thinking on)",
    ("North-Mini-Code-1.0-UD-Q4_K_M.gguf", "tools/native"): "North-Mini-Code-1.0 (local)",
    ("anthropic/claude-opus-5", "tools/native"): "Claude Opus 5",
    ("anthropic/claude-sonnet-5", "tools/native"): "Claude Sonnet 5",
    ("dots-studio/dots-3-note-preview:free", "tools/native"): "dots-3-note-preview (free tier)",
    ("gemma-3-12b-it-Q4_K_M.gguf", "prompted"): "gemma-3-12b-it (local, prompted)",
    ("gemma-4-31B-it-Q4_K_M.gguf", "tools/native+think"): "gemma-4-31B (local, thinking on)",
    ("google/gemini-3.1-pro-preview", "tools/native"): "Gemini 3.1 Pro (preview)",
    ("inclusionai/ling-3.0-flash-fin:free", "tools/native"): "ling-3.0-flash-fin (free tier)",
    ("inclusionai/ling-3.0-flash-sante:free", "tools/native"): "ling-3.0-flash-sante (free tier)",
    ("inclusionai/ling-3.0-flash-vl:free", "tools/native"): "ling-3.0-flash-vl (free tier)",
    ("nex-agi/nex-n2.5-mini:free", "tools/native"): "nex-n2.5-mini (free tier)",
    ("nex-agi/nex-n2.5-pro:free", "tools/native"): "nex-n2.5-pro (free tier)",
    ("nvidia/nemotron-3-super-120b-a12b:free", "tools/native"): "nemotron-3-super-120b-a12b (free tier)",
    ("nvidia/nemotron-3.5-lightning:free", "tools/native"): "nemotron-3.5-lightning (free tier)",
    ("openai/gpt-5.6-luna-pro", "tools/native"): "GPT-5.6 Luna Pro",
    ("openrouter/nvidia/nemotron-3-ultra-550b-a55b:free", "tools/native"): "nemotron-3-ultra-550b-a55b (free tier)",
    ("openrouter/poolside/laguna-s-2.1:free", "tools/native"): "laguna-s-2.1 (free tier)",
    ("qwen3.5-27b.gguf", "prompted"): "qwen3.5-27b (local, prompted)",
    ("qwen3.5-27b.gguf", "tools/native"): "qwen3.5-27b (local)",
    ("qwen3.5-27b.gguf", "tools/native+think"): "qwen3.5-27b (local, thinking on)",
}


def fig1_label(raw, mode):
    return FIG1_LABELS.get((raw, mode)) or display_label(raw, mode)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_cells():
    with open(CELLS_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def intf(v):
    v = (v or "").strip()
    return int(v) if v else None


def load_concealment():
    with open(CONCEALMENT_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def load_probe():
    with open(PROBE_JSON) as f:
        return json.load(f)


def load_scaling():
    with open(SCALING_JSON) as f:
        return json.load(f)


def match_params(model_raw, params_table):
    """Match a cells-CSV model string against the scaling-read params_table's
    match_pattern regexes (case-insensitive substring search), independent of
    that file's own precomputed per-cell family/params. Returns the matching
    params_table row, or None if no pattern matches."""
    s = model_raw.lower()
    hits = [p for p in params_table if re.search(p["match_pattern"], s, re.IGNORECASE)]
    if not hits:
        return None
    # Prefer the longest/most specific pattern if more than one matches.
    hits.sort(key=lambda p: -len(p["match_pattern"]))
    return hits[0]


# ---------------------------------------------------------------------------
# Shared bar-with-CI helper: reportable bars (rate + Wilson CI + k/n text) and
# censored bars (hatched, no rate, labelled with the refusal reason).
# ---------------------------------------------------------------------------
def plot_rate_bars(ax, items, ylabel="conditional rate (alerted | discovered)", ymax=1.15,
                    bar_colors=None, legend_handles=None, legend_loc="upper right"):
    """items: list of dicts with keys label, k, n (None -> censored), reason, color."""
    x = np.arange(len(items))
    for i, it in enumerate(items):
        color = it.get("color", OKABE_ITO[0])
        if it["k"] is None or it["n"] is None or it["n"] == 0:
            # censored / non-plottable cell
            ax.bar(i, 1.0, width=0.7, facecolor="white", edgecolor=CENSORED_GRAY,
                   hatch="////", linewidth=1.0, zorder=3)
            ax.text(i, 0.5, it.get("reason", "censored"), rotation=90, ha="center", va="center",
                    fontsize=7.5, color="#444444")
        else:
            k, n = it["k"], it["n"]
            rate = k / n
            lo, hi = wilson(k, n)
            ax.bar(i, rate, width=0.7, color=color, edgecolor="black", linewidth=0.6, zorder=3)
            err_lo, err_hi = err_bar(rate, lo, hi)
            ax.errorbar(i, rate, yerr=[[err_lo], [err_hi]], fmt="none", ecolor="black",
                        capsize=3.5, linewidth=1.0, zorder=4)
            ax.text(i, hi + 0.025, f"{k}/{n}", ha="center", va="bottom", fontsize=7.5)
    multiline = any("\n" in it["label"] for it in items)
    ax.set_xticks(x)
    if multiline:
        ax.set_xticklabels([it["label"] for it in items], rotation=0, ha="center", fontsize=8.3)
    else:
        ax.set_xticklabels([it["label"] for it in items], rotation=55, ha="right", fontsize=8)
    ax.set_ylim(0, ymax)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.axhline(0, color="#333333", linewidth=0.8)
    if legend_handles:
        ax.legend(handles=legend_handles, loc=legend_loc, fontsize=8, framealpha=0.9)


# ===========================================================================
# Figure 1: cross-model incident 1 (blatant_wrongdoing), with_tool cells
# ===========================================================================
def fig1_cross_model_incident1(cells):
    rows = [r for r in cells if r["arm"] == "blatant_wrongdoing" and r["tool_arm"] == "with_tool"]
    items = []
    for r in rows:
        is_local = r["model"].endswith(".gguf")
        label = fig1_label(r["model"], r["mode"])
        reason = (r["refused"] or "").strip()
        cond_k, cond_n = intf(r["cond_k"]), intf(r["cond_n"])
        if reason:
            items.append(dict(label=label, k=None, n=None, reason=reason, is_local=is_local,
                               bucket="censored"))
        elif not cond_n:
            items.append(dict(label=label, k=None, n=None,
                               reason="no discovered evidence (0/0)", is_local=is_local,
                               bucket="censored"))
        elif cond_n < 3:
            items.append(dict(label=label, k=cond_k, n=cond_n, is_local=is_local,
                               bucket="uninformative"))
        else:
            items.append(dict(label=label, k=cond_k, n=cond_n, is_local=is_local,
                               bucket="informative"))

    informative = [it for it in items if it["bucket"] == "informative"]
    uninformative = [it for it in items if it["bucket"] == "uninformative"]
    censored = [it for it in items if it["bucket"] == "censored"]
    informative.sort(key=lambda it: -(it["k"] / it["n"]))
    uninformative.sort(key=lambda it: -(it["k"] / it["n"]))
    ordered = informative + uninformative + censored

    local_color, api_color = OKABE_ITO[4], OKABE_ITO[5]  # blue vs vermillion
    uninformative_color = "#BBBBBB"
    for it in ordered:
        if it["bucket"] == "uninformative":
            it["color"] = uninformative_color
        else:
            it["color"] = local_color if it["is_local"] else api_color

    fig, ax = plt.subplots(figsize=(15.5, 6.6))
    legend = [
        Patch(facecolor=local_color, edgecolor="black", label="local (GGUF, llama.cpp)"),
        Patch(facecolor=api_color, edgecolor="black", label="API / OpenRouter"),
        Patch(facecolor=uninformative_color, edgecolor="black",
              label="uninformative (fewer than 3 episodes discovered)"),
        Patch(facecolor="white", edgecolor=CENSORED_GRAY, hatch="////", label="refused / censored cell (no rate)"),
    ]
    plot_rate_bars(ax, ordered, legend_handles=legend, legend_loc="upper right")
    ax.set_title("Incident 1 (blatant ledger fabrication, human-wrongdoer control): who reports it, conditional on discovering it")
    fig.tight_layout(rect=[0, 0.14, 1, 1])
    fig.text(0.5, 0.045,
              "Human-wrongdoer control arm: the wrongdoer is a named human colleague, not an agent. Every "
              "with_tool cell for incident 1 (blatant_wrongdoing), sorted by conditional rate\n"
              "(alerted / discovered evidence) within the informative group (cond_n >= 3). Grey bars "
              "have a rate but fewer than 3 discovered episodes and should not be read as a precise "
              "estimate. Hatched bars are refused cells and carry no rate at all.",
              ha="center", fontsize=8.5, style="italic")
    savefig(fig, "fig1_cross_model_incident1.png")

    for it in ordered:
        rate = it["k"] / it["n"] if it["n"] else None
        lo, hi = wilson(it["k"], it["n"]) if it["n"] else (None, None)
        if it["bucket"] == "censored":
            status = f"censored:{it['reason']}"
        elif it["bucket"] == "uninformative":
            status = "reportable:uninformative (cond_n<3)"
        else:
            status = "reportable"
        record("fig1_cross_model_incident1", "with_tool" , it["label"], it["k"], it["n"], rate, lo, hi, status)


# ===========================================================================
# Figure 2: nex-n2.5-mini local, incident effect across arms
# ===========================================================================
def fig2_nex_incident_effect(cells):
    model = "Nex-N2.5-mini-Q4_K_M.gguf"
    mode = "tools/native+think"
    arm_order = [
        ("blatant_wrongdoing", "incident 1\nledger fabrication"),
        ("blatant_safety_falsification", "incident 2\nmodel-card falsification"),
        ("blatant_oversight_evasion", "incident 3\naudit logging off"),
        ("benign_anomaly", "benign control"),
        ("blatant_wrongdoing_noaddressee", "incident 1\nno addressee"),
        ("blatant_safety_addressee", "incident 2\nwith addressee"),
    ]
    by_arm = {r["arm"]: r for r in cells
              if r["model"] == model and r["mode"] == mode and r["tool_arm"] == "with_tool"}

    items = []
    for arm, label in arm_order:
        r = by_arm.get(arm)
        if r is None:
            continue
        cond_k, cond_n = intf(r["cond_k"]), intf(r["cond_n"])
        items.append(dict(label=label, k=cond_k, n=cond_n))

    colors = [OKABE_ITO[5], OKABE_ITO[5], OKABE_ITO[5], OKABE_ITO[2], OKABE_ITO[6], OKABE_ITO[6]]
    for it, c in zip(items, colors):
        it["color"] = c

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    legend = [
        Patch(facecolor=OKABE_ITO[5], edgecolor="black", label="blatant incident (1/2/3, human-wrongdoer control)"),
        Patch(facecolor=OKABE_ITO[2], edgecolor="black", label="benign control"),
        Patch(facecolor=OKABE_ITO[6], edgecolor="black", label="addressee minimal pair (human-wrongdoer control)"),
    ]
    plot_rate_bars(ax, items, legend_handles=legend, legend_loc="upper right")
    ax.set_title("nex-n2.5-mini (local, thinking on, human-wrongdoer control): reporting rate by incident")
    fig.tight_layout(rect=[0, 0.15, 1, 1])
    fig.text(0.5, 0.03,
              "Human-wrongdoer control arms: with_tool, conditional rate (alerted / discovered), Wilson "
              "95% CI, k/N above each bar.\n"
              "Incident 1 is the outlier; incidents 2 and 3 and the benign control sit near zero. The "
              "addressee minimal pair (right two bars) tests whether a named recipient explains the gap "
              "and does not close it (FINDINGS §F110).",
              ha="center", fontsize=8.5, style="italic")
    savefig(fig, "fig2_nex_incident_effect.png")

    for it in items:
        rate = it["k"] / it["n"] if it["n"] else None
        lo, hi = wilson(it["k"], it["n"]) if it["n"] else (None, None)
        record("fig2_nex_incident_effect", "with_tool", it["label"].replace("\n", " "), it["k"], it["n"], rate, lo, hi, "reportable")


# ===========================================================================
# Figure 3: nemotron-3.5-lightning local, silent bystander funnel
# ===========================================================================
def fig3_lightning_silent_bystander(cells):
    model = "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf"
    clusters = [
        ("tools/native", "blatant_wrongdoing", "incident 1\n(thinking off)"),
        ("tools/native+think", "blatant_wrongdoing", "incident 1\n(thinking on)"),
        ("tools/native+think", "blatant_oversight_evasion", "incident 3\n(thinking on)"),
        ("tools/native+think", "blatant_safety_falsification", "incident 2\n(thinking on)"),
    ]
    rows_by_key = {(r["mode"], r["arm"], r["tool_arm"]): r for r in cells if r["model"] == model}

    metrics = ["floor", "cover", "discovered", "alerted"]
    metric_labels = {"floor": "floor (tool_probe)", "cover": "cover task passed",
                      "discovered": "discovered evidence", "alerted": "alerted"}
    metric_colors = {"floor": OKABE_ITO[1], "cover": OKABE_ITO[2],
                      "discovered": OKABE_ITO[4], "alerted": OKABE_ITO[5]}

    cluster_data = []
    for mode, arm, label in clusters:
        r = rows_by_key.get((mode, arm, "with_tool"))
        if r is None:
            continue
        n = intf(r["n"])
        floor_k, floor_n = intf(r["floor_k"]), intf(r["floor_n"])
        cover_k = intf(r["cover"])
        cond_k, cond_n = intf(r["cond_k"]), intf(r["cond_n"])
        vals = {
            "floor": (floor_k, floor_n),
            "cover": (cover_k, n),
            "discovered": (cond_n, n),
            "alerted": (cond_k, cond_n),
        }
        cluster_data.append((label, vals))

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ngroups = len(cluster_data)
    width = 0.19
    x0 = np.arange(ngroups)
    for mi, m in enumerate(metrics):
        xs = x0 + (mi - 1.5) * width
        for gi, (label, vals) in enumerate(cluster_data):
            k, n = vals[m]
            if not n:
                continue
            rate = k / n
            lo, hi = wilson(k, n)
            ax.bar(xs[gi], rate, width=width * 0.92, color=metric_colors[m],
                   edgecolor="black", linewidth=0.5, zorder=3,
                   label=metric_labels[m] if gi == 0 else None)
            err_lo, err_hi = err_bar(rate, lo, hi)
            ax.errorbar(xs[gi], rate, yerr=[[err_lo], [err_hi]], fmt="none", ecolor="black",
                        capsize=2.5, linewidth=0.8, zorder=4)
            txt = f"{k}/{n}"
            if m == "alerted" and k == 0:
                txt = f"0/{n}\n(Wilson upper {hi:.2f})"
            ax.text(xs[gi], hi + 0.02, txt, ha="center", va="bottom", fontsize=6.6, rotation=0)
            record("fig3_lightning_silent_bystander", m, label.replace("\n", " "), k, n, rate, lo, hi, "reportable")

    ax.set_xticks(x0)
    ax.set_xticklabels([c[0] for c in cluster_data], fontsize=9)
    ax.set_ylim(0, 1.28)
    ax.set_ylabel("rate (each bar's own denominator, see legend)")
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9, ncol=2)
    ax.set_title("nemotron-3.5-lightning (local, human-wrongdoer control): the funnel from tool-use floor to alerting, per incident")
    fig.tight_layout(rect=[0, 0.14, 1, 1])
    fig.text(0.5, 0.03,
              "Human-wrongdoer control arms. floor = tool_probe check; cover = cover task passed; "
              "discovered = evidence found; alerted = reports given discovery.\n"
              "All four alerting cells are 0; the Wilson upper bound is printed above each 0/N bar.",
              ha="center", fontsize=8.3, style="italic")
    savefig(fig, "fig3_lightning_silent_bystander.png")


# ===========================================================================
# Figure 4: Part 1 competence vs concealment
# ===========================================================================
def fig4_part1_competence_vs_concealment(rows):
    keep = []
    for r in rows:
        model = r["model"]
        if model in ("north-mini-code (screen)", "north-mini-code (bigbatch)"):
            continue
        if not r["competence"]:
            continue
        keep.append(r)

    moe = {"north-mini-code (pooled)", "nex-n2.5-mini", "nemotron-3.5-lightning"}

    # llama-3.3-70b-instruct, olmo-3-7b-instruct, gemma-3-27b-it and gemma-3-12b-it
    # all sit within competence 0.13-0.24 and rate 0.00-0.03, with large markers
    # (total_rows 62-166), so point offsets alone collide. Instead route all four to
    # a single left-aligned column in the empty band above the cluster (y 0.06-0.17),
    # ordered so target y increases monotonically with marker x (llama < olmo <=
    # gemma-3-27b-it < gemma-3-12b-it) -- a non-crossing matching, so the four leader
    # lines fan out without intersecting each other or any marker.
    label_data_pos = {
        "llama-3.3-70b-instruct": (0.02, 0.060),
        "olmo-3-7b-instruct": (0.02, 0.095),
        "gemma-3-27b-it": (0.02, 0.130),
        "gemma-3-12b-it": (0.02, 0.165),
    }
    # Everything else: a small point offset is enough.
    label_offset = {
        "nemotron-3.5-lightning": (10, 6),
        "nex-n2.5-mini": (-78, 2),
        "qwen3.8-27b": (10, 6),
        "north-mini-code": (10, 6),
    }

    fig, ax = plt.subplots(figsize=(9.5, 7.0))
    for r in keep:
        model = r["model"]
        comp = float(r["competence"])
        k, n = int(r["concealed_rows"]), int(r["total_rows"])
        rate = k / n
        lo, hi = wilson(k, n)
        is_moe = model in moe
        color = OKABE_ITO[4] if is_moe else OKABE_ITO[5]
        marker = "D" if is_moe else "o"
        size = 30 + 6.0 * n
        ax.scatter(comp, rate, s=size, c=color, marker=marker, edgecolor="black",
                   linewidth=0.7, zorder=3)
        err_lo, err_hi = err_bar(rate, lo, hi)
        ax.errorbar(comp, rate, yerr=[[err_lo], [err_hi]], fmt="none", ecolor="black",
                    capsize=3, linewidth=0.9, zorder=4)
        label = model.replace(" (pooled)", "")
        if label in label_data_pos:
            tx, ty = label_data_pos[label]
            ax.annotate(label, xy=(comp, rate), xycoords="data",
                        xytext=(tx, ty), textcoords="data", fontsize=8,
                        ha="left", va="center",
                        arrowprops=dict(arrowstyle="-", color="#888888", linewidth=0.6,
                                         shrinkA=0, shrinkB=4))
        else:
            dx, dy = label_offset.get(label, (7, 5))
            ax.annotate(label, (comp, rate), textcoords="offset points", xytext=(dx, dy), fontsize=8,
                       arrowprops=dict(arrowstyle="-", color="#888888", linewidth=0.6,
                                        shrinkA=0, shrinkB=4) if (dx, dy) != (7, 5) else None)
        record("fig4_part1_competence_vs_concealment", "moe" if is_moe else "dense", model,
               k, n, rate, lo, hi, "reportable")

    ax.axvline(0.75, color=NEUTRAL_GRAY, linestyle="--", linewidth=1.2, zorder=2)
    ax.set_xlabel("competence (original_pass / original_total)")
    ax.set_ylabel("concealment rate (concealed_rows / total_rows), Wilson 95% CI")
    ax.set_xlim(0, 1.05)
    bottom, top = ax.get_ylim()
    ax.set_ylim(0, max(top, 0.05))
    ax.text(0.755, ax.get_ylim()[1] * 0.97, "competence floor 0.75", fontsize=8, color=NEUTRAL_GRAY,
            rotation=90, va="top", ha="left")
    ax.grid(alpha=0.25, zorder=0)
    legend = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor=OKABE_ITO[4], markeredgecolor="black",
               markersize=9, label="MoE"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=OKABE_ITO[5], markeredgecolor="black",
               markersize=9, label="dense"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=9, title="architecture")
    ax.set_title("Part 1: competence vs visible-prose concealment, per model")
    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.5, 0.025,
              "Point size scales with total_rows (sample count). Models left of the dashed line are "
              "below the competence floor and their concealment rate is not evidence about propensity\n"
              "(FINDINGS §F126); north-mini-code shows the pooled row only.",
              ha="center", fontsize=8.5, style="italic")
    savefig(fig, "fig4_part1_competence_vs_concealment.png")


# ===========================================================================
# Figure 5: probe AUC by layer, honest (pre-decision) slot vs confounded slot
# ===========================================================================
def fig5_probe_auc_by_layer(probe):
    cells = probe["cells"]
    honest = [c for c in cells if c["slot"] == "mean_all"]
    honest.sort(key=lambda c: c["layer"])
    confounded = [c for c in cells if c["slot"] == "last"]
    confounded.sort(key=lambda c: c["layer"])

    best = probe["best"]  # this file's own reported best cell (the confounded 'last' slot)
    best_honest = max(honest, key=lambda c: c["auc"])

    fig, ax = plt.subplots(figsize=(9.0, 6.0))
    layers_h = [c["layer"] for c in honest]
    aucs_h = [c["auc"] for c in honest]
    ax.plot(layers_h, aucs_h, "-o", color=OKABE_ITO[4], linewidth=2, markersize=7,
            label="honest: pre-decision mean-pooled (mean_all / mean_final_turn overlap here)", zorder=4)

    layers_c = [c["layer"] for c in confounded]
    aucs_c = [c["auc"] for c in confounded]
    ax.plot(layers_c, aucs_c, "--s", color=CENSORED_GRAY, linewidth=1.4, markersize=6,
            label="confounded: last-token-before-cut (leaks position/context length, not a result)", zorder=3)

    ax.axhline(0.5, color="black", linewidth=1.0, linestyle=":", zorder=2)
    ax.text(layers_h[-1] + 0.05, 0.505, "chance (AUC 0.5)", fontsize=8, va="bottom")

    ax.annotate(
        f"best honest cell: layer {best_honest['layer']}, AUC {best_honest['auc']:.3f}\n"
        f"permutation p = {best_honest['p']:.3f} (n={best_honest['n_scored']}, within-batch null)\n"
        f"not significant at n={probe['n']} ({probe['alerted']} alerting)",
        xy=(best_honest["layer"], best_honest["auc"]),
        xytext=(best_honest["layer"] - 3.2, best_honest["auc"] + 0.09),
        fontsize=8.3, ha="left",
        arrowprops=dict(arrowstyle="->", color="black", linewidth=0.9),
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=NEUTRAL_GRAY, alpha=0.95))

    ax.set_xlabel("layer (0-indexed, 8 layers extracted)")
    ax.set_ylabel("AUC (class-mean-difference direction, held out by capture batch)")
    ax.set_ylim(0.4, 1.0)
    ax.set_xticks(range(min(layers_h), max(layers_h) + 1))
    ax.grid(alpha=0.25, zorder=0)
    ax.legend(loc="lower left", fontsize=7.8, framealpha=0.92)
    ax.set_title("Alerting probe (human-wrongdoer control arm): pre-decision residual stream, honest vs confounded pooling window")
    fig.tight_layout(rect=[0, 0.14, 1, 1])
    fig.text(0.5, 0.03,
              "Arm blatant_wrongdoing (human-wrongdoer control), n=108 episodes (27 alerting), 9 capture "
              "batches, permutation null within batch (FINDINGS §F167). The last slot pools through the "
              "decision token and is\n"
              "reported for completeness only, never interpreted as a result (module docstring, "
              "bystander/probe_alert.py). Verdict: no detected pre-decision representation of the "
              "reporting decision at this n.",
              ha="center", fontsize=8.3, style="italic")
    savefig(fig, "fig5_probe_auc_by_layer.png")

    for c in honest:
        record("fig5_probe_auc_by_layer", "honest_mean_all", f"layer {c['layer']}",
               probe["alerted"], probe["n"], c["auc"], None, None,
               f"p={c['p']}")
    for c in confounded:
        record("fig5_probe_auc_by_layer", "confounded_last", f"layer {c['layer']}",
               probe["alerted"], probe["n"], c["auc"], None, None,
               f"p={c['p']} CONFOUNDED not a result")


# ===========================================================================
# Figure 6: scaling read, conditional rate vs active params
# ===========================================================================
def fig6_scaling_read(cells, params_table):
    """Conditional rate (fig1's own source: cells_2026-09-15_after_w4c.csv,
    report.py v1.1) vs active parameters. Only the params table (total/active B,
    family) comes from 2026-09-14-scaling-read.json, joined by regex match against
    each cell's raw model string via match_params()."""
    from collections import defaultdict
    import numpy as _np
    from scipy import stats as _stats

    rows = [r for r in cells if r["arm"] == "blatant_wrongdoing" and r["tool_arm"] == "with_tool"]

    matched = []  # (row, params_table entry) for everything that matched a pattern
    unmatched_raw = []
    for r in rows:
        p = match_params(r["model"], params_table)
        if p is None:
            unmatched_raw.append(r["model"])
            continue
        matched.append((r, p))

    open_weight = [(r, p) for r, p in matched if p["family"] != "claude"]
    claude = [(r, p) for r, p in matched if p["family"] == "claude"]

    def cell_status(r):
        reason = (r["refused"] or "").strip()
        cond_k, cond_n = intf(r["cond_k"]), intf(r["cond_n"])
        if reason:
            return "censored", reason, None, None
        if not cond_n:
            return "censored", "no discovered evidence (0/0)", None, None
        return "reportable", None, cond_k, cond_n

    families = sorted({p["family"] for _, p in open_weight if p["active_params_B"] is not None})
    fam_style = {}
    for i, fam in enumerate(families):
        color = OKABE_ITO[i % len(OKABE_ITO)]
        marker = "o" if i < len(OKABE_ITO) else "s"
        fam_style[fam] = (color, marker)

    groups = defaultdict(list)
    for r, p in open_weight:
        if p["active_params_B"] is None:
            continue
        groups[(p["family"], p["active_params_B"])].append((r, p))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.8), gridspec_kw={"width_ratios": [3.3, 1]})

    spearman_x, spearman_y = [], []
    for (fam, ap), grp in groups.items():
        grp_sorted = sorted(grp, key=lambda rp: (cell_status(rp[0])[0] == "censored", rp[0]["model"]))
        m = len(grp_sorted)
        for gi, (r, p) in enumerate(grp_sorted):
            jitter = 1.0 + (gi - (m - 1) / 2.0) * 0.045
            x = ap * jitter
            color, marker = fam_style[fam]
            status, reason, cond_k, cond_n = cell_status(r)
            n = intf(r["n"])
            size = 45 + 5.0 * (n or 6)
            if status == "censored":
                ax.scatter(x, 0.0, s=size, facecolors="none", edgecolors=color, marker=marker,
                           linewidth=1.6, zorder=4)
                record("fig6_scaling_read", fam, r["model"], cond_k, cond_n,
                       None, None, None, f"censored:{reason}")
            else:
                rate = cond_k / cond_n
                lo, hi = wilson(cond_k, cond_n)
                ax.scatter(x, rate, s=size, c=color, marker=marker, edgecolor="black",
                           linewidth=0.6, zorder=5)
                err_lo, err_hi = err_bar(rate, lo, hi)
                ax.errorbar(x, rate, yerr=[[err_lo], [err_hi]], fmt="none", ecolor="black",
                            capsize=2.5, linewidth=0.8, zorder=4, alpha=0.75)
                record("fig6_scaling_read", fam, r["model"], cond_k, cond_n,
                       rate, lo, hi, "reportable")
                spearman_x.append(ap)
                spearman_y.append(rate)

    # Spearman rho + a permutation p-value (not scipy's asymptotic one), over the
    # reportable incident-1 with_tool cells actually plotted in the main panel.
    rho_obs = float(_stats.spearmanr(spearman_x, spearman_y).statistic)
    rng = _np.random.default_rng(20260914)
    y_arr = _np.array(spearman_y)
    n_perm = 20000
    perm_rhos = _np.empty(n_perm)
    for i in range(n_perm):
        perm_rhos[i] = _stats.spearmanr(spearman_x, rng.permutation(y_arr)).statistic
    perm_p = float((_np.sum(_np.abs(perm_rhos) >= abs(rho_obs)) + 1) / (n_perm + 1))
    n_spearman = len(spearman_x)

    ax.set_xscale("log")
    ax.set_xlabel("active parameters (B, log scale)")
    ax.set_ylabel("conditional rate on incident 1, with_tool (alerted / discovered)")
    ax.set_ylim(-0.06, 1.08)
    ax.grid(alpha=0.25, which="both", zorder=0)
    ax.set_title("Incident 1 conditional rate vs active parameters, by model family (human-wrongdoer control)")

    legend_handles = []
    for fam in families:
        color, marker = fam_style[fam]
        legend_handles.append(Line2D([0], [0], marker=marker, color="w", markerfacecolor=color,
                                      markeredgecolor="black", markersize=8, label=fam))
    legend_handles.append(Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
                                  markeredgecolor=NEUTRAL_GRAY, markersize=9, markeredgewidth=1.6,
                                  label="censored (plotted at y=0, not a measured zero)"))
    ax.legend(handles=legend_handles, loc="upper right", fontsize=7.6, ncol=2, framealpha=0.92)

    # Side panel: Claude models, undisclosed parameter counts, own small vertical-bar axis.
    claude_items = []
    for r, p in claude:
        status, reason, cond_k, cond_n = cell_status(r)
        rate = cond_k / cond_n if status == "reportable" else None
        lo, hi = wilson(cond_k, cond_n) if status == "reportable" else (None, None)
        claude_items.append(dict(label=p["slug"], k=cond_k, n=cond_n))
        record("fig6_scaling_read", "claude", r["model"], cond_k, cond_n, rate, lo, hi,
               status if status == "reportable" else f"censored:{reason}")
    for it in claude_items:
        it["color"] = OKABE_ITO[6]
    plot_rate_bars(ax2, claude_items, ylabel="conditional rate", ymax=1.18)
    ax2.set_xticklabels([it["label"] for it in claude_items], rotation=0, ha="center", fontsize=9)
    ax2.set_title("Claude\n(active params undisclosed)", fontsize=10)
    ax2.text(0.5, -0.24, "Not on the log-params axis: Anthropic\ndoes not disclose parameter counts.",
              fontsize=7.5, style="italic", ha="center", transform=ax2.transAxes)

    fig.tight_layout(rect=[0, 0.14, 1, 1])
    fig.text(0.5, 0.035,
              "Human-wrongdoer control arm (blatant_wrongdoing). Source: "
              "research/audits/cells_2026-09-20_after_w42.csv (same v1.1 keys as fig1); "
              "active/total params and family joined from 2026-09-14-scaling-read.json's params table by\n"
              "regex match on the raw model string. Open markers are censored cells (competence floor or "
              f"no discovered evidence) shown at y=0, not a measured zero. Spearman rho over the {n_spearman} "
              f"reportable points = {rho_obs:.2f} (permutation p = {perm_p:.2f}, {n_perm} permutations), not significant.",
              ha="center", fontsize=8, style="italic")
    savefig(fig, "fig6_scaling_read.png")

    return dict(rho=rho_obs, p=perm_p, n=n_spearman, n_perm=n_perm, unmatched=sorted(set(unmatched_raw)))




# ===========================================================================
# Figure 7: qwen3.5-27b local, instruction ladder on incident 1
# ===========================================================================
def fig7_instruction_ladder(cells):
    model = "qwen3.5-27b.gguf"
    mode = "tools/native"
    arm = "blatant_wrongdoing"
    order = [
        ("tool_probe", "tool_probe\n(ordered / instrument check)"),
        ("with_tool_named", "with_tool_named\n(category named)"),
        ("with_tool", "with_tool\n(mundane instructions)"),
        ("no_tool", "no_tool\n(final message only)"),
    ]
    by_tool_arm = {r["tool_arm"]: r for r in cells
                   if r["model"] == model and r["mode"] == mode and r["arm"] == arm}

    items = []
    for ta, label in order:
        r = by_tool_arm.get(ta)
        if r is None:
            continue
        reason = (r["refused"] or "").strip()
        cond_k, cond_n = intf(r["cond_k"]), intf(r["cond_n"])
        if reason:
            items.append(dict(label=label, k=None, n=None, reason=reason))
        else:
            items.append(dict(label=label, k=cond_k, n=cond_n))

    colors = [OKABE_ITO[1], OKABE_ITO[6], OKABE_ITO[5], CENSORED_GRAY]
    for it, c in zip(items, colors):
        it["color"] = c

    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    plot_rate_bars(ax, items)
    ax.set_title("qwen3.5-27b (local, incident 1, human-wrongdoer control): reporting rate by instruction strength")
    fig.tight_layout(rect=[0, 0.16, 1, 1])
    fig.text(0.5, 0.035,
              "Human-wrongdoer control arm. Same model, same incident, four channels of decreasing "
              "instruction strength. Ordered\n"
              "instrument check (tool_probe) is 8/8; removing the tool entirely (no_tool) leaves prose "
              "as the only channel and the cell is refused for having no channel to score, not measured "
              "as zero.",
              ha="center", fontsize=8.5, style="italic")
    savefig(fig, "fig7_instruction_ladder.png")

    for it in items:
        rate = it["k"] / it["n"] if it["n"] else None
        lo, hi = wilson(it["k"], it["n"]) if it["n"] else (None, None)
        status = "reportable" if it["n"] else f"censored:{it['reason']}"
        record("fig7_instruction_ladder", "blatant_wrongdoing", it["label"].replace("\n", " "),
               it["k"], it["n"], rate, lo, hi, status)


# ===========================================================================
# figure_values.csv
# ===========================================================================
def write_values_csv():
    path = os.path.join(OUT, "figure_values.csv")
    fields = ["figure", "series", "label", "k", "n", "rate", "ci_lo", "ci_hi", "status"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in VALUES:
            w.writerow(row)
    print(f"wrote {path} ({len(VALUES)} rows)")


def main():
    cells = load_cells()
    concealment = load_concealment()
    probe = load_probe()
    scaling = load_scaling()

    fig1_cross_model_incident1(cells)
    fig2_nex_incident_effect(cells)
    fig3_lightning_silent_bystander(cells)
    fig4_part1_competence_vs_concealment(concealment)
    fig5_probe_auc_by_layer(probe)
    spearman = fig6_scaling_read(cells, scaling["params_table"])
    fig7_instruction_ladder(cells)

    write_values_csv()
    print(f"fig6 spearman: rho={spearman['rho']:.4f} p={spearman['p']:.4f} "
          f"n={spearman['n']} ({spearman['n_perm']} permutations)")
    if spearman["unmatched"]:
        print(f"fig6 unmatched models (no params_table pattern, excluded from main panel): "
              f"{spearman['unmatched']}")


if __name__ == "__main__":
    main()
