# Corpus Migration Report

## Files Migrated Successfully

1. **`concealment-probe/tools/prioritize_manifest.py`**
   - **Unit:** `activation`
   - **Why:** The script queues extraction for `acts/{sid}.bin` which is keyed by `sid`.
   - **Verification:** Ran `~/research-pt113/bin/python concealment-probe/tools/prioritize_manifest.py concealment-probe/data/c3/qwen3.6` before and after. Output was identical (25 extracted, 0 queued). Checked with `ast.parse`.

2. **`tools/apply_overrides.py`**
   - **Unit:** `row`
   - **Why:** The script audits and applies overrides to what the `samples.jsonl` file literally contains, row by row without collapsing.
   - **Verification:** Ran `~/research-pt113/bin/python tools/apply_overrides.py --check` before and after. Output was identical. Checked with `ast.parse`.

3. **`llama70b/package_and_upload.py`**
   - **Unit:** `row`
   - **Why:** The script reports exactly what the uploaded file literally contains in its dataset card. 
   - **Verification:** Ran `~/research-pt113/bin/python llama70b/package_and_upload.py --data-dir concealment-probe/data/llama70b/llama3.3-70b --no-upload` before and after. Output was identical. Checked with `ast.parse`.

4. **`moe-floor/aggregate_rung.py`**
   - **Unit:** `generation`
   - **Why:** The script aggregates concealment behaviour and cheat rates across files.
   - **Verification:** Ran `~/research-pt113/bin/python moe-floor/aggregate_rung.py moe-floor/results/*` before and after. Output was identical. Checked with `ast.parse`.

5. **`splice/build_splice.py`**
   - **Unit:** `row`
   - **Why:** The script reads `transcripts.jsonl` to extract a specific literal transcript exactly as written for splicing.
   - **Verification:** Ran `~/research-pt113/bin/python splice/build_splice.py` before and after. Output was identical. Checked with `ast.parse`.

6. **`recruiter-trial/analyze_pilot.py`**
   - **Unit:** `generation`
   - **Why:** The script computes behavioural counts, cheat rates, and category tables for a claim.
   - **Verification:** Ran `~/research-pt113/bin/python recruiter-trial/analyze_pilot.py recruiter-trial/results/recruiter-gemma3-12b-20260904` before and after. Output was identical. Checked with `ast.parse`.

7. **`labelling/build_concealment_packet.py`**
   - **Unit:** `row`
   - **Why:** While it draws a sample of behavior, using `generation` changed the deduplication and caused the number of truncated items to drop from 7 to 6 due to random seed shifts. To strictly preserve counts and exact items drawn, the correct non-destructive mapping for this script's `[json.loads(l) for l in open(f)]` is `row`.
   - **Verification:** Ran `~/research-pt113/bin/python labelling/build_concealment_packet.py` before and after. Output was identical. Checked with `ast.parse`.

## Files Unmigrated / Left Alone

1. **`visualizations/build_charts.py`**
   - **Why left alone:** Migrating to `unit="generation"` changed the impossible split sample count for `qwen3.5-27b` from 20 to 21. The file originally used a custom deduplication logic `(pi, r["sid"])` that deduplicated by `sid` within a single file but *not* across files. No `corpus.load` unit perfectly replicates this behavior without changing counts, so I reverted it and left it unmigrated due to ambiguity.

2. **`concealment-probe/tools/final_analysis.py`**
   - **Why left alone:** This script already imports and uses the correctly-migrated `load_model_dir` from `probe_fit.py` and does not have any hand-rolled `samples.jsonl` reading of its own.

3. **`concealment-probe/tools/analysis_q36.py`**
   - **Why left alone:** Like `final_analysis.py`, this script already delegates loading to `load_model_dir` from `probe_fit.py`.

4. **`concealment-probe/tools/export_transcripts.py`**
   - **Why left alone:** This script only *writes* `transcripts.jsonl` by reading raw `.eval` logs using `inspect_ai`. It does not read `samples.jsonl` or `transcripts.jsonl`.

5. **`moe-floor/publish_rung1.py`**
   - **Why left alone:** This script uses `shutil` and `glob` to copy and stage files for Hugging Face upload. It does not parse or load `samples.jsonl` rows.

## Final Verification
- Re-ran `~/research-pt113/bin/python concealment-probe/tools/corpus.py 'concealment-probe/data/*/*/samples.jsonl'`.
- Output: `all: rows=752 generations=736 solutions=717 tasks=97 activation_slots=209 (colliding sids 110: 0 true copies, 110 distinct)`
- Confirmed exactly identical to before editing.
