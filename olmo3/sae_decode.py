#!/usr/bin/env python3
"""sae_decode.py — decode captured Olmo-3 base-model activations through
decoderesearch/olmo-3-saes (Matryoshka BatchTopK, 65k latents, layers 4/16/28).

CPU-only (encoder matmul on fp32 .bin activations); run AFTER the capture
pipeline. Qualitative first pass: top-K latents per position for a few
concealed_cheat vs original_pass samples, plus latent-overlap stats.

Caveats to carry into any writeup:
 - SAEs trained on BASE model over Pile Uncopyrighted, context 1024,
   prepend_bos=true; our sequences are instruct-generated code transcripts,
   often longer than 1024 — out-of-distribution in both content and length.
 - Activations here are the base model teacher-forced over instruct text.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np

def load_sae(layer, cache_dir):
    from sae_lens import SAE
    sae = SAE.from_pretrained("decoderesearch/olmo-3-saes",
                              f"olmo-3-1025-7b/btk-mat-layer-{layer}-k-100",
                              device="cpu")
    return sae

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="data/olmo3-7b dir (manifest.tsv + acts/)")
    ap.add_argument("--layer", type=int, choices=[4,16,28], required=True)
    ap.add_argument("--sids", nargs="+", required=True, help="sample ids to decode")
    ap.add_argument("--topk", type=int, default=20)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sae = load_sae(args.layer, None)
    d = Path(args.data_dir)
    manifest = {}
    for line in open(d/"manifest.tsv"):
        parts = line.rstrip("\n").split("\t")
        manifest.setdefault(parts[0], []).append(parts)

    out = []
    for sid in args.sids:
        rows = [p for p in manifest.get(sid, []) if f"l_out-{args.layer}" in "\t".join(p)]
        if not rows:
            print(f"WARN no manifest rows for {sid} layer {args.layer}", file=sys.stderr); continue
        for p in rows:
            binpath = d/"acts"/p[-1] if not p[-1].startswith("/") else Path(p[-1])
            x = np.fromfile(binpath, dtype=np.float32).reshape(-1, 4096)
            import torch
            with torch.no_grad():
                feats = sae.encode(torch.from_numpy(x))
            v, i = feats.max(dim=0)  # per-latent max over positions
            top = torch.topk(v, args.topk)
            out.append(dict(sid=sid, layer=args.layer, n_pos=x.shape[0],
                            top_latents=[[int(a), float(b)] for a, b in zip(top.indices, top.values)],
                            mean_l0=float((feats > 0).float().sum(dim=1).mean())))
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"wrote {args.out} ({len(out)} rows)")

if __name__ == "__main__":
    main()
