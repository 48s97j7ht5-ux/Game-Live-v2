"""MakeHuman body pose units → skinMesh vertex deltas (factory only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from factory.mh_runtime import bootstrap, load_default_skeleton

ROOT = Path(__file__).resolve().parents[1]
BODY_JSON = ROOT / "factory/mh/poseunits/body-poseunits.json"
OBJ = ROOT / "models/base.obj"
REST_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

# (unit_name, weight, mirror_left_to_right)
PoseUnitSpec = tuple[str, float, bool]


def _quat_from_frame_mat(fr: np.ndarray) -> np.ndarray:
    import transformations as tm

    m4 = np.eye(4, dtype=np.float64)
    m4[:3, :4] = np.asarray(fr, dtype=np.float64)
    return tm.quaternion_from_matrix(m4, True)


def load_body_pose_json(path: Path = BODY_JSON) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def unit_bone_quats(
    body: dict,
    bone_map: dict[str, int],
    unit_name: str,
    *,
    mirror_lr: bool,
) -> dict[str, np.ndarray]:
    poses = body["poses"]
    if unit_name not in poses:
        raise KeyError(f"unknown body pose unit: {unit_name}")
    out: dict[str, np.ndarray] = {}
    for bname, quat in poses[unit_name].items():
        if bname not in bone_map:
            continue
        q = np.asarray(quat, dtype=np.float64)
        out[bname] = q
        if mirror_lr and bname.endswith(".L"):
            rb = bname[:-2] + ".R"
            if rb in bone_map:
                out[rb] = np.array([q[0], -q[1], q[2], q[3]], dtype=np.float64)
    return out


def blend_pose_units(
    skel,
    body: dict,
    units: Iterable[PoseUnitSpec],
) -> None:
    """Apply weighted body pose units; mutates skeleton pose."""
    import transformations as tm

    bone_map = skel.getBoneToIdxMapping()
    n_bones = skel.getBoneCount()
    acc = [REST_QUAT.copy() for _ in range(n_bones)]

    for unit_name, weight, mirror_lr in units:
        if weight <= 0:
            continue
        frame = np.zeros((n_bones, 3, 4), dtype=np.float32)
        frame[:, :3, :3] = np.eye(3, dtype=np.float32)
        for bname, q in unit_bone_quats(body, bone_map, unit_name, mirror_lr=mirror_lr).items():
            frame[bone_map[bname]] = tm.quaternion_matrix(q)[:3, :4]
        w = float(weight)
        for bi in range(n_bones):
            q_delta = tm.quaternion_slerp(REST_QUAT, _quat_from_frame_mat(frame[bi]), w)
            if np.allclose(acc[bi], REST_QUAT):
                acc[bi] = q_delta
            else:
                acc[bi] = tm.quaternion_multiply(q_delta, acc[bi])

    pose_mats = np.tile(np.identity(4, dtype=np.float32), (n_bones, 1, 1))
    for bi in range(n_bones):
        pose_mats[bi, :3, :4] = tm.quaternion_matrix(acc[bi])[:3, :4]
    skel.setToRestPose()
    skel.setPose(pose_mats)


def skin_rest_mesh(skel, human) -> tuple[np.ndarray, np.ndarray]:
    coords = human.getRestposeCoordinates().copy()
    skel.setToRestPose()
    mapping = skel.vertexWeights.data
    posed = skel.skinMesh(coords, mapping)
    return coords, posed


def bake_pose_vertices(units: Iterable[PoseUnitSpec]) -> np.ndarray:
    bootstrap()
    body = load_body_pose_json()
    skel, human = load_default_skeleton(OBJ)
    rest, _ = skin_rest_mesh(skel, human)
    blend_pose_units(skel, body, units)
    mapping = skel.vertexWeights.data
    posed = skel.skinMesh(rest, mapping)
    return posed
