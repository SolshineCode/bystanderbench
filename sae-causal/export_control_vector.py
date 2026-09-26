#!/usr/bin/env python
"""Export a GemmaScope-2 SAE feature's decoder row as a llama.cpp control vector.

llama.cpp format (common/common.cpp, common_control_vector_load_one):
  tensors named `direction.<N>`, N >= 1, 1-D f32 of length n_embd.
  `direction.N` is stored at index N-1 and applied by build_cvec(cur, il) with
  il = N-1, i.e. added to the residual stream AT THE OUTPUT OF 0-BASED BLOCK N-1.

GemmaScope-2 declares `hf_hook_point_in = "model.layers.L.output"` = output of
0-based block L. So steering at SAE layer L requires the tensor name
`direction.{L+1}`. This script does that arithmetic once, here, and prints it.

Scale: SAE decoder rows are unit-norm, so a scale equal to the feature's typical
activation magnitude injects roughly "one unit of the feature". Pass the observed
mean activation (e.g. from the results/sae cell table) as --scale.
"""
import argparse, json, os
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sae-repo", default="google/gemma-scope-2-12b-it")
    ap.add_argument("--sae-subdir", default="resid_post_all/layer_20_width_16k_l0_small")
    ap.add_argument("--layer", type=int, required=True, help="SAE layer L (model.layers.L.output)")
    ap.add_argument("--feature", type=int, required=True)
    ap.add_argument("--scale", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from huggingface_hub import hf_hub_download
    from safetensors.numpy import load_file
    # NOTE: the repo root contains a data directory literally named `gguf/`, which
    # shadows the real package as an empty namespace package. Pin the real one.
    import sys
    sys.path.insert(0, os.path.expanduser("~/llama.cpp/gguf-py"))
    import gguf

    cfg = json.load(open(hf_hub_download(a.sae_repo, f"{a.sae_subdir}/config.json")))
    want = f"model.layers.{a.layer}.output"
    if cfg.get("hf_hook_point_in") != want:
        raise SystemExit(f"REFUSING: {a.sae_subdir} hooks {cfg.get('hf_hook_point_in')}, not {want}")
    p = load_file(hf_hub_download(a.sae_repo, f"{a.sae_subdir}/params.safetensors"))
    v = p["w_dec"][a.feature].astype(np.float32)
    n = float(np.linalg.norm(v))
    vec = v * (a.scale / max(n, 1e-9))

    tensor_name = f"direction.{a.layer + 1}"   # il = layer, so N = layer + 1
    w = gguf.GGUFWriter(a.out, "controlvector")
    w.add_string("controlvector.model_hint", cfg.get("model_name", "gemma3"))
    w.add_uint32("controlvector.layer_count", a.layer + 1)
    w.add_tensor(tensor_name, vec)
    w.write_header_to_file(); w.write_kv_data_to_file(); w.write_tensors_to_file(); w.close()

    print(json.dumps({"out": a.out, "tensor": tensor_name, "sae_layer": a.layer,
                      "applied_after_0based_block": a.layer, "feature": a.feature,
                      "decoder_row_norm": n, "scale": a.scale, "n_embd": int(vec.shape[0]),
                      "sae": f"{a.sae_repo}/{a.sae_subdir}"}, indent=1))


if __name__ == "__main__":
    main()
