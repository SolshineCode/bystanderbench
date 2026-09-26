#!/usr/bin/env python3
"""Markdown -> speakable English. The notation in this write-up is unreadable aloud
verbatim: "9/48" becomes "nine forty-eighths", "§F122" becomes a glyph, and a table
becomes pipes. Everything here exists because one of those came out wrong on a read-through.
"""
import re, sys

def num(s):
    return s

def speak(md: str) -> str:
    out = []
    for raw in md.splitlines():
        ln = raw.rstrip()
        if ln.startswith("|"):                       # tables: read as sentences
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue                             # separator row
            out.append(". ".join(c for c in cells if c) + ".")
            continue
        m = re.match(r"^(#+)\s+(.*)", ln)
        if m:
            out.append("")                           # a beat before a heading
            out.append(m.group(2).rstrip(".") + ".")
            out.append("")
            continue
        ln = re.sub(r"^\s*[-*]\s+", "", ln)
        ln = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", ln)
        out.append(ln)
    t = "\n".join(out)

    t = re.sub(r"`([^`]*)`", r"\1", t)                # code spans
    t = re.sub(r"\*\*([^*]*)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]*)\*", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)

    t = t.replace("§F", "finding ").replace("§", "section ")
    t = t.replace("&", " and ")
    t = re.sub(r"\bn\s*=\s*(\d+)", r"n equals \1", t)
    t = re.sub(r"\bp\s*=\s*([\d.]+)", r"p equals \1", t)
    t = re.sub(r"(\d)\s*%", r"\1 percent", t)
    t = re.sub(r"\$([\d.]+)", r"\1 dollars", t)
    # k/n: say "9 of 48", not "nine forty-eighths". Guard against dates and versions.
    t = re.sub(r"(?<![\d/.-])(\d{1,4})/(\d{1,4})(?![\d/])", r"\1 of \2", t)
    t = re.sub(r"\bv1\.0\b", "version one point oh", t)
    t = re.sub(r"\bMoE\b", "mixture of experts", t)
    t = re.sub(r"\bSAEs?\b", lambda m: "sparse autoencoder" + ("s" if m.group(0).endswith("s") else ""), t)
    t = re.sub(r"\bNLA\b", "natural language autoencoder", t)
    t = re.sub(r"\bCI\b", "confidence interval", t)
    t = re.sub(r"\bICC\b", "intra class correlation", t)
    t = re.sub(r"\bCoT\b", "chain of thought", t)
    t = t.replace("alert_oversight", "alert underscore oversight")
    t = t.replace("ops-escalate", "ops escalate")
    t = re.sub(r"\bcover_task_passed\b", "cover task passed", t)
    t = re.sub(r"_", " ", t)
    t = re.sub(r"\s*—\s*", ", ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

if __name__ == "__main__":
    sys.stdout.write(speak(open(sys.argv[1]).read()))
