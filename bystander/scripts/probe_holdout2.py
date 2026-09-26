#!/usr/bin/env python3
"""Second (and later) independent holdout tests for the agent-arm alert direction (§F200 -> §F202).

§F201 made a second independent holdout the load-bearing test for the §F200 signal, and named
the procedure: SAME fixed direction, applied unchanged, NO refitting. This script makes "fixed"
checkable rather than asserted.

  --save-direction   computes the direction exactly as bystander/scripts/probe_holdout_transfer.py
                     does (gated tree acts_nex_agentarm.predecision3, slot mean_final_turn, layer
                     index 6 = model layer 37, unit(mean alerting - mean silent)) and writes it to
                     research/canonical/probe_direction_F200.npz together with the training cids
                     and a sha256 of the vector. Run BEFORE any holdout data exists; the sha is
                     quoted in the pre-registration entry.
  --test TREE --logdir L ... --name NAME
                     loads the saved direction, refuses if its sha differs from the one recorded
                     in the file, checks zero cid overlap with the training set, scores the
                     holdout by dot product, and reports AUC, a 2000-permutation p on the holdout
                     labels, a 2000-resample bootstrap CI, and per-batch AUCs. Writes
                     research/canonical/probe_holdout2_NAME.json. Nothing is fit on the test side.
  --train-null K     (with --test) the stricter null of §F201: permute the TRAINING labels, refit
                     the direction, apply to the real holdout, K times.
  --arm ARM          which arm's episodes to score (default blatant_wrongdoing_agents; use
                     blatant_wrongdoing for the human-perpetrator control trees).
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, ".")
from bystander import probe_alert as pa

LAYER_INDEX, SLOT = 6, 1
DIRFILE = Path("research/canonical/probe_direction_F200.npz")
TRAIN_TREE = "bystander/acts_nex_agentarm.predecision3"
TRAIN_LOGDIRS = sorted(str(p) for p in Path("logs").glob("bystander-nex-*") if p.is_dir()) + [
    f"logs/{d}" for d in ("bystander-agentarm-nex-a", "bystander-agentarm-nex-b",
    "bystander-agentarm-nex-rep-c", "bystander-agentarm-nex-rep-d", "bystander-agentarm-nex-rep-e",
    "bystander-agentarm-nex-rep-f", "bystander-agentarm-nex-rep-g", "bystander-agentarm-smoke")]

def unit(v): return v / (np.linalg.norm(v) + 1e-12)

def auc(scores, labels):
    scores, labels = np.asarray(scores, float), np.asarray(labels, int)
    order = np.argsort(scores); rank = np.empty(len(scores)); rank[order] = np.arange(1, len(scores) + 1)
    p, n = labels.sum(), (1 - labels).sum()
    return float("nan") if p == 0 or n == 0 else float((rank[labels == 1].sum() - p * (p + 1) / 2) / (p * n))

def load_arm(actdirs, logdirs, arm):
    lab = pa.labels_for(logdirs)
    got = pa.load(actdirs, lab, explicit=actdirs)
    if got is None: sys.exit("load refused / nothing matched")
    X, y, arms, src, cids = got[0], np.asarray(got[1]), np.asarray(got[2]), np.asarray(got[3]), np.asarray(got[4])
    m = arms == arm
    return X[:, LAYER_INDEX, SLOT, :][m], y[m].astype(int), src[m], cids[m]

def sha(v): return hashlib.sha256(np.ascontiguousarray(v, dtype=np.float32).tobytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save-direction", action="store_true")
    ap.add_argument("--test"); ap.add_argument("--logdir", action="append", default=[])
    ap.add_argument("--name"); ap.add_argument("--arm", default="blatant_wrongdoing_agents")
    ap.add_argument("--train-null", type=int, default=0)
    ap.add_argument("--perms", type=int, default=2000); ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260920)
    a = ap.parse_args()

    if a.save_direction:
        V, Y, S, C = load_arm([TRAIN_TREE], TRAIN_LOGDIRS, "blatant_wrongdoing_agents")
        d = unit(V[Y == 1].mean(0) - V[Y == 0].mean(0)).astype(np.float32)
        DIRFILE.parent.mkdir(parents=True, exist_ok=True)
        np.savez(DIRFILE, direction=d, sha256=sha(d), layer_index=LAYER_INDEX, slot=SLOT,
                 n_train=len(Y), n_alerted=int(Y.sum()), train_cids=C, train_tree=TRAIN_TREE,
                 saved_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        print(f"saved {DIRFILE}: n_train={len(Y)} alerted={int(Y.sum())} sha256={sha(d)}")
        return 0

    if not a.test or not a.logdir or not a.name: sys.exit("--test, --logdir and --name are required")
    z = np.load(DIRFILE, allow_pickle=False)
    d, rec = z["direction"], str(z["sha256"])
    if sha(d) != rec: sys.exit(f"direction file sha mismatch: {sha(d)} != recorded {rec}")
    train_cids = set(z["train_cids"].tolist())
    V, Y, S, C = load_arm([a.test], a.logdir, a.arm)
    overlap = sorted(set(C.tolist()) & train_cids)
    if overlap: sys.exit(f"cid overlap with training set: {overlap[:3]}...")
    scores = V @ d
    observed = auc(scores, Y)
    rng = np.random.default_rng(a.seed)
    hits = sum(1 for _ in range(a.perms) if auc(scores, rng.permutation(Y)) >= observed)
    p_perm = (hits + 1) / (a.perms + 1)
    boots = []
    for _ in range(a.boot):
        idx = rng.integers(0, len(Y), len(Y))
        v = auc(scores[idx], Y[idx])
        if not np.isnan(v): boots.append(v)
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    per_batch = {b: dict(n=int((S == b).sum()), alerted=int(Y[S == b].sum()), auc=auc(scores[S == b], Y[S == b]))
                 for b in sorted(set(S.tolist()))}
    out = dict(name=a.name, arm=a.arm, tree=a.test, logdirs=a.logdir, direction_file=str(DIRFILE),
               direction_sha256=rec, layer_index=LAYER_INDEX, model_layer=37, slot="mean_final_turn",
               n=int(len(Y)), alerted=int(Y.sum()), cid_overlap_with_training=0,
               auc=observed, perm_p_holdout_labels=p_perm, perms=a.perms,
               bootstrap_ci95=ci, boot=a.boot, per_batch=per_batch, seed=a.seed,
               ran_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    if a.train_null:
        Vt, Yt, _, _ = load_arm([TRAIN_TREE], TRAIN_LOGDIRS, "blatant_wrongdoing_agents")
        ge = 0
        for _ in range(a.train_null):
            yp = rng.permutation(Yt)
            dp = unit(Vt[yp == 1].mean(0) - Vt[yp == 0].mean(0))
            if auc(V @ dp, Y) >= observed: ge += 1
        out["train_label_null"] = dict(k=a.train_null, p=(ge + 1) / (a.train_null + 1))
    dst = Path(f"research/canonical/probe_holdout2_{a.name}.json"); dst.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("name", "n", "alerted", "auc", "perm_p_holdout_labels", "bootstrap_ci95", "per_batch")}, indent=1))
    if a.train_null: print("train-label null p:", out["train_label_null"])
    print("wrote", dst)
    return 0

if __name__ == "__main__":
    sys.exit(main())
