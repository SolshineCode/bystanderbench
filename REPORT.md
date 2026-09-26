# Migration Report

## Migrated Files

* **`concealment-probe/tools/prioritize_manifest.py`**
  * **Unit**: `activation` (Queues extraction for `acts/{sid}.bin` which is keyed by sid).
  * **Verification**: Numbers identical. Executed `python concealment-probe/tools/prioritize_manifest.py concealment-probe/data/c3/qwen3.6` before and after, which printed 25 already extracted, 0 queued in both cases.

* **`tools/apply_overrides.py`**
  * **Unit**: `row` (Audits and applies overrides to what the file literally contains, row by row).
  * **Verification**: Numbers identical. Executed `python tools/apply_overrides.py --check` before and after, yielding identical output (PASS).

* **`llama70b/package_and_upload.py`**
  * **Unit**: `row` (Reports what the uploaded file literally contains in its dataset card).
  * **Verification**: Edited, not executed (due to complexity of mocking the upload script inputs), but verified syntax using `python -c "import ast;ast.parse(open('llama70b/package_and_upload.py').read())"`.

* **`moe-floor/aggregate_rung.py`**
  * **Unit**: `generation` (Aggregates behaviour counts, rates, and categories for a claim).
  * **Verification**: Numbers identical. Executed `python moe-floor/aggregate_rung.py moe-floor/results/*` before and after, producing identical rates and category counts.

* **`splice/build_splice.py`**
  * **Unit**: `row` (Reads the file literally to find a specific row matching a hardcoded sid).
  * **Verification**: Numbers identical. Executed `python splice/build_splice.py` before and after, extracting identical spliced cases and feedback strings.

* **`recruiter-trial/analyze_pilot.py`**
  * **Unit**: `generation` (Counts behavioural categories and computes rates per arm).
  * **Verification**: Numbers identical. Executed `python recruiter-trial/analyze_pilot.py recruiter-trial/results/recruiter-gemma3-12b-20260904` before and after, producing identical output and behavioral counts.


## Unmigrated Files

* **`concealment-probe/tools/final_analysis.py`**
  * Left alone because it does not read `.jsonl` files manually; it uses `load_model_dir` from `probe_fit.py` which is already migrated.
* **`concealment-probe/tools/analysis_q36.py`**
  * Left alone because it also relies entirely on the already-migrated `load_model_dir` function.
* **`concealment-probe/tools/export_transcripts.py`**
  * Left alone because it *writes* `transcripts.jsonl` from Inspect `.eval` logs and doesn't read the corpus.
* **`visualizations/build_charts.py`**
  * Left alone because migrating to `unit="generation"` changed the sample count (`n_imp` for `qwen3.5-27b` increased from 20 to 21), violating the "DO NOT change any number" constraint.
* **`moe-floor/publish_rung1.py`**
  * Left alone because it does not parse or load `.jsonl` data, only copies files directly using `shutil`.
* **`labelling/build_concealment_packet.py`**
  * Left alone because migrating to `unit="generation"` changed a count (truncated char count from 7 to 6), violating the "DO NOT change any number" constraint.
