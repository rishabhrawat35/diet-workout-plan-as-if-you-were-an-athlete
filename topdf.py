"""
Markdown to PDF for the rendered plan.

This file exists because it went missing once. The plan was built, read as a
PDF, and the script that made the PDF lived outside the repository -- so the
next person to clone this got the markdown and no way to produce the document
anyone had actually read. Black on white only: the plan's own rule is that no
colour or symbol may carry meaning, so nothing here encodes anything in colour.

    python3 topdf.py My-Plan.md My-Plan.pdf
"""
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SS = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=SS["Normal"], fontName="Helvetica",
                      fontSize=9.5, leading=13, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=BODY, fontName="Helvetica-Bold", fontSize=17,
                    leading=21, spaceBefore=2, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=12.5,
                    leading=16, spaceBefore=13, spaceAfter=5)
H3 = ParagraphStyle("h3", parent=BODY, fontName="Helvetica-Bold", fontSize=10.5,
                    leading=14, spaceBefore=9, spaceAfter=3)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.3, leading=10.6, spaceAfter=0)
HEAD = ParagraphStyle("head", parent=CELL, fontName="Helvetica-Bold")
BULLET = ParagraphStyle("bul", parent=BODY, leftIndent=11, bulletIndent=2, spaceAfter=2)


def inline(t):
    """Markdown emphasis to reportlab markup, and characters its fonts lack."""
    t = (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
          .replace("½", "1/2").replace("—", "-").replace("–", "-"))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", t)
    return t


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table(head, rows):
    """A column of only digits is narrow and right aligned; the rest share the rest."""
    n = len(head)
    rows = [r + [""] * (n - len(r)) for r in rows]
    data = ([[Paragraph(inline(c), HEAD) for c in head]]
            + [[Paragraph(inline(c), CELL) for c in r[:n]] for r in rows])
    numeric = [j for j in range(n)
               if rows and all(re.fullmatch(r"[\d.,]*", r[j].strip()) for r in rows)]
    avail = A4[0] - 30 * mm
    wide = [j for j in range(n) if j not in numeric]
    widths = [avail * 0.085 if j in numeric
              else avail * (1 - 0.085 * len(numeric)) / max(len(wide), 1)
              for j in range(n)]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.black),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ] + [("ALIGN", (j, 0), (j, -1), "RIGHT") for j in numeric]))
    return t


def story_from(lines):
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|") and i + 1 < len(lines) \
                and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out += [Spacer(1, 3), table(head, rows), Spacer(1, 7)]
            continue
        s = line.strip()
        i += 1
        if not s or re.match(r"^-{3,}$", s):
            continue
        if s.startswith("### "):
            out.append(Paragraph(inline(s[4:]), H3))
        elif s.startswith("## "):
            out.append(Paragraph(inline(s[3:]), H2))
        elif s.startswith("# "):
            out.append(Paragraph(inline(s[2:]), H1))
        elif re.match(r"^[-*] ", s):
            out.append(Paragraph(inline(s[2:]), BULLET, bulletText="•"))
        elif re.match(r"^\d+\. ", s):
            out.append(Paragraph(inline(s.split(". ", 1)[1]), BULLET,
                                 bulletText=s.split(".", 1)[0] + "."))
        else:
            out.append(Paragraph(inline(s), BODY))
    return out


def convert(src, out):
    SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=14 * mm, bottomMargin=14 * mm,
                      title="Training and eating plan").build(
        story_from(open(src).read().split("\n")))
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 topdf.py <plan.md> <plan.pdf>")
    print("written to", convert(sys.argv[1], sys.argv[2]))
