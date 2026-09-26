# RunPod pod cells (gemma-4-31b 2026-09-14 §F163, gemma-3-27b 2026-09-15 §F172)

Verbatim launcher scripts from the overnight sessions, filed here because the ledger cites them.
Not parameterised; read them as a record of exactly what ran. Pattern:

1. `pod_<model>_setup.sh` runs ON the pod: build llama.cpp (CUDA), try to link `extract_resid`,
   curl the GGUF (record its sha256), start `llama-server` on :8080.
2. `w*_pod_<model>_cell.sh` runs locally: SSH tunnel to :8080, smoke (1 floor episode, read the
   transcript), floor n=6, three incident ceilings n=12, token capture over the tunnel.
3. `w11_competence_gate.sh` (09-15): applies COVER_MIN=0.75 to ceiling 1 the moment it lands and
   stops the rest if it fails; captures what completed; writes the DONE marker.
4. `w11_pod_extract*.sh`: extraction ON the pod against the generating file. Two traps found 09-15:
   the capture manifest carries absolute local paths (symlink `/home/darkstar/<repo> ->
   /workspace/bluedot` on the pod), and newer llama.cpp names the helper lib `libllama-common`
   (link with `-lllama-common build/common/libllama-common-base.a`, not `-lcommon`).
5. `w11_pod_nla.sh`: NLA v4 on the freed GPU (`nla-decode/runpod/`), results rsynced back.

Always: sha256 the local copy of any GGUF before assuming it is the pod's file (§F172: the local
gemma-3-27b was a different quantiser's build of the same size ±256 B). Terminate via the API and
re-list pods before writing the spend line.
