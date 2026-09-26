### 1. Is `sample.output.model` acceptable provenance?
**Verdict:** Unsound at `basename` granularity.
**Reasoning:** Using `os.path.basename` (lines 24, 28) strips directory context. Different models, symlinks, or quantization variants (e.g., `Q4/model.gguf` vs `Q8/model.gguf`) sharing a filename will incorrectly pool together. If a server restarts mid-run with a different model sharing the same basename, `len(served) == 1` still holds (line 29), failing to detect the corrupted run.

### 2. Is reasoning content a sound proxy for the thinking-on condition?
**Verdict:** Unsound; it introduces post-treatment selection bias.
**Reasoning:** Checking for `type == "reasoning"` (lines 44-48) measures the *model's behavior* rather than the *assigned condition*.
- A thinking-on model that fails to output reasoning blocks (or emits `<think>` inline that isn't parsed as a reasoning type) is misclassified into `native` (thinking-off).
- A thinking-off model that spontaneously outputs parsed reasoning blocks is misclassified as `+think`.
- A run where the model thinks on only some episodes has its non-thinking episodes pooled into `+think` due to the log-level `any(...)` aggregation.

### 3. Before/After Pooling Analysis
**Verdict:** Nex and Qwen pooling is legitimate; Nemotron split is a severe confound.
**Reasoning:**
- **Nex-N2.5-mini (11/53 -> 16/83) & Qwen3.5-27b:** Legitimate pooling. Discarding the placeholder unified previously orphaned runs (e.g., `bystander-nex-local-n6`, `bystander-blatant-qwen35-27b`) into their respective main model cells. This correctly shares their floors and aggregates the previously excluded samples.
- **NVIDIA-Nemotron (split across `native` and `native+think`):** Confound. In the Before table, runs like `bystander-reasoning-nemotron` (presumably thinking-on) existed. In After, `with_tool` is split into `native` (n=24) and `native+think` (n=12). This reveals the proxy failed to find reasoning blocks in a thinking-on run, lumping it into `native`. Grouping failed thinking-on runs with genuine thinking-off runs corrupts the experimental arms.

### 4. Does discarding "local-model" mask ambiguity?
**Verdict:** Yes.
**Reasoning:** `served.discard(os.path.basename(m))` (line 28) removes the placeholder. If a log genuinely contains mixed samples—some served by `"model.gguf"` and others returning `"local-model"` (e.g., due to API fallback, server restarts, or load balancing across different backends)—discarding the placeholder leaves only `"model.gguf"`. The script blindly attributes the ambiguous `"local-model"` samples to `"model.gguf"`.

### 5. Anything else a sceptical reviewer would raise?
**Verdict:** Log-level `any()` aggregation is brittle.
**Reasoning:** Applying `any()` across all samples (line 48) means a single reasoning token in one sample permanently forces the `+think` mode on the entire log. If a run contains mixed conditions, or if the model only sporadically thinks, the label applies monolithically. Additionally, appending `+think` (line 50) mutates the `mode` string, which could silently break downstream reporting scripts expecting strict matches (e.g., exactly `"tools/native"`).
