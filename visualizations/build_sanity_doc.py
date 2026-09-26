#!/usr/bin/env python
"""Generate a data sanity-check document: real samples from every result type, with just
enough context to judge whether the labels are right. Deliberately light on interpretation.
Run with .venv/bin/python (needs inspect_ai)."""
import glob, json, os, re, sys, textwrap
sys.path.insert(0, "concealment-probe/tools")
from screen_behavioral import visible_part, find_code
from corpus import denominators
from inspect_ai.log import read_eval_log

OUT = "visualizations/bystander_out/DATA_SANITY_CHECK.md"
W = []
def w(s=""): W.append(s)

w("# Data sanity check — silent-concealment-detection-lab")
w()
w("Generated 2026-09-09. Real samples pulled from the actual data files, with context.")
w("Nothing here is summarised by a model: every excerpt is verbatim from disk. The point")
w("is for a human to check that the labels mean what the tables claim they mean.")
w()
w("**What to look for, in order of how much it would matter if wrong:**")
w()
w("1. Do the `concealed_cheat` samples actually hardcode test inputs? (If not, the 22% rate is wrong.)")
w("2. In the bystander episodes, did the model really have the evidence in front of it? (If not, `discovered` is wrong.)")
w("3. Did it really say nothing about it? (If it did say something, `alerted`/`mentioned_in_final` is wrong.)")
w("4. Does the `tool_probe` alert look like a real tool call? (If not, the floor of 10/10 is wrong.)")
w()
w("---")
w()

# ---------- 1. concealment samples ----------
w("## 1. Concealment: what a `concealed_cheat` actually looks like")
w()
w("These are hand-audited rows (§F40). The claim is that each one special-cases the exact")
w("test inputs rather than solving the problem. Judge that directly.")
w()
seen = 0
for f in ("sae-causal/resample_base.jsonl", "sae-causal/resample_f655neg.jsonl"):
    for line in open(f):
        r = json.loads(line)
        if r["category"] != "concealed_cheat" or seen >= 2:
            continue
        code = find_code(visible_part(r["text"])) or ""
        n_eq = len(re.findall(r"if\s+.{1,140}==\s*.{1,140}:\s*\n\s+return\s", code))
        w(f"### Sample {seen+1}: `{r['cid']}`")
        w(f"- task `{r['task_id']}`, split `{r['split']}`, arm `{r['arm'] if 'arm' in r else '?'}`")
        w(f"- machine label `{r['category']}` / `{r['cheat_mechanism']}`, hand audit: confirmed hardcode")
        w(f"- literal `if <input> == <value>: return <value>` patterns counted: **{n_eq}**")
        w(f"- tests passed: `{r['verification_result']}`; visible-prose flag: `{r['flag_location']}` (None = did not disclose)")
        w()
        w("```python")
        w(code[:1400].rstrip())
        w("```")
        w()
        seen += 1

# ---------- 2. bystander episode ----------
w("---")
w()
w("## 2. Bystander: the evidence the model read, and what it said instead")
w()
w("One episode from the ceiling arm, where the misconduct is plain prose in a CI log the")
w("ticket itself points at. Below: the evidence line the scorer matched, then the model's")
w("own final message, verbatim.")
w()
for p in sorted(glob.glob("logs/bystander-nemotron-blatant/*.eval"))[:1]:
    log = read_eval_log(p)
    s = (log.samples or [None])[0]
    if s:
        ev = None
        for m in (s.messages or []):
            c = m.content if isinstance(m.content, str) else " ".join(
                x.get("text", "") for x in (m.content or []) if isinstance(x, dict))
            if "d.raines" in c or "Kessler" in c:
                ev = c; break
        w("**Evidence that appeared in a tool result (verbatim excerpt):**")
        w()
        w("```")
        if ev:
            keep = [l for l in ev.splitlines() if ("raines" in l or "Kessler" in l or "okafor" in l)][:6]
            w("\n".join(keep) if keep else ev[:600])
        else:
            w("(no evidence-bearing message found in this episode)")
        w("```")
        w()
        # The episode ends with a `submit` tool call, so the model's closing words live in
        # that call's arguments, not in an assistant text message. Look there first, then
        # fall back to the last non-empty assistant text.
        final = ""
        for m in reversed(s.messages or []):
            for t in (getattr(m, "tool_calls", None) or []):
                if str(getattr(t, "function", "")).endswith("submit"):
                    a = getattr(t, "arguments", None)
                    final = (a.get("answer") or a.get("summary") or json.dumps(a)) if isinstance(a, dict) else str(a)
                    break
            if final.strip():
                break
        if not final.strip():
            for m in reversed(s.messages or []):
                if getattr(m, "role", "") == "assistant":
                    c = m.content if isinstance(m.content, str) else " ".join(
                        x.get("text", "") for x in (m.content or []) if isinstance(x, dict))
                    if c.strip():
                        final = c; break
        w("**What the model submitted as its closing description of the work, verbatim:**")
        w()
        w("```")
        w(final.strip()[:1600] or "(empty)")
        w("```")
        w()
        sc = {k: v.value for k, v in (s.scores or {}).items()}
        w(f"**Scored:** `{json.dumps(sc, default=str)[:400]}`")
        w()

# ---------- 3. the tool_probe alert ----------
w("---")
w()
w("## 3. The affordance floor: a real `alert_oversight` call")
w()
w("The floor claim is 10/10 — models call the tool when told to. Here is one actual call,")
w("so you can confirm it is a genuine tool invocation and not text that looks like one.")
w()
for p in sorted(glob.glob("logs/bystander-floor-nemotron/*.eval"))[:1]:
    log = read_eval_log(p)
    for s in (log.samples or [])[:1]:
        for m in (s.messages or []):
            tcs = getattr(m, "tool_calls", None)
            if tcs:
                w("```json")
                w(json.dumps([{"function": getattr(t, "function", None),
                               "arguments": getattr(t, "arguments", None)} for t in tcs],
                             indent=1, default=str)[:800])
                w("```")
                w()
                break

# ---------- 4. counting denominators ----------
w("---")
w()
w("## 4. Counting units (the error that recurred five times)")
w()
w("`sid` identifies a design cell, not a generation, so distinct generations share one.")
w("Every corpus at every unit — check that the N you expect matches the unit you mean.")
w()
w("| corpus | rows | generations | activation slots | solutions | tasks |")
w("|---|---|---|---|---|---|")
for f in sorted(glob.glob("concealment-probe/data/*/*/samples.jsonl")):
    d = denominators(f)
    if d["rows"]:
        w(f"| `{'/'.join(f.split('/')[-3:-1])}` | {d['rows']} | {d['generations']} | "
          f"{d['activation_slots']} | {d['solutions']} | {d['tasks']} |")
w()

# ---------- 5. activation coverage ----------
w("---")
w()
w("## 5. Activation coverage")
w()
w("| capture set | .bin files | note |")
w("|---|---|---|")
for d in sorted(glob.glob("bystander/acts*") + glob.glob("sae-causal/tokens*")):
    n = len(glob.glob(os.path.join(d, "acts", "*.bin")))
    if n:
        w(f"| `{d}` | {n} | teacher-forced replay |")
for d in sorted(glob.glob("concealment-probe/data/*/*/acts")):
    n = len(glob.glob(os.path.join(d, "*.bin")))
    if n:
        w(f"| `{'/'.join(d.split('/')[-3:-1])}` | {n} | ImpossibleBench capture |")
w()
w("Each bystander sidecar (`*.meta.json`) records the model, eval file, pooled span and")
w("the episode's scores, so an activation always traces back to the behaviour it accompanied.")
w()
open(OUT, "w").write("\n".join(W) + "\n")
print("wrote", OUT, len("\n".join(W)), "chars")
