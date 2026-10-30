"""MkDocs pre_build 钩子。

构建前把 ``content/*.yaml``（内容真源）渲染成 ``docs/`` 下的 Markdown，
这样 ``python -m mkdocs build --strict`` 一次命令即可得到最新的静态站点。

同时把仓库根目录的 ``LICENSE`` 同步到站点资源目录，保证站内公布的协议
与仓库里那份永远是同一份，不会出现两份文本不一致。
"""

from __future__ import annotations

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
