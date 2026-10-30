"""MkDocs pre_build 钩子。

构建前把 ``content/*.yaml``（内容真源）渲染成 ``docs/`` 下的 Markdown，
这样 ``python -m mkdocs build --strict`` 一次命令即可得到最新的静态站点。

同时把仓库根目录的 ``LICENSE`` 同步到站点资源目录，保证站内公布的协议
与仓库里那份永远是同一份，不会出现两份文本不一致。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_content import build_all  # noqa: E402


def sync_license(docs_dir: Path) -> Path | None:
    """复制仓库根目录的 LICENSE 到站点资源目录（不覆盖手写内容，只做同步）。"""
    src = REPO_ROOT / "LICENSE"
    if not src.is_file():
        return None
    dest = docs_dir / "assets" / "downloads" / "LICENSE.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def on_pre_build(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    for path in build_all(docs_dir):
        print("[content] rendered {0}".format(path.relative_to(docs_dir)))
    dest = sync_license(docs_dir)
    if dest is not None:
        print("[license] synced {0}".format(dest.relative_to(docs_dir)))
    return config


def on_post_build(config, **kwargs):
    """生成 GitHub Pages 真正会读到的 ``/404.html``。

    站点使用目录式 URL（``use_directory_urls: true``），所以 ``docs/404.md``
    会被生成到 ``404/index.html``；而 GitHub Pages 在路径不存在时固定读取
    根目录下的 ``404.html``——那份默认是 Material 自带的「404 - Not found」，
    不含任何指路信息。

    这里把渲染好的 ``404/index.html`` 取过来改写成 ``404.html``，并把页内
    所有相对地址换成绝对地址：GitHub Pages 是「在任意请求路径上返回同一份
    404.html」，浏览器会以那个请求路径为基准解析相对地址，相对写法必然指错
    （样式表甚至会 404，页面变成裸 HTML）。正文仍然只有 ``docs/404.md``
    这一个来源。
    """
    site_dir = Path(config["site_dir"])
    src = site_dir / "404" / "index.html"
    dst = site_dir / "404.html"
    if not src.is_file():
        print("[404] skipped: {0} not found".format(src))
        return

    base = (config.get("site_url") or "").strip().rstrip("/") + "/"
    if not base.strip("/"):
        print("[404] skipped: site_url is not set, cannot rewrite relative links")
        return

    html = src.read_text(encoding="utf-8")
    html = re.sub(r'((?:href|src))="\.\./', r'\1="' + base, html)
    html = re.sub(r'((?:href|src))="\.\."', r'\1="' + base, html)

    leftover = re.findall(r'(?:href|src)="\.{1,2}[^"]*"', html)
    if leftover:
        raise RuntimeError("[404] relative links left in 404.html: {0}".format(sorted(set(leftover))))

    dst.write_text(html, encoding="utf-8")
    print("[404] wrote {0} (absolute base {1})".format(dst.relative_to(site_dir), base))
