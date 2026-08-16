"""Pack official MakeHuman lip/cheek vertices and their hm08 UV faces.

Vertices come from official CC0 mouth/cheek targets (not a bounding box).
Core = upper/lower lip volume only. lowerlip-ext-up is omitted on hm08: it
pulls center verts onto the chin. Width + angles-up add lateral commissures.

Y band: never extend below the official lower-lip volume (stops chin bleed).
UV: all corners in the lip set, or all-but-one only when every face corner
is still on or above that lower-lip floor (no triangle spanning onto chin).
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

LIP_VOLUME_FILES = [
    TARGETS / "mouth/mouth-upperlip-volume-incr.target",
    TARGETS / "mouth/mouth-lowerlip-volume-incr.target",
]
LIP_EXTRA = [
    (TARGETS / "mouth/mouth-lowerlip-width-incr.target", 0.01, 0.20),
    (TARGETS / "mouth/mouth-angles-up.target", 0.07, 0.28),
]
LIP_Y_TOP_PAD = 0.008
LIP_Z_PAD = 0.008
LIP_EXTRA_Z_SLACK = 0.032
LIP_MAX_ABS_X = 0.26
LIP_UV_MAX_ABS_X = 0.25
LIP_CHEEK_Z_CUT = 0.012
LIP_BORDER_LATERAL = 0.20
LIP_FILES = [(p, MIN_MAG) for p in LIP_VOLUME_FILES] + [(p, m) for p, m, _ in LIP_EXTRA]
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


def lip_bounds(
    volume: set[int], verts: list[tuple[float, float, float]]
) -> tuple[float, float, float, float]:
    lower = {i for i in volume if i in parse_target(LIP_VOLUME_FILES[1])}
    upper = {i for i in volume if i in parse_target(LIP_VOLUME_FILES[0])}
    y_floor = min(verts[i][1] for i in lower)
    y_ceil = max(verts[i][1] for i in upper) + LIP_Y_TOP_PAD
    zs = [verts[i][2] for i in volume]
    return y_floor, y_ceil, min(zs) - LIP_Z_PAD, max(zs) + LIP_Z_PAD


def collect_lips(verts: list[tuple[float, float, float]]) -> set[int]:
    volume = {i for path in LIP_VOLUME_FILES for i in parse_target(path)}
    y_floor, y_ceil, z0, z1 = lip_bounds(volume, verts)
    lips = set(volume)

    def in_core_band(index: int) -> bool:
        _, y, z = verts[index]
        return y_floor <= y <= y_ceil and z0 <= z <= z1

    def in_extra_band(index: int, min_abs_x: float) -> bool:
        x, y, z = verts[index]
        if y < y_floor or y > y_ceil:
            return False
        if abs(x) < min_abs_x or abs(x) > LIP_MAX_ABS_X:
            return False
        return z >= z0 - LIP_EXTRA_Z_SLACK and z <= z1 + LIP_Z_PAD

    for path, min_mag, min_abs_x in LIP_EXTRA:
        for index in parse_target(path, min_mag):
            if index in lips:
                continue
            if in_extra_band(index, min_abs_x):
                lips.add(index)

    def cheek_smear(index: int) -> bool:
        x, _, z = verts[index]
        return abs(x) > 0.22 and z < z0 + LIP_CHEEK_Z_CUT

    return {
        i
        for i in lips
        if (in_core_band(i) or in_extra_band(i, LIP_BORDER_LATERAL))
        and abs(verts[i][0]) <= LIP_MAX_ABS_X
        and not cheek_smear(i)
    }


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
    y_floor: float | None = None,
    max_abs_x: float | None = None,
    border_lateral: float | None = None,
) -> list[list[float]]:
    tris: list[list[float]] = []
    for corners in faces:
        if any(v >= BODY_VERTS for v, _ in corners):
            continue
        corner_verts = [v for v, _ in corners]
        lip_corners = [v for v in corner_verts if v in ids]
        if len(lip_corners) == len(corners):
            ok = True
        elif border_lateral is not None and len(lip_corners) == len(corners) - 1:
            ok = any(abs(verts[v][0]) >= border_lateral for v in lip_corners)
        else:
            ok = False
        if not ok:
            continue
        if y_floor is not None and any(verts[v][1] < y_floor for v in corner_verts):
            continue
        if max_abs_x is not None and any(abs(verts[v][0]) > max_abs_x for v in corner_verts):
            continue
        pts = [uvs[vt] for _, vt in corners]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[0], pts[i], pts[i + 1]
            tris.append([round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5), round(c[0], 5), round(c[1], 5)])
    return tris


def find_zones() -> dict:
    verts = parse_body_verts()
    uvs, faces = parse_body_faces()
    volume = {i for path in LIP_VOLUME_FILES for i in parse_target(path)}
    y_floor, _, _, _ = lip_bounds(volume, verts)
    lips = sorted(collect_lips(verts))
    cheeks = sorted({i for path, mag in CHEEK_FILES for i in parse_target(path, mag)})
    lip_uv = uv_tris(
        set(lips),
        uvs,
        faces,
        verts,
        y_floor=y_floor,
        max_abs_x=LIP_UV_MAX_ABS_X,
        border_lateral=LIP_BORDER_LATERAL,
    )
    cheek_uv = uv_tris(set(cheeks), uvs, faces, verts)
    return {
        "source": {
            "official": "makehumancommunity/makehuman makehuman/data/targets",
            "lips": [str(path.relative_to(ROOT)) for path, _ in LIP_FILES],
            "cheeks": [str(path.relative_to(ROOT)) for path, _ in CHEEK_FILES],
            "minMag": {str(path.relative_to(ROOT)): mag for path, mag in LIP_FILES + CHEEK_FILES},
            "note": "mouth-lowerlip-ext-up omitted on hm08 (chin falloff)",
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
    assert 130 <= len(zones["lips"]) <= 200, len(zones["lips"])
    assert 120 <= len(zones["cheeks"]) <= 250, len(zones["cheeks"])
    assert 180 <= len(zones["lipUv"]) <= 700, len(zones["lipUv"])
    assert 20 <= len(zones["cheekUv"]) <= 400, len(zones["cheekUv"])
    OUT.write_text(json.dumps(zones, separators=(",", ":")))
    print(
        f"lips {len(zones['lips'])} uv {len(zones['lipUv'])} "
        f"cheeks {len(zones['cheeks'])} uv {len(zones['cheekUv'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
