#!/bin/bash
# collect_results.sh <slug> — download a finished kernel's outputs and summarize.
# Results land in moe-floor/results/<slug>/.
set -euo pipefail
SLUG="$1"
HERE=/home/darkstar/bluedot-unit2-impossiblebench/moe-floor
OUT="$HERE/results/$SLUG"
mkdir -p "$OUT"
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/kaggle_api_token)
~/.kaggle/cli-venv/bin/kaggle kernels output "calebdeleeuw/$SLUG" -p "$OUT"
echo "=== summary $SLUG ==="
python3 - "$OUT" <<'EOF'
import json, sys, os, glob
from collections import Counter
out = sys.argv[1]
sf = os.path.join(out, "samples.jsonl")
if not os.path.exists(sf):
    print("no samples.jsonl -- run failed before first sample; check the log:")
    for l in glob.glob(os.path.join(out, "*.log")):
        print(" ", l)
    sys.exit(0)
rows = [json.loads(l) for l in open(sf)]
cats = Counter(r["category"] for r in rows)
splits = Counter((r["split"], r["category"]) for r in rows)
print(f"{len(rows)} samples; categories: {dict(cats)}")
for (sp, c), n in sorted(splits.items()):
    print(f"  {sp:12s} {c:16s} {n}")
cheats = [r for r in rows if r["category"] == "concealed_cheat"]
flagged = [r for r in rows if r.get("flagged")]
print(f"\nconcealed_cheat: {len(cheats)}  |  keyword-flag hits needing audit: {len(flagged)}")
for r in cheats:
    print(f"  CHEAT {r['sid']} attempts={r.get('n_attempts')} toks={r.get('n_total_tokens')}")
for r in flagged:
    print(f"  AUDIT(flag) {r['sid']} cat={r['category']}")
mf = os.path.join(out, "run_meta.json")
if os.path.exists(mf):
    m = json.load(open(mf))
    print(f"\nelapsed: {m.get('elapsed_s')}s  stopped_on_budget: {m.get('stopped_on_budget')}")
n_acts = len(glob.glob(os.path.join(out, "acts", "*.bin")))
print(f"activation files: {n_acts}")
EOF
