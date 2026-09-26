#!/usr/bin/env python3
"""Map labelled assistant turns (cid, msg_idx) to token spans in the captured token streams.

AUTONOMOUS DRAFT (Claude, 2026-09-23, branch autonomous/2026-09-23). No model is loaded and no
GPU is touched: the vocabulary is read from the GGUF metadata with gguf-py (mmap, header fields
only), and the stored token ids are scanned for `<|im_start|>assistant` blocks.

Mapping rule: the k-th `<|im_start|>assistant` block in a stream <-> the k-th assistant message in
the Inspect transcript. (The Qwen chat template folds tool results into user blocks, so counting
ALL blocks would misalign; assistant blocks are one-to-one with assistant messages.)

Validation, per episode, all must hold or the episode is REFUSED (not guessed):
  1. the number of assistant blocks equals the number of assistant messages
     (a stream truncated at a decision index legitimately has fewer: then only the leading
      blocks that exist are mapped, and the episode is flagged `truncated_stream`)
  2. for every mapped turn with visible text, at least one 6-word window of that text appears
     in the decoded block (tool-call-only turns are checked on the tool name instead)

Output per turn: token_start (index of the block's <|im_start|>), content_start (first token
after "assistant\\n"), token_end (index of its <|im_end|>, or stream end). The activation "just
before this turn" is at position token_start - 1.

Usage: python map_turns_to_tokens.py EPISODES.jsonl MANIFEST.tsv [MANIFEST.tsv ...] --out spans.jsonl
"""
import argparse, json, re, sys
sys.path.insert(0, "/home/darkstar/llama.cpp/gguf-py")
import gguf

GGUF = "/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf"


def load_vocab():
    r = gguf.GGUFReader(GGUF)
    f = r.fields["tokenizer.ggml.tokens"]
    toks = [bytes(f.parts[i]).decode("utf-8", "replace") for i in f.data]
    # gpt2 byte-level BPE: map the unicode stand-ins back to bytes
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]; n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b); cs.append(256 + n); n += 1
    u2b = {chr(c): b for b, c in zip(bs, cs)}
    return toks, u2b


def decode(ids, toks, u2b):
    out = bytearray()
    for i in ids:
        t = toks[i]
        if t.startswith("<|") and t.endswith("|>"):
            out += t.encode()
        else:
            out += bytes(u2b.get(ch, 63) for ch in t)
    return out.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes"); ap.add_argument("manifests", nargs="+"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    toks, u2b = load_vocab()
    START, END = toks.index("<|im_start|>"), toks.index("<|im_end|>")
    stream_of = {}
    for m in a.manifests:
        for line in open(m):
            path = line.split("\t")[0]
            # older manifests store repo-relative paths ("bystander/acts_..."); resolve against the repo
            if not path.startswith("/"):
                path = "/home/darkstar/bluedot-unit2-impossiblebench/" + path
            stream_of[path.rsplit("/", 1)[-1][:-4]] = path
    stats = {"episodes": 0, "mapped": 0, "refused": 0, "truncated": 0, "turns_mapped": 0}
    with open(a.out, "w") as fh:
        for line in open(a.episodes):
            e = json.loads(line); cid = e["cid"]; stats["episodes"] += 1
            if cid not in stream_of:
                fh.write(json.dumps({"cid": cid, "status": "no_stream"}) + "\n"); stats["refused"] += 1; continue
            ids = [int(x) for x in open(stream_of[cid]).read().split()]
            blocks = []
            for i, t in enumerate(ids):
                if t == START and decode(ids[i + 1:i + 3], toks, u2b).startswith("assistant"):
                    j = next((k for k in range(i + 1, len(ids)) if ids[k] == END), len(ids))
                    cs = i + 1
                    while cs < j and "\n" not in decode(ids[i + 1:cs + 1], toks, u2b):
                        cs += 1
                    blocks.append((i, cs + 1, j))
            amsg = [t for t in e["turns"] if t["role"] == "assistant"]
            # The template appends a generation prompt (`<|im_start|>assistant\n<think>`, no <|im_end|>)
            # at the end of the stream. It is not a message. Drop exactly that, and only when it is
            # the last block and unterminated. Verified on the pilot by decoding the tail.
            if len(blocks) == len(amsg) + 1 and blocks[-1][2] == len(ids):
                blocks = blocks[:-1]
            truncated = len(blocks) < len(amsg)
            if len(blocks) > len(amsg):
                fh.write(json.dumps({"cid": cid, "status": "refused_more_blocks_than_messages",
                                     "blocks": len(blocks), "assistant_msgs": len(amsg)}) + "\n")
                stats["refused"] += 1; continue
            bad = []
            rows = []
            for k, (s, c, en) in enumerate(blocks):
                t = amsg[k]; text = decode(ids[c:en], toks, u2b)
                words = (t.get("text") or "").split()
                if len(words) >= 6:
                    ok = any(" ".join(words[w:w + 6]) in text for w in range(0, len(words) - 5, max(1, len(words) // 8)))
                else:
                    ok = all(tc["fn"] in text for tc in t.get("tool_calls", [])) if t.get("tool_calls") else True
                if not ok:
                    bad.append(t["idx"])
                rows.append({"cid": cid, "msg_idx": t["idx"], "token_start": s, "content_start": c, "token_end": en})
            if bad:
                fh.write(json.dumps({"cid": cid, "status": "refused_text_mismatch", "bad_msg_idx": bad[:5]}) + "\n")
                stats["refused"] += 1; continue
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            fh.write(json.dumps({"cid": cid, "status": "truncated_stream" if truncated else "ok",
                                 "blocks": len(blocks), "assistant_msgs": len(amsg), "stream_len": len(ids)}) + "\n")
            stats["mapped"] += 1; stats["truncated"] += truncated; stats["turns_mapped"] += len(rows)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
