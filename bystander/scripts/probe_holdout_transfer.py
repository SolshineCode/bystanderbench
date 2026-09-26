#!/usr/bin/env python3
"""The genuine falsification test for the agent-arm probe (F199 -> F200).

Fits the alert direction ONCE on the gated training tree (acts_nex_agentarm.predecision3,
mean_final_turn slot, the layer that won in F199's honest re-derivation), then applies that
FIXED, unmodified direction to a holdout batch captured and pre-decision cut AFTER the
direction was fixed. This is not leave-one-batch-out cross-validation over one pool; the
holdout episodes did not exist when the direction was computed.

Usage: python bystander/scripts/probe_holdout_transfer.py
"""
import sys, numpy as np
sys.path.insert(0, ".")
from pathlib import Path
from bystander import probe_alert as pa

LAYER_INDEX = 6       # index into RESID_LAYERS, = model layer 37; the F199 winning cell
SLOT = 1               # mean_final_turn
SEED = 20260919
N_PERM = 2000

def unit(v):
    return v / (np.linalg.norm(v) + 1e-12)

def auc(scores, labels):
    order = np.argsort(scores)
    rank = np.empty(len(scores)); rank[order] = np.arange(1, len(scores) + 1)
    p, n = labels.sum(), (1 - labels).sum()
    return float("nan") if p == 0 or n == 0 else (rank[labels == 1].sum() - p * (p + 1) / 2) / (p * n)

def load_agent_arm(actdirs, logdirs):
    lab = pa.labels_for(logdirs)
    X, y, arm = pa.load(actdirs, lab)[:3]
    y, arm = np.asarray(y), np.asarray(arm)
    ag = arm == "blatant_wrongdoing_agents"
    return X[:, LAYER_INDEX, SLOT, :][ag], y[ag].astype(int)

train_logdirs = sorted(str(p) for p in Path("logs").glob("bystander-nex-*") if p.is_dir())
train_logdirs += [f"logs/{d}" for d in (
    "bystander-agentarm-nex-a", "bystander-agentarm-nex-b",
    "bystander-agentarm-nex-rep-c", "bystander-agentarm-nex-rep-d",
    "bystander-agentarm-nex-rep-e", "bystander-agentarm-nex-rep-f",
    "bystander-agentarm-nex-rep-g", "bystander-agentarm-smoke")]
V_train, Y_train = load_agent_arm(["bystander/acts_nex_agentarm.predecision3"], train_logdirs)
print(f"train (gated tree, fixed once): n={len(Y_train)} alerted={Y_train.sum()}")
d = unit(V_train[Y_train == 1].mean(0) - V_train[Y_train == 0].mean(0))

holdout_logdirs = ["logs/bystander-agentarm-nex-holdout-i", "logs/bystander-agentarm-nex-holdout-j"]
V_test, Y_test = load_agent_arm(["bystander/acts_nex_agentarm_holdout.predecision"], holdout_logdirs)
print(f"test (holdout, captured after the direction was fixed): n={len(Y_test)} alerted={Y_test.sum()}")

scores = V_test @ d
observed = auc(scores, Y_test)
print(f"\nAUC of the fixed direction on the holdout: {observed:.4f}")

rng = np.random.default_rng(SEED)
hits = sum(1 for _ in range(N_PERM) if auc(scores, rng.permutation(Y_test)) >= observed)
print(f"permutation p (holdout labels shuffled, direction never refit): {(hits + 1) / (N_PERM + 1):.4f}")
