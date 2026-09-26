#!/usr/bin/env python3
"""Stage and publish the MoE-floor rung-1 dataset to DarkStarDeleeuw (private).

Stages results for the three rung-1 models + card + pipeline scripts, then uploads.
Identity hard-assert (DarkStarDeleeuw) inherited from llama70b.package_and_upload.

Usage: publish_rung1.py [--no-upload]
"""
import argparse, glob, os, shutil, sys

BASE = "/home/darkstar/bluedot-unit2-impossiblebench"
HERE = os.path.join(BASE, "moe-floor")
sys.path.insert(0, os.path.join(BASE, "llama70b"))
from package_and_upload import read_hf_token  # noqa: E402

REPO_ID = "DarkStarDeleeuw/bluedot-unit2-moe-floor-rung1"
SLUGS = {
    "olmoe-1b7b": "moe-floor-olmoe-1b7b-20260903",
    "olmo-0724-7b": "moe-floor-olmo-0724-7b-20260903",
    "olmo2-7b": "moe-floor-olmo2-7b-20260903",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--staging", default=os.path.join(BASE, "hf_upload_moe_floor_rung1"))
    args = ap.parse_args()

    st = os.path.abspath(args.staging)
    os.makedirs(st, exist_ok=True)
    shutil.copy2(os.path.join(HERE, "rung1_card.md"), os.path.join(st, "README.md"))

    for tag, slug in SLUGS.items():
        src = os.path.join(HERE, "results", slug)
        dst = os.path.join(st, tag)
        os.makedirs(dst, exist_ok=True)
        for fn in ("samples.jsonl", "transcripts.jsonl", "run_meta.json", "label_overrides.json"):
            p = os.path.join(src, fn)
            if os.path.exists(p):
                shutil.copy2(p, dst)
        for sub in ("tokens", "acts"):
            d = os.path.join(dst, sub)
            shutil.rmtree(d, ignore_errors=True)
            if os.path.isdir(os.path.join(src, sub)):
                shutil.copytree(os.path.join(src, sub), d)
        for p in glob.glob(os.path.join(src, "*.log")):
            shutil.copy2(p, dst)
        n_acts = len(glob.glob(os.path.join(dst, "acts", "*.bin")))
        print(f"staged {tag}: acts={n_acts}")

    pl = os.path.join(st, "pipeline")
    os.makedirs(pl, exist_ok=True)
    for fn in ("kernel_template.py", "make_kernels.py", "aggregate_rung.py",
               "collect_results.sh", "push_kernel.sh"):
        shutil.copy2(os.path.join(HERE, fn), pl)

    if args.no_upload:
        print(f"staged only -> {st}")
        return
    from huggingface_hub import HfApi
    api = HfApi(token=read_hf_token())
    who = api.whoami()
    assert who.get("name") == "DarkStarDeleeuw", f"token is '{who.get('name')}', refusing"
    api.create_repo(REPO_ID, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(folder_path=st, repo_id=REPO_ID, repo_type="dataset",
                      commit_message="MoE-floor rung 1: OLMoE vs dense OLMo, transcripts + activations + audited labels")
    print(f"published: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
