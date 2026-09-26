#!/usr/bin/env python3
"""Minimal markdown to .docx for the course write-ups, with figures embedded.

Handles what these documents actually use: ATX headings, paragraphs, bold runs,
inline code, bullet lists, block quotes, and pipe tables. Figures are inserted by
an explicit map from a marker string to an image path, so a figure never lands in
the wrong place silently.

Usage: python visualizations/md_to_docx.py <in.md> <out.docx> [marker=image.png ...]
"""
import sys, re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_hyperlink(par, text, url):   # real Word hyperlink (added 2026-09-25)
    from docx.oxml.shared import OxmlElement, qn
    r_id = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "1155CC"); rPr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
    r.append(rPr); t = OxmlElement("w:t"); t.text = text; r.append(t); h.append(r); par._p.append(h)

def add_runs(par, text):
    for part in re.split(r'(\[[^\]]+\]\(https?://[^)]+\)|\*\*[^*]+\*\*|`[^`]+`|(?<![*\w])\*[^*\s][^*]*\*(?![*\w]))', text):
        if not part:
            continue
        m = re.fullmatch(r'\[([^\]]+)\]\((https?://[^)]+)\)', part)
        if m:
            add_hyperlink(par, m.group(1), m.group(2)); continue
        if part.startswith('**') and part.endswith('**'):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        elif part.startswith('`') and part.endswith('`'):
            r = par.add_run(part[1:-1]); r.font.name = 'Consolas'; r.font.size = Pt(9.5)
        else:
            par.add_run(part)

def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    figs = {}
    for a in sys.argv[3:]:
        k, v = a.split('=', 1); figs[k] = v
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    lines = src.read_text().split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        placed = False
        for marker, img in list(figs.items()):
            if marker and marker in ln:
                from PIL import Image   # cap tall figures so one never exceeds a page (2026-09-24)
                w, h = Image.open(img).size
                if 6.3 * h / w > 8.5: doc.add_picture(img, height=Inches(8.5))
                else: doc.add_picture(img, width=Inches(6.3))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                del figs[marker]; placed = True
        if ln.startswith('|') and i + 1 < len(lines) and set(lines[i+1].replace('|','').strip()) <= set('-: '):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not set(''.join(cells)) <= set('-: '):
                    rows.append(cells)
                i += 1
            if rows:
                t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Light Grid Accent 1'
                for r, cells in enumerate(rows):
                    for c, cell in enumerate(cells[:len(rows[0])]):
                        p = t.cell(r, c).paragraphs[0]; add_runs(p, cell)
                        if r == 0:
                            for run in p.runs: run.bold = True
                doc.add_paragraph()
            continue
        if ln.startswith('#'):
            lvl = len(ln) - len(ln.lstrip('#'))
            doc.add_heading(ln.lstrip('#').strip(), level=min(lvl, 4))
        elif ln.startswith('> '):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.35)
            add_runs(p, ln[2:].lstrip('> '))
            for r in p.runs: r.italic = True; r.font.color.rgb = RGBColor(0x55,0x55,0x55)
        elif ln.startswith('- '):
            add_runs(doc.add_paragraph(style='List Bullet'), ln[2:])
        elif re.match(r'^\d+\. ', ln):   # numbered list item (added 2026-09-24)
            add_runs(doc.add_paragraph(style='List Number'), re.sub(r'^\d+\. ', '', ln))
        elif re.match(r'^Figure \d+\. ', ln):   # figure caption (added 2026-09-24)
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, ln)
            for r in p.runs: r.italic = True; r.font.size = Pt(9.5); r.font.color.rgb = RGBColor(0x44,0x44,0x44)
        elif ln.strip() == '':
            pass
        elif not placed:
            buf = [ln]
            while i + 1 < len(lines) and lines[i+1].strip() and not re.match(r'^(#|\||> |- |\d+\. |Figure \d+\. |\[\[FIG:)', lines[i+1]):
                i += 1; buf.append(lines[i])
            add_runs(doc.add_paragraph(), ' '.join(x.strip() for x in buf))
        i += 1
    for marker, img in figs.items():
        doc.add_picture(img, width=Inches(6.3))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.save(out)
    print(f"wrote {out}")

if __name__ == '__main__':
    main()
