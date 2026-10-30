"""量一下某个页面的打印溢出：打印为 PDF 后看第 2 页还有多少内容。"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROFILE = Path(tempfile.gettempdir()) / "chrome_print_profile_measure"
WORK = Path(tempfile.gettempdir()) / "l0_print_measure"


def main(argv: list[str]) -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    for target in argv[1:]:
        html = SITE / target / "index.html"
        pdf = WORK / (target.replace("/", "-") + ".pdf")
        subprocess.run(
            [
                str(CHROME),
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--user-data-dir={0}".format(PROFILE),
                "--virtual-time-budget=5000",
                "--no-pdf-header-footer",
                "--print-to-pdf={0}".format(pdf),
                html.as_uri(),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        doc = pymupdf.open(pdf)
        print("== {0} → {1} 页（页面高 {2:.0f}pt）".format(target, doc.page_count, doc[0].rect.height))
        for index, page in enumerate(doc):
            blocks = [b for b in page.get_text("blocks") if b[4].strip()]
            if not blocks:
                print("   第 {0} 页：空".format(index + 1))
                continue
            top = min(b[1] for b in blocks)
            bottom = max(b[3] for b in blocks)
            used = bottom - top
            print("   第 {0} 页：内容高 {1:.0f}pt（占 {2:.0%}），最后一行：{3}".format(
                index + 1,
                used,
                used / page.rect.height,
                blocks[-1][4].strip().replace("\n", " ")[:40],
            ))
        doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
