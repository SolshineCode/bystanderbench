#!/usr/bin/env python3
"""Package BystanderBench activation captures as a PRIVATE HF dataset and upload.

The bystander captures had no upload path — MANIFEST.md listed 134 MB of them as
"local-only, not in git and not yet on HF", which means the only copy of the residual
streams the mech-interp tools need lives on one disk. This closes that.

Layout produced (one dir per capture tree, preserved):
    <tree>/manifest.tsv            byte offsets, as written by capture_activations.py
    <tree>/*.meta.json             per-episode sidecar: cid, arm, tool_arm, scores, layers
    <tree>/*.txt                   the teacher-forced text that was replayed
    <tree>/acts/*.bin              float32 [n_layers, 3, d_model], C order
    README.md                      dataset card, generated from the data, not a template

Every bin is size-checked against n_layers * 3 * d_model * 4 before upload (§F87: the
wrong-layer-list bug was caught by exactly this arithmetic and nothing else).

Token: HF_AGENT_TOKEN / HF_TOKEN from ~/.hermes/.env, never printed.

Usage:
  package_acts_to_hf.py --repo-id DarkStarDeleeuw/<name> --layers 8,20,32,44,50,53,64,72 \
      --d-model 8192 --model-label "Llama-3.3-70B-Instruct-Q4_K_M" \
      bystander/acts_llama70b [more dirs ...] [--no-upload]
"""
from __future__ import annotations
import argparse, json, os, shutil, sys, glob
from collections import Counter
from pathlib import Path

# Repo root from this file, not an absolute path (2026-09-12).
BASE = Path(__file__).resolve().parent.parent


def read_hf_token() -> str:
    for line in open(os.path.expanduser("~/.hermes/.env")):
        line = line.strip()
        if line.startswith(("HF_AGENT_TOKEN=", "HF_TOKEN=")):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    raise SystemExit("HF_AGENT_TOKEN/HF_TOKEN not found in ~/.hermes/.env")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--layers", required=True, help="comma list, must match what was captured")
    ap.add_argument("--d-model", type=int, required=True)
    ap.add_argument("--model-label", required=True)
    ap.add_argument("--serving", default="", help="serving config, recorded verbatim on the card")
    ap.add_argument("--stage", default=str(BASE / "bystander/.hf_stage"))
    ap.add_argument("--no-upload", action="store_true")
    a = ap.parse_args()

    layers = [int(x) for x in a.layers.split(",")]
    expect = len(layers) * 3 * a.d_model * 4

    stage = Path(a.stage)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    total_bins = 0
    arms: Counter = Counter()
    alerted = discovered = cover = 0
    scored = 0
    for d in a.dirs:
        src = Path(d)
        if not src.is_dir():
            raise SystemExit(f"not a directory: {src}")
        dst = stage / src.name
        (dst / "acts").mkdir(parents=True)
        for f in src.glob("*.meta.json"):
            shutil.copy2(f, dst / f.name)
            md = json.loads(f.read_text())
            arms[f"{md.get('arm')}/{md.get('tool_arm')}"] += 1
            sc = (md.get("scores") or {}).get("bystander_scorer") or {}
            if sc:
                scored += 1
                alerted += int(bool(sc.get("alerted")))
                discovered += int(bool(sc.get("discovered_content")))
                cover += int(bool(sc.get("cover_task_passed")))
        for f in src.glob("*.txt"):
            shutil.copy2(f, dst / f.name)
        if (src / "manifest.tsv").exists():
            shutil.copy2(src / "manifest.tsv", dst / "manifest.tsv")
        if (src / "extract.log").exists():
            shutil.copy2(src / "extract.log", dst / "extract.log")
        for f in sorted((src / "acts").glob("*.bin")):
            sz = f.stat().st_size
            if sz != expect:
                raise SystemExit(
                    f"REFUSING to upload: {f} is {sz} bytes, expected {expect} "
                    f"({len(layers)} layers x 3 x {a.d_model} x 4). A size mismatch is how the "
                    f"§F87 wrong-layer-list bug was caught; it is never a rounding issue."
                )
            shutil.copy2(f, dst / "acts" / f.name)
            total_bins += 1

    card = f"""---
license: cc-by-4.0
tags: [interpretability, activations, agentic-safety, bystandebench]
---

# BystanderBench residual-stream capture — {a.model_label}

Teacher-forced residual activations for BystanderBench episodes: each finished episode is
replayed through the same local GGUF that produced it, and the residual stream is pooled and
written out. **These are a replay, not the generating forward pass.**

- **model**: `{a.model_label}`
- **layers**: `{a.layers}` ({len(layers)} layers)
- **d_model**: {a.d_model}
- **bin layout**: float32, shape `[{len(layers)}, 3, {a.d_model}]`, C order, {expect} bytes each
- **bins**: {total_bins}
- **serving**: {a.serving or "see extract.log"}

## Cells included

| arm / tool_arm | episodes |
|---|---|
""" + "\n".join(f"| `{k}` | {v} |" for k, v in sorted(arms.items())) + f"""

Across {scored} episodes with scores attached: `alerted` {alerted}, `discovered_content`
{discovered}, `cover_task_passed` {cover}. **Do not compute a rate from this dataset.** Capture
is prioritised and not necessarily exhaustive, and released rates come only from
`bystander/report.py`, which applies the affordance floor, the competence gate and the
evidence-only discovery rule. The scores here are carried per episode so an analysis can
condition on them, not so they can be summed.

## Files

- `*/manifest.tsv` — byte offsets written by `capture_activations.py`
- `*/*.meta.json` — per-episode sidecar: cid, arm, tool_arm, episode, n_tokens, pool span, scores
- `*/*.txt` — the exact text replayed
- `*/acts/*.bin` — the activations
- `*/extract.log` — the extractor's own log, including the `(N layers x 3 x d)` line per bin

Every bin was size-checked against {expect} bytes before upload. Provenance and the
methodology that produced the episodes: `bystander/METHODOLOGY-v1.0.md` (frozen) with the v1.1 changelog `bystander/METHODOLOGY-v1.1.md` and
`research/FINDINGS.md` in the source repo.
"""
    (stage / "README.md").write_text(card)

    print(f"staged {total_bins} bins from {len(a.dirs)} tree(s) -> {stage}")
    print(f"  every bin verified at {expect} bytes ({len(layers)} layers x 3 x {a.d_model} x 4)")
    print(f"  arms: {dict(arms)}")
    if a.no_upload:
        print("--no-upload: stopping before the HF call")
        return

    from huggingface_hub import HfApi
    api = HfApi(token=read_hf_token())
    api.create_repo(a.repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(folder_path=str(stage), repo_id=a.repo_id, repo_type="dataset",
                      commit_message=f"BystanderBench capture: {a.model_label}, {total_bins} bins")
    print(f"uploaded to https://huggingface.co/datasets/{a.repo_id} (private)")


if __name__ == "__main__":
    main()
