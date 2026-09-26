"""Read research/f211/mech/*/ bins; report pooled (slot 1) projection on d and on r, by layer."""
import json, glob, os, sys, numpy as np
sys.path.insert(0, os.path.expanduser("~/llama.cpp/gguf-py")); import gguf
d = np.load("research/canonical/probe_direction_F200.npz")["direction"].astype(np.float64); d /= np.linalg.norm(d)
r = gguf.GGUFReader("bystander/cvec/abl_random_L1-39.gguf").tensors[0].data.astype(np.float64)
M = "research/f211/mech"; out = {}
for cond in ["plain", "stockadd", "abl_probe", "abl_random", "clamp050"]:
    for b in sorted(glob.glob(f"{M}/{cond}/*.bin")):
        meta = json.load(open(b[:-4] + ".json")); L = meta.get("layers") or meta.get("layer_ids")
        a = np.fromfile(b, dtype=np.float32).reshape(len(L), 3, -1).astype(np.float64)
        s = os.path.basename(b)[:-4].split("_")[-1]
        out.setdefault(s, {})[cond] = {"proj_d": {int(l): round(float(a[i, 1] @ d), 4) for i, l in enumerate(L)},
                                       "proj_r": {int(l): round(float(a[i, 1] @ r), 4) for i, l in enumerate(L)},
                                       "norm": {int(l): round(float(np.linalg.norm(a[i, 1])), 3) for i, l in enumerate(L)}}
for s, c in out.items():
    print("==", s)
    for cond, v in c.items():
        print(f"  {cond:11s} d:", v["proj_d"]); print(f"  {'':11s} r:", v["proj_r"])
json.dump(out, open(f"{M}/summary.json", "w"), indent=1)
