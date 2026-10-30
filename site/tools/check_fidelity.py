"""内容完整性检查：学生原稿的每一句话都要出现在对应的页面里。

导入器可能因为正则没覆盖到某种写法而漏掉内容，这里逐句核对。
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
REPO_ROOT = ROOT.parent

TAG_RE = re.compile(r"<[^>]+>")
SKIP_PREFIX = ("<!--", "|---", "---")
PAGE_HEAD_RE = re.compile(r"^#{1,3}\s*第\s*\d+\s*页\s*[｜|：:]\s*")
LIST_MARK_RE = re.compile(r"^([-*]\s+|\d+[.)]\s+)")


def normalize(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = re.sub(r'<span style="[^"]*">', "", text)
    text = re.sub(r"</span>", "", text)
    text = re.sub(r"[\s`*>#\-|｜:：，。、！？「」（）()\[\]_＿□]+", "", text)
    return text


def source_units(path: Path) -> list[str]:
    """原稿里的每个内容单元（按行）。"""
    units = []
    for raw in path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line or line.startswith(SKIP_PREFIX):
            continue
        if set(line) <= set("|:- "):
            continue
        if line.startswith("**中文母语者学习"):
            continue  # 稿件抬头，不进正文
        if line.startswith("# "):
            continue  # 稿件大标题 = 课程名，出现在概览页与导航里
        line = PAGE_HEAD_RE.sub("", line)
        line = LIST_MARK_RE.sub("", line)
        units.append(line)
    return units


def page_text(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    start = html.find('<div class="l0-page')
    end = html.find("</article>", start)
    return normalize(html[start:end])


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    from import_lessons import SPECS  # noqa: E402

    missing_total = 0
    report = []
    for spec in SPECS:
        src = REPO_ROOT / spec["source"]
        if not src.is_file():
            continue
        units = source_units(src)
        pages = sorted((SITE / spec["dir"]).glob("page-*/index.html"))
        blob = "".join(page_text(p) for p in pages)
        missing = []
        for unit in units:
            norm = normalize(unit)
            if not norm:
                continue
            # 长句按片段核对：正文可能把一句话拆成多个块
            if norm in blob:
                continue
            pieces = [norm[i: i + 12] for i in range(0, len(norm), 12)]
            if pieces and all(p in blob for p in pieces if len(p) >= 6):
                continue
            missing.append(unit)
        report.append("{0}: {1} 句原文中 {2} 句未出现在页面里".format(
            spec["id"], len(units), len(missing)))
        for unit in missing:
            report.append("    · {0}".format(unit[:90]))
        missing_total += len(missing)

    report.append("")
    report.append("合计缺失 {0} 句".format(missing_total))
    out = ROOT / "design" / "fidelity-report.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 1 if missing_total else 0


if __name__ == "__main__":
    sys.exit(main())
