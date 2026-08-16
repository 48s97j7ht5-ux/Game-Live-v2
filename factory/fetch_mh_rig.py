"""Download official MakeHuman hm08 rig + weights (CC0) into factory/mh/rigs/."""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "factory/mh/rigs"
BASE = "https://api.github.com/repos/makehumancommunity/makehuman/contents/makehuman/data/rigs"

FILES = ("default.mhskel", "default_weights.mhw")


def fetch(name: str) -> None:
    url = f"{BASE}/{name}?ref=master"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.raw"})
    data = urllib.request.urlopen(req, timeout=120).read()
    path = DEST / name
    path.write_bytes(data)
    print(f"wrote {path} ({len(data)} bytes)")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        fetch(name)


if __name__ == "__main__":
    main()
