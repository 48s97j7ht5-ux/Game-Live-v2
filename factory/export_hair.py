#!/usr/bin/env python3
"""Build workbench hair shells from the official hm08 helper-hair cage.

MakeHuman docs: hair is clothes (MHCLO) stored in data/hair and bound to the
basemesh helper named helper-hair. Community packs (hair01 CC0, etc.) live on
files.makehumancommunity.org; this exporter uses the helper already inside
models/base.obj so the workbench can cycle styles without that download.

Drop a fitted MHCLO/OBJ into models/hair/ and list it in web/parts/hair.json
to replace a generated shell.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "models" / "base.obj"
OUT = ROOT / "models" / "hair"

HEADER = """# Hair shell from hm08 helper-hair (MakeHuman CC0 basemesh helper)
# Official rule: hair is MHCLO clothes in the hair folder, fitted to helper-hair.
# https://static.makehumancommunity.org/makehuman/docs/hairstyles_and_clothes.html
o hair
g hair
"""


def load_obj(path: Path) -> tuple[list[tuple[float, float, float]], dict[str, list[list[int]]]]:
    verts: list[tuple[float, float, float]] = []
    groups: dict[str, list[list[int]]] = defaultdict(list)
    current = "none"
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            x, y, z = map(float, line.split()[1:4])
            verts.append((x, y, z))
        elif line.startswith("g "):
            current = line.split()[1]
        elif line.startswith("f "):
            groups[current].append([int(part.split("/")[0]) - 1 for part in line.split()[1:]])
    return verts, groups


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return (a[0] ** 2 + a[1] ** 2 + a[2] ** 2) ** 0.5


def norm(a):
    ln = length(a) or 1.0
    return scale(a, 1.0 / ln)


def face_normal(verts, face):
    a, b, c = verts[face[0]], verts[face[1]], verts[face[2]]
    return norm(cross(sub(b, a), sub(c, a)))


def vertex_normals(verts, faces):
    acc = [(0.0, 0.0, 0.0)] * len(verts)
    used = set()
    for face in faces:
        n = face_normal(verts, face)
        for i in face:
            used.add(i)
            acc[i] = add(acc[i], n)
    out = [(0.0, 1.0, 0.0)] * len(verts)
    for i in used:
        out[i] = norm(acc[i])
    return out


def remap(verts, faces):
    used = sorted({i for face in faces for i in face})
    index = {old: new for new, old in enumerate(used)}
    new_verts = [verts[i] for i in used]
    new_faces = [[index[i] for i in face] for face in faces]
    return new_verts, new_faces


def boundary_loops(faces):
    count = defaultdict(int)
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            count[key] += 1
    edges = [key for key, n in count.items() if n == 1]
    return edges


def write_obj(path: Path, verts, faces) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks = [HEADER]
    for x, y, z in verts:
        chunks.append(f"v {x:.5f} {y:.5f} {z:.5f}\n")
    for face in faces:
        chunks.append("f " + " ".join(str(i + 1) for i in face) + "\n")
    path.write_text("".join(chunks))
    print(f"wrote {path} v={len(verts)} f={len(faces)}")


def filter_faces(verts, faces, min_y: float, back_y: float, front_z: float):
    """Keep the crown plus optional nape of helper-hair (not the full fitting cage)."""
    kept = []
    for face in faces:
        cy = sum(verts[i][1] for i in face) / len(face)
        cz = sum(verts[i][2] for i in face) / len(face)
        if cy >= min_y or (cy >= back_y and cz <= front_z):
            kept.append(face)
    return kept


def shell(cage_verts, cage_faces, inner: float, outer: float, drop: float, front_keep: float) -> tuple[list, list]:
    """Solid hair from helper-hair: inner/outer offset plus a back/side skirt."""
    normals = vertex_normals(cage_verts, cage_faces)
    n = len(cage_verts)
    inner_v = [add(cage_verts[i], scale(normals[i], inner)) for i in range(n)]
    outer_v = []
    for i, p in enumerate(cage_verts):
        extra = drop * max(0.0, (front_keep - p[2]) / 2.4) ** 1.2
        grown = add(p, scale(normals[i], outer + extra * 0.15))
        outer_v.append((grown[0], grown[1] - extra, grown[2] - extra * 0.12))
    verts = inner_v + outer_v
    faces = []
    for face in cage_faces:
        faces.append(list(reversed(face)))  # inner, inward
        faces.append([i + n for i in face])  # outer
    for a, b in boundary_loops(cage_faces):
        faces.append([a, b, b + n, a + n])
    return verts, faces


def main() -> None:
    verts, groups = load_obj(BASE)
    helper = groups["helper-hair"]
    styles = {
        "short": dict(cut=dict(min_y=7.15, back_y=6.95, front_z=0.2), inner=0.02, outer=0.16, drop=0.08, front_keep=0.7),
        "bob": dict(cut=dict(min_y=6.55, back_y=6.15, front_z=0.35), inner=0.02, outer=0.2, drop=0.55, front_keep=0.95),
        "long": dict(cut=dict(min_y=6.7, back_y=4.6, front_z=0.25), inner=0.02, outer=0.22, drop=1.4, front_keep=1.0),
    }
    for name, params in styles.items():
        cut = params.pop("cut")
        cage_v, cage_f = remap(verts, filter_faces(verts, helper, **cut))
        hv, hf = shell(cage_v, cage_f, **params)
        write_obj(OUT / f"{name}.obj", hv, hf)


if __name__ == "__main__":
    main()
