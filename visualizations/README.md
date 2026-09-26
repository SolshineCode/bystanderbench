# Visualization pipeline (audited data only)

`build_charts.py` renders the program-wide result charts from AUDITED sources only
(taxonomy-v2 screen summaries, prepared local samples.jsonl + hand-audited
overrides). Raw unlabeled logs are never read. Pending sources are declared in the
registry and auto-included on re-run once their audited files exist (gemma local
captures, nemotron-3.5-lightning, laguna-xs).

    python3 visualizations/build_charts.py            # -> visualizations/out/

Every rate bar carries a 95% Wilson CI and its k/N; `out/verification_table.csv`
lists every plotted value for independent re-checking. Palettes validated with the
dataviz skill's checker (colorblind-safe; see build_charts.py header). Chart 5's
pooled CIs are labeled descriptive-only (i.i.d. is false across clustered models).

Review provenance: charts + table cross-checked against
`research/model-testing-audit-2026-09-05.md` by an independent agy (Gemini 3.1 Pro)
pass on 2026-09-05; its three flagged disagreements were verified by hand — in all
three the CSV was correct and the audit-doc rows were stale (since corrected).
