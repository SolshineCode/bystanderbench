#!/usr/bin/env python3
"""Render the labeller packets as PDF, with answer sheets as CSV.

Tarballs of markdown are a developer's format. The people doing this work are not
programmers, are being paid for about 90 minutes, and should not spend any of it working out
how to open a .tar.gz or read raw markdown. So: one PDF per packet, holding the instructions
and every item in order, and one CSV answer sheet that opens in Excel, Sheets or Numbers.

Blinding is unchanged. The renderer reads only files already cleared for raters, and the
answer keys live outside the packet directories entirely.
"""
from __future__ import annotations
import csv, html, re, sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "research" / "labelling" / "send"

CSS_TEXT = """
@page { size: A4; margin: 20mm 18mm; @bottom-center {
  content: counter(page) " of " counter(pages); font-size: 8.5pt; color: #777; } }
body { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.7pt; line-height: 1.48;
       color: #1a1a1a; }
h1 { font-size: 19pt; margin: 0 0 4pt; line-height: 1.2; }
h2 { font-size: 13.5pt; margin: 20pt 0 5pt; padding-top: 5pt; border-top: 1px solid #ddd; }
h3 { font-size: 11.6pt; margin: 14pt 0 3pt; }
code, pre { font-family: "DejaVu Sans Mono", monospace; font-size: 9.2pt;
            background: #f4f4f2; padding: 0 2px; }
pre { padding: 7pt; white-space: pre-wrap; word-wrap: break-word; border-left: 2px solid #ccc; }
blockquote { margin: 9pt 0 9pt 12pt; padding-left: 10pt; border-left: 3px solid #bbb;
             color: #333; font-style: italic; }
table { border-collapse: collapse; width: 100%; font-size: 9.6pt; margin: 8pt 0; }
th, td { border: 1px solid #bbb; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #eee; }
.item { page-break-before: always; }
.item h2 { border-top: none; margin-top: 0; }
.excerpt { background: #fafaf8; border: 1px solid #e2e2dd; padding: 8pt; margin: 6pt 0; }
"""


def md2html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def verbatim(text: str) -> str:
    """Render an ITEM or COMPONENT so its content survives intact.

    The markdown renderer treats `<bos>`, `<start_of_turn>`, `<pad>` and friends as HTML tags
    and eats them. Measured on the first build: `<start_of_turn>` 23 in source to 1 in the
    PDF, `<pad>` 12 to 0, `<end_of_turn>` 14 to 0, and 6 of 91 `>>>marker<<<` pairs lost
    because a line beginning `>>>` becomes a blockquote. Packet 1 tells the rater to watch for
    those tags and to say if a component reacts to them, so a PDF that hides them makes the
    task impossible to do as written.

    Headings still render; everything else is escaped and preformatted.
    """
    out = []
    buf: list[str] = []

    def flush():
        if buf:
            body = html.escape("\n".join(buf).strip("\n"))
            if body.strip():
                out.append(f"<pre class='excerpt'>{body}</pre>")
            buf.clear()

    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush()
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{lvl}>{html.escape(m.group(2))}</h{lvl}>")
        else:
            buf.append(line)
    flush()
    return "".join(out)


def build(title: str, parts: list[str], out: Path) -> None:
    html = f"<html><head><meta charset='utf-8'><title>{title}</title></head><body>" \
           + "".join(parts) + "</body></html>"
    HTML(string=html).write_pdf(out, stylesheets=[CSS(string=CSS_TEXT)])
    print(f"  wrote {out.relative_to(BASE)}")


def packet_features() -> None:
    d = BASE / "labelling" / "packet_features"
    parts = [md2html((d / "INSTRUCTIONS.md").read_text())]
    for f in sorted(d.glob("component_*.md")):
        parts.append("<div class='item'>" + verbatim(f.read_text()) + "</div>")
    build("Packet 1", parts, OUT / "packet-1-reading-task.pdf")
    with (OUT / "packet-1-ANSWERS.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["component", "what it responds to (one sentence)", "confidence 1-5"])
        for c in "ABCDEFG":
            w.writerow([c, "", ""])
        w.writerow([]); w.writerow(["rater name", ""]); w.writerow(["date", ""])
        w.writerow(["roughly how long this took", ""])
        w.writerow(["excerpts or components you skipped", ""])
        w.writerow(["anything that felt like a bad question", ""])
        # Sending all packets at once means order cannot be enforced, so measure it instead
        # of assuming it (§F142). An honest "yes" here is worth far more than a rule nobody
        # can check, and it is the difference between a known confound and a hidden one.
        w.writerow(["did you look at packet 2 or 3 before doing this one? (yes/no, "
                    "no problem either way)", ""])
    print(f"  wrote {(OUT / 'packet-1-ANSWERS.csv').relative_to(BASE)}")


def packet_concealment() -> None:
    d = BASE / "labelling" / "packet_concealment"
    parts = [md2html((d / "INSTRUCTIONS.md").read_text())]
    items = sorted((d / "items").glob("item_*.md"))
    for f in items:
        parts.append("<div class='item'>" + verbatim(f.read_text()) + "</div>")
    build("Packet 2", parts, OUT / "packet-2-reading-task.pdf")
    with (OUT / "packet-2-ANSWERS.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "Q1 says it can't be done (YES/NO/UNCLEAR)",
                    "Q2 special-cases the tests (YES/NO/UNCLEAR)", "notes"])
        for f in items:
            w.writerow([re.search(r"item_(\d+)", f.name).group(1), "", "", ""])
        w.writerow([]); w.writerow(["rater name", ""]); w.writerow(["date", ""])
        w.writerow(["roughly how long this took", ""])
    print(f"  wrote {(OUT / 'packet-2-ANSWERS.csv').relative_to(BASE)} ({len(items)} items)")


def packet_bystander() -> None:
    src = BASE / "research" / "labelling" / "packets"
    parts = [md2html((src / "JOB1-INSTRUCTIONS.md").read_text())]
    # The 57 messages have to be IN the PDF. As CSV cells they are multi-paragraph text that
    # Excel and Sheets show as one clipped line, so a rater reading from the spreadsheet sees
    # a fragment of each message and answers on that.
    rows = list(csv.DictReader((src / "job1_packet.csv").open()))
    for r in rows:
        parts.append("<div class='item'><h2>Item " + html.escape(r["item"]) + "</h2>"
                     + f"<pre class='excerpt'>{html.escape(r['message_the_agent_sent'].strip())}</pre>"
                     + "</div>")
    build("Packet 3", parts, OUT / "packet-3-reading-task.pdf")
    # Already a CSV and already the answer sheet: copy it under the matching name.
    rows = list(csv.reader((src / "job1_packet.csv").open()))
    with (OUT / "packet-3-ANSWERS.csv").open("w", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print(f"  wrote {(OUT / 'packet-3-ANSWERS.csv').relative_to(BASE)} ({len(rows)-1} items)")


def main() -> int:
    # 2026-09-13: this script takes NO arguments. It rebuilds research/labelling/send/ from
    # scratch, every time. I invoked it as `labelling_pdf.py <in.md> <out.pdf>` expecting a
    # generic converter; it ignored both and regenerated the seven files that were already
    # in a labeller's inbox. Nothing changed materially (six byte-identical, one PDF
    # differing by three bytes of metadata, text verified identical), but the next person
    # may not check. Refuse rather than silently ignore.
    import sys as _sys
    if len(_sys.argv) > 1:
        print("labelling_pdf.py takes no arguments: it rebuilds research/labelling/send/ "
              "in full from the packet sources.\n"
              f"Ignoring would have silently regenerated live rater-facing files. Got: "
              f"{_sys.argv[1:]}", file=_sys.stderr)
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    build("Start here", [md2html((BASE / "labelling" / "START-HERE.md").read_text())],
          OUT / "0-START-HERE.pdf")
    packet_features()
    packet_concealment()
    packet_bystander()
    # Verify the renderer did not eat content. This is checked rather than assumed because
    # the first build silently dropped most of the chat-template tags (§F141).
    import subprocess
    src_all = "".join(f.read_text() for f in
                      sorted((BASE / "labelling" / "packet_features").glob("component_*.md")))
    pdf_txt = subprocess.run(["pdftotext", str(OUT / "packet-1-reading-task.pdf"), "-"],
                             capture_output=True, text=True).stdout
    bad = []
    for tok in ("<bos>", "<start_of_turn>", "<end_of_turn>", "<pad>", ">>>"):
        a, b = src_all.count(tok), pdf_txt.count(tok)
        if b < a:
            bad.append(f"{tok}: source {a}, pdf {b}")
    if bad:
        print("REFUSING: packet 1 PDF lost content the rater is told to look for:")
        for x in bad:
            print("   ", x)
        return 1
    print("  packet 1 PDF keeps every template tag and marker")

    # A key inside the send directory is the one mistake that cannot be undone.
    leaked = [p for p in OUT.iterdir() if "key" in p.name.lower()]
    if leaked:
        print(f"REFUSING: key-looking files in the send directory: {leaked}")
        return 1
    print(f"\nsend directory clean: {len(list(OUT.iterdir()))} files, no key files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
