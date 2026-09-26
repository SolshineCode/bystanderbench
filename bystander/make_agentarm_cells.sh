#!/bin/bash
# Build the paired control-vs-treatment cell table for the agent-perpetrator arm.
# Content-defined logdir set, same discipline as make_cells_csv.sh: every logdir that
# holds a *bystander*.eval and is not -partial, so a new cell cannot be silently missed
# by a name pattern (the failure that dropped eight frontier dirs on 2026-09-15).
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source .venv/bin/activate
OUT="${1:-research/audits/cells_agentarm_$(date +%Y-%m-%d_%H%M).csv}"
DIRS=()
while IFS= read -r d; do DIRS+=("$d"); done < <(
  find logs -maxdepth 1 -type d ! -name '*-partial' -print | sort |
  while read -r d; do ls "$d"/*bystander*.eval >/dev/null 2>&1 && echo "$d"; done)
echo "logdirs: ${#DIRS[@]}"
python -m bystander.report "${DIRS[@]}" --csv "$OUT" > "${OUT%.csv}.report.txt" 2>&1
echo "wrote $OUT"
python3 - "$OUT" <<'PY'
import csv,sys
rows=[r for r in csv.DictReader(open(sys.argv[1]))]
agents=[r for r in rows if r['arm']=='blatant_wrongdoing_agents']
print(f"total cells {len(rows)}, agent-arm cells {len(agents)}")
for r in agents:
    print(f"  {r['model'][:36]:36s} {r['mode']:18s} n={r['n']:>3s} cond={r['cond_k']}/{r['cond_n']} cover={r['cover']} refused={r['refused']}")
PY
