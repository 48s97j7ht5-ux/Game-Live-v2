"""Pack official MakeHuman default.mhskel + default_weights.mhw for hm08 web skinning.

Source (CC0): makehumancommunity/makehuman makehuman/data/rigs/
Requires models/base.obj rest coordinates (same vertex order as MakeHuman basemesh).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ = ROOT / "models/base.obj"
MH_SKEL = ROOT / "factory/mh/rigs/default.mhskel"
MH_WEIGHTS = ROOT / "factory/mh/rigs/default_weights.mhw"
OUT = ROOT / "web/data/body-skeleton.json"
BODY_VERTS = 13380


def parse_obj_verts(path: Path) -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            verts.append((float(x), float(y), float(z)))
    return verts


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vnorm(a):
    l = math.sqrt(vdot(a, a))
    if l < 1e-12:
        return (0.0, 1.0, 0.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def vmean(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        return (0.0, 0.0, 0.0)
    s = [0.0, 0.0, 0.0]
    for p in points:
        s[0] += p[0]
        s[1] += p[1]
        s[2] += p[2]
    n = float(len(points))
    return (s[0] / n, s[1] / n, s[2] / n)


def mat4_identity():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def mat4_mul(a, b):
    out = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = sum(a[i][k] * b[k][j] for k in range(4))
    return out


def mat4_inv(m):
    # Gauss-Jordan 4x4
    a = [row[:] for row in m]
    inv = mat4_identity()
    for col in range(4):
        pivot = col
        for row in range(col + 1, 4):
            if abs(a[row][col]) > abs(a[pivot][col]):
                pivot = row
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("singular matrix")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            inv[col], inv[pivot] = inv[pivot], inv[col]
        div = a[col][col]
        for j in range(4):
            a[col][j] /= div
            inv[col][j] /= div
        for row in range(4):
            if row == col:
                continue
            factor = a[row][col]
            for j in range(4):
                a[row][j] -= factor * a[col][j]
                inv[row][j] -= factor * inv[col][j]
    return inv


def bone_rest_matrix(
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
    normal: tuple[float, float, float],
) -> list[list[float]]:
    y_axis = vnorm(vsub(tail, head))
    n = vnorm(normal)
    z_axis = vnorm(vcross(n, y_axis))
    x_axis = vnorm(vcross(y_axis, z_axis))
    return [
        [x_axis[0], y_axis[0], z_axis[0], head[0]],
        [x_axis[1], y_axis[1], z_axis[1], head[1]],
        [x_axis[2], y_axis[2], z_axis[2], head[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def plane_normal(
    joints: dict[str, list[int]],
    planes: dict[str, list[str]],
    plane_name: str,
    verts: list[tuple[float, float, float]],
) -> tuple[float, float, float]:
    if plane_name not in planes:
        return (0.0, 1.0, 0.0)
    j1, j2, j3 = planes[plane_name]

    def jpos(name: str):
        idxs = joints.get(name, [])
        return vmean([verts[i] for i in idxs if i < len(verts)])

    p1, p2, p3 = jpos(j1), jpos(j2), jpos(j3)
    pvec = vnorm(vsub(p2, p1))
    yvec = vnorm(vsub(p3, p2))
    return vnorm(vcross(yvec, pvec))


def breadth_first_bones(bones: dict) -> list[str]:
    order: list[str] = []
    prev = -1
    while len(order) != len(bones) and prev != len(order):
        prev = len(order)
        for name, spec in bones.items():
            if name in order:
                continue
            parent = spec.get("parent")
            if not parent or parent in order:
                order.append(name)
    if len(order) != len(bones):
        raise RuntimeError("mhskel bone hierarchy cycle or missing parent")
    return order


def pack() -> dict:
    verts = parse_obj_verts(OBJ)
    skel = json.loads(MH_SKEL.read_text())
    weights_doc = json.loads(MH_WEIGHTS.read_text())
    joints = skel["joints"]
    planes = skel.get("planes", {})
    bones_def = skel["bones"]
    order = breadth_first_bones(bones_def)

    def joint_pos(joint_name: str):
        idxs = joints.get(joint_name, [])
        return vmean([verts[i] for i in idxs if i < len(verts)])

    rest_global: dict[str, list[list[float]]] = {}
    for name in order:
        spec = bones_def[name]
        head = joint_pos(spec["head"])
        tail = joint_pos(spec["tail"])
        roll = spec.get("rotation_plane", 0)
        if isinstance(roll, list):
            normal = (0.0, 1.0, 0.0)
            count = 0
            acc = [0.0, 0.0, 0.0]
            for plane_name in roll:
                n = plane_normal(joints, planes, plane_name, verts)
                if vdot(n, n) > 1e-8:
                    acc = vadd(acc, n)
                    count += 1
            if count:
                normal = vnorm(tuple(acc))
        elif isinstance(roll, str):
            normal = plane_normal(joints, planes, roll, verts)
        else:
            normal = (0.0, 1.0, 0.0)
        rest_global[name] = bone_rest_matrix(head, tail, normal)

    parents: list[int] = []
    inv_bind: list[float] = []
    for name in order:
        parent_name = bones_def[name].get("parent")
        parents.append(order.index(parent_name) if parent_name else -1)
        g = rest_global[name]
        if parent_name:
            pg = rest_global[parent_name]
            rel = mat4_mul(mat4_inv(pg), g)
        else:
            rel = g
        inv = mat4_inv(g)
        for row in inv:
            inv_bind.extend(row)

    bone_index = {name: i for i, name in enumerate(order)}
    vert_weights: list[list[tuple[int, float]]] = [[] for _ in range(BODY_VERTS)]
    for bone_name, pairs in weights_doc["weights"].items():
        if bone_name not in bone_index:
            continue
        bi = bone_index[bone_name]
        for vi, wt in pairs:
            if vi >= BODY_VERTS or wt <= 0:
                continue
            vert_weights[vi].append((bi, float(wt)))

    skin_index: list[int] = []
    skin_weight: list[float] = []
    for vi in range(BODY_VERTS):
        pairs = sorted(vert_weights[vi], key=lambda x: -x[1])[:4]
        total = sum(w for _, w in pairs) or 1.0
        idx = [p[0] for p in pairs]
        wts = [p[1] / total for p in pairs]
        while len(idx) < 4:
            idx.append(0)
            wts.append(0.0)
        skin_index.extend(idx)
        skin_weight.extend(wts)

    return {
        "mesh": "hm08",
        "license": "CC0 MakeHuman default.mhskel + default_weights.mhw",
        "source": "factory/mh/rigs/default.mhskel",
        "bodyVerts": BODY_VERTS,
        "bones": order,
        "parents": parents,
        "inverseBindMatrices": [round(x, 6) for x in inv_bind],
        "skinIndex": skin_index,
        "skinWeight": [round(x, 6) for x in skin_weight],
    }


def main() -> None:
    if not MH_SKEL.is_file() or not MH_WEIGHTS.is_file():
        raise FileNotFoundError("Run factory/fetch_mh_rig.py or vendor rigs under factory/mh/rigs/")
    data = pack()
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"skeleton bones {len(data['bones'])} -> {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
