"""检查新讲义 PDF：页数 + 首页主色（用于确认各课的视觉基准）。"""

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent

PDFS = [
    "日语/第零课_同一个声音可以怎么写_学生版_v1.pdf",
    "日语/日语第一课_重写版_学生版 (1).pdf",
    "日语/日语第二课_自主生成问题_重写版_v4_学生版.pdf",
    "日语/日语第三课_寻找规律的边界_学生版_v1.pdf",
    "日语/日语第一课_教师版_问题生成与符号交接_v1.pdf",
    "日语/日语第三课_教师版_问题生成与证据检验_v1.pdf",
    "英语/英语第一课_轻松版_学生版.pdf",
    "英语/英语第一课_轻松版_教师版.pdf",
]

for rel in PDFS:
    path = ROOT / rel
    if not path.is_file():
        print("缺失:", rel)
        continue
    doc = pymupdf.open(path)
    page = doc[0]
    colors = {}
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                key = "#%06x" % span["color"]
                colors[key] = colors.get(key, 0) + len(span["text"])
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:5]
    size = page.rect
    print("=" * 60)
    print(rel)
    print("  页数: {0}   首页尺寸: {1:.0f}x{2:.0f} pt".format(
        doc.page_count, size.width, size.height))
    print("  主要文字色: " + ", ".join("{0}({1}字)".format(c, n) for c, n in top))
    fonts = set()
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                fonts.add(span["font"])
    print("  字体: " + ", ".join(sorted(fonts)))
    doc.close()
