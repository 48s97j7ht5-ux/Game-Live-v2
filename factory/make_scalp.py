#!/usr/bin/env python3
"""Grow a thin scalp cap from the clay crown so hair cards do not show skull."""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "models/base.obj"
OUT = ROOT / "models/hair/scalp.obj"

CROWN = 881  # highest midline body vert
YMIN = 7.45
ZMAX = 1.26
EAR_X = 0.76
EAR_Y = 7.70
OFFSET = 0.04  # ~4 mm in MakeHuman decimetres, under the wig, above the clay


def load_body() -> tuple[list[tuple[float, float, float]], list[list[int]]]:
    verts: list[tuple[float, float, float]] = []
    faces: list[list[int]] = []
    group = ""
    for line in BASE.read_text().splitlines():
        if line.startswith("v "):
            parts = line.split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("g "):
            group = line.split()[1]
        elif line.startswith("f ") and group == "body":
            faces.append([int(item.split("/")[0]) - 1 for item in line.split()[1:]])
    return verts, faces


def normals_and_adj(
    verts: list[tuple[float, float, float]], faces: list[list[int]]
) -> tuple[list[list[float]], list[list[int]]]:
    n = 13380
    adj: list[list[int]] = [[] for _ in range(n)]
    normals = [[0.0, 0.0, 0.0] for _ in range(n)]
    for face in faces:
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            if b not in adj[a]:
                adj[a].append(b)
            if a not in adj[b]:
                adj[b].append(a)
        a, b, c = verts[face[0]], verts[face[1]], verts[face[2]]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        for i in face:
            normals[i][0] += nx
            normals[i][1] += ny
            normals[i][2] += nz
    for i in range(n):
        nx, ny, nz = normals[i]
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        normals[i] = [nx / length, ny / length, nz / length]
    return normals, adj


def accept(vert: tuple[float, float, float], normal: list[float]) -> bool:
    x, y, z = vert
    if y < YMIN or z > ZMAX:
        return False
    if abs(x) > EAR_X and y < EAR_Y and z < 0.90:
        return False
    if z > 1.18 and normal[1] < 0.25:
        return False
    return True


def flood(
    verts: list[tuple[float, float, float]],
    normals: list[list[float]],
    adj: list[list[int]],
) -> set[int]:
    keep: set[int] = set()
    queue = [CROWN]
    while queue:
        i = queue.pop()
        if i in keep:
            continue
        if not accept(verts[i], normals[i]):
            continue
        keep.add(i)
        queue.extend(adj[i])
    return keep


def write_obj(
    verts: list[tuple[float, float, float]],
    faces: list[list[int]],
    normals: list[list[float]],
    keep: set[int],
) -> None:
    index = {old: k for k, old in enumerate(sorted(keep))}
    lines = [
        "# MakeHuman hm08 scalp cap — body verts grown along normals",
        "# Not a helper. Sits under official hair cards so clay skull is not visible.",
        "o scalp",
        "g scalp",
    ]
    for old in sorted(keep):
        x, y, z = verts[old]
        nx, ny, nz = normals[old]
        lines.append(
            f"v {x + OFFSET * nx:.6f} {y + OFFSET * ny:.6f} {z + OFFSET * nz:.6f}"
        )
    face_count = 0
    for face in faces:
        if not all(i in keep for i in face):
            continue
        lines.append("f " + " ".join(str(index[i] + 1) for i in face))
        face_count += 1
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} verts={len(keep)} faces={face_count}")


def main() -> None:
    verts, faces = load_body()
    normals, adj = normals_and_adj(verts, faces)
    keep = flood(verts, normals, adj)
    if len(keep) < 180:
        raise SystemExit(f"scalp too small: {len(keep)} verts")
    write_obj(verts, faces, normals, keep)


if __name__ == "__main__":
    main()
