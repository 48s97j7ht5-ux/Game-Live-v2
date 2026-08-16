"""Bake hm08 pose vertex deltas from official MakeHuman body pose units.

MakeHuman poses are skeleton pose units (bone quaternions in
makehuman/data/poseunits/body-poseunits.json), not modeling sliders.
We rotate body vertices in weighted regions around hm08 joint helper
centroids — same data MH uses before skinning.

Modeling .target mixes are intentionally not used for poses (too subtle).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ = ROOT / "models/base.obj"
POSEUNITS = ROOT / "factory/mh/poseunits/body-poseunits.json"
OUT = ROOT / "web/data/body-poses.json"
BODY_VERTS = 13380

# MH rig bone → hm08 helper joint group centroid in models/base.obj
BONE_JOINT = {
    "shoulder.L": "joint-l-shoulder",
    "upperarm01.L": "joint-l-elbow",
    "upperarm02.L": "joint-l-hand",
    "wrist.L": "joint-l-hand",
    "scapula.L": "joint-l-clavicle",
    "pelvis.L": "joint-pelvis",
    "upperleg.L": "joint-l-upper-leg",
    "lowerleg.L": "joint-l-knee",
}

BONE_RADIUS = {
    "shoulder.L": 1.65,
    "upperarm01.L": 1.25,
    "upperarm02.L": 1.05,
    "wrist.L": 0.95,
    "scapula.L": 1.45,
    "pelvis.L": 1.85,
    "upperleg.L": 1.55,
    "lowerleg.L": 1.25,
    "pelvis.R": 1.85,
    "upperleg.R": 1.55,
    "lowerleg.R": 1.25,
}

POSE_STRENGTH = 1.35

# Official unit names from body-poseunits.json (Left-side definitions; Right mirrored).
POSE_RECIPES = {
    "poseAkimbo": {
        "label": "руки в боки",
        "units": ["UpperArmDownLeft", "UpperArmRollOutLeft", "LowerArmBend1Left1", "HandDownLeft"],
        "mirror": True,
    },
    "poseStep": {
        "label": "шаг",
        "units_left": ["UpperLegForwardLeft", "LowerLegBendLeft1"],
        "units_right": ["UpperLegBackwardLeft"],
    },
}


def parse_obj_verts(path: Path) -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            verts.append((float(x), float(y), float(z)))
    return verts


def joint_centroids(path: Path) -> dict[str, tuple[float, float, float]]:
    verts = parse_obj_verts(path)
    group = ""
    sums: dict[str, list[float]] = {}
    for line in path.read_text().splitlines():
        if line.startswith("g "):
            group = line.split()[1]
        elif line.startswith("f ") and group.startswith("joint"):
            for item in line.split()[1:]:
                index = int(item.split("/")[0]) - 1
                if index >= len(verts):
                    continue
                x, y, z = verts[index]
                bucket = sums.setdefault(group, [0.0, 0.0, 0.0, 0.0])
                bucket[0] += x
                bucket[1] += y
                bucket[2] += z
                bucket[3] += 1.0
    out: dict[str, tuple[float, float, float]] = {}
    for name, (sx, sy, sz, n) in sums.items():
        if n:
            out[name] = (sx / n, sy / n, sz / n)
    return out


def quat_mul(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def quat_normalize(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    return (w / n, x / n, y / n, z / n)


def quat_rotate_vec(q: tuple[float, float, float, float], v: tuple[float, float, float]) -> tuple[float, float, float]:
    w, x, y, z = quat_normalize(q)
    vx, vy, vz = v
    ix = w * vx + y * vz - z * vy
    iy = w * vy + z * vx - x * vz
    iz = w * vz + x * vy - y * vx
    iw = -x * vx - y * vy - z * vz
    return (
        ix * w + iw * -x + iy * -z - iz * -y,
        iy * w + iw * -y + iz * -x - ix * -z,
        iz * w + iw * -z + ix * -y - iy * -x,
    )


def mirror_bone(name: str) -> str:
    if name.endswith(".L"):
        return name[:-2] + ".R"
    if name.endswith(".R"):
        return name[:-2] + ".L"
    return name


def mirror_quat_for_right(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    w, x, y, z = q
    return (w, -x, y, -z)


def pivot_for_bone(bone: str, joints: dict[str, tuple[float, float, float]]) -> tuple[float, float, float] | None:
    key = bone
    if bone.endswith(".R"):
        key = mirror_bone(bone)
    joint_name = BONE_JOINT.get(key)
    if not joint_name:
        return None
    if bone.endswith(".R"):
        joint_name = joint_name.replace("joint-l-", "joint-r-")
    pivot = joints.get(joint_name)
    if not pivot:
        return None
    if bone.endswith(".R"):
        return (-pivot[0], pivot[1], pivot[2])
    return pivot


def side_weight(bone: str, x: float) -> float:
    if bone.endswith(".L"):
        return 1.0 if x <= 0.06 else max(0.0, 1.0 - (x - 0.06) / 0.12)
    if bone.endswith(".R"):
        return 1.0 if x >= -0.06 else max(0.0, 1.0 - (-0.06 - x) / 0.12)
    return 1.0


def apply_unit(
    pos: list[tuple[float, float, float]],
    unit: dict[str, list[float]],
    joints: dict[str, tuple[float, float, float]],
    *,
    mirror_right: bool,
) -> None:
    for bone, quat_raw in unit.items():
        if len(quat_raw) != 4:
            continue
        q = tuple(float(v) for v in quat_raw)
        targets = [(bone, q)]
        if mirror_right and bone.endswith(".L"):
            rb = mirror_bone(bone)
            targets.append((rb, mirror_quat_for_right(q)))
        for bname, quat in targets:
            pivot = pivot_for_bone(bname, joints)
            if not pivot:
                continue
            radius = BONE_RADIUS.get(bname, BONE_RADIUS.get(mirror_bone(bname) if bname.endswith(".R") else bname, 1.0))
            px, py, pz = pivot
            for i in range(BODY_VERTS):
                x, y, z = pos[i]
                sw = side_weight(bname, x)
                if sw <= 0:
                    continue
                dx, dy, dz = x - px, y - py, z - pz
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist >= radius:
                    continue
                w = sw * (1.0 - dist / radius) ** 2
                if w <= 0:
                    continue
                rx, ry, rz = quat_rotate_vec(quat, (dx, dy, dz))
                nx, ny, nz = px + dx + (rx - dx) * w, py + dy + (ry - dy) * w, pz + dz + (rz - dz) * w
                pos[i] = (nx, ny, nz)


def bake_pose(units: list[str], pose_data: dict, joints: dict[str, tuple[float, float, float]], *, mirror: bool) -> dict[int, tuple[float, float, float]]:
    rest = parse_obj_verts(OBJ)
    pos = rest[:BODY_VERTS]
    for name in units:
        unit = pose_data["poses"].get(name)
        if unit:
            apply_unit(pos, unit, joints, mirror_right=mirror)
    deltas: dict[int, tuple[float, float, float]] = {}
    for i in range(BODY_VERTS):
        dx = pos[i][0] - rest[i][0]
        dy = pos[i][1] - rest[i][1]
        dz = pos[i][2] - rest[i][2]
        if dx or dy or dz:
            deltas[i] = (dx * POSE_STRENGTH, dy * POSE_STRENGTH, dz * POSE_STRENGTH)
    return deltas


def bake_step(pose_data: dict, joints: dict[str, tuple[float, float, float]]) -> dict[int, tuple[float, float, float]]:
    rest = parse_obj_verts(OBJ)
    pos = rest[:BODY_VERTS]
    for name in POSE_RECIPES["poseStep"]["units_left"]:
        unit = pose_data["poses"].get(name)
        if unit:
            apply_unit(pos, unit, joints, mirror_right=False)
    for name in POSE_RECIPES["poseStep"]["units_right"]:
        unit = pose_data["poses"].get(name)
        if unit:
            apply_unit(pos, unit, joints, mirror_right=True)
    deltas: dict[int, tuple[float, float, float]] = {}
    for i in range(BODY_VERTS):
        dx = pos[i][0] - rest[i][0]
        dy = pos[i][1] - rest[i][1]
        dz = pos[i][2] - rest[i][2]
        if dx or dy or dz:
            deltas[i] = (dx * POSE_STRENGTH, dy * POSE_STRENGTH, dz * POSE_STRENGTH)
    return deltas


def pack() -> dict:
    pose_data = json.loads(POSEUNITS.read_text())
    joints = joint_centroids(OBJ)
    loaded = {
        "poseAkimbo": bake_pose(POSE_RECIPES["poseAkimbo"]["units"], pose_data, joints, mirror=True),
        "poseStep": bake_step(pose_data, joints),
    }
    indices = sorted({index for pose in loaded.values() for index in pose})
    packed = {
        "mesh": "hm08",
        "license": "CC0 MakeHuman body pose units",
        "source": "factory/mh/poseunits/body-poseunits.json",
        "index": indices,
        "rest": [],
        "targets": {},
        "poses": [
            {"id": "rest", "label": "стоя", "key": None},
            {"id": "akimbo", "label": POSE_RECIPES["poseAkimbo"]["label"], "key": "poseAkimbo"},
            {"id": "step", "label": POSE_RECIPES["poseStep"]["label"], "key": "poseStep"},
        ],
    }
    verts = parse_obj_verts(OBJ)
    for index in indices:
        x, y, z = verts[index]
        packed["rest"].extend([round(x, 4), round(y, 4), round(z, 4)])
    for name, pose in loaded.items():
        slots = []
        deltas = []
        for slot, index in enumerate(indices):
            dx, dy, dz = pose.get(index, (0.0, 0.0, 0.0))
            if dx == 0 and dy == 0 and dz == 0:
                continue
            slots.append(slot)
            deltas.extend([round(dx, 4), round(dy, 4), round(dz, 4)])
        packed["targets"][name] = {"s": slots, "d": deltas}
    return packed


def main() -> None:
    data = pack()
    assert len(data["poses"]) == 3
    assert len(data["targets"]["poseAkimbo"]["s"]) > 800
    assert len(data["targets"]["poseStep"]["s"]) > 300
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(
        f"poses {len(data['poses'])} indices {len(data['index'])} "
        f"akimbo {len(data['targets']['poseAkimbo']['s'])} step {len(data['targets']['poseStep']['s'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
