"""Download official MakeHuman arms/legs modeling targets (CC0) into factory/mh/targets/armslegs/."""

from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor/makehuman"
DEST = ROOT / "factory/mh/targets/armslegs"
REPO = "https://github.com/makehumancommunity/makehuman.git"
REMOTE = "makehuman/data/targets/armslegs"


def ensure_repo() -> Path:
    if (VENDOR / "makehuman/data/targets/armslegs").is_dir():
        return VENDOR
    VENDOR.parent.mkdir(parents=True, exist_ok=True)
    if VENDOR.exists():
        import shutil

        shutil.rmtree(VENDOR)
    subprocess.run(["git", "clone", "--depth", "1", REPO, str(VENDOR)], check=True)
    return VENDOR


def main() -> None:
    src = ensure_repo() / "makehuman/data/targets/armslegs"
    if not src.is_dir():
        raise FileNotFoundError(src)
    DEST.mkdir(parents=True, exist_ok=True)
    n = 0
    for path in sorted(src.glob("*.target")):
        dest = DEST / path.name
        if not dest.exists() or dest.read_bytes() != path.read_bytes():
            dest.write_bytes(path.read_bytes())
            n += 1
    print(f"synced {len(list(DEST.glob('*.target')))} targets ({n} updated) -> {DEST}")


if __name__ == "__main__":
    main()
