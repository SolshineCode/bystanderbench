#!/usr/bin/env python3
"""Generic markdown -> PDF, for one-off rater packets.

Separate from labelling_pdf.py, which is a fixed-purpose builder that rebuilds the whole
send/ directory and now refuses arguments (2026-09-13). Escaping matters here for the same
reason as §F141: code and template tags inside an item must survive into the PDF verbatim,
so item bodies go through html.escape into <pre>, never through the markdown renderer.
"""
import html, re, sys
from pathlib import Path
import markdown as md
from weasyprint import HTML, CSS

CSS_TEXT = """
@page { size: A4; margin: 18mm 16mm; }
body { font: 11.5pt/1.5 "DejaVu Sans", sans-serif; color: #111; }
h1 { font-size: 19pt; margin: 0 0 10pt; }
h2 { font-size: 14pt; margin: 16pt 0 6pt; border-bottom: 1px solid #bbb; padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 13pt 0 4pt; }
pre { background: #f4f4f4; border: 1px solid #ddd; padding: 7pt; white-space: pre-wrap;
      word-wrap: break-word; font: 9.5pt/1.35 "DejaVu Sans Mono", monospace; }
strong { font-weight: 700; }
p { margin: 5pt 0; }
"""

def convert(src: Path, dst: Path) -> None:
    text = src.read_text()
    out, buf, in_fence = [], [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if in_fence:
                out.append(f"<pre>{html.escape(chr(10).join(buf).strip(chr(10)))}</pre>")
                buf, in_fence = [], False
            else:
                in_fence = True
            continue
        (buf if in_fence else out).append(line)
    if in_fence:
        raise SystemExit(f"{src}: unclosed code fence")
    body = md.markdown("\n".join(out), extensions=["tables"])
    HTML(string=f"<html><body>{body}</body></html>").write_pdf(
        str(dst), stylesheets=[CSS(string=CSS_TEXT)])

    # §F141 guard: confirm the fenced blocks actually survived into the PDF.
    import subprocess
    got = subprocess.run(["pdftotext", str(dst), "-"], capture_output=True, text=True).stdout
    fences = re.findall(r"```\n(.*?)```", text, re.S)
    missing = []
    for f in fences:
        probe = [l.strip() for l in f.strip().split("\n") if len(l.strip()) > 12]
        if probe and probe[0] not in got:
            missing.append(probe[0][:60])
    if missing:
        raise SystemExit(f"{dst}: {len(missing)} fenced block(s) did NOT survive rendering: {missing}")
    print(f"wrote {dst} ({len(fences)} fenced blocks, all verified present in the PDF)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: md_to_pdf.py <in.md> <out.pdf>")
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
