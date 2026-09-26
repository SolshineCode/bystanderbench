#!/usr/bin/env python3
"""Export the frozen §F200 alert direction as a llama.cpp control vector (§F208).

WHY THIS EXISTS. §F200-§F207 established the direction correlationally: a frozen
mean-difference vector at l_out-37 separates alerting from silent pre-decision episodes
on 11 fresh holdouts (pooled AUC 0.760). Correlational separation does not show the
direction participates in the decision. The causal test is to add -c*d (suppress) or
+c*d (amplify) to the residual stream at the SAME tensor the probe reads, and measure
the alert rate. This script builds the vectors; bystander/launchers/w45_*.sh runs them.

THE LAYER ARITHMETIC, established by reading llama.cpp source on 2026-09-21, NOT assumed:
  common/common.cpp common_control_vector_load_one: tensor `direction.N` is written to the
    flat buffer at offset n_embd*(N-1).
  src/llama-adapter.cpp llama_adapter_cvec::apply: tensors[il] is filled from offset
    n_embd*(il-1).
  Therefore direction.N is applied at il = N  (NOT N-1).
  src/models/qwen35moe.cpp:255-256: `cur = build_cvec(cur, il); cb(cur, "l_out", il);`
    so the vector is added to l_out-<il> immediately before that tensor is named --
    i.e. direction.37 perturbs exactly the tensor concealment-probe/tools/extract_resid
    pools as layer 37.
  NOTE: sae-causal/export_control_vector.py's docstring states the opposite (il = N-1).
  That is an off-by-one in the older script; see §F208 for what it means for that arm.

SCALE UNITS. The probe pools the residual over pre-decision tokens and dots with unit d,
so adding c*d at every token shifts an episode's probe score by exactly c. The natural
unit is the training-set alerting-minus-silent projection gap (0.1697), so --scale is
given in raw units and --dose prints the multiple of that gap for the record.

CONTROL. --random SEED builds a matched-magnitude vector orthogonal to d (Gram-Schmidt,
then renormalised). A random 2048-d vector is already near-orthogonal; making it exact
means the control arm differs from the treatment arm in direction and nothing else.
"""
import argparse, hashlib, json, os, sys
import numpy as np

DIRFILE = "research/canonical/probe_direction_F200.npz"
LAYER = 37          # model layer the probe reads (LAYER_INDEX 6 of 4,8,16,24,30,34,37,39)
N_LAYER = 40        # qwen35moe.block_count for nex-n2.5-mini
TRAIN_GAP = 0.169700  # mean proj(alerting) - mean proj(silent) on the §F200 training tree


def sha(v):
    return hashlib.sha256(np.ascontiguousarray(v, dtype=np.float32).tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, required=True,
                    help="signed magnitude added to the residual; negative suppresses")
    ap.add_argument("--random", type=int, default=None,
                    help="seed for a matched-magnitude control direction orthogonal to d")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    z = np.load(DIRFILE, allow_pickle=False)
    d = z["direction"].astype(np.float32)
    if sha(d) != str(z["sha256"]):
        sys.exit(f"REFUSING: direction sha mismatch {sha(d)} != {str(z['sha256'])}")
    if int(z["layer_index"]) != 6 or int(z["slot"]) != 1:
        sys.exit("REFUSING: direction file is not the layer-index-6 / slot-1 vector")
    d = d / np.linalg.norm(d)

    if a.random is None:
        v, kind, cos = d, "probe_F200", 1.0
    else:
        rng = np.random.default_rng(a.random)
        r = rng.standard_normal(d.shape[0]).astype(np.float32)
        r = r - float(r @ d) * d                      # Gram-Schmidt against d
        r = r / np.linalg.norm(r)
        v, kind, cos = r, f"random_seed{a.random}", float(r @ d)

    vec = (v * a.scale).astype(np.float32)

    sys.path.insert(0, os.path.expanduser("~/llama.cpp/gguf-py"))
    import gguf
    name = f"direction.{LAYER}"
    w = gguf.GGUFWriter(a.out, "controlvector")
    w.add_string("controlvector.model_hint", "qwen35moe")
    w.add_uint32("controlvector.layer_count", N_LAYER)
    w.add_tensor(name, vec)
    w.write_header_to_file(); w.write_kv_data_to_file(); w.write_tensors_to_file(); w.close()

    print(json.dumps({
        "out": a.out, "tensor": name, "applied_at_il": LAYER,
        "perturbs_tensor": f"l_out-{LAYER}", "kind": kind,
        "cos_with_probe_direction": round(cos, 6),
        "scale": a.scale, "dose_in_training_gaps": round(a.scale / TRAIN_GAP, 3),
        "n_embd": int(vec.shape[0]), "vector_sha256": sha(vec),
        "source_direction_sha256": str(z["sha256"]),
    }, indent=1))


if __name__ == "__main__":
    sys.exit(main())
