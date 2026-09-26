# Build prefixes.jsonl: the reconstructed FINAL-STAGE context of each of the 24
# recruiter-pilot episodes, plus everything needed to verify that
# reconstruction without a second data source.
#
# CPU only.  No tokenizer, no model -- this is pure JSON surgery; the token-count
# verification lives in verify_prefixes.py.
#
# Usage:
#   python build_prefixes.py [--results DIR] [--out prefixes.jsonl]
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nla_v4_common import final_stage_context   # noqa: E402

DEFAULT_RESULTS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
    "recruiter-trial", "results", "recruiter-gemma3-12b-20260904")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=DEFAULT_RESULTS)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prefixes.jsonl"))
    a = ap.parse_args()
    R = os.path.abspath(a.results)

    samples = {}
    for line in open(os.path.join(R, "samples.jsonl")):
        r = json.loads(line)
        samples[r["sid"]] = r

    rows, n_meta, n_nometa = [], 0, 0
    for line in open(os.path.join(R, "transcripts.jsonl")):
        t = json.loads(line)
        sid = t["sid"]
        prefix, response = final_stage_context(t)
        n_stages = len(t["stages"])
        s = samples.get(sid, {})

        # stage_acts/<sid>.json holds capture_stage()'s own token counts.  Five
        # episodes lost their LAST stage to a CUDA OOM during the pilot
        # (STAGE_CAPTURE_FAILED ... stage3 in the run log), so `stages` there is
        # keyed by attempt number and is NOT positionally aligned with the
        # transcript's stages.  Match on attempt, never on index.
        meta_path = os.path.join(R, "stage_acts", sid + ".json")
        by_attempt = {}
        if os.path.exists(meta_path):
            m = json.load(open(meta_path))
            for sm in m["stages"]:
                by_attempt[sm["attempt"]] = sm
        fin = by_attempt.get(n_stages)
        if fin:
            n_meta += 1
        else:
            n_nometa += 1

        rows.append({
            "sid": sid,
            "category": t.get("category", s.get("category")),
            "arm": t["arm"],
            "split": t["split"],
            "task_id": s.get("task_id"),
            "variant": s.get("variant"),
            "beats_received": t["stages"][-1]["beats_received"],
            "final_attempt": n_stages,
            "n_stages": n_stages,
            "verification_result": t.get("verification_result"),
            "prefix_messages": prefix,
            "response": response,
            "expected_prompt_tokens": fin["pool_start"] if fin else None,
            "expected_full_tokens": fin["n_tokens"] if fin else None,
            "final_stage_meta_available": bool(fin),
            # every stage's recorded counts, so verify_prefixes.py can check the
            # whole reconstruction chain (stage k's context is a prefix of the
            # final one) even for the five episodes missing the last stage.
            "stage_expectations": [
                {"attempt": k, "prompt_tokens": by_attempt[k]["pool_start"],
                 "full_tokens": by_attempt[k]["n_tokens"],
                 "beats_received": by_attempt[k].get("beats_received"),
                 "compacted": by_attempt[k].get("compacted")}
                for k in sorted(by_attempt)],
        })

    rows.sort(key=lambda r: r["sid"])
    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} episodes -> {a.out}")
    print(f"  final-stage meta present: {n_meta}   missing (pilot OOM): {n_nometa}")
    print(f"  total stage expectations: {sum(len(r['stage_expectations']) for r in rows)}")


if __name__ == "__main__":
    main()
