"""重新打包交付件：lesson0-site.zip

包结构与之前一致：site/ 目录内容，统一挂在 lesson0-site/ 前缀下，
另外把仓库根目录的 LICENSE 放进包根（它是许可协议的唯一真源）。
"""

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "lesson0-site.zip"
PREFIX = "lesson0-site"

SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache"}
SKIP_SUFFIX = {".pyc", ".pyo"}

entries = []
for dirpath, dirnames, filenames in os.walk(SITE):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        src = Path(dirpath) / name
        if src.suffix in SKIP_SUFFIX:
            continue
        arc = "{0}/{1}".format(PREFIX, src.relative_to(SITE).as_posix())
        entries.append((src, arc))

license_file = ROOT / "LICENSE"
if license_file.is_file():
    entries.append((license_file, "{0}/LICENSE".format(PREFIX)))

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for src, arc in entries:
        zf.write(src, arc)

print("entries: {0}".format(len(entries)))
print("size   : {0} bytes".format(OUT.stat().st_size))
