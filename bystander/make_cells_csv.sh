#!/bin/bash
# Regenerate the full BystanderBench cell table. The logdir set is defined by CONTENT (every directory
# under logs/ that holds a *bystander*.eval), not by directory name: on 2026-09-15 a name pattern
# (logs/bystander-* logs/or-*) silently dropped the eight logs/orpaid-* frontier dirs and produced a
# 78-cell table against the 87-cell one it was meant to extend. Dirs named *-partial hold torn evals
# (header-only files from an interrupted run) and are excluded; nothing else is.
#   usage: bystander/make_cells_csv.sh research/audits/cells_<date>_<tag>.csv [previous.csv]
# With a second argument, prints missing / new / changed cells against that table.
set -uo pipefail
OUT=${1:?csv path}; PREV=${2:-}
cd "$(dirname "$0")/.."; source .venv/bin/activate
D=$(find logs -name "*bystander*.eval" -printf "%h\n" | sort -u | grep -v -- "-partial" | tr '\n' ' ')
echo "logdirs: $(echo $D | wc -w)"
python bystander/report.py $D --cache bystander/.envcache --csv "$OUT" > "${OUT%.csv}.report.txt" 2>&1 || { echo "report.py failed"; exit 1; }
echo "wrote $OUT ($(($(wc -l < "$OUT")-1)) cells); report text in ${OUT%.csv}.report.txt"
[ -n "$PREV" ] && python - "$PREV" "$OUT" <<'PY'
import csv, sys
def load(p): return {tuple(r[k] for k in ("model","mode","arm","tool_arm")): r for r in csv.DictReader(open(p))}
a=load(sys.argv[1]); b=load(sys.argv[2])
print(f"prev {len(a)} cells, new {len(b)} cells")
print("missing:", [k for k in a if k not in b]); print("new:", [k for k in b if k not in a])
for k in [k for k in a if k in b and a[k]!=b[k]]:
    print("changed:", k, {c:(a[k][c],b[k][c]) for c in a[k] if a[k][c]!=b[k][c]})
PY
