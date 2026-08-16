"""Vendor MakeHuman source tree for factory/mh_runtime.py (read-only at bake time)."""

from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "vendor/makehuman"
REPO = "https://github.com/makehumancommunity/makehuman.git"


def main() -> None:
    if (DEST / "makehuman/shared/skeleton.py").is_file():
        print(f"makehuman already at {DEST}")
        return
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        import shutil

        shutil.rmtree(DEST)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO, str(DEST)],
        check=True,
    )
    print(f"cloned {REPO} -> {DEST}")


if __name__ == "__main__":
    main()
