# Review of report.py changes

1. **Normalization Soundness:**
   The normalization is **not sound**. By stripping the `openrouter/` prefix, it conflates models served via OpenRouter (e.g., `openrouter/anthropic/claude-opus-5`) with models served directly by the provider API (e.g., `anthropic/claude-opus-5`). These represent two genuinely different serving paths that can have different latencies, system prompts, safety filters, and sampling stacks. However, for local GGUF models, the normalization correctly avoids any changes due to the `"local-model" not in m` check.

2. **Changes between before.csv and after.csv:**
   - **Changed Cells (n, alerted, cond_k, cond_n, floor):**
     - `dots-studio/dots-3-note-preview:free` (`with_tool`): `n` changed 6 → 24 (+18). Explained by pooling.
     - `nex-agi/nex-n2.5-mini:free` (`with_tool`): `n` changed 6 → 24 (+18). Explained by pooling.
     - `nex-agi/nex-n2.5-pro:free` (`with_tool`): `n` changed 6 → 24 (+18). Explained by pooling.
     - `nvidia/nemotron-3-ultra-550b-a55b:free` (`with_tool`): `n` changed 12 → 24 (+12). Explained by pooling. *(Note: This cell appeared under this name after stripping the prefix from the old batch)*.
     - `poolside/laguna-s-2.1:free` (`with_tool`): `n` changed 12 → 24 (+12). Explained by pooling. *(Note: This cell appeared under this name after stripping the prefix from the old batch)*.
   - **Cells changed for another reason:** None.
   - **Disappeared Cells:** The following 7 cells disappeared purely because their `openrouter/` prefix was stripped (they reappeared as new cells, and in two cases subsequently merged with new batches):
     - `openrouter/liquid/lfm-2.5-2.6b:free` (`tool_probe`)
     - `openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (`tool_probe`)
     - `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` (`tool_probe`)
     - `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` (`with_tool`)
     - `openrouter/poolside/laguna-s-2.1:free` (`tool_probe`)
     - `openrouter/poolside/laguna-s-2.1:free` (`with_tool`)
     - `openrouter/poolside/laguna-xs-2.1:free` (`tool_probe`)
   - **Refused count change:** None. (No new refused cells were added, and all prior refused counts/reasons remained identical).

3. **How the change hides real provenance differences:**
   1. **Dynamic OpenRouter Routes:** OpenRouter's free-tier routes (e.g., `:free`) dynamically load-balance across different anonymous providers over time. Pooling Sept 11 and Sept 14 runs under the same route hides the fact they likely used different underlying hardware and quantizations.
   2. **API vs Aggregator Conflation:** Stripping `openrouter/` merges runs served by OpenRouter with direct provider API runs. This hides genuine differences in their serving paths (e.g., wrapper prompts, moderation filters).
   3. **Global Replace Bug:** The `.replace("openrouter/", "")` method replaces the string anywhere, not just as a prefix. This would falsely alter and pool models that legitimately contain that substring (e.g., `org/openrouter-model`).

---

## Disposition (Claude, 2026-09-14 22:50)

Reviewer: Antigravity CLI, Gemini 3.1 Pro (High), scoped directory with the diff and the before/after cell tables.

1. Direct-provider vs OpenRouter conflation: valid in principle, moot in this corpus (every API cell, paid and free, is routed through OpenRouter; the paid Claude/Gemini/GPT cells have carried the stripped key since VERSION 1.1). Accepted anyway: the strip now fires only when `eval.model` itself records the `openrouter/` route, so a direct-provider run would keep a distinct key. Guard test added.
2. Cell diff: agrees with mine. Five cells changed by exactly their new batch sizes, seven keys re-spelled without the prefix, refused count unchanged.
3. Global replace: valid. Now a prefix check. Guard test covers `org/openrouter-model`.
4. Free-tier route drift across dates: real, and already the standing disclosure in METHODOLOGY v1.1 (free-tier cells are dated snapshots of a route, not of a checkpoint). Pooling 09-11 and 09-14 batches of one route is the same operation as pooling two batches within one night; the batch dates are in the logdirs.

Cell table after the tightened fix is byte-identical to `cells_2026-09-14_after_w9.csv`.
