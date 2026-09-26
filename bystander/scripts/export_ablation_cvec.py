#!/usr/bin/env python3
"""Export a UNIT direction as a llama.cpp control vector for the §F211 ablation/clamp arms.

Unlike export_probe_cvec.py (which bakes a signed scale into the vector for additive steering),
this writes the unit direction itself, at one or more layers, for the patched llama.cpp build in
~/llama.cpp-ablate. That build reads LLAMA_CVEC_MODE:
  ablate : per token, cur -= (u.cur) u        (directional ablation, "abliteration")
  clamp  : per token, cur += (t - u.cur) u    (projection set to t = LLAMA_CVEC_CLAMP)
Stock llama.cpp would ADD this unit vector instead, so these files must never be served by the
stock binary; the launcher refuses unless the server log shows the CVEC_MODE line.

Layer arithmetic as in export_probe_cvec.py: direction.N is applied at il = N, on l_out-N.
Loaded with `--control-vector-scaled FILE:1.0` so the tensor stays unit norm.
"""
import argparse, hashlib, json, os, sys
import numpy as np

DIRFILE = "research/canonical/probe_direction_F200.npz"
N_LAYER = 40


def sha(v):
    return hashlib.sha256(np.ascontiguousarray(v, dtype=np.float32).tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", required=True, help="e.g. '37' or '1-39'")
    ap.add_argument("--random", type=int, default=None,
                    help="seed for the random unit direction orthogonal to d (§F208 used 20260921)")
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
        u, kind = d, "probe_F200"
    else:
        # identical construction to export_probe_cvec.py so the control is the SAME vector
        rng = np.random.default_rng(a.random)
        r = rng.standard_normal(d.shape[0]).astype(np.float32)
        r = r - float(r @ d) * d
        u, kind = (r / np.linalg.norm(r)).astype(np.float32), f"random_seed{a.random}"

    if "-" in a.layers:
        lo, hi = map(int, a.layers.split("-")); layers = list(range(lo, hi + 1))
    else:
        layers = [int(x) for x in a.layers.split(",")]
    if min(layers) < 1 or max(layers) >= N_LAYER:
        sys.exit("layers must be in 1..39 (direction.0 is never applied)")

    sys.path.insert(0, os.path.expanduser("~/llama.cpp/gguf-py"))
    import gguf
    w = gguf.GGUFWriter(a.out, "controlvector")
    w.add_string("controlvector.model_hint", "qwen35moe")
    w.add_uint32("controlvector.layer_count", N_LAYER)
    for L in layers:
        w.add_tensor(f"direction.{L}", u.copy())
    w.write_header_to_file(); w.write_kv_data_to_file(); w.write_tensors_to_file(); w.close()

    print(json.dumps({
        "out": a.out, "layers": [layers[0], layers[-1]], "n_layers": len(layers), "kind": kind,
        "norm": round(float(np.linalg.norm(u)), 6), "cos_with_probe_direction": round(float(u @ d), 6),
        "vector_sha256": sha(u), "source_direction_sha256": str(z["sha256"]),
    }, indent=1))


if __name__ == "__main__":
    sys.exit(main())
