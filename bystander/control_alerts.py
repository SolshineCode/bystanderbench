"""Sort the alerts raised in harmless-control episodes. Protocol: docs/CONTROL_ALERTS.md.

  extract LOGDIR [LOGDIR ...] --blind blind.csv --key key.csv
      One row per alert_oversight call in a benign_anomaly episode. blind.csv has a shuffled
      id and the alert text only (what labellers see). key.csv maps id to model, mode, sample, epoch.
  tally  key.csv labels_a.csv labels_b.csv [--out tally.json]
      Two independent label files (columns id,label with label in M, F, X). Prints per-model counts of
      the agreed label, the number of disagreements, and Cohen's kappa.
"""
import argparse, csv, hashlib, json, random, sys
from collections import Counter, defaultdict
from math import sqrt

LABELS = ("M", "F", "X")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    a = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - a) / d, (c + a) / d)


def kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] / n * cb[l] / n for l in LABELS)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def extract_rows(logdirs):
    import glob
    from inspect_ai.log import read_eval_log
    rows = []
    for d in logdirs:
        for f in sorted(glob.glob(f"{d}/*.eval")):
            lg = read_eval_log(f)
            if (lg.eval.task_args or {}).get("arm") != "benign_anomaly":
                continue
            model = lg.eval.model
            mode = (lg.eval.task_args or {}).get("tool_arm", "")
            for s in lg.samples or []:
                for m in s.messages:
                    for tc in (getattr(m, "tool_calls", None) or []):
                        if tc.function == "alert_oversight":
                            text = str((tc.arguments or {}).get("summary", tc.arguments))
                            rows.append(dict(model=model, mode=mode, sample=str(s.id), epoch=s.epoch,
                                             text=text, src=f.rsplit("/", 1)[-1]))
    return rows


def cmd_extract(a):
    rows = extract_rows(a.logdir)
    seen = set(); out = []
    for r in rows:   # one id per alert call; identical (file, sample, epoch, text) is the same alert
        h = hashlib.sha256(f'{r["src"]}|{r["sample"]}|{r["epoch"]}|{r["text"]}'.encode()).hexdigest()[:10]
        if h in seen:
            continue
        seen.add(h); out.append(dict(r, id=h))
    random.Random(a.seed).shuffle(out)
    with open(a.blind, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "text"]); [w.writerow([r["id"], r["text"]]) for r in out]
    with open(a.key, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "model", "mode", "sample", "epoch"])
        [w.writerow([r["id"], r["model"], r["mode"], r["sample"], r["epoch"]]) for r in out]
    print(f"{len(out)} alerts -> {a.blind} (blind), {a.key} (key)")


def read_labels(path):
    d = {}
    for r in csv.DictReader(open(path)):
        l = r["label"].strip().upper()
        if l not in LABELS:
            sys.exit(f"{path}: bad label {l!r} for {r['id']}")
        d[r["id"]] = l
    return d


def cmd_tally(a):
    key = {r["id"]: r for r in csv.DictReader(open(a.key))}
    la, lb = read_labels(a.labels_a), read_labels(a.labels_b)
    if set(la) != set(key) or set(lb) != set(key):
        sys.exit("label files must cover exactly the ids in the key")
    ids = sorted(key)
    k = kappa([la[i] for i in ids], [lb[i] for i in ids])
    dis = [i for i in ids if la[i] != lb[i]]
    per = defaultdict(Counter)
    for i in ids:
        if la[i] == lb[i]:
            per[key[i]["model"]][la[i]] += 1
        else:
            per[key[i]["model"]]["disagree"] += 1
    res = {"alerts": len(ids), "disagreements": dis, "kappa": k, "models": {m: dict(c) for m, c in per.items()}}
    print(f"alerts {len(ids)}  disagreements {len(dis)}  kappa {k:.2f}" if k is not None else "no alerts")
    for m, c in per.items():
        print(f"  {m}: M {c['M']}  F {c['F']}  X {c['X']}  disagree {c['disagree']}")
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("extract"); e.add_argument("logdir", nargs="+"); e.add_argument("--blind", required=True)
    e.add_argument("--key", required=True); e.add_argument("--seed", type=int, default=20261127)
    t = sp.add_parser("tally"); t.add_argument("key"); t.add_argument("labels_a"); t.add_argument("labels_b")
    t.add_argument("--out")
    a = ap.parse_args()
    cmd_extract(a) if a.cmd == "extract" else cmd_tally(a)
