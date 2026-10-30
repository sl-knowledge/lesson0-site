"""MkDocs pre_build 钩子。

构建前把 ``content/*.yaml``（内容真源）渲染成 ``docs/`` 下的 Markdown，
这样 ``python -m mkdocs build --strict`` 一次命令即可得到最新的静态站点。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_content import build_all  # noqa: E402


def on_pre_build(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    for path in build_all(docs_dir):
        print("[content] rendered {0}".format(path.relative_to(docs_dir)))
    return config
