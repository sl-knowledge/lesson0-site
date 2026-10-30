"""批量打印所有学生页，检查是否每页正好一张 A4。

用法：python tools/check_print.py [课程目录 ...]
例如：python tools/check_print.py jp/l0 jp/l1
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROFILE = Path(tempfile.gettempdir()) / "chrome_print_profile_batch"


def student_pages(course_dir: str) -> list[Path]:
    base = SITE / course_dir
    return sorted(p for p in base.glob("page-*/index.html"))


def print_page(html: Path, out_pdf: Path) -> int:
    subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--user-data-dir={0}".format(PROFILE),
            "--virtual-time-budget=5000",
            "--no-pdf-header-footer",
            "--print-to-pdf={0}".format(out_pdf),
            html.as_uri(),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    doc = pymupdf.open(out_pdf)
    count = doc.page_count
    doc.close()
    return count


def main(argv: list[str]) -> int:
    courses = argv[1:] or ["jp/l0", "jp/l1", "jp/l2", "jp/l3", "en/l1"]
    work = Path(tempfile.gettempdir()) / "l0_print_batch"
    work.mkdir(parents=True, exist_ok=True)

    bad = []
    total = 0
    for course in courses:
        for html in student_pages(course):
            out_pdf = work / (html.parent.parent.name + "-" + html.parent.name + ".pdf")
            count = print_page(html, out_pdf)
            total += 1
            flag = "OK " if count == 1 else "!! "
            print("{0}{1} → {2} page(s)".format(flag, html.parent.as_posix(), count))
            if count != 1:
                bad.append((html.parent.as_posix(), count))

    print("---")
    print("共 {0} 个学生页；超过一张 A4 的页面：{1}".format(total, len(bad)))
    for path, count in bad:
        print("  {0} → {1} 页".format(path, count))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
