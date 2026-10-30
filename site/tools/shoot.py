"""用无头 Chrome 截取若干页面，便于人工检查版式。

用法：python tools/shoot.py jp/l1/page-3 ...
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
OUT = ROOT / "design" / "shots"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROFILE = Path(tempfile.gettempdir()) / "chrome_shot_profile"


def main(argv: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = argv[1:] or ["index", "jp/l1/page-3", "jp/l3/page-4", "en/l1/page-2", "teacher/index"]
    for target in targets:
        html = SITE / target / "index.html"
        if not html.is_file():
            html = SITE / (target + ".html")
        if not html.is_file():
            print("找不到页面：", target)
            continue
        name = target.replace("/", "-") or "index"
        shot = OUT / (name + ".png")
        subprocess.run(
            [
                str(CHROME),
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--user-data-dir={0}".format(PROFILE),
                "--virtual-time-budget=5000",
                "--window-size=1280,1900",
                "--screenshot={0}".format(shot),
                html.as_uri(),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        print(target, "->", shot.name, shot.exists() and shot.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
