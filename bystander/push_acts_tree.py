#!/usr/bin/env python3
"""Push a bystander token+activation tree to the private DarkStarDeleeuw account, then read it back.

    HF_TOKEN=... python bystander/push_acts_tree.py bystander/acts_<tag> \
        DarkStarDeleeuw/bluedot-unit2-bystander-<tag>-<date> [--readback N] [--extra path:dest ...]

Discipline (CLAUDE.md "Data permanence", §F116): identity hard-asserted as DarkStarDeleeuw, every
file uploaded from the staging dir (the staging dir IS the published content), then N files chosen
at random are downloaded again and MD5-compared byte for byte against the local copies. The script
exits non-zero if any read-back differs, so a "pushed" line in a log is tied to a verified outcome.
"""
import argparse, hashlib, os, random, sys, tempfile
from huggingface_hub import HfApi, hf_hub_download

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("repo")
ap.add_argument("--readback", type=int, default=6)
ap.add_argument("--extra", nargs="*", default=[], help="local:dest pairs uploaded beside the tree")
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

tok = os.environ.get("HF_TOKEN") or sys.exit("HF_TOKEN not set")
api = HfApi(token=tok)
who = api.whoami()["name"]
assert who == "DarkStarDeleeuw", f"identity guard: got {who!r}, refusing to publish"
assert a.repo.startswith("DarkStarDeleeuw/"), a.repo

files = []
for root, _, names in os.walk(a.src):
    for n in names:
        p = os.path.join(root, n); files.append((p, os.path.relpath(p, a.src)))
bins = [f for f in files if f[1].endswith(".bin")]
print(f"{a.src}: {len(files)} files ({len(bins)} .bin, {sum(os.path.getsize(p) for p, _ in files)/1e6:.1f} MB) -> {a.repo}")
if a.dry_run: sys.exit(0)

api.create_repo(a.repo, repo_type="dataset", private=True, exist_ok=True)
api.upload_folder(folder_path=a.src, repo_id=a.repo, repo_type="dataset",
                  commit_message=f"push {os.path.basename(a.src)} ({len(files)} files)")
for pair in a.extra:
    loc, dest = pair.split(":", 1)
    api.upload_file(path_or_fileobj=loc, path_in_repo=dest, repo_id=a.repo, repo_type="dataset")
    print("extra uploaded", loc, "->", dest)

info = api.dataset_info(a.repo)
assert info.private, "repo is not private"
remote = {s.rfilename for s in info.siblings}
missing = [rel for _, rel in files if rel not in remote]
assert not missing, f"missing on hub after upload: {missing[:5]}"
print(f"hub lists {len(remote)} files; all {len(files)} local files present; private={info.private}")

others = [f for f in files if not f[1].endswith(".bin")]
rng = random.Random(0)
sample = rng.sample(others, min(2, len(others))) + rng.sample(bins, min(max(a.readback - 2, 1), len(bins)))
bad = 0
with tempfile.TemporaryDirectory() as td:
    for p, rel in sample:
        q = hf_hub_download(a.repo, rel, repo_type="dataset", token=tok, cache_dir=td)
        h1 = hashlib.md5(open(p, "rb").read()).hexdigest(); h2 = hashlib.md5(open(q, "rb").read()).hexdigest()
        ok = h1 == h2; bad += (not ok)
        print(f"  readback {rel}: {'OK' if ok else 'MISMATCH'} {h1[:8]}")
print(f"read-back {len(sample) - bad}/{len(sample)} OK")
sys.exit(1 if bad else 0)
