#!/usr/bin/env python3
"""Build the blind NLA validation round (§F152 / §F156).

WHY. §F152 claims the NLA decoder's positive control works, on the strength of ME reading
four decodes and deciding they matched their sources. CLAUDE.md's interpretability rule 3 is
explicit that an interpretation you reached yourself is a single-agent autolabel and stays
flagged until independently checked. This is that check.

DESIGN. Four decodes, eight candidate source texts, rater picks one per decode. Two of the
eight are the real sources; the other six are decoys. The decoys are deliberately balanced
four code / four prose, because the decodes plainly reveal the DOMAIN ("Python function
definition", "UK weather advisory"). Domain is not what is in question. Whether the decode
identifies the SPECIFIC text is. So the analysis scores against within-domain chance, which
is 1/4 for the code items and 1/4 for the prose items, not 1/8.

READING THE RESULT. All four correct by luck is (1/4)^4 = 1/256, p = 0.004. Three of four is
not significant on its own. A null here does not mean the decoder is broken; it means my
reading of it was not independently reproducible, which is the thing worth knowing before
§F152 reaches a paper.

The answer key is written to _key/ and must never be sent to a rater.
"""
import csv, json, random
from pathlib import Path

OUT = Path("research/labelling/nla-round-a")
KEY = OUT / "_key"
OUT.mkdir(parents=True, exist_ok=True); KEY.mkdir(exist_ok=True)

REAL_CODE = ("def check(candidate):\n    assert candidate(5) == 7\n\n"
             "def solve(k):\n    if k == 5:\n        return 7  # hardcoded to pass the test\n"
             "    return 0\n")
REAL_PROSE = "The forecast says heavy rain and strong winds across the coast tomorrow."

CANDIDATES = [
    ("REAL_CODE", REAL_CODE),
    ("decoy_code_prime",
     "def is_prime(n):\n    if n < 2:\n        return False\n"
     "    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n"
     "    return True\n"),
    ("decoy_code_linkedlist",
     "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\n"
     "def reverse(head):\n    prev = None\n    while head:\n"
     "        head.next, prev, head = prev, head, head.next\n    return prev\n"),
    # This decoy deliberately shares "def solve(" with the real source. Without it, only
    # the real text contains that token and the two code items are answerable from one word,
    # which tests token recovery rather than text identification. With it, a rater has to use
    # the rest of the description (the hardcoded return, the assert) to choose.
    ("decoy_code_solve",
     "def solve(n):\n    total = 0\n    for i in range(n):\n        total += i * i\n"
     "    return total\n"),
    ("REAL_PROSE", REAL_PROSE),
    ("decoy_prose_snow",
     "Snow is expected to settle above 400 metres overnight, with icy roads by morning."),
    # Was a thunderstorm decoy until 2026-09-13. The val_weather_mid decode offers
    # "thunderstorms" as a secondary guess for the next token (it leads with the correct
    # "winds"), so that decoy was an artefact of my own wording rather than a real
    # distractor: it would have tested whether a rater trusts a verbatim quote over a
    # paraphrase. Swapped for one the decodes do not mention at all.
    ("decoy_prose_fog",
     "Fog is expected to linger in low-lying areas until mid-morning on Tuesday."),
    ("decoy_prose_museum",
     "The museum will close early on Friday because of scheduled maintenance work."),
]

rows = [json.loads(l) for l in open("nla-decode/results/runpod-2026-09-13b/decodes.jsonl")]
vals = [r for r in rows if r["name"].startswith("val_")]
assert len(vals) == 4, f"expected 4 validation decodes, got {len(vals)}"

rng = random.Random(20260913)          # fixed seed: the shuffle is reproducible
cands = CANDIDATES[:]; rng.shuffle(cands)
cand_ids = {name: f"S{i+1}" for i, (name, _) in enumerate(cands)}

items = []
for v in vals:
    truth = "REAL_CODE" if "code_cheat" in v["name"] else "REAL_PROSE"
    items.append({"decode": v["decode"], "truth": truth, "src_name": v["name"]})
rng.shuffle(items)
for i, it in enumerate(items, 1):
    it["item"] = f"D{i}"

# ---- rater-facing markdown ----
md = ["# Round A: which text was this description generated from?",
      "",
      "About 15 minutes. Four questions. There are no trick questions and no penalty for guessing.",
      "",
      "## What you're looking at",
      "",
      "A program read something inside an AI model and tried to write, in English, what that",
      "part of the model was responding to. It did not get to see the original text. It only",
      "saw a pattern of numbers.",
      "",
      "Your job: read each description, then pick which of the eight texts below you think it",
      "was describing.",
      "",
      "Some descriptions will feel obvious and some will not. If two texts seem equally good,",
      "pick one and say in the notes that it was a coin flip. That is useful information, not",
      "a failure.",
      "",
      "**Please do not look anything up or paste this into an AI assistant.** The whole point",
      "is what a person notices unaided.",
      "",
      "## The eight texts",
      ""]
for name, text in cands:
    md += [f"**{cand_ids[name]}**", "", "```", text.rstrip("\n"), "```", ""]
md += ["## The four descriptions", ""]
for it in items:
    md += [f"### {it['item']}", "", "```", it["decode"].strip(), "```", "",
           f"Which text (S1-S8) was **{it['item']}** describing? Write your answer in the CSV.", ""]
md += ["## When you're done", "",
       "Fill in `round-a-ANSWERS.csv` and send it back. The last rows are for your name, the",
       "date, and roughly how long it took.", ""]
(OUT / "round-a-reading-task.md").write_text("\n".join(md))

# ---- blank answer sheet ----
with open(OUT / "round-a-ANSWERS.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "which_text_S1_to_S8", "how_sure_1_to_5", "notes_optional"])
    for it in items:
        w.writerow([it["item"], "", "", ""])
    for meta in ["rater name", "date", "roughly how long this took",
                 "did you use any AI help? (yes/no, honest answer is fine)"]:
        w.writerow([meta, "", "", ""])

# ---- key (NEVER SENT) ----
with open(KEY / "round-a_KEY.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "correct_candidate_id", "truth_name", "decode_source_vector",
                "within_domain_chance"])
    for it in items:
        w.writerow([it["item"], cand_ids[it["truth"]], it["truth"], it["src_name"], "1/4"])

print("candidate order:", [cand_ids[n] + "=" + n for n, _ in cands])
print("items:", [(it["item"], it["src_name"]) for it in items])
print("wrote", OUT / "round-a-reading-task.md", OUT / "round-a-ANSWERS.csv", KEY / "round-a_KEY.csv")
