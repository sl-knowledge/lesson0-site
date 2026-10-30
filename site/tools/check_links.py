"""站内链接自检：确认 _site 里的所有相对链接都指向真实存在的文件。

用法：python tools/check_links.py
发现断链时以非零码退出。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"

LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
SKIP_PREFIX = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:", "#")


def iter_html(site: Path):
    for path in sorted(site.rglob("*.html")):
        yield path


def resolve(page: Path, target: str) -> Path | None:
    """把页面里的相对链接解析成站点内的真实路径；外部链接返回 None。"""
    if target.startswith(SKIP_PREFIX):
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return None
    path = unquote(parts.path)
    if not path:
        return None
    base = page.parent
    if path.startswith("/"):
        candidate = SITE / path.lstrip("/")
    else:
        candidate = (base / path).resolve()
    return candidate


def exists(candidate: Path) -> bool:
    if candidate.is_file():
        return True
    if candidate.is_dir():
        return (candidate / "index.html").is_file()
    # 目录式 URL：foo/ → foo/index.html
    return (candidate / "index.html").is_file()


def main() -> int:
    if not SITE.is_dir():
        print("找不到 _site，请先运行：python -m mkdocs build --strict")
        return 2

    broken: list[str] = []
    checked = 0
    for page in iter_html(SITE):
        html = page.read_text(encoding="utf-8", errors="replace")
        for target in LINK_RE.findall(html):
            candidate = resolve(page, target)
            if candidate is None:
                continue
            checked += 1
            if not exists(candidate):
                rel_page = page.relative_to(SITE)
                broken.append("{0}  →  {1}".format(rel_page, target))

    print("检查了 {0} 个页面、{1} 条站内链接".format(len(list(iter_html(SITE))), checked))
    if broken:
        print("发现 {0} 条断链：".format(len(broken)))
        for item in broken:
            print("  -", item)
        return 1
    print("全部链接可达 [OK]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
