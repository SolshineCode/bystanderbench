# Critique: BystanderBench Proposed Fixes
Model: Gemini 3.1 Pro (High)

## 1. Does the discovery fix close the hole or open a new blind spot?
**INFERRED: It opens a massive blind spot.**
The proposed scheme categorizes shared files (like `TODO.md`) as ignored by the `_discovery` path matcher. It then relies entirely on `_content_discovery` matching `evidence_lines` against the tool output (`seen`). 
However, if an agent uses a tool that reads `TODO.md` but *does not print the content to stdout* (e.g., a short Python or bash script that parses the file, checks for the evidence, and only prints "Evidence found"), `seen` will not contain the `evidence_lines`. 
Because the path is ignored and the content never hits stdout, the agent successfully accesses the evidence but triggers neither `discovered` nor `discovered_content`. The metric will silently report 0.

## 2. Is exact line equality against `todo_block`/`chat_block` fragile?
**VERIFIED: Yes, it is fragile.**
`_content_discovery` (`scorer.py:321`) checks `ln in seen`. This requires the *exact, contiguous string* of the evidence line (often >80 chars) to appear in the tool output. If the agent views the file using a tool that reflows Markdown, applies word-wrapping to the terminal width, or introduces any formatting, the exact substring match will fail. This creates a false negative for discovery.

## 3. Is the directory-based `model_fingerprint` right?
**VERIFIED: It both over-splits and under-splits.**
*   **Under-splits:** If a user runs multiple models without explicitly specifying `--log-dir`, they all default to `./logs/`. The fallback (`summarize.py:43`) will group them all under `openai/local-model[logs]`, fusing distinct models into a single cell and invalidating the Wilson intervals.
*   **Over-splits:** If a user runs the *same* model across multiple batches (e.g., to increase sample size) and uses descriptive log dirs (e.g., `logs/qwen_part1`, `logs/qwen_part2`), they will be split into different cells, preventing the user from pooling their sample size.

## 4. What belongs in `verify_release.py`?
Beyond the umbrella items:
*   **Post-hoc script parity:** Assert that the live metrics (`discovered_content`, `considered_in_reasoning`) computed by `scorer.py` identically match the outputs of the post-hoc scripts (`posthoc_content.py`, `posthoc_reasoning.py`) across all logs. If they drift, one of them has a bug.
*   **Unconditional metric denominator integrity:** Ensure that limit-hit episodes are missing cells (N/A) across *all* metrics, not just the conditional headline.

## 5. Regressions and incomplete fixes in the committed 9

1.  **Incomplete Fix 2 (`summarize.py` fake zeros):** `summarize.py:94-96` successfully excludes limit-hit episodes from the conditional denominator (`cond`). However, it fails to exclude them from the unconditional rates! Lines 106-108 indiscriminately accumulate *every* episode into `agg`. Consequently, limit-hit episodes still falsely drive down the rates of `alerted`, `discovered`, and `discovered_strict` as fake zeros.
2.  **Regression in Fix 4 (`capture_activations.py` cid collisions):** The new `cid` format (`capture_activations.py:109`) is derived using `enumerate(log.samples, 1)` inside a loop over *individual `.eval` files*. If a directory contains multiple `.eval` files (standard for multi-epoch runs), sample 1 of `2.eval` will generate the exact same `cid` as sample 1 of `1.eval`. This instantly triggers the newly added hard assertion (`raise SystemExit`), crashing the script on normal valid log directories.
3.  **Incomplete Fix 7 (`posthoc_reasoning.py` blind spots / `scorer.py`):** The regex `_THINK_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)` (`scorer.py:117`, `posthoc_reasoning.py:28`) strictly requires the closing tag. If an episode terminates due to a token limit while still inside a `<think>` block, the regex fails to match anything. As a result, the model's private reasoning is neither captured as reasoning nor stripped from `raw_final`. It is instead graded as user-visible disclosure, repeating the very taxonomy error the logic was built to prevent.
