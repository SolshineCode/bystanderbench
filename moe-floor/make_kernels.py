#!/usr/bin/env python3
"""Render per-model Kaggle kernel dirs from kernel_template.py.

Usage: make_kernels.py            # renders all rung-1 kernels
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = "20260903"

# tag -> (model_id, layers[, quant])   quant: "fp16" (default) | "bnb4"
MODELS = {
    # rung 1 (~7B total): MoE vs two same-lab dense controls, fp16
    "olmoe-1b7b": ("allenai/OLMoE-1B-7B-0125-Instruct", list(range(2, 17, 2))),        # 16 blocks, d=2048
    "olmo2-7b":   ("allenai/OLMo-2-1124-7B-Instruct",   list(range(4, 33, 4))),        # 32 blocks, d=4096
    "olmo-0724-7b": ("allenai/OLMo-7B-0724-Instruct-hf", list(range(4, 33, 4))),       # 32 blocks, d=4096
    # rung 2 (~14B total, same-generation same-lab pair): NF4 both sides
    # (same-quant-within-pair rule); report cheat rates split by mechanism per
    # the section-14 standing rule -- rung 1 showed arch can be matched while
    # the arms measure different behaviors (check_override vs hardcode).
    "qwen15-moe-a27b": ("Qwen/Qwen1.5-MoE-A2.7B-Chat", list(range(2, 25, 2)), "bnb4"),  # 24 blocks, d=2048, 14.32B
    "qwen15-14b":      ("Qwen/Qwen1.5-14B-Chat",       list(range(4, 41, 4)), "bnb4"),  # 40 blocks, d=5120, 14.17B
    # rung-2 triplet completion (Wael, arXiv:2605.13769 design): dense matched on
    # ACTIVE params (~2.7B active -> 3.95B verified from safetensors index), same
    # lab/generation. Gap vs qwen15-14b attributes sparsity-vs-capacity cleanly.
    "qwen15-4b":       ("Qwen/Qwen1.5-4B-Chat",        list(range(4, 41, 4)), "bnb4"),  # 40 blocks, d=2560, 3.95B
    # rung-1 EXTENSION (2026-09-05): larger N per Caleb -- 3 rung-1 models rerun at
    # near-full split coverage (103 tasks/split available); per-model limits sized
    # to each model's measured throughput vs the 9h session cap. New waves fold
    # into existing audited counts via the multi-path loader (distinct
    # trajectories; never sid-dedup across waves).
    "olmoe-1b7b-ext":   ("allenai/OLMoE-1B-7B-0125-Instruct", list(range(2, 17, 2)), "fp16", (90, 10)),
    "olmo-0724-7b-ext": ("allenai/OLMo-7B-0724-Instruct-hf",  list(range(4, 33, 4)), "fp16", (70, 8)),
    "olmo2-7b-ext":     ("allenai/OLMo-2-1124-7B-Instruct",   list(range(4, 33, 4)), "fp16", (55, 6)),
}


def main():
    tpl = open(os.path.join(HERE, "kernel_template.py")).read()
    assert "@@MODEL_ID@@" in tpl
    for tag, spec in MODELS.items():
        mid, layers = spec[0], spec[1]
        quant = {"bnb4": "bnb"}.get(spec[2] if len(spec) > 2 else "fp16", "none")
        limits = spec[3] if len(spec) > 3 else (25, 12)
        slug = f"moe-floor-{tag}-{DATE}".replace(".", "-")
        assert len(slug) <= 50, slug
        d = os.path.join(HERE, "kernels", slug)
        os.makedirs(d, exist_ok=True)
        script = (tpl.replace("@@MODEL_ID@@", mid)
                     .replace("@@MODEL_TAG@@", tag)
                     .replace("@@LAYERS@@", json.dumps(layers))
                     .replace("@@QUANT_MODE@@", quant)
                     .replace("@@LIMIT_IMP@@", str(limits[0]))
                     .replace("@@LIMIT_ORIG@@", str(limits[1])))
        open(os.path.join(d, "script.py"), "w").write(script)
        meta = {
            "id": f"calebdeleeuw/{slug}",
            "title": slug,
            "code_file": "script.py",
            "language": "python",
            "kernel_type": "script",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": True,
            "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
        }
        json.dump(meta, open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
        print(f"rendered {d}")


if __name__ == "__main__":
    main()
