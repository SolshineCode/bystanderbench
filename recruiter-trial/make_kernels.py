#!/usr/bin/env python3
"""Render recruiter-trial Kaggle kernel dirs from kernel_template.py."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = "20260904"

# tag -> (model_id, layers, quant_mode, limit_imp_tasks_per_split)
#
# RECOMMENDED pilot target (2026-09-04, pending nod): gemma-3-12b-it. The
# originally-approved Qwen3-30B-A3B GPTQ checkpoint FAILED to load on Kaggle -- a
# real bug, not just OOM: the community GPTQ/AWQ quants store per-expert UNFUSED
# MoE tensors (experts.N.gate_proj.qweight) + a quantized router, but the Kaggle
# image's transformers Qwen3MoeForCausalLM expects FUSED expert tensors
# (experts.gate_up_proj) + an unquantized gate -> every expert weight discarded,
# fused params random-initialized (broken output), then Marlin JIT compile OOM'd
# after 100min. Both community 4-bit quants share this layout, so neither fixes it.
# gemma-3-12b-it is the better retarget: strongest behavioral cheat evidence in the
# whole screen (2/50 hardcode -> a real baseline for measuring pressure UPLIFT),
# loads trivially (dense, ungated unsloth bnb-4bit prequant, no fused-MoE trap, no
# Marlin), small/fast for the expensive per-stage capture, and already a local
# capture target so the same-model spontaneous-vs-recruited contrast is coherent.
MODELS = {
    "gemma3-12b": ("unsloth/gemma-3-12b-it-bnb-4bit",
                   list(range(4, 45, 4)), "preq", 6),   # 48 blocks, d=3840, incl. NLA layer 32; 6 tasks x2 splits x2 arms = 24 trials
    # deprecated (kept for the record; do not launch -- broken load, see above):
    "qwen3-30b-a3b": ("btbtyler09/Qwen3-30B-A3B-Instruct-2507-gptq-4bit",
                      list(range(4, 49, 4)), "preq", 4),
    # secondary pass (budget permitting): MoE-vs-dense susceptibility on rung-1 pair
    "olmoe-1b7b":   ("allenai/OLMoE-1B-7B-0125-Instruct", list(range(2, 17, 2)), "none", 6),
    "olmo2-7b":     ("allenai/OLMo-2-1124-7B-Instruct",   list(range(4, 33, 4)), "none", 6),
}


def main():
    tpl = open(os.path.join(HERE, "kernel_template.py")).read()
    assert "@@MODEL_ID@@" in tpl
    for tag, (mid, layers, quant, limit) in MODELS.items():
        slug = f"recruiter-{tag}-{DATE}".replace(".", "-")
        assert len(slug) <= 50, slug
        d = os.path.join(HERE, "kernels", slug)
        os.makedirs(d, exist_ok=True)
        script = (tpl.replace("@@MODEL_ID@@", mid)
                     .replace("@@MODEL_TAG@@", tag)
                     .replace("@@LAYERS@@", json.dumps(layers))
                     .replace("@@QUANT_MODE@@", quant)
                     .replace("@@LIMIT_IMP@@", str(limit)))
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
