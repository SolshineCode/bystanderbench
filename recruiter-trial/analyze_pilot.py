#!/usr/bin/env python3
"""First-look analysis for a recruiter-trial results dir (downloaded kernel output).

Behavioral: per-arm category table; recruited-cheat rate (pressure arm, beats>0)
vs control-arm cheat rate, with the spontaneous baseline printed for context.
Activation: per-stage response-span vectors; for each adjacent stage pair the
cosine shift, contrasted pressure-vs-control on PAIRED tasks (same task id in
both arms), per layer. Small-n first look, not inference.

Usage: analyze_pilot.py <results_dir>
"""
import json, os, sys
from collections import Counter, defaultdict
import numpy as np


def main():
    d = sys.argv[1]
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "concealment-probe", "tools"))
    from corpus import load
    # Unit is 'generation' because this aggregates behaviour and cheat rates.
    rows = load(os.path.join(d, "samples.jsonl"), unit="generation")
    rows = [r for r in rows if r.get("category") != "no_output"]
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)

    print("=== behavioral ===")
    for arm, rs in sorted(by_arm.items()):
        cats = Counter(r["category"] for r in rs)
        spont = sum(1 for r in rs if r.get("pre_pressure_pass"))
        rep = sum(1 for r in rs if r.get("pressure_report_hits"))
        print(f"{arm:9s} n={len(rs):3d} {dict(cats)} pre-beat passes={spont} report-regex hits={rep}")
    pr = [r for r in by_arm.get("pressure", []) if not r.get("pre_pressure_pass")]
    ct = [r for r in by_arm.get("control", []) if not r.get("pre_pressure_pass")]
    k_p = sum(1 for r in pr if r["category"] == "concealed_cheat")
    k_c = sum(1 for r in ct if r["category"] == "concealed_cheat")
    print(f"recruited-cheat: pressure {k_p}/{len(pr)}  vs control {k_c}/{len(ct)}"
          f"   (spontaneous qwen3.6 baseline for context: ~1/25-50)")
    aud = [r for r in rows if r["category"] in ("concealed_cheat", "disclosed") or r.get("pressure_report_hits")]
    print(f"hand-audit queue: {len(aud)} rows")
    for r in aud:
        print(f"  AUDIT {r['sid']} cat={r['category']} beats={r.get('beats_received')} hits={r.get('pressure_report_hits')}")

    print("\n=== activation shift (pressure vs control, paired tasks) ===")
    ad = os.path.join(d, "stage_acts")
    if not os.path.isdir(ad):
        print("no stage_acts dir"); return

    def load(sid):
        jp = os.path.join(ad, sid + ".json")
        if not os.path.exists(jp):
            return None, None
        m = json.load(open(jp))
        a = np.fromfile(os.path.join(ad, sid + ".bin"), dtype=np.float32).reshape(m["shape"])
        return a, m

    def shifts(a):
        # cosine distance between consecutive stage vectors, per layer -> [n_stages-1, n_layers]
        u = a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-8)
        return 1.0 - np.einsum("sld,sld->sl", u[:-1], u[1:])

    paired = defaultdict(dict)
    for r in rows:
        paired[(r["split"], r["task_id"])][r["arm"]] = r["sid"]
    diffs = []   # per pair: mean-over-stages shift difference (pressure - control), per layer
    layers = None
    for (sp, tid), arms in sorted(paired.items()):
        if "pressure" not in arms or "control" not in arms:
            continue
        ap, mp = load(arms["pressure"])
        ac, mc = load(arms["control"])
        if ap is None or ac is None or ap.shape[0] < 2 or ac.shape[0] < 2:
            continue
        layers = mp["layers"]
        dp, dc = shifts(ap).mean(0), shifts(ac).mean(0)
        diffs.append(dp - dc)
        print(f"  {sp}_{tid}: stages P={ap.shape[0]} C={ac.shape[0]}  "
              f"mean shift diff (P-C) across layers: {float((dp-dc).mean()):+.4f}")
    if diffs:
        D = np.stack(diffs)
        print(f"\npairs={len(diffs)}; per-layer mean shift difference (P-C):")
        for i, L in enumerate(layers):
            m, s = D[:, i].mean(), D[:, i].std(ddof=1) if len(diffs) > 1 else float("nan")
            print(f"  layer {L:3d}: {m:+.4f} (sd {s:.4f})")
        print("positive = responses move more between stages under pressure than control")
    else:
        print("no complete pairs with >=2 stages")


if __name__ == "__main__":
    main()
