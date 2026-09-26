#!/usr/bin/env python3
"""Validate a labelling tranche (AUTONOMOUS DRAFT 2026-09-23). Same checks as validate_pilot.py:
kappa A vs B on the overlap, then for labeller A over ALL episodes: coverage, reporting <=> alert
call, outcome correctness, phase regressions, and evidence_seen accuracy against the mechanical
truth taken from the environment's own evidence strings.

Usage: python validate_tranche.py research/audits/nla_labels/tranche1
"""
import glob, json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_pilot import kappa, PRE

from evidence import EVP  # one copy of the evidence regex (evidence.py)
TRUE = (True, "true", "True")


def load(pattern):
    rows = [json.loads(l) for f in sorted(glob.glob(pattern)) for l in open(f)]
    return ({(r["cid"], r["msg_idx"]): r for r in rows if r.get("msg_idx") is not None},
            {r["cid"]: r for r in rows if r.get("msg_idx") is None})


def main(d):
    E = {json.loads(l)["cid"]: json.loads(l) for l in open(f"{d}/episodes.jsonl")}
    alert, ev = {}, {}
    for cid, e in E.items():
        first = next((t["idx"] for t in e["turns"] if t["role"] == "tool" and EVP.search(t.get("text", ""))), None)
        for t in e["turns"]:
            if t["role"] == "assistant":
                alert[(cid, t["idx"])] = any(c["fn"] == "alert_oversight" for c in t.get("tool_calls", []))
                ev[(cid, t["idx"])] = first is not None and first < t["idx"]
    A, Aep = load(f"{d}/labels_A_part*.jsonl")
    B, Bep = load(f"{d}/labels_B_*.jsonl")
    out = {"episodes": len(E), "turns": len(alert), "A_turn_labels": len(A),
           "A_missing": len(set(alert) - set(A)), "A_extra": len(set(A) - set(alert))}
    keys = sorted(set(A) & set(B))
    out["overlap_turns"] = len(keys)
    for f in ("phase", "evidence_seen", "mentions_wrongdoing"):
        if keys:
            k, po = kappa([str(A[x][f]) for x in keys], [str(B[x][f]) for x in keys])
            out[f"kappa_{f}"] = round(k, 3); out[f"agree_{f}"] = round(po, 3)
    out["phase_disagreements"] = collections.Counter(
        f"{A[x]['phase']}|{B[x]['phase']}" for x in keys if A[x]["phase"] != B[x]["phase"]).most_common(8)
    ks = [x for x in alert if x in A]
    out["A_reporting_tp_fp_fn"] = (sum(alert[x] and A[x]["phase"] == "reporting" for x in ks),
                                   sum(not alert[x] and A[x]["phase"] == "reporting" for x in ks),
                                   sum(alert[x] and A[x]["phase"] != "reporting" for x in ks))
    out["A_evidence_seen_accuracy"] = round(sum((A[x]["evidence_seen"] in TRUE) == ev[x] for x in ks) / len(ks), 3)
    ep_alert = {cid: any(v for k, v in alert.items() if k[0] == cid) for cid in E}
    out["A_outcome_correct"] = f"{sum((Aep.get(c, {}).get('episode_outcome') == 'reported') == ep_alert[c] for c in E)}/{len(E)}"
    reg = 0
    for cid in E:
        seen = False
        for x in sorted(k for k in ks if k[0] == cid):
            if A[x]["evidence_seen"] in TRUE: seen = True
            if seen and A[x]["phase"] in PRE: reg += 1
    out["A_phase_regressions"] = reg
    out["phase_counts_A"] = collections.Counter(A[x]["phase"] for x in ks)
    out["reported_episodes"] = sum(ep_alert.values())
    json.dump(out, open(f"{d}/validation.json", "w"), indent=1, default=str)
    for k, v in out.items():
        print(f"  {k}: {v}")
    print("GATE kappa_phase >= 0.7 on overlap:", "PASS" if out.get("kappa_phase", 0) >= 0.7 else "FAIL")


if __name__ == "__main__":
    main(sys.argv[1])
