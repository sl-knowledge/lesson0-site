"""渲染新讲义 PDF 首页为 PNG，用于比对视觉版式。"""

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "design" / "probe"
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("日语/日语第一课_重写版_学生版 (1).pdf", "jp-l1-p1.png"),
    ("英语/英语第一课_轻松版_学生版.pdf", "en-l1-p1.png"),
    ("英语/英语第一课_轻松版_教师版.pdf", "en-l1-teacher-p1.png"),
]

for rel, name in TARGETS:
    path = ROOT / rel
    doc = pymupdf.open(path)
    pix = doc[0].get_pixmap(dpi=110)
    dest = OUT / name
    pix.save(dest)
    print(rel, "->", dest.name, pix.width, "x", pix.height)
    doc.close()
