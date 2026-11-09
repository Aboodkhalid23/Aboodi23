#!/usr/bin/env python3
"""يحوّل سكربت (عنوان + هوك + سكربت) لملف وورد عربي من اليمين لليسار، بخط كبير يتقرا بسهولة.

الاستخدام:
    python3 scripts/make-docx.py <ملف السكربت.md>   # يطلّع نفس الاسم بس .docx جنبه

الملف يتحمّل من گوگل درايف وينفتح بأي جهاز (آيباد، موبايل، وورد، برامج التلقين).
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

HEADINGS = ("الهوك", "السكربت")


def rtl(paragraph, size, bold=False):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.space_after = Pt(size * 0.6)
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
    for run in paragraph.runs:
        run.bold = bold
        run.font.size = Pt(size)
        rpr = run._r.get_or_add_rPr()
        rpr.append(OxmlElement("w:rtl"))
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        fonts.set(qn("w:cs"), "Arial")
        cs = OxmlElement("w:szCs")
        cs.set(qn("w:val"), str(size * 2))
        rpr.append(cs)
        if bold:
            rpr.append(OxmlElement("w:bCs"))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    doc = Document()
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("العنوان"):
            rtl(doc.add_paragraph(line), 22, bold=True)
        elif line in HEADINGS:
            rtl(doc.add_paragraph(line), 20, bold=True)
        else:
            rtl(doc.add_paragraph(line), 18)
    out = src.with_suffix(".docx")
    doc.save(out)
    print(out)


if __name__ == "__main__":
    main()
