"""Pack official MakeHuman lip/cheek vertices and their hm08 UV faces.

Vertices come from official CC0 mouth/cheek targets (not a bounding box).
Volume = lip pads. Width + ext = commissures / outer lip. Angles/dimples
are skipped: those official targets walk onto the cheek.

Only verts with a real displacement are kept. Width and angles-up extras
require lateral |x| and the core lip Y/Z band so philtrum and cheek
falloff stay unpainted.

UV triangles are body faces in models/base.obj: all corners in the lip
set, or all-but-one when the painted corners are lateral (commissure).
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

# Core lip pads (volume + ext). Width/angles extras are lateral-only so
# philtrum and cheek falloff from official targets stay unpainted.
LIP_CORE_FILES = [
    (TARGETS / "mouth/mouth-upperlip-volume-incr.target", 0.01),
    (TARGETS / "mouth/mouth-lowerlip-volume-incr.target", 0.01),
    (TARGETS / "mouth/mouth-lowerlip-ext-up.target", 0.01),
]
LIP_EXTRA = [
    (TARGETS / "mouth/mouth-lowerlip-width-incr.target", 0.01, 0.18),
    (TARGETS / "mouth/mouth-angles-up.target", 0.05, 0.24),
]
LIP_BAND_PAD = 0.015
LIP_BORDER_LATERAL = 0.17
# One ring of hm08 body faces at commissures (not in official targets).
LIP_COMMISURE_MIN_ABS_X = 0.18
LIP_COMMISURE_MIN_LIP_NEIGHBORS = 2
LIP_FILES = LIP_CORE_FILES + [(p, m) for p, m, _ in LIP_EXTRA]
CHEEK_FILES = [
    (TARGETS / "cheek/l-cheek-volume-incr.target", 0.01),
    (TARGETS / "cheek/r-cheek-volume-incr.target", 0.01),
]


def parse_target(path: Path, min_mag: float = MIN_MAG) -> list[int]:
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
        if mag >= min_mag:
            out.append(index)
    return out


def parse_body_verts() -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    for line in BASE_OBJ.read_text().splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            verts.append((float(x), float(y), float(z)))
    return verts


def lip_band(core: set[int], verts: list[tuple[float, float, float]]) -> tuple[float, float, float, float]:
    ys = [verts[i][1] for i in core]
    zs = [verts[i][2] for i in core]
    return (
        min(ys) - LIP_BAND_PAD,
        max(ys) + LIP_BAND_PAD,
        min(zs) - LIP_BAND_PAD,
        max(zs) + LIP_BAND_PAD,
    )


def body_adjacency(faces: list[list[tuple[int, int]]]) -> dict[int, set[int]]:
    adj: dict[int, set[int]] = {}
    for corners in faces:
        verts_on_face = [v for v, _ in corners if v < BODY_VERTS]
        for a in verts_on_face:
            for b in verts_on_face:
                if a != b:
                    adj.setdefault(a, set()).add(b)
    return adj


def expand_commissure_ring(
    lips: set[int],
    verts: list[tuple[float, float, float]],
    adj: dict[int, set[int]],
    y0: float,
    y1: float,
    z0: float,
    z1: float,
) -> None:
    def in_band(index: int) -> bool:
        _, y, z = verts[index]
        return y0 <= y <= y1 and z0 <= z <= z1

    candidates: set[int] = set()
    for index in lips:
        for neighbor in adj.get(index, ()):
            if neighbor in lips or neighbor >= BODY_VERTS:
                continue
            x, _, _ = verts[neighbor]
            if abs(x) < LIP_COMMISURE_MIN_ABS_X or not in_band(neighbor):
                continue
            if len(adj.get(neighbor, set()) & lips) < LIP_COMMISURE_MIN_LIP_NEIGHBORS:
                continue
            candidates.add(neighbor)
    lips |= candidates


def collect_lips(
    verts: list[tuple[float, float, float]],
    faces: list[list[tuple[int, int]]],
) -> set[int]:
    lips = {i for path, mag in LIP_CORE_FILES for i in parse_target(path, mag)}
    y0, y1, z0, z1 = lip_band(lips, verts)

    def in_band(index: int) -> bool:
        _, y, z = verts[index]
        return y0 <= y <= y1 and z0 <= z <= z1

    for path, min_mag, min_abs_x in LIP_EXTRA:
        for index in parse_target(path, min_mag):
            if index in lips:
                continue
            x, _, _ = verts[index]
            if abs(x) >= min_abs_x and in_band(index):
                lips.add(index)
    expand_commissure_ring(lips, verts, body_adjacency(faces), y0, y1, z0, z1)
    return lips


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


def uv_tris(
    ids: set[int],
    uvs: list[tuple[float, float]],
    faces: list[list[tuple[int, int]]],
    verts: list[tuple[float, float, float]],
    *,
    border_lateral: float | None = None,
) -> list[list[float]]:
    tris: list[list[float]] = []
    for corners in faces:
        if any(v >= BODY_VERTS for v, _ in corners):
            continue
        lip_corners = [v for v, _ in corners if v in ids]
        if len(lip_corners) == len(corners):
            pass
        elif border_lateral is not None and len(lip_corners) == len(corners) - 1:
            if not any(abs(verts[v][0]) >= border_lateral for v in lip_corners):
                continue
        else:
            continue
        pts = [uvs[vt] for _, vt in corners]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[0], pts[i], pts[i + 1]
            tris.append([round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5), round(c[0], 5), round(c[1], 5)])
    return tris


def find_zones() -> dict:
    verts = parse_body_verts()
    uvs, faces = parse_body_faces()
    lips = sorted(collect_lips(verts, faces))
    cheeks = sorted({i for path, mag in CHEEK_FILES for i in parse_target(path, mag)})
    lip_uv = uv_tris(set(lips), uvs, faces, verts, border_lateral=LIP_BORDER_LATERAL)
    cheek_uv = uv_tris(set(cheeks), uvs, faces, verts)
    return {
        "source": {
            "official": "makehumancommunity/makehuman makehuman/data/targets",
            "lips": [str(path.relative_to(ROOT)) for path, _ in LIP_FILES],
            "cheeks": [str(path.relative_to(ROOT)) for path, _ in CHEEK_FILES],
            "minMag": {str(path.relative_to(ROOT)): mag for path, mag in LIP_FILES + CHEEK_FILES},
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
    assert 140 <= len(zones["lips"]) <= 235, len(zones["lips"])
    assert 120 <= len(zones["cheeks"]) <= 250, len(zones["cheeks"])
    assert 250 <= len(zones["lipUv"]) <= 700, len(zones["lipUv"])
    assert 20 <= len(zones["cheekUv"]) <= 400, len(zones["cheekUv"])
    OUT.write_text(json.dumps(zones, separators=(",", ":")))
    print(
        f"lips {len(zones['lips'])} uv {len(zones['lipUv'])} "
        f"cheeks {len(zones['cheeks'])} uv {len(zones['cheekUv'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
