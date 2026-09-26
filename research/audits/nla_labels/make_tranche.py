#!/usr/bin/env python3
"""Make a labelling tranche from an explicit list of captured cids (AUTONOMOUS, 2026-09-23 night).

Groups the cids by source logdir, extracts only those episodes with extract_episodes.py (so
the same no-truncation, visible-only rules apply), splits into 4 parts, draws a seeded 12-episode
overlap for labeller B, and writes `manifests.txt`, the capture manifests the token mapping needs.

Usage: python make_tranche.py OUTDIR SEED CIDS_FILE
"""
import glob, json, os, random, subprocess, sys, tempfile

BASE = "/home/darkstar/bluedot-unit2-impossiblebench"
HERE = os.path.dirname(os.path.abspath(__file__))


def main(outdir, seed, cids_file):
    want = [l.strip() for l in open(cids_file) if l.strip()]
    os.makedirs(outdir, exist_ok=True)
    # A cid can sit in several capture trees, and some trees (e.g. acts_nex_pos.predecision) hold
    # streams TRUNCATED at the decision point. Pick, per cid, the tree with the LONGEST stream (the
    # full episode). The first-found tree was wrong for 19 of 48 human-arm episodes (2026-09-24).
    manif, best = {}, {}
    for m in glob.glob(f"{BASE}/bystander/acts_*/manifest.tsv"):
        for l in open(m):
            p = l.split("\t")[0]
            cid = p.rsplit("/", 1)[-1][:-4]
            fp = p if p.startswith("/") else f"{BASE}/{p}"
            try:
                n = sum(1 for _ in open(fp))
            except OSError:
                continue
            if n > best.get(cid, -1):
                best[cid], manif[cid] = n, m
    logdirs = sorted({f"{BASE}/logs/{c.split('__')[0]}" for c in want})
    with tempfile.TemporaryDirectory() as td:
        tmp = f"{td}/all.jsonl"
        subprocess.run([f"{BASE}/.venv/bin/python", f"{HERE}/extract_episodes.py", *logdirs, "--out", tmp], check=True)
        E = [json.loads(l) for l in open(tmp)]
    keep = set(want)
    E = [e for e in E if e["cid"] in keep]
    missing = sorted(keep - {e["cid"] for e in E})
    with open(f"{outdir}/episodes.jsonl", "w") as f:
        for e in E: f.write(json.dumps(e) + "\n")
    n = len(E); k = (n + 3) // 4
    for j in range(4):
        json.dump(E[j * k:(j + 1) * k], open(f"{outdir}/part{j}.json", "w"))
    rnd = random.Random(seed); ov = sorted(rnd.sample(range(n), min(12, n)))
    json.dump([E[i] for i in ov], open(f"{outdir}/overlap_B.json", "w"))
    ms = sorted({manif[e["cid"]] for e in E if e["cid"] in manif})
    open(f"{outdir}/manifests.txt", "w").write("\n".join(ms) + "\n")
    print(json.dumps({"requested": len(want), "extracted": n, "parts": [len(E[j*k:(j+1)*k]) for j in range(4)],
                      "missing (errored/non-success)": missing, "manifests": len(ms),
                      "arms": sorted({e["arm"] for e in E})}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
