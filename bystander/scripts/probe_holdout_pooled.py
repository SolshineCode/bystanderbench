#!/usr/bin/env python3
"""Pooled read over every fresh holdout of the fixed §F200 direction (§F202 procedure).

§F205 reported the pooled statement over five holdouts with numbers computed inline; this makes
that computation a file. Input: the per-holdout JSONs written by probe_holdout2.py --test. Each
one names its tree and log dirs, so the pooled set is exactly the set of holdouts on record and
nothing is re-typed from memory. The direction is re-checked against its sha; every tree is
re-scored by dot product; scores are concatenated; AUC, permutation p and bootstrap CI are
computed on the pool, with per-holdout AUCs beside them.

  python bystander/scripts/probe_holdout_pooled.py research/canonical/probe_holdout2_holdout2.json ... \
      --name pooled_2026-09-20 [--perms 4000] [--boot 2000] [--seed 20260920]
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, ".")
sys.path.insert(0, "bystander/scripts")
import probe_holdout2 as ph

ap = argparse.ArgumentParser()
ap.add_argument("jsons", nargs="+"); ap.add_argument("--name", required=True)
ap.add_argument("--perms", type=int, default=4000); ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--seed", type=int, default=20260920)
a = ap.parse_args()

z = np.load(ph.DIRFILE, allow_pickle=False)
d, rec = z["direction"], str(z["sha256"])
if ph.sha(d) != rec: sys.exit(f"direction file sha mismatch: {ph.sha(d)} != recorded {rec}")
train_cids = set(z["train_cids"].tolist())

scores, labels, holdout, per = [], [], [], {}
seen_cids = set()
for j in a.jsons:
    spec = json.load(open(j))
    if spec.get("direction_sha256") != rec: sys.exit(f"{j}: recorded direction sha differs")
    V, Y, S, C = ph.load_arm([spec["tree"]], spec["logdirs"], spec["arm"])
    if set(C.tolist()) & train_cids: sys.exit(f"{j}: cid overlap with training")
    dup = set(C.tolist()) & seen_cids
    if dup: sys.exit(f"{j}: cid overlap with another holdout: {sorted(dup)[:3]}")
    seen_cids |= set(C.tolist())
    s = V @ d
    scores.append(s); labels.append(Y); holdout += [spec["name"]] * len(Y)
    per[spec["name"]] = dict(n=int(len(Y)), alerted=int(Y.sum()), auc=ph.auc(s, Y),
                             recorded_auc=spec.get("auc"), recorded_p=spec.get("perm_p_holdout_labels"))
    if abs(per[spec["name"]]["auc"] - spec["auc"]) > 1e-9: sys.exit(f"{j}: re-scored AUC differs from recorded")

scores, labels = np.concatenate(scores), np.concatenate(labels)
observed = ph.auc(scores, labels)
rng = np.random.default_rng(a.seed)
hits = sum(1 for _ in range(a.perms) if ph.auc(scores, rng.permutation(labels)) >= observed)
p_perm = (hits + 1) / (a.perms + 1)
boots = []
for _ in range(a.boot):
    idx = rng.integers(0, len(labels), len(labels)); v = ph.auc(scores[idx], labels[idx])
    if not np.isnan(v): boots.append(v)
ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
out = dict(name=a.name, direction_sha256=rec, holdouts=per, n=int(len(labels)), alerted=int(labels.sum()),
           pooled_auc=observed, perm_p=p_perm, perms=a.perms, bootstrap_ci95=ci, boot=a.boot, seed=a.seed,
           ran_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
print(json.dumps(out, indent=1))
outp = Path(f"research/canonical/probe_holdout_pooled_{a.name}.json"); outp.write_text(json.dumps(out, indent=1))
print("wrote", outp)
