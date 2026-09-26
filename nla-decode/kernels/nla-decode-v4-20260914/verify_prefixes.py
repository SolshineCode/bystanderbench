# Verify prefixes.jsonl against the token counts capture_stage() recorded during
# the recruiter pilot.  CPU ONLY -- AutoTokenizer, no torch, no model, no GPU.
#
# The claim being tested is narrow and falsifiable: for every stage of every
# episode, re-rendering the reconstructed context through the same chat template
# and tokenising it the same way reproduces capture_stage()'s pool_start and
# n_tokens EXACTLY.  Those integers were written by the pilot run itself from
# the real context_messages, so an exact match on a ~6800-token prompt is not
# something a wrong reconstruction survives.
#
# Five episodes lost their FINAL stage's capture to a CUDA OOM in the pilot, so
# for those the final stage has no recorded counts.  They are not silently
# passed: every earlier stage of the same episode -- rebuilt from the same
# prefix_messages list, differing only in where it is truncated -- is checked
# against real counts, and the final stage falls back to the structural check
# (rendered prompt ends with the generation prompt; the response follows it).
#
# Usage:
#   python verify_prefixes.py [--prefixes prefixes.jsonl] [--tokenizer REPO]
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nla_v4_common import CTX, PILOT_TOKENIZER, render_stage, stage_context  # noqa: E402

# google/gemma-3-12b-it is the upstream repo; unsloth/gemma-3-12b-it-bnb-4bit is
# what run_meta.json says the pilot actually loaded, and its tokenizer is the
# one whose counts we are reproducing.  Try upstream first (it is what the task
# asks for), fall back, and SAY which one answered.
TOKENIZER_CANDIDATES = ["google/gemma-3-12b-it", PILOT_TOKENIZER]

GEN_PROMPT_SUFFIX = "<start_of_turn>model\n"


def load_tokenizer(preferred=None):
    from transformers import AutoTokenizer
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    cands = [preferred] if preferred else TOKENIZER_CANDIDATES
    errs = []
    for repo in cands:
        try:
            tok = AutoTokenizer.from_pretrained(repo, token=token)
            return tok, repo
        except Exception as e:
            errs.append(f"{repo}: {type(e).__name__}: {str(e).splitlines()[0]}")
    raise SystemExit("no usable tokenizer:\n  " + "\n  ".join(errs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prefixes.jsonl"))
    ap.add_argument("--tokenizer", default=None)
    a = ap.parse_args()

    tok, repo = load_tokenizer(a.tokenizer)
    print(f"tokenizer: {repo}  (vocab {len(tok)}, {type(tok).__name__})")
    if repo != PILOT_TOKENIZER:
        print(f"NOTE: pilot used {PILOT_TOKENIZER}; counts are only expected to "
              f"match if the two tokenizers are identical.")
    print(f"CTX cap: {CTX}\n")

    rows = [json.loads(l) for l in open(a.prefixes)]
    n_pass = n_fail = 0
    n_stage_checked = n_stage_ok = 0
    weak_only = []

    for r in rows:
        sid, n_stages = r["sid"], r["n_stages"]
        exp = {e["attempt"]: e for e in r["stage_expectations"]}
        msgs, resp = r["prefix_messages"], r["response"]
        problems, details = [], []

        for k in range(1, n_stages + 1):
            ctx_k, resp_k = stage_context(msgs, resp, k, n_stages)
            _p, _rk, toks, ps, pe = render_stage(tok, ctx_k, resp_k)
            e = exp.get(k)
            if e is None:
                details.append(f"s{k}:ps={ps},pe={pe}(no meta)")
                continue
            n_stage_checked += 1
            if ps == e["prompt_tokens"] and pe == e["full_tokens"]:
                n_stage_ok += 1
                details.append(f"s{k}:{ps}/{pe} OK")
            else:
                problems.append(f"stage{k} got ps={ps} pe={pe}, "
                                f"meta ps={e['prompt_tokens']} pe={e['full_tokens']}")
                details.append(f"s{k}:{ps}/{pe} MISMATCH")

        # ---- final stage: strong check if meta exists, structural check if not
        prompt_txt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        full_txt = tok.apply_chat_template(
            msgs + [{"role": "assistant", "content": resp}],
            add_generation_prompt=False, tokenize=False)
        if not prompt_txt.endswith(GEN_PROMPT_SUFFIX):
            problems.append(f"rendered prompt does not end with {GEN_PROMPT_SUFFIX!r} "
                            f"(ends {prompt_txt[-40:]!r})")
        if not full_txt.startswith(prompt_txt):
            problems.append("rendered full chat is not prompt_txt + response suffix")
        elif resp.strip() and resp.strip()[:200] not in full_txt[len(prompt_txt):]:
            problems.append("response text does not appear after the generation prompt")

        if not r["final_stage_meta_available"]:
            weak_only.append(sid)

        status = "PASS" if not problems else "FAIL"
        if problems:
            n_fail += 1
        else:
            n_pass += 1
        tag = "" if r["final_stage_meta_available"] else "  [final stage: STRUCTURAL ONLY, pilot OOM]"
        print(f"{status}  {sid:<38} {' '.join(details)}{tag}")
        for p in problems:
            print(f"        !! {p}")

    print()
    print(f"episodes: {n_pass} pass / {n_fail} fail  (of {len(rows)})")
    print(f"stage token-count checks against pilot meta: {n_stage_ok}/{n_stage_checked} exact")
    if weak_only:
        print(f"final-stage counts UNAVAILABLE for {len(weak_only)} episodes "
              f"(capture_stage OOMed in the pilot): {', '.join(weak_only)}")
        print("  For these the final prefix rests on the structural check plus exact "
              "matches on every earlier stage of the same message list.")
    if n_fail:
        raise SystemExit(1)
    print("\nALL PREFIXES VERIFIED")


if __name__ == "__main__":
    main()
