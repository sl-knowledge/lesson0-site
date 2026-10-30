"""YAML → Markdown 生成器。

内容真源是 ``content/*.yaml``；本脚本把它们渲染成 ``docs/`` 下的 Markdown，
再由 MkDocs 构建成静态站点。

约定
----
1. 每个页面都带 YAML front matter（``title``），保证 MkDocs 能正确提取页面标题。
2. 组件一律输出静态 HTML，配合 ``docs/assets/stylesheets/extra.css`` 呈现；
   需要进入目录（TOC）的标题使用 Markdown 二级/三级标题。
3. 站内链接由本脚本按 MkDocs 的 ``use_directory_urls: true`` 规则计算相对 URL。
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
DOCS_DIR = ROOT / "docs"

# 讲义配色：墨绿（主）/ 平假名蓝 / 片假名琥珀
TONE_CLASS = {
    "ink": "l0-t-ink",
    "blue": "l0-t-blue",
    "amber": "l0-t-amber",
    "muted": "l0-t-muted",
}

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_STRONG_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_ITALIC_RE = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")
# 行内彩色强调：[[g:が]] / [[a:を]] / [[b:き]]
_COLOR_RE = re.compile(r"\[\[([gab]):([^\[\]]+)\]\]")
COLOR_CLASS = {"g": "l0-t-ink", "a": "l0-t-amber", "b": "l0-t-blue"}
# 行内空白：[[blank]]
_BLANK_RE = re.compile(r"\[\[blank\]\]")


# --------------------------------------------------------------------------- #
# 行内格式化
# --------------------------------------------------------------------------- #
def inline(text: Any) -> str:
    """把行内 Markdown（粗体、斜体、代码、链接、彩色强调、空白）转成 HTML 片段。"""
    if text is None:
        return ""
    s = html.escape(str(text), quote=False)
    s = _STRONG_RE.sub(r"<strong>\1</strong>", s)
    s = _CODE_RE.sub(r"<code>\1</code>", s)
    s = _LINK_RE.sub(r'<a href="\2">\1</a>', s)
    s = _COLOR_RE.sub(
        lambda m: '<span class="{cls}">{text}</span>'.format(
            cls=COLOR_CLASS.get(m.group(1), "l0-t-ink"), text=m.group(2)
        ),
        s,
    )
    s = _BLANK_RE.sub('<span class="l0-blank"></span>', s)
    s = _ITALIC_RE.sub(r"<em>\1</em>", s)
    return s


def dest_dir(to_file: str) -> str:
    """源文件在 _site 中对应的目录（``use_directory_urls: true``）。

    ``student/page-1.md`` → ``student/page-1``；``student/index.md`` → ``student``。
    """
    path = PurePosixPath(to_file)
    if path.name == "index.md":
        parent = path.parent.as_posix()
        return parent if parent != "." else "."
    return path.with_suffix("").as_posix()


def rel_url(from_file: str, to_file: str) -> str:
    """计算两个页面之间的相对 URL（相对各自在 _site 中的实际位置）。"""
    from_dir = dest_dir(from_file)
    to_dir = dest_dir(to_file)
    rel = os.path.relpath(to_dir, from_dir).replace("\\", "/")
    return rel if rel.endswith("/") else rel + "/"


def asset_url(from_file: str, asset_path: str) -> str:
    """计算静态文件（PDF 等）的相对 URL。"""
    from_dir = dest_dir(from_file)
    return os.path.relpath(asset_path, from_dir).replace("\\", "/")


# --------------------------------------------------------------------------- #
# 组件
# --------------------------------------------------------------------------- #
def render_big(item: dict) -> str:
    """卡片主文字；支持按字符分色（汉字墨绿 / 平假名蓝 / 片假名琥珀）。"""
    if item.get("parts"):
        return "".join(
            '<span class="{cls}">{text}</span>'.format(
                cls=TONE_CLASS.get(part.get("c", "ink"), TONE_CLASS["ink"]),
                text=inline(part.get("t", "")),
            )
            for part in item["parts"]
        )
    accent = item.get("accent", "ink")
    return '<span class="{cls}">{text}</span>'.format(
        cls=TONE_CLASS.get(accent, TONE_CLASS["ink"]), text=inline(item.get("big", ""))
    )


def render_card(item: dict) -> str:
    cls = ["l0-card"]
    if item.get("tone"):
        cls.append("l0-card--" + item["tone"])
    if item.get("span"):
        cls.append("l0-card--span-%d" % item["span"])
    parts = ['<div class="{cls}">'.format(cls=" ".join(cls))]
    if item.get("big") or item.get("parts"):
        parts.append('<div class="l0-card__big">{0}</div>'.format(render_big(item)))
    if item.get("reading"):
        rcls = "l0-card__reading"
        if item.get("reading_tone"):
            rcls += " l0-card__reading--" + item["reading_tone"]
        parts.append('<div class="{cls}">{text}</div>'.format(cls=rcls, text=inline(item["reading"])))
    if item.get("label"):
        parts.append('<div class="l0-card__label">{text}</div>'.format(text=inline(item["label"])))
    parts.append("</div>")
    return "".join(parts)


def render_cards(block: dict, ctx: dict = None) -> str:
    items = block.get("items", [])
    cols = block.get("cols") or min(len(items), 3)
    out = []
    if block.get("panel"):
        out.append('<div class="l0-panel">')
    out.append('<div class="l0-cards l0-cards--{n}">'.format(n=cols))
    out.extend(render_card(item) for item in items)
    out.append("</div>")
    if block.get("caption"):
        out.append('<p class="l0-caption">{0}</p>'.format(inline(block["caption"])))
    if block.get("panel"):
        out.append("</div>")
    return "\n".join(out)


def render_hero(block: dict, ctx: dict = None) -> str:
    tone = block.get("tone", "blue")
    out = ['<div class="l0-hero l0-hero--{0}">'.format(tone)]
    out.append('<div class="l0-hero__big">{0}</div>'.format(render_big(block)))
    if block.get("reading"):
        rcls = "l0-hero__reading"
        if block.get("reading_tone"):
            rcls += " l0-hero__reading--" + block["reading_tone"]
        out.append('<div class="{cls}">{text}</div>'.format(cls=rcls, text=inline(block["reading"])))
    if block.get("caption"):
        out.append('<div class="l0-hero__cap">{0}</div>'.format(inline(block["caption"])))
    out.append("</div>")
    return "\n".join(out)


def render_question(block: dict, ctx: dict = None) -> str:
    label = block.get("label", "问题")
    badge = "{0} {1}".format(label, block["num"]) if block.get("num") else label
    return (
        '<div class="l0-q"><span class="l0-badge">{badge}</span>'
        '<span class="l0-q__text">{text}</span></div>'
    ).format(badge=inline(badge), text=inline(block.get("text", "")))


def render_write(block: dict, ctx: dict = None) -> str:
    if block.get("box"):
        out = ['<div class="l0-write l0-write--box">']
        if block.get("label"):
            if block.get("inline"):
                out.append(
                    '<div class="l0-write__label">{0}<span class="l0-write__rule"></span></div>'.format(
                        inline(block["label"])
                    )
                )
            else:
                out.append('<div class="l0-write__label">{0}</div>'.format(inline(block["label"])))
        out.append(render_rules(block.get("lines", 1)))
        out.append("</div>")
        return "\n".join(out)

    # 无边框的书写区：标签与横线同一行，和讲义原稿一致
    out = []
    lines = max(1, int(block.get("lines", 1)))
    if block.get("label"):
        out.append(
            '<div class="l0-write__label l0-write__label--inline">{0}'
            '<span class="l0-write__rule"></span></div>'.format(inline(block["label"]))
        )
        if lines > 1:
            out.append(render_rules(lines - 1))
        return "\n".join(out)
    out.append(render_rules(lines))
    return "\n".join(out)


def render_rules(lines: int) -> str:
    rules = "".join('<hr class="l0-rule">' for _ in range(max(1, int(lines))))
    return '<div class="l0-rules">{0}</div>'.format(rules)


def render_note(block: dict, ctx: dict = None) -> str:
    tone = block.get("tone", "green")
    out = ['<div class="l0-note l0-note--{0}">'.format(tone)]
    if block.get("title"):
        out.append('<p class="l0-note__title">{0}</p>'.format(inline(block["title"])))
    if block.get("text"):
        out.append('<p>{0}</p>'.format(inline(block["text"])))
    out.append("</div>")
    return "\n".join(out)


def render_ask(block: dict, ctx: dict = None) -> str:
    """行内粗体标签 + 问题：原稿里「观察 3：……」的写法。"""
    return '<p class="l0-ask"><span class="l0-ask__label">{0}</span> {1}</p>'.format(
        inline(block.get("label", "")), inline(block.get("text", ""))
    )


def render_label(block: dict, ctx: dict = None) -> str:
    """小标题：一段内容的引导句，如「再观察：」。"""
    return '<p class="l0-label">{0}</p>'.format(inline(block.get("text", "")))


def render_step(block: dict, ctx: dict = None) -> str:
    """步骤条：徽章 + 标题，如「第 2 步 · 换个角度想一想」。"""
    out = ['<p class="l0-step"><span class="l0-badge">{0}</span>'.format(inline(block.get("label", "")))]
    if block.get("title"):
        out.append('<span class="l0-step__title">{0}</span>'.format(inline(block["title"])))
    out.append("</p>")
    return "".join(out)


def render_hint(block: dict, ctx: dict = None) -> str:
    """灰色小字提示。"""
    return '<p class="l0-hint">{0}</p>'.format(inline(block.get("text", "")))


def render_admonition(block: dict, ctx: dict = None) -> str:
    kind = block.get("kind", "note")
    out = ['<div class="l0-adm l0-adm--{0}">'.format(kind)]
    if block.get("title"):
        out.append('<p class="l0-adm__title">{0}</p>'.format(inline(block["title"])))
    out.append('<p>{0}</p>'.format(inline(block.get("text", ""))))
    out.append("</div>")
    return "\n".join(out)


def render_banner(block: dict, ctx: dict = None) -> str:
    tone = block.get("tone", "teacher")
    out = ['<div class="l0-banner l0-banner--{0}">'.format(tone)]
    if block.get("title"):
        out.append('<p class="l0-banner__title">{0}</p>'.format(inline(block["title"])))
    out.append('<p class="l0-banner__text">{0}</p>'.format(inline(block.get("text", ""))))
    out.append("</div>")
    return "\n".join(out)


def cell_html(cell: Any, ctx: dict = None) -> str:
    ctx = ctx or {}
    """表格 / 列表单元格：字符串走行内格式化；字典支持站内链接 {to, text}。"""
    if isinstance(cell, dict):
        text = cell.get("text") or cell.get("title") or ""
        if cell.get("to"):
            href = rel_url(ctx["file"], cell["to"])
            return '<a href="{href}">{text}</a>'.format(href=href, text=inline(text))
        return inline(text)
    return inline(cell)


def render_list(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    items = block.get("items", [])
    cls = "l0-list"
    tag = "ul"
    marker = block.get("marker")
    if marker == "checkbox":
        cls += " l0-list--check"
    elif marker == "ordered":
        cls += " l0-list--ordered"
        tag = "ol"
    out = ['<{tag} class="{cls}">'.format(tag=tag, cls=cls)]
    if block.get("label"):
        out.append('<span class="l0-list__label">{0}</span>'.format(inline(block["label"])))
    out.extend("<li>{0}</li>".format(cell_html(item, ctx)) for item in items)
    out.append("</{0}>".format(tag))
    return "\n".join(out)


def render_table(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    headers = block.get("headers", [])
    rows = block.get("rows", [])
    out = []
    if block.get("caption"):
        out.append('<p class="l0-table__caption">{0}</p>'.format(inline(block["caption"])))
    out.append('<div class="l0-tablewrap"><table class="l0-table">')
    if headers:
        out.append("<thead><tr>")
        out.extend("<th>{0}</th>".format(inline(h)) for h in headers)
        out.append("</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        out.append("<tr>")
        out.extend("<td>{0}</td>".format(cell_html(cell, ctx)) for cell in row)
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_pagehead(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    total = ctx.get("total", "")
    index = ctx.get("index", "")
    return (
        '<div class="l0-pagehead"><span class="l0-pagehead__title">{0}</span>'
        '<span class="l0-pagehead__num">{1} / {2}</span></div>'
    ).format(inline(block.get("title", "")), index, total)


def render_para(block: dict, ctx: dict = None) -> str:
    cls = "l0-lead" if block.get("lead") else "l0-para"
    return '<p class="{0}">{1}</p>'.format(cls, inline(block.get("text", "")))


def render_heading(block: dict, ctx: dict = None) -> str:
    """Markdown 二级/三级标题：进入站点目录（TOC）。"""
    level = int(block.get("level", 2))
    return "{0} {1}".format("#" * level, str(block.get("text", "")).strip())


def render_md(block: dict, ctx: dict = None) -> str:
    return str(block.get("text", "")).strip()


def render_hr(block: dict, ctx: dict = None) -> str:
    return '<hr class="l0-hr">'


def render_foot(block: dict, ctx: dict = None) -> str:
    return '<p class="l0-foot">{0}</p>'.format(inline(block.get("text", "")))


def render_linkcard(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    href = rel_url(ctx["file"], block["to"])
    return (
        '<a class="l0-linkcard" href="{href}">'
        '<span class="l0-linkcard__eyebrow">{eyebrow}</span>'
        '<span class="l0-linkcard__title">{title}</span>'
        '<span class="l0-linkcard__desc">{desc}</span>'
        "</a>"
    ).format(
        href=href,
        eyebrow=inline(block.get("eyebrow", "")),
        title=inline(block.get("title", "")),
        desc=inline(block.get("desc", "")),
    )


def render_pagelist(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    items = block.get("items", [])
    out = ['<div class="l0-pagelist">']
    for item in items:
        href = rel_url(ctx["file"], item["to"])
        out.append(
            '<a class="l0-pagelist__item" href="{href}">'
            '<span class="l0-pagelist__num">{num}</span>'
            '<span class="l0-pagelist__body">'
            '<span class="l0-pagelist__title">{title}</span>'
            '<span class="l0-pagelist__desc">{desc}</span>'
            "</span></a>".format(
                href=href,
                num=inline(item.get("num", "")),
                title=inline(item.get("title", "")),
                desc=inline(item.get("desc", "")),
            )
        )
    out.append("</div>")
    return "\n".join(out)


def render_cover(block: dict, ctx: dict = None) -> str:
    out = ['<div class="l0-cover">']
    if block.get("eyebrow"):
        out.append('<p class="l0-cover__eyebrow">{0}</p>'.format(inline(block["eyebrow"])))
    out.append('<h1 class="l0-cover__title">{0}</h1>'.format(inline(block.get("title", ""))))
    if block.get("lead"):
        out.append('<p class="l0-cover__lead">{0}</p>'.format(inline(block["lead"])))
    out.append("</div>")
    return "\n".join(out)


def render_download(block: dict, ctx: dict = None) -> str:
    """可下载文件（如打印版 PDF）的提示块，链接按页面位置自动计算。"""
    ctx = ctx or {}
    href = asset_url(ctx.get("file", "index.md"), block["to"])
    out = ['<div class="l0-note l0-note--{0}">'.format(block.get("tone", "amber"))]
    if block.get("title"):
        out.append('<p class="l0-note__title">{0}</p>'.format(inline(block["title"])))
    if block.get("text"):
        out.append('<p>{0}</p>'.format(inline(block["text"])))
    out.append(
        '<p><a class="l0-btn l0-btn--small" href="{href}">{label}</a></p>'.format(
            href=href, label=inline(block.get("label", "下载"))
        )
    )
    out.append("</div>")
    return "\n".join(out)


def render_buttons(block: dict, ctx: dict = None) -> str:
    ctx = ctx or {}
    out = ['<div class="l0-buttons">']
    for btn in block.get("items", []):
        if btn.get("asset"):
            href = asset_url(ctx.get("file", "index.md"), btn["to"])
        elif btn.get("to"):
            href = rel_url(ctx.get("file", "index.md"), btn["to"])
        else:
            href = btn.get("url", "#")
        cls = "l0-btn"
        if btn.get("primary"):
            cls += " l0-btn--primary"
        if btn.get("warn"):
            cls += " l0-btn--warn"
        out.append(
            '<a class="{cls}" href="{href}">{text}</a>'.format(
                cls=cls, href=href, text=inline(btn.get("text", ""))
            )
        )
    out.append("</div>")
    return "\n".join(out)


RENDERERS = {
    "cards": render_cards,
    "hero": render_hero,
    "question": render_question,
    "write": render_write,
    "note": render_note,
    "admonition": render_admonition,
    "banner": render_banner,
    "list": render_list,
    "table": render_table,
    "pagehead": render_pagehead,
    "para": render_para,
    "md": render_md,
    "hr": render_hr,
    "foot": render_foot,
    "heading": render_heading,
    "h2": lambda b, c: render_heading(dict(b, level=2)),
    "h3": lambda b, c: render_heading(dict(b, level=3)),
    "linkcard": render_linkcard,
    "pagelist": render_pagelist,
    "buttons": render_buttons,
    "download": render_download,
    "cover": lambda b, c: render_cover(b, c),
    "label": render_label,
    "ask": render_ask,
    "step": render_step,
    "hint": render_hint,
}


def render_blocks(blocks: list[dict], ctx: dict) -> list[str]:
    chunks: list[str] = []
    for block in blocks or []:
        kind = block.get("type")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            raise ValueError("未知的内容块类型：{0}".format(kind))
        chunks.append(renderer(block, ctx))
    return chunks


# --------------------------------------------------------------------------- #
# 页面
# --------------------------------------------------------------------------- #
def front_matter(title: str, extra: dict | None = None) -> str:
    meta = {"title": title}
    meta.update(extra or {})
    body = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    return "---\n{0}\n---".format(body)


def page_document(title: str, chunks: list[str], source: str) -> str:
    parts = [front_matter(title), "<!-- 本文件由 tools/build_content.py 从 {0} 自动生成，请勿直接编辑。 -->".format(source)]
    parts.extend(chunk for chunk in chunks if chunk.strip())
    return "\n\n".join(parts) + "\n"


def wrap_page(inner: list[str], extra_class: str = "") -> str:
    """把页面内容包进带 markdown="1" 的容器：容器内既有静态 HTML 组件，
    也有 Markdown 标题（进入站点目录）。"""
    cls = "l0-page" + ((" " + extra_class) if extra_class else "")
    body = "\n\n".join(chunk for chunk in inner if chunk.strip())
    return '<div class="{cls}" markdown="1">\n\n{body}\n\n</div>'.format(cls=cls, body=body)


def render_student_page(page: dict, ctx: dict, pages: list[dict], index: int) -> str:
    title = page["title"]
    inner: list[str] = [render_pagehead({"title": page.get("head", "")}, ctx)]
    inner.append("# {0}".format(title))
    if page.get("lead"):
        inner.append(render_para({"text": page["lead"], "lead": True}))
    inner.extend(render_blocks(page.get("blocks", []), ctx))
    inner.append(render_pager(page, pages, index))
    return page_document(title, [wrap_page(inner, "l0-page--student")], "content/student.yaml")


def _flatten(chunks: list[Any]) -> list[str]:
    out: list[str] = []
    for chunk in chunks:
        if isinstance(chunk, list):
            out.extend(_flatten(chunk))
        else:
            out.append(chunk)
    return out


def build_all(docs_dir: Path | None = None) -> list[Path]:
    """读取 content/*.yaml，生成 docs/ 下的 Markdown 页面。"""
    docs_dir = Path(docs_dir) if docs_dir else DOCS_DIR
    written: list[Path] = []

    # ---- 首页 -------------------------------------------------------------
    home = load_yaml("home.yaml")
    ctx = {"file": "index.md"}
    inner = [render_cover(home.get("cover", {}), ctx)]
    inner.extend(render_blocks(home.get("blocks", []), ctx))
    written.append(
        write_doc(
            docs_dir,
            "index.md",
            page_document(home["title"], [wrap_page(inner, "l0-page--home")], "content/home.yaml"),
        )
    )

    # ---- 课程与讲义 -------------------------------------------------------
    # courses.yaml 决定有哪些课、每课的学生讲义与教师页来自哪个内容文件
    courses = load_yaml("courses.yaml")
    teacher_cards: list[dict] = []

    for course in courses.get("courses", []):
        for lesson in course.get("lessons", []):
            student = load_yaml(lesson["content"])
            pages = student.get("pages", [])
            total = len(pages)

            overview = student.get("overview")
            if overview:
                overview_file = lesson.get("overview_file") or overview_file_of(pages)
                ctx = {"file": overview_file}
                inner = ["# {0}".format(overview["title"])]
                if overview.get("lead"):
                    inner.append(render_para({"text": overview["lead"], "lead": True}))
                inner.extend(render_blocks(overview.get("blocks", []), ctx))
                written.append(
                    write_doc(
                        docs_dir,
                        overview_file,
                        page_document(
                            overview["title"],
                            [wrap_page(inner, "l0-page--student")],
                            "content/{0}".format(lesson["content"]),
                        ),
                    )
                )

            for index, page in enumerate(pages, start=1):
                ctx = {"file": page["file"], "index": index, "total": total}
                written.append(
                    write_doc(
                        docs_dir,
                        page["file"],
                        render_student_page(page, ctx, pages, index),
                    )
                )

            teacher = load_yaml(lesson["teacher"])
            ctx = {"file": teacher["file"]}
            inner = ["# {0}".format(teacher["title"])]
            if teacher.get("lead"):
                inner.append(render_para({"text": teacher["lead"], "lead": True}))
            inner.extend(render_blocks(teacher.get("blocks", []), ctx))
            written.append(
                write_doc(
                    docs_dir,
                    teacher["file"],
                    page_document(
                        teacher["title"],
                        [wrap_page(inner, "l0-page--teacher")],
                        "content/{0}".format(lesson["teacher"]),
                    ),
                )
            )
            teacher_cards.append(
                {
                    "eyebrow": "{0} · {1}".format(course.get("label", ""), lesson.get("label", "")),
                    "title": teacher["title"],
                    "desc": lesson.get("teacher_desc", ""),
                    "to": teacher["file"],
                }
            )

    # ---- 教师区首页 -------------------------------------------------------
    index_cfg = courses.get("teacher_index", {})
    index_file = index_cfg.get("file", "teacher/index.md")
    ctx = {"file": index_file}
    inner = ["# {0}".format(index_cfg.get("title", "教师区"))]
    if index_cfg.get("lead"):
        inner.append(render_para({"text": index_cfg["lead"], "lead": True}))
    inner.extend(render_blocks(index_cfg.get("blocks", []), ctx))
    inner.extend(
        render_blocks([dict(card, type="linkcard") for card in teacher_cards], ctx)
    )
    written.append(
        write_doc(
            docs_dir,
            index_file,
            page_document(
                index_cfg.get("title", "教师区"),
                [wrap_page(inner, "l0-page--teacher")],
                "content/courses.yaml",
            ),
        )
    )

    return written


def overview_file_of(pages: list[dict]) -> str:
    """从页面路径推出概览页路径：jp/l1/page-1.md → jp/l1/index.md。"""
    if not pages:
        return "index.md"
    parent = PurePosixPath(pages[0]["file"]).parent.as_posix()
    return "{0}/index.md".format(parent) if parent != "." else "index.md"


def render_pager(page: dict, pages: list[dict], index: int) -> str:
    out = ['<div class="l0-pager">']
    if index > 1:
        prev = pages[index - 2]
        out.append(
            '<a class="l0-pager__link l0-pager__link--prev" href="{href}">← 上一页：{title}</a>'.format(
                href=rel_url(page["file"], prev["file"]),
                title=inline(prev.get("pager") or prev["title"]),
            )
        )
    if index < len(pages):
        nxt = pages[index]
        out.append(
            '<a class="l0-pager__link l0-pager__link--next" href="{href}">下一页：{title} →</a>'.format(
                href=rel_url(page["file"], nxt["file"]),
                title=inline(nxt.get("pager") or nxt["title"]),
            )
        )
    out.append("</div>")
    return "\n".join(out)


def load_yaml(name: str) -> dict:
    path = CONTENT_DIR / name
    if not path.exists():
        raise FileNotFoundError("缺少内容文件：{0}".format(path))
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def write_doc(docs_dir: Path, rel_path: str, content: str) -> Path:
    target = docs_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    return target


if __name__ == "__main__":
    for item in build_all():
        print("generated:", item.relative_to(ROOT))
