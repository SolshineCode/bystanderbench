# 2026-09-15 W11 gemma-3-27b pod cell: GGUF provenance check (and a gemma-4-31b re-check)

Verbatim working note from the overnight session (job dir 8bfa76b1), kept as the audit record behind §F172's provenance paragraph.

```
W11 gemma-3-27b pod cell (2026-09-15) -- GGUF provenance, verified by sha256 at 01:10 PDT
POD   /workspace/google_gemma-3-27b-it-Q4_K_M.gguf  sha256 4e83142e3ad3719ac61334f70a956dcc60bbba8adb29de5114161310bb9f7170  16546404992 B
      = bartowski/google_gemma-3-27b-it-GGUF (repo sha 4a05c54413), served with --no-prefill-assistant; ALL cell text generated from this file.
LOCAL ~/gguf-downloads/gemma-3-27b/gemma-3-27b-it-Q4_K_M.gguf  sha256 edc9aff4d811a285b9157618130b08688b0768d94ee5355b02dc0cb713012e15  16546404736 B
      = ggml-org/gemma-3-27b-it-GGUF (commit f94c25afed0072339c5fa3b705a7b4222afe5f62). NOT the same file: different quantiser build, 256 B size delta.
CORRECTION of the working assumption earlier tonight ("local GGUF is the bartowski build, size matches"): wrong on both counts.
Consequence: residual extraction for this cell runs ON THE POD against the bartowski file (extract_resid relinked 01:12 against
libllama-common + libllama-common-base.a of the pod's newer llama.cpp). No local extraction of pod-generated text on the ggml-org file.
Part 1 gemma-3-27b (nla-screen, 2026-09-08 extraction) used the LOCAL ggml-org file end to end; that provenance is unaffected.

LOOSE END (found 01:25, same class): bystander/acts_gemma4_31b_pod/acts/ holds 43 bins dated 2026-09-14 09:06, extracted
AFTER that pod was terminated (02:04) -- so on a LOCAL gemma-4-31b GGUF. Verify by sha256 that the local file is the same
build the pod served (pod_gemma4_setup.sh names the repo); if not, mark those bins cross-build in FINDINGS and MANIFEST.
RESOLVED 01:33: local ~/gguf-downloads/gemma-4-31b/gemma-4-31B-it-Q4_K_M.gguf sha256 38bd64c8...bb17f84 == hub LFS sha256 of
unsloth/gemma-4-31B-it-GGUF main (the exact URL pod_gemma4_setup.sh fetched), size 18323733440 both. Repo commit history checked
below for changes between the pod's 2026-09-14 fetch and now. If no commit touched the file in that window, the gemma-4-31b bins
(w7_gemma4_local_extract.sh) are same-file and need no correction.
CLOSED 01:34: unsloth/gemma-4-31B-it-GGUF last commit 2026-07-17 (c1ac76e99d); no change across the 09-14 pod fetch and the local file. Same-file. No correction needed.
```
