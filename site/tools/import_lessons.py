"""把 ``日语/``、``英语/`` 下的原始讲义 Markdown 导入成站点内容 YAML。

用法::

    python tools/import_lessons.py

导入结果写到 ``content/lessons/*.yaml``。这些 YAML 和其它内容文件一样是站点的
内容真源：导入器负责省掉手工誊抄，重新导入会覆盖同名文件（覆盖前请先备份手改）。

原始稿件里的写法与站点组件的对应关系：

======================================  ====================================
原稿                                     站点组件
======================================  ====================================
``## 第 N 页｜标题``                     一页（页眉 + 标题 + 正文块）
``### 标签 N｜问题``                     问题条（徽章「标签 N」）
``### 第 N 步｜标题``                    步骤条
``### 其它标题``                         小标题
``**标签：** 正文``                      问题条 / 提示框（按标签判定）
``**标签：** ______``                    书写区
``> 引用``                               提示框
``*提示：……*``                          灰色小字提示
``- [ ] 项目``                           勾选清单
``| 表格 |``                             表格
``______``（行内）                        行内空白
``<span style="color:…">字</span>``      彩色强调（``[[g:字]]``）
======================================  ====================================
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent          # site/
REPO_ROOT = ROOT.parent                                 # 仓库根
CONTENT_DIR = ROOT / "content"
OUT_DIR = CONTENT_DIR / "lessons"

# 原始稿件里的彩色强调
SPAN_RE = re.compile(r'<span style="color:(#[0-9a-fA-F]{6}); font-weight:bold">(.*?)</span>')
COLOR_TOKEN = {"#008577": "g", "#b96112": "a", "#236baa": "b"}

PAGE_RE = re.compile(r"^##\s*第\s*(\d+)\s*页\s*[｜|：:]\s*(.+?)\s*$")
HEADING3_RE = re.compile(r"^###\s+(.+?)\s*$")
BOLD_LABEL_RE = re.compile(r"^\*\*([^*]+?)\*\*\s*[：:]?\s*(.*)$")
STEP_RE = re.compile(r"^第\s*(\d+)\s*步\s*[｜|：:]\s*(.+)$")
LABEL_NUM_RE = re.compile(r"^(.+?)\s*(\d+)\s*[｜|：:]\s*(.+)$")
LABEL_TEXT_RE = re.compile(r"^(.+?)\s*[｜|：:]\s*(.+)$")
BLANK_ONLY_RE = re.compile(r"^[\s]*[＿_]{3,}[\s]*$")
WRITE_LINE_RE = re.compile(r"^(.{0,24}?[：:])\s*[＿_]{3,}\s*$")
ORDERED_RE = re.compile(r"^\d+[.)]\s+")
CHECK_RE = re.compile(r"^-\s*\[[ xX]\]\s+")

# 会渲染成「问题条」的小标题标签
QUESTION_LABELS = {
    "想一想", "动手", "发现", "预测", "回顾", "好奇", "小问题", "最后一个小问题",
    "观察", "整理", "归纳", "问题", "你的问题", "追问", "猜想", "理由", "核对",
    "设计", "判断", "修正", "我的问题", "我的检验", "我的新问题", "再想一步",
    "我的主动问题", "我的暂时结论",
}
# 行内加粗标签：属于这些的一律是「问题条」，其余是「提示框」
QUESTION_BOLD = {
    "问题", "观察", "你的问题", "追问", "猜想", "理由", "核对", "设计", "判断",
    "修正", "我的问题", "我的检验", "我的新问题", "整理", "归纳", "再想一步",
    "我的主动问题", "我的暂时结论", "小问题", "最后一个小问题",
    "预测", "依据", "回顾", "好奇", "发现", "翻页之前，再问自己一句",
}

SPECS = [
    {
        "id": "jp-l1",
        "course": "jp",
        "course_label": "日语",
        "lesson_label": "第一课",
        "title": "第一课 · 一句话，为什么能有不同说法？",
        "pager": "一句话，为什么能有不同说法？",
        "dir": "jp/l1",
        "source": "日语/日语第一课_重写版_学生版.md",
        "teacher_source": "日语/日语第一课_教师版_问题生成与符号交接_v1.md",
        "teacher_title": "第一课 · 教师用：认知衔接、符号交接与自主问题生成",
        "pdf": "assets/downloads/lesson1-jp-student-v1.pdf",
        "pdf_label": "下载学生版 PDF（A4 · 4 页）",
    },
    {
        "id": "jp-l2",
        "course": "jp",
        "course_label": "日语",
        "lesson_label": "第二课",
        "title": "第二课 · 你发现了一个新问题吗？",
        "pager": "你发现了一个新问题吗？",
        "dir": "jp/l2",
        "source": "日语/日语第二课_自主生成问题_重写版_v4_学生版.md",
        "teacher_source": "日语/日语第二课_教师版_问题生成与分级支架_v4.md",
        "teacher_title": "第二课 · 教师用：学生自主问题生成与分级支架",
        "pdf": "assets/downloads/lesson2-jp-student-v4.pdf",
        "pdf_label": "下载学生版 PDF（A4 · 6 页）",
    },
    {
        "id": "jp-l3",
        "course": "jp",
        "course_label": "日语",
        "lesson_label": "第三课",
        "title": "第三课 · 看起来很像，就一定按同一条规则变化吗？",
        "pager": "看起来很像，就一定同一条规则吗？",
        "dir": "jp/l3",
        "source": "日语/日语第三课_寻找规律的边界_学生版_v1.md",
        "teacher_source": "日语/日语第三课_教师版_问题生成与证据检验_v1.md",
        "teacher_title": "第三课 · 教师用：从相似处找规律，也要检验边界",
        "pdf": "assets/downloads/lesson3-jp-student-v1.pdf",
        "pdf_label": "下载学生版 PDF（A4 · 6 页）",
    },
    {
        "id": "en-l1",
        "course": "en",
        "course_label": "英语",
        "lesson_label": "英语第一课",
        "title": "英语第一课 · 按中文的方式写英语，会丢掉什么？",
        "pager": "按中文的方式写英语，会丢掉什么？",
        "dir": "en/l1",
        "source": "英语/英语第一课_v2_学生版.md",
        "teacher_source": "英语/英语第一课_v2_教师版.md",
        "teacher_title": "英语第一课 · 教师用：按中文的方式写英语，会丢掉什么？",
        "pdf": "assets/downloads/lesson1-en-student-v2.pdf",
        "pdf_label": "下载学生版 PDF（A4 · 4 页）",
    },
]


# --------------------------------------------------------------------------- #
# 文本清洗
# --------------------------------------------------------------------------- #
def clean(text: str) -> str:
    """原稿 → 站点行内标记。"""
    text = SPAN_RE.sub(
        lambda m: "[[{0}:{1}]]".format(COLOR_TOKEN.get(m.group(1).lower(), "g"), m.group(2)),
        text,
    )
    text = re.sub(r"_{3,}", "[[blank]]", text)
    text = re.sub(r"[ \t]+$", "", text)
    return text.strip()


def short_title(title: str, limit: int = 14) -> str:
    """翻页条用的短标题。"""
    title = title.strip()
    if len(title) <= limit:
        return title
    for sep in ("？", "。", "，", "：", "；"):
        if sep in title:
            head = title.split(sep)[0]
            if len(head) >= 6:
                return head
    return title[:limit] + "…"


def is_block_start(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if s.startswith(("#", "|", ">", "-", "*")):
        return True
    if ORDERED_RE.match(s):
        return True
    return False


# --------------------------------------------------------------------------- #
# 块级解析
# --------------------------------------------------------------------------- #
def parse_table(lines: list[str]) -> dict:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # 对齐行
        rows.append([clean(c) for c in cells])
    headers = rows[0] if rows else []
    body = rows[1:] if len(rows) > 1 else []
    block = {"type": "table", "rows": body}
    if headers:
        block["headers"] = headers
    return block


def note_from_quote(quote: list[str]) -> dict:
    """引用块 → 提示框（首行若是加粗小标题则作为标题）。"""
    parts = []
    for line in quote:
        if not line.strip():
            parts.append("\n")
        else:
            parts.append(line + " ")
    text = "".join(parts).strip()
    title = ""
    m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", text)
    if m:
        title = clean(m.group(1))
        text = clean(m.group(2))
    else:
        text = clean(text)
    return {"type": "note", "tone": "green", "title": title, "text": text}


def split_label(label: str) -> tuple[str, str]:
    """「观察 3」→ ("观察", "3")。"""
    m = re.match(r"^(.+?)\s*(\d+)$", label.strip())
    if m:
        return m.group(1).strip(), m.group(2)
    return label.strip(), ""


def heading3_block(text: str) -> dict:
    """``### 标题`` → 问题条 / 步骤条 / 小标题。"""
    m = STEP_RE.match(text)
    if m:
        return {"type": "step", "label": "第 {0} 步".format(m.group(1)), "title": clean(m.group(2))}
    m = LABEL_NUM_RE.match(text)
    if m and m.group(1).strip() in QUESTION_LABELS:
        return {
            "type": "question",
            "label": m.group(1).strip(),
            "num": m.group(2),
            "text": clean(m.group(3)),
        }
    m = LABEL_TEXT_RE.match(text)
    if m and m.group(1).strip() in QUESTION_LABELS:
        return {"type": "question", "label": m.group(1).strip(), "text": clean(m.group(2))}
    return {"type": "label", "text": clean(text)}


def bold_label_block(label: str, rest: str) -> dict:
    """``**标签：** 正文`` → 书写区 / 提问行 / 提示框。"""
    label = label.strip()
    if BLANK_ONLY_RE.match(rest or ""):
        return {"type": "write", "label": clean(label) + "：", "lines": 1}
    base, num = split_label(label)
    if base in QUESTION_BOLD:
        # 原稿里这些是「行内粗体标签 + 问题」：观察 3：…
        return {"type": "ask", "label": clean(label), "text": clean(rest)}
    if "□" in rest:
        items = [clean(x) for x in re.split(r"□", rest) if x.strip()]
        return {
            "type": "list",
            "marker": "checkbox",
            "label": clean(label) + "：",
            "items": items,
        }
    return {"type": "note", "tone": "green", "title": clean(label), "text": clean(rest)}


def convert_blocks(lines: list[str], mode: str) -> list[dict]:
    """把一页的原始行转成内容块。``mode`` 为 student / teacher。"""
    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not s or s == "---" and False:
            i += 1
            continue
        if s == "---":
            blocks.append({"type": "hr"})
            i += 1
            continue
        if s.startswith("<!--"):
            i += 1
            continue

        # 表格
        if s.startswith("|"):
            chunk = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                chunk.append(lines[i])
                i += 1
            blocks.append(parse_table(chunk))
            continue

        # 引用
        if s.startswith(">"):
            chunk = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                chunk.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(note_from_quote(chunk))
            continue

        # 一级标题：稿件大标题，页面已经有自己的标题，跳过
        if s.startswith("# "):
            i += 1
            continue

        # 三级标题
        if s.startswith("### "):
            text = s[4:].strip()
            if mode == "teacher":
                blocks.append({"type": "heading", "level": 3, "text": clean(text)})
            else:
                blocks.append(heading3_block(text))
            i += 1
            continue

        # 二级标题（教师稿）
        if s.startswith("## "):
            blocks.append({"type": "heading", "level": 2, "text": clean(s[3:].strip())})
            i += 1
            continue

        # 勾选清单
        if CHECK_RE.match(s):
            items = []
            while i < len(lines) and CHECK_RE.match(lines[i].strip()):
                items.append(clean(CHECK_RE.sub("", lines[i].strip())))
                i += 1
            blocks.append({"type": "list", "marker": "checkbox", "items": items})
            continue

        # 无序列表
        if s.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(clean(lines[i].strip()[2:]))
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        # 有序列表
        if ORDERED_RE.match(s):
            items = []
            while i < len(lines) and ORDERED_RE.match(lines[i].strip()):
                items.append(clean(ORDERED_RE.sub("", lines[i].strip())))
                i += 1
            blocks.append({"type": "list", "marker": "ordered", "items": items})
            continue

        # 行内加粗标签
        m = BOLD_LABEL_RE.match(s)
        if m:
            label, rest = m.group(1), m.group(2).strip()
            if not label.endswith(("：", ":")):
                base = label.strip()
                if base not in QUESTION_BOLD:
                    # 不是「标签：」形式，整段当作加粗正文
                    blocks.append({"type": "para", "text": clean(s)})
                    i += 1
                    continue
                label = base
                rest = rest
            else:
                label = label.rstrip("：:")
            if mode == "teacher":
                blocks.append({"type": "para", "text": "**{0}：** {1}".format(label, clean(rest))})
            else:
                blocks.append(bold_label_block(label, rest))
            i += 1
            continue

        # 灰色小字提示
        if s.startswith("*") and s.endswith("*") and not s.startswith("**") and len(s) > 2:
            blocks.append({"type": "hint", "text": clean(s.strip("*"))})
            i += 1
            continue

        # 整行只有「标签 + 空白」→ 书写区
        m = WRITE_LINE_RE.match(s)
        if m:
            blocks.append({"type": "write", "label": clean(m.group(1)), "lines": 1})
            i += 1
            continue

        # 整行只有横线 → 一条书写线
        if re.fullmatch(r"[\s_＿]{3,}", s):
            blocks.append({"type": "write", "label": "", "lines": 1})
            i += 1
            continue

        # 普通段落（可能跨行；行尾两个空格是原稿里的硬换行）
        para = []
        while i < len(lines) and not is_block_start(lines[i]):
            para.append(lines[i].rstrip())
            i += 1
        if not para:
            para = [s]
            i += 1
        parts = []
        for line in para:
            if line.endswith("  "):
                parts.append(line.rstrip() + "\n")
            else:
                parts.append(line + " ")
        text = clean("".join(parts))
        if text.endswith(("：", ":")) and len(text) <= 16 and mode == "student":
            blocks.append({"type": "label", "text": text})
        else:
            blocks.append({"type": "para", "text": text})

    return blocks


# --------------------------------------------------------------------------- #
# 分页
# --------------------------------------------------------------------------- #
def split_pages(text: str) -> tuple[list[str], list[tuple[int, str, list[str]]]]:
    """把原稿切成 (前言行, [(页码, 页标题, 页内行)])。"""
    lines = text.replace("\r\n", "\n").split("\n")
    intro: list[str] = []
    pages: list[tuple[int, str, list[str]]] = []
    current: list[str] | None = None
    title = ""
    num = 0

    for line in lines:
        m = PAGE_RE.match(line.strip())
        if m:
            if current is not None:
                pages.append((num, title, current))
            num = int(m.group(1))
            title = m.group(2).strip()
            current = []
            continue
        if current is None:
            intro.append(line)
        else:
            current.append(line)
    if current is not None:
        pages.append((num, title, current))
    return intro, pages


def is_doc_meta(block: dict) -> bool:
    """文档大标题与「中文母语者学习…」这类说明行不属于正文。"""
    if block.get("type") != "para":
        return False
    text = block.get("text", "")
    return text.startswith("# ") or text.startswith("**中文母语者学习")


def import_student(spec: dict) -> dict:
    source = REPO_ROOT / spec["source"]
    text = source.read_text(encoding="utf-8")
    intro, pages = split_pages(text)

    # 前言里的引文属于第 1 页的引子
    intro_blocks = [b for b in convert_blocks(intro, "student") if not is_doc_meta(b)]

    out_pages = []
    for index, (num, title, lines) in enumerate(pages, start=1):
        blocks = convert_blocks(lines, "student")
        if index == 1:
            blocks = intro_blocks + blocks
        out_pages.append(
            {
                "file": "{0}/page-{1}.md".format(spec["dir"], num),
                "title": title,
                "head": "{0} · {1}".format(spec["lesson_label"], title),
                "blocks": blocks,
                "pager": short_title(title),
            }
        )

    total = len(out_pages)
    overview_blocks = [
        {
            "type": "note",
            "title": "怎么用",
            "text": "**每一页都先写下自己的想法，再翻到下一页。** 空白处不是装饰，是这一课真正要产出的东西：你的问题，和你打算怎么检验它。",
        },
        {
            "type": "pagelist",
            "items": [
                {
                    "num": str(index),
                    "title": short_title(page["title"]),
                    "desc": "",
                    "to": page["file"],
                }
                for index, page in enumerate(out_pages, start=1)
            ],
        },
        {
            "type": "download",
            "tone": "amber",
            "title": "打印版",
            "text": "同一份讲义另有可打印的 PDF（A4，{0} 页）。浏览器里直接打印也可以，页面已按讲义排版。作者 SL，内容以 CC BY-NC-SA 4.0 授权。{1}".format(
                total, spec.get("print_note", "")
            ),
            "to": spec["pdf"],
            "label": spec["pdf_label"],
        },
        {"type": "hr"},
        {"type": "foot", "text": "{0} · 学生讲义 v1 · 中文母语者学习{1} · 作者 SL".format(
            spec["title"], spec["course_label"])},
    ]

    return {
        "id": spec["id"],
        "course": spec["course"],
        "title": spec["title"],
        "overview": {
            "title": "{0} · 学生版 · 概览与用法".format(spec["lesson_label"]),
            "lead": "共 {0} 页，每页一个观察。这一课不背词条：先写下自己的想法，再翻到下一页核对。".format(total),
            "blocks": overview_blocks,
        },
        "pages": out_pages,
    }


def import_teacher(spec: dict) -> dict:
    source = REPO_ROOT / spec["teacher_source"]
    text = source.read_text(encoding="utf-8")
    lines = text.replace("\r\n", "\n").split("\n")

    blocks = convert_blocks(lines, "teacher")
    blocks = [
        {
            "type": "banner",
            "tone": "teacher",
            "title": "仅教师使用 · 请勿投屏或分发本页链接",
            "text": "本页包含预设教学路径、逐级提示与示范答案。站点是纯静态页面，没有访问控制：请不要向学生投屏此页，也不要把本页链接发给学生。",
        }
    ] + blocks

    return {
        "id": spec["id"],
        "title": spec["teacher_title"],
        "file": "teacher/{0}.md".format(spec["id"]),
        "lead": "这一页是{0}的教师后台：预设路径、逐级提示与示范答案。学生不应预先看到本页内容。".format(spec["lesson_label"]),
        "blocks": blocks,
    }


def dump(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 本文件由 tools/import_lessons.py 从 {0} 自动生成，可手工修改。\n".format(
            "原始讲义 Markdown"))
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, width=100)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        student = import_student(spec)
        teacher = import_teacher(spec)
        dump(student, OUT_DIR / "{0}.yaml".format(spec["id"]))
        dump(teacher, OUT_DIR / "{0}-teacher.yaml".format(spec["id"]))
        print("[import] {0}: {1} 个学生页 + 1 个教师页".format(spec["id"], len(student["pages"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
