#!/usr/bin/env python3
"""Build tight hair from the hm08 *body* scalp, not from helper-hair.

Official MakeClothes docs:
  - helper mesh is a fitting cage (base mesh + helper). Clothes/hair are a
    separate proxy: each clothes vertex tracks 3 verts on helper OR body.
  - helper-hair is not a hairstyle and is not drawn (same as helper-tights).
  - bangs in community packs are their own MHCLO, not the helper front curtain.

Rendering helper-hair as hair produced slab "bangs" over the face.
These shells offset the actual skull/nape skin by a few centimetres.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "models" / "base.obj"
OUT = ROOT / "models" / "hair"

HEADER = """# Tight hair from hm08 body scalp (CC0). Not helper-hair.
# MakeClothes: hair is a proxy fitted to helper/body; helpers are not rendered.
# https://static.makehumancommunity.org/assets/creatingassets/makeclothes/introduction.html
o {name}
g {name}
"""


def load_obj(path: Path):
    verts = []
    groups = defaultdict(list)
    current = "none"
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            verts.append(tuple(map(float, line.split()[1:4])))
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


def centroid(verts, face):
    n = len(face)
    return (
        sum(verts[i][0] for i in face) / n,
        sum(verts[i][1] for i in face) / n,
        sum(verts[i][2] for i in face) / n,
    )


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
    return [verts[i] for i in used], [[index[i] for i in face] for face in faces]


def boundary_edges(faces):
    count = defaultdict(int)
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            count[tuple(sorted((a, b)))] += 1
    return [key for key, n in count.items() if n == 1]


def write_obj(path: Path, verts, faces, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks = [HEADER.format(name=name)]
    for x, y, z in verts:
        chunks.append(f"v {x:.5f} {y:.5f} {z:.5f}\n")
    for face in faces:
        chunks.append("f " + " ".join(str(i + 1) for i in face) + "\n")
    path.write_text("".join(chunks))
    print(f"wrote {path} v={len(verts)} f={len(faces)}")


def is_face_skin(x, y, z) -> bool:
    return z > 1.14 and y < 8.08


def is_scalp(x, y, z) -> bool:
    return y >= 7.48 and not is_face_skin(x, y, z)


def is_bob(x, y, z) -> bool:
    if is_scalp(x, y, z):
        return True
    if is_face_skin(x, y, z):
        return False
    if y >= 6.62 and z < 0.42 and abs(x) < 0.92:
        return True
    if y >= 6.85 and abs(x) > 0.52 and z < 0.85:
        return True
    return False


def is_long(x, y, z) -> bool:
    if is_bob(x, y, z):
        return True
    if is_face_skin(x, y, z):
        return False
    return y >= 5.05 and z < 0.32 and abs(x) < 0.72


def is_hairline(x, y, z) -> bool:
    return 7.84 <= y <= 8.14 and 0.98 <= z <= 1.40 and abs(x) < 0.40


def pick_faces(verts, faces, pred):
    return [face for face in faces if pred(*centroid(verts, face))]


def thin_shell(cage_verts, cage_faces, inner: float, outer: float) -> tuple[list, list]:
    normals = vertex_normals(cage_verts, cage_faces)
    n = len(cage_verts)
    inner_v = [add(p, scale(normals[i], inner)) for i, p in enumerate(cage_verts)]
    outer_v = [add(p, scale(normals[i], outer)) for i, p in enumerate(cage_verts)]
    verts = inner_v + outer_v
    faces = []
    for face in cage_faces:
        faces.append(list(reversed(face)))
        faces.append([i + n for i in face])
    for a, b in boundary_edges(cage_faces):
        faces.append([a, b, b + n, a + n])
    return verts, faces


def bangs_shell(cage_verts, cage_faces, hang: float) -> tuple[list, list]:
    """Thin fringe: stay close to the forehead, hang down, do not inflate into slabs."""
    normals = vertex_normals(cage_verts, cage_faces)
    n = len(cage_verts)
    inner_v = []
    outer_v = []
    for i, p in enumerate(cage_verts):
        t = max(0.0, min(1.0, (p[2] - 0.98) / 0.40))
        nrm = normals[i]
        inner_v.append(add(p, scale(nrm, 0.02)))
        hung = (p[0] + nrm[0] * 0.045, p[1] + nrm[1] * 0.045 - hang * t, p[2] + nrm[2] * 0.045 + 0.02 * t)
        outer_v.append(hung)
    verts = inner_v + outer_v
    faces = []
    for face in cage_faces:
        faces.append(list(reversed(face)))
        faces.append([i + n for i in face])
    for a, b in boundary_edges(cage_faces):
        faces.append([a, b, b + n, a + n])
    return verts, faces


def main() -> None:
    verts, groups = load_obj(BASE)
    body = groups["body"]
    styles = {
        "short": (is_scalp, 0.01, 0.055),
        "bob": (is_bob, 0.01, 0.07),
        "long": (is_long, 0.01, 0.08),
    }
    for name, (pred, inner, outer) in styles.items():
        cage_v, cage_f = remap(verts, pick_faces(verts, body, pred))
        write_obj(OUT / f"{name}.obj", *thin_shell(cage_v, cage_f, inner, outer), "hair")
    cage_v, cage_f = remap(verts, pick_faces(verts, body, is_hairline))
    write_obj(OUT / "bangs_brow.obj", *bangs_shell(cage_v, cage_f, 0.16), "bangs")
    write_obj(OUT / "bangs_face.obj", *bangs_shell(cage_v, cage_f, 0.38), "bangs")


if __name__ == "__main__":
    main()
