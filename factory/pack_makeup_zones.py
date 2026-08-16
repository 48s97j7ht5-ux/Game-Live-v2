"""Pack official MakeHuman lip/cheek vertices and their hm08 UV faces.

Vertices come from official CC0 volume targets (not a bounding box).
Only verts with a real displacement are kept — the morph falloff around
the lips/cheeks is what made lipstick look like a smudge.

  mouth/mouth-upperlip-volume-incr.target
  mouth/mouth-lowerlip-volume-incr.target
  cheek/l-cheek-volume-incr.target
  cheek/r-cheek-volume-incr.target

UV triangles are the official body faces in models/base.obj whose every
corner is one of those verts. Makeup paints those UV islands
(default.mhmat: shaderConfig vertexColors false).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_OBJ = ROOT / "models/base.obj"
TARGETS = ROOT / "factory/mh/targets"
OUT = ROOT / "web/data/makeup-zones.json"
BODY_VERTS = 13380
MIN_MAG = 0.01

LIP_FILES = [
    TARGETS / "mouth/mouth-upperlip-volume-incr.target",
    TARGETS / "mouth/mouth-lowerlip-volume-incr.target",
]
CHEEK_FILES = [
    TARGETS / "cheek/l-cheek-volume-incr.target",
    TARGETS / "cheek/r-cheek-volume-incr.target",
]


def parse_target(path: Path) -> list[int]:
    out: list[int] = []
    for line in path.read_text().splitlines():
        if not line or line[0] == "#":
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        index = int(parts[0])
        if index >= BODY_VERTS:
            continue
        mag = math.sqrt(float(parts[1]) ** 2 + float(parts[2]) ** 2 + float(parts[3]) ** 2)
        if mag >= MIN_MAG:
            out.append(index)
    return out


def parse_body_faces() -> tuple[list[tuple[float, float]], list[list[tuple[int, int]]]]:
    uvs: list[tuple[float, float]] = []
    faces: list[list[tuple[int, int]]] = []
    group = ""
    for line in BASE_OBJ.read_text().splitlines():
        if line.startswith("vt "):
            _, u, v, *_ = line.split()
            uvs.append((float(u), float(v)))
        elif line.startswith("g "):
            group = line.split()[1]
        elif line.startswith("f ") and group == "body":
            corners = []
            for item in line.split()[1:]:
                bits = item.split("/")
                v = int(bits[0]) - 1
                vt = int(bits[1]) - 1 if len(bits) > 1 and bits[1] else 0
                corners.append((v, vt))
            faces.append(corners)
    return uvs, faces


def uv_box(tris: list[list[float]]) -> list[float]:
    us = [t[0] for t in tris] + [t[2] for t in tris] + [t[4] for t in tris]
    vs = [t[1] for t in tris] + [t[3] for t in tris] + [t[5] for t in tris]
    return [round(min(us), 5), round(min(vs), 5), round(max(us), 5), round(max(vs), 5)]


def cheek_boxes(tris: list[list[float]]) -> list[list[float]]:
    cents = [((t[0] + t[2] + t[4]) / 3, (t[1] + t[3] + t[5]) / 3) for t in tris]
    mid = sorted(c[1] for c in cents)[len(cents) // 2]
    low = [t for t, c in zip(tris, cents) if c[1] < mid]
    high = [t for t, c in zip(tris, cents) if c[1] >= mid]
    return [uv_box(low), uv_box(high)]


def uv_tris(ids: set[int], uvs: list[tuple[float, float]], faces: list[list[tuple[int, int]]]) -> list[list[float]]:
    tris: list[list[float]] = []
    for corners in faces:
        if any(v >= BODY_VERTS or v not in ids for v, _ in corners):
            continue
        pts = [uvs[vt] for _, vt in corners]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[0], pts[i], pts[i + 1]
            tris.append([round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5), round(c[0], 5), round(c[1], 5)])
    return tris


def find_zones() -> dict:
    lips = sorted({i for path in LIP_FILES for i in parse_target(path)})
    cheeks = sorted({i for path in CHEEK_FILES for i in parse_target(path)})
    uvs, faces = parse_body_faces()
    lip_uv = uv_tris(set(lips), uvs, faces)
    cheek_uv = uv_tris(set(cheeks), uvs, faces)
    return {
        "source": {
            "official": "makehumancommunity/makehuman makehuman/data/targets",
            "lips": [str(path.relative_to(ROOT)) for path in LIP_FILES],
            "cheeks": [str(path.relative_to(ROOT)) for path in CHEEK_FILES],
            "minMag": MIN_MAG,
        },
        "lips": lips,
        "cheeks": cheeks,
        "lipUv": lip_uv,
        "cheekUv": cheek_uv,
        "lipBox": uv_box(lip_uv),
        "cheekBoxes": cheek_boxes(cheek_uv),
    }


def main() -> None:
    zones = find_zones()
    assert 80 <= len(zones["lips"]) <= 200, len(zones["lips"])
    assert 120 <= len(zones["cheeks"]) <= 250, len(zones["cheeks"])
    assert 20 <= len(zones["lipUv"]) <= 400, len(zones["lipUv"])
    assert 20 <= len(zones["cheekUv"]) <= 400, len(zones["cheekUv"])
    OUT.write_text(json.dumps(zones, separators=(",", ":")))
    print(
        f"lips {len(zones['lips'])} uv {len(zones['lipUv'])} "
        f"cheeks {len(zones['cheeks'])} uv {len(zones['cheekUv'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
