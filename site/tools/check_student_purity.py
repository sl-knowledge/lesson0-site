"""检查学生页有没有混入教师后台用语。

教学纪律：学生不应预先看到教师的预设路径、逐级提示与示范答案。

判定方式：
1. 对所有学生页扫描教师侧词汇（教师、预设、分诊、示范、支架…）。
2. 命中后看上下文：能在**学生原稿**里找到的算合法（是原稿自己的话），
   找不到的说明内容串了，报错并返回非零退出码。
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
REPO_ROOT = ROOT.parent

FORBIDDEN = [
    "教师", "不要提前", "预设", "分诊", "示范", "应答", "提示顺序",
    "教学边界", "教师版", "教师用", "逐级提示", "支架", "答案",
]
ALLOW = ["老师"]  # 「我希望 AI／老师帮我做的事」是学生自己的问题

TAG_RE = re.compile(r"<[^>]+>")


def load_sources() -> dict[str, str]:
    """学生原稿全文：导入器 SPECS 里的 source，加上第零课的原始稿。"""
    sources: dict[str, str] = {}
    sys.path.insert(0, str(ROOT / "tools"))
    from import_lessons import SPECS  # noqa: E402

    for spec in SPECS:
        path = REPO_ROOT / spec["source"]
        if path.is_file():
            sources[spec["id"]] = path.read_text(encoding="utf-8")
    zero = REPO_ROOT / "日语" / "第零课_同一个声音可以怎么写_学生版_v1.md"
    if zero.is_file():
        sources["jp-l0"] = zero.read_text(encoding="utf-8")
    return sources


def normalize(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = re.sub(r"[\s`*>#\-—|｜:：]+", "", text)
    return text


def page_content(html: str) -> str:
    """只取正文（.l0-page 容器），排除导航、页脚、翻页条等公共区域。"""
    start = html.find('<div class="l0-page')
    if start < 0:
        return html
    end = html.find("</article>", start)
    body = html[start:end if end > 0 else len(html)]
    pager = body.find('<div class="l0-pager"')
    if pager > 0:
        body = body[:pager]
    return body


def in_source(context: str, source: str) -> bool:
    """上下文（逐级收紧）是否出现在学生原稿里。"""
    for width in (16, 10, 6):
        for start in range(0, max(1, len(context) - width + 1), 4):
            chunk = context[start: start + width * 2 + 4]
            if chunk and normalize(chunk) in source:
                return True
    return False


def student_pages() -> list[Path]:
    pages = []
    for course in ("jp", "en"):
        for overview in (SITE / course).glob("*/index.html"):
            if (overview.parent / "page-1").is_dir():
                pages.append(overview)
                pages.extend(sorted(overview.parent.glob("page-*/index.html")))
    return pages


def lesson_of(path: Path) -> str:
    parts = path.relative_to(SITE).parts
    return parts[0] + "-" + parts[1].replace("page-", "").replace("index", "").rstrip("-") if parts[1].startswith("page-") else parts[0] + "-" + parts[1]


def main() -> int:
    sources = {k: normalize(v) for k, v in load_sources().items()}
    problems = []
    for path in student_pages():
        html = path.read_text(encoding="utf-8")
        raw = page_content(html)
        text = TAG_RE.sub(" ", raw)
        lesson = lesson_of(path)
        source = sources.get(lesson, "")
        for word in FORBIDDEN:
            for hit in re.finditer(re.escape(word), text):
                context = text[max(0, hit.start() - 30): hit.end() + 30].strip()
                if any(ok in context for ok in ALLOW):
                    continue
                if in_source(context, source):
                    continue  # 学生原稿里本来就这么写
                problems.append((path.relative_to(SITE).as_posix(), word, context))

    lines = ["检查 {0} 个学生页".format(len(student_pages()))]
    if not problems:
        lines.append("没有发现教师用语 [OK]")
    else:
        lines.append("发现 {0} 处疑似教师用语：".format(len(problems)))
        for path, word, context in problems:
            lines.append("  {0}  「{1}」  …{2}…".format(path, word, context))
    report = ROOT / "design" / "purity-report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
