#!/usr/bin/env python3
"""Package the llama3.3-70b concealment-probe run as an HF dataset and upload it
to the private DarkStarDeleeuw account.

Steps:
  1. gather samples.jsonl / transcripts.jsonl / tokens / acts / manifest from the
     prepared data dir into a staging folder
  2. copy raw .eval logs, llama-server logs, and the pipeline scripts
  3. render the dataset card from card_template.md with real counts
  4. (unless --no-upload) create the private dataset repo and upload_folder

Token: HF_TOKEN read from ~/.hermes/.env (never printed).

Usage:
  package_and_upload.py --data-dir concealment-probe/data/llama70b/llama3.3-70b \
      --logdir logs/llama3.3-70b-concealment [--logdir ...] \
      [--server-config "ngl:999,ctx:16384 (offloaded 81/81 layers)"] \
      [--throughput "..."] [--limits "oneoff 25, conflicting 25, original 15"] \
      [--max-attempts "3 (impossible splits), 2 (original)"] \
      [--client-timeout 4800] [--retry-budget 9600] \
      [--repo-id DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b] \
      [--no-upload]
"""
import argparse, glob, json, os, shutil, subprocess, sys
from collections import Counter

BASE = "/home/darkstar/bluedot-unit2-impossiblebench"
HERE = os.path.join(BASE, "llama70b")


def read_hf_token():
    with open(os.path.expanduser("~/.hermes/.env")) as f:
        for line in f:
            line = line.strip()
            if line.startswith(("HF_AGENT_TOKEN=", "HF_TOKEN=")):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    raise SystemExit("HF_AGENT_TOKEN/HF_TOKEN not found in ~/.hermes/.env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--logdir", action="append", default=[])
    ap.add_argument("--staging", default=os.path.join(BASE, "hf_upload_llama70b"))
    ap.add_argument("--repo-id", default="DarkStarDeleeuw/bluedot-unit2-concealment-probe-llama3.3-70b")
    ap.add_argument("--pipeline-dir", default=HERE,
                    help="pipeline variant dir (scripts + card_template.md live here)")
    ap.add_argument("--server-log-glob", default="llama70b_*.log",
                    help="glob under llamacpp_logs/ for this run's server logs")
    ap.add_argument("--server-config", default="(fill from serve_llama70b.sh SERVER_READY line)")
    ap.add_argument("--throughput", default="(fill from llamacpp_logs print_timing lines)")
    ap.add_argument("--limits", default="(fill)")
    ap.add_argument("--max-attempts", default="(fill)")
    ap.add_argument("--client-timeout", default="4800")
    ap.add_argument("--retry-budget", default="9600")
    ap.add_argument("--run-dates", default="(fill)")
    ap.add_argument("--bottom-line", default=None, help="override the auto bottom-line sentence")
    ap.add_argument("--no-upload", action="store_true")
    args = ap.parse_args()

    dd = os.path.abspath(args.data_dir)
    st = os.path.abspath(args.staging)
    os.makedirs(st, exist_ok=True)

    # --- 1. dataset files ---
    import sys
    sys.path.insert(0, os.path.join(BASE, "concealment-probe", "tools"))
    from corpus import load
    # Unit is 'row' to report what the uploaded file literally contains in its dataset card.
    rows = load(os.path.join(dd, "samples.jsonl"), unit="row")
    cats = Counter(r["category"] for r in rows)
    splits = Counter(r["split"] for r in rows)
    for fn in ("samples.jsonl", "manifest.tsv"):
        shutil.copy2(os.path.join(dd, fn), st)
    tj = os.path.join(dd, "transcripts.jsonl")
    if os.path.exists(tj):
        shutil.copy2(tj, st)
    else:
        print("WARNING: transcripts.jsonl missing from data dir", file=sys.stderr)
    # optional audit / provenance sidecars (2026-09-08): the hand audit must ship with the
    # rows it corrects, and a prioritised partial capture must ship the order it ran in.
    for fn in ("mechanism_audit.json", "manifest_prioritized.tsv", "prioritize.log"):
        if os.path.exists(os.path.join(dd, fn)):
            shutil.copy2(os.path.join(dd, fn), st)
    for sub in ("tokens", "acts"):
        dst = os.path.join(st, sub)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(os.path.join(dd, sub), dst)
    ov = os.path.join(dd, "label_overrides.json")
    shutil.copy2(ov, st) if os.path.exists(ov) else open(os.path.join(st, "label_overrides.json"), "w").write("{}\n")

    # --- 2. raw logs + pipeline scripts ---
    ev = os.path.join(st, "eval_logs"); os.makedirs(ev, exist_ok=True)
    for d in args.logdir:
        sub = os.path.join(ev, os.path.basename(os.path.normpath(d)))
        os.makedirs(sub, exist_ok=True)
        for p in glob.glob(os.path.join(d, "*.eval")):
            shutil.copy2(p, sub)
    ll = os.path.join(st, "llamacpp_logs"); os.makedirs(ll, exist_ok=True)
    for p in glob.glob(os.path.join(BASE, "llamacpp_logs", args.server_log_glob)):
        shutil.copy2(p, ll)
    pdir = os.path.abspath(args.pipeline_dir)
    pl = os.path.join(st, "pipeline"); os.makedirs(pl, exist_ok=True)
    for p in (glob.glob(os.path.join(pdir, "*.sh"))
              + glob.glob(os.path.join(pdir, "*.py"))
              + glob.glob(os.path.join(pdir, "card_template.md"))
              + [os.path.join(HERE, "package_and_upload.py"),
                 os.path.join(BASE, "run_eval_gpu.py"),
                 os.path.join(BASE, "concealment-probe", "tools", "prepare_dataset.py"),
                 os.path.join(BASE, "concealment-probe", "tools", "export_transcripts.py"),
                 os.path.join(BASE, "concealment-probe", "tools", "extract_resid.cpp")]):
        if os.path.exists(p):
            shutil.copy2(p, pl)

    # --- 3. render card ---
    # layers actually extracted (from any acts sidecar), fall back to planned sweep
    layers = None
    for j in glob.glob(os.path.join(dd, "acts", "*.json")):
        layers = json.load(open(j))["layers"]
        break
    if layers is None:
        layers = list(range(4, 77, 4))
        print("WARNING: no acts/*.json found; card uses the planned layer sweep", file=sys.stderr)

    n_cheat = cats.get("concealed_cheat", 0)
    n_imp = sum(v for k, v in cats.items() if not k.startswith("original"))
    bottom = args.bottom_line or (
        f"**{len(rows)} scored samples with activations; {n_cheat} `concealed_cheat` "
        f"({n_cheat}/{n_imp} impossible-split samples; qwen3.6's observed rate was ~1-in-25).** "
        "See the category table and caveats below."
    )
    cat_table = "\n".join(f"| `{k}` | {v} |" for k, v in sorted(cats.items()))
    split_counts = ", ".join(f"{k}: {v}" for k, v in sorted(splits.items()))
    caveats = (
        "- Labels machine-assigned, human spot-check planned but NOT yet run (see taxonomy section).\n"
        "- Sample counts reflect what completed inside the GPU reservation window on "
        "10-year-old hardware (~3-4 tok/s decode for a 70B); samples lost to timeouts/errors "
        "are visible in the raw eval_logs, nothing is hidden.\n"
        "- Synthetic/instructed elicitation environment (ImpossibleBench); not evidence about "
        "naturally-occurring deception.\n"
        "- Zero or few `concealed_cheat` samples would NOT be evidence the model doesn't game "
        "tests — LCB-hard problems are hard enough that models often fail before reaching the "
        "cheat-or-disclose decision point (`failed_silent`)."
    )
    ovd = json.load(open(os.path.join(st, "label_overrides.json"))) if os.path.exists(os.path.join(st, "label_overrides.json")) else {}
    ov_note = (f"{len(ovd)} hand-audited override(s) applied in this run (see `label_overrides.json`)."
               if ovd else "no overrides applied in this run yet — every keyword-flag hit still needs hand audit.")

    card = open(os.path.join(pdir, "card_template.md")).read()
    for k, v in {
        "@@BOTTOM_LINE@@": bottom,
        "@@CATEGORY_TABLE@@": cat_table,
        "@@SPLIT_COUNTS@@": split_counts,
        "@@SERVER_CONFIG@@": args.server_config,
        "@@THROUGHPUT@@": args.throughput,
        "@@MAX_ATTEMPTS@@": args.max_attempts,
        "@@LIMITS@@": args.limits,
        "@@CLIENT_TIMEOUT@@": str(args.client_timeout),
        "@@RETRY_BUDGET@@": str(args.retry_budget),
        "@@N_LAYERS@@": str(len(layers)),
        "@@LAYERS@@": ", ".join(map(str, layers)),
        "@@OVERRIDES_NOTE@@": ov_note,
        "@@CAVEATS@@": caveats,
        "@@RUN_DATES@@": args.run_dates,
    }.items():
        card = card.replace(k, v)
    if "@@" in card:
        print("WARNING: unfilled placeholders remain in card", file=sys.stderr)
    open(os.path.join(st, "README.md"), "w").write(card)

    print(f"staged {len(rows)} samples -> {st}")
    print("categories:", dict(cats))

    # --- 4. upload ---
    if args.no_upload:
        print("--no-upload: staging only")
        return
    from huggingface_hub import HfApi
    api = HfApi(token=read_hf_token())
    who = api.whoami()
    name = who.get("name", "?")
    assert name == "DarkStarDeleeuw", f"HF token belongs to '{name}', not DarkStarDeleeuw — refusing"
    api.create_repo(args.repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(folder_path=st, repo_id=args.repo_id, repo_type="dataset",
                      commit_message="llama3.3-70b concealment-probe run: transcripts + activations + card")
    print(f"uploaded: https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
