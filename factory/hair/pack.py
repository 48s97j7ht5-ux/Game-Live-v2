#!/usr/bin/env python3
"""Pack clay hair as MakeHuman clothes (type Hair): OBJ + MHCLO + mhmat.

Official MH / MakeClothes:
  Hair is clothes (data/hair). Helper-hair is a fitting cage and is not drawn.
  ProxyRefVert.fromTriple: vert = w0*h[v0]+w1*h[v1]+w2*h[v2] + offset.
  Community packs ship bangs as a second MHCLO, not as part of the bob.

Geometry: thin scalp shells from hm08 ``g body`` (same filters as the previous
export). These are placeholders until a fitted community hair OBJ is dropped in.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "models" / "base.obj"
OUT = ROOT / "models" / "hair"

HEADER = """# Tight hair from hm08 body scalp (CC0). Not helper-hair.
# MakeHuman clothes type Hair: mesh + MHCLO proxy. Helpers are not rendered.
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


def thin_shell(cage_verts, cage_faces, inner: float, outer: float):
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


def bangs_shell(cage_verts, cage_faces, hang: float):
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


def _head_indices(body_verts):
    return [i for i, p in enumerate(body_verts) if p[1] >= 4.8]


def _buckets(body_verts, candidates, step=0.12):
    boxes = defaultdict(list)
    for i in candidates:
        x, y, z = body_verts[i]
        boxes[(int(x / step), int(y / step), int(z / step))].append(i)
    return boxes, step


def _nearest3(pt, body_verts, boxes, step):
    gx, gy, gz = int(pt[0] / step), int(pt[1] / step), int(pt[2] / step)
    nearby = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nearby.extend(boxes.get((gx + dx, gy + dy, gz + dz), ()))
    pool = nearby or [i for bucket in boxes.values() for i in bucket]
    scored = sorted(
        pool,
        key=lambda i: (body_verts[i][0] - pt[0]) ** 2
        + (body_verts[i][1] - pt[1]) ** 2
        + (body_verts[i][2] - pt[2]) ** 2,
    )
    if len(scored) < 3:
        scored = (scored + [0, 1, 2])[:3]
    return scored[:3]


def write_mhclo(path: Path, *, name: str, obj_name: str, verts, body_verts, z_depth: int) -> None:
    """MakeClothes-style proxy. See makehuman/shared/proxy.py ProxyRefVert.fromTriple."""
    candidates = _head_indices(body_verts)
    boxes, step = _buckets(body_verts, candidates)
    weights = (0.5, 0.3, 0.2)
    lines = [
        "# Game-Live hair proxy (MakeHuman clothes type Hair)",
        f"name {name}",
        "uuid game-live-hair-placeholder",
        "basemesh hm08",
        f"obj_file {obj_name}",
        f"material {name}.mhmat",
        f"z_depth {z_depth}",
        "x_scale 4108 4168 1.4980",
        "y_scale 15080 4793 1.9221",
        "z_scale 13716 13383 1.0299",
        "max_pole 8",
        "verts 0",
    ]
    for pt in verts:
        i0, i1, i2 = _nearest3(pt, body_verts, boxes, step)
        hx = weights[0] * body_verts[i0][0] + weights[1] * body_verts[i1][0] + weights[2] * body_verts[i2][0]
        hy = weights[0] * body_verts[i0][1] + weights[1] * body_verts[i1][1] + weights[2] * body_verts[i2][1]
        hz = weights[0] * body_verts[i0][2] + weights[1] * body_verts[i1][2] + weights[2] * body_verts[i2][2]
        lines.append(
            "  %d %d %d %.4f %.4f %.4f %.4f %.4f %.4f"
            % (i0, i1, i2, weights[0], weights[1], weights[2], pt[0] - hx, pt[1] - hy, pt[2] - hz)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mhmat(path: Path, name: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"name {name}",
                "description Game-Live hair placeholder material",
                "diffuseColor 0.12 0.08 0.06",
                "specularColor 0.08 0.08 0.08",
                "shininess 0.12",
                "transparent True",
                "alphaToCoverage True",
                "backfaceCull False",
                "shadeless False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def pack() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    verts, groups = load_obj(BASE)
    body = groups["body"]
    written = []
    styles = {
        "short": (is_scalp, 0.01, 0.055, 80),
        "bob": (is_bob, 0.01, 0.07, 80),
        "long": (is_long, 0.01, 0.08, 80),
    }
    for name, (pred, inner, outer, z_depth) in styles.items():
        cage_v, cage_f = remap(verts, pick_faces(verts, body, pred))
        mesh_v, mesh_f = thin_shell(cage_v, cage_f, inner, outer)
        write_obj(OUT / f"{name}.obj", mesh_v, mesh_f, "hair")
        write_mhclo(OUT / f"{name}.mhclo", name=name, obj_name=f"{name}.obj", verts=mesh_v, body_verts=verts, z_depth=z_depth)
        write_mhmat(OUT / f"{name}.mhmat", name)
        written.append({"id": name, "verts": len(mesh_v), "faces": len(mesh_f)})
    cage_v, cage_f = remap(verts, pick_faces(verts, body, is_hairline))
    for name, hang in (("bangs_brow", 0.16), ("bangs_face", 0.38)):
        mesh_v, mesh_f = bangs_shell(cage_v, cage_f, hang)
        write_obj(OUT / f"{name}.obj", mesh_v, mesh_f, "bangs")
        write_mhclo(OUT / f"{name}.mhclo", name=name, obj_name=f"{name}.obj", verts=mesh_v, body_verts=verts, z_depth=82)
        write_mhmat(OUT / f"{name}.mhmat", name)
        written.append({"id": name, "verts": len(mesh_v), "faces": len(mesh_f)})
    (OUT / "NOTICE").write_text(
        "Hair is MakeHuman clothes type Hair: mesh + MHCLO proxy + mhmat.\n"
        "helper-hair is not exported and must not be drawn.\n"
        "These OBJ shells offset the hm08 body scalp/nape (CC0). They are\n"
        "placeholders until a fitted community MHCLO (hair01 / similar) is dropped in.\n"
        "Bangs are a separate clothes layer, as in community packs.\n"
        "MPFB Hair Editor (Blender curves: frizz/curl/clump) does not apply to mesh shells.\n",
        encoding="utf-8",
    )
    return {"files": written}


if __name__ == "__main__":
    print(json.dumps(pack(), indent=2))
