"""Bake hm08 body poses via MakeHuman skeleton.skinMesh().

NOT USED IN CI — shredded hm08 in the browser. See factory/mh/POSES.md.
Kept for a future glTF export path only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from factory.mh_pose_bake import PoseUnitSpec, bake_pose_vertices, load_body_pose_json

OBJ = ROOT / "models/base.obj"
OUT = ROOT / "web/data/body-poses.json"
BODY_VERTS = 13380

# Official body-poseunits.json blends (see factory/mh/recipes/*.json).
POSE_RECIPES: dict[str, dict] = {
    "poseAkimbo": {
        "label": "руки в боки",
        "units": [
            ("UpperArmRollOutLeft", 1.0, True),
            ("UpperArmDownLeft", 0.65, True),
            ("LowerArmBend1Left1", 0.85, True),
            ("HandBendOutLeft", 0.45, True),
        ],
    },
    "poseStep": {
        "label": "шаг",
        "units": [
            ("UpperLegForwardLeft", 1.0, False),
            ("UpperLegBackwardLeft", 0.85, True),
            ("LowerLegBendLeft1", 0.35, False),
            ("FootUpLeft", 0.25, False),
        ],
    },
}


def parse_obj_verts(path: Path) -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            verts.append((float(x), float(y), float(z)))
    return verts


def delta_dict(rest: list[tuple[float, float, float]], posed) -> dict[int, tuple[float, float, float]]:
    out: dict[int, tuple[float, float, float]] = {}
    for i, (x, y, z) in enumerate(rest):
        if i >= BODY_VERTS:
            continue
        px, py, pz = float(posed[i, 0]), float(posed[i, 1]), float(posed[i, 2])
        dx, dy, dz = px - x, py - y, pz - z
        if abs(dx) + abs(dy) + abs(dz) < 1e-6:
            continue
        out[i] = (dx, dy, dz)
    return out


def pack() -> dict:
    load_body_pose_json()
    verts = parse_obj_verts(OBJ)
    if len(verts) < BODY_VERTS:
        raise ValueError(f"hm08 body too small: {len(verts)} verts")

    loaded: dict[str, dict[int, tuple[float, float, float]]] = {}
    for key, rec in POSE_RECIPES.items():
        units: list[PoseUnitSpec] = rec["units"]
        posed = bake_pose_vertices(units)
        loaded[key] = delta_dict(verts, posed)

    indices = sorted({index for pose in loaded.values() for index in pose})
    packed = {
        "mesh": "hm08",
        "license": "CC0 MakeHuman body-poseunits + default rig (skinMesh bake)",
        "method": "mh-skinmesh-v1",
        "note": "Baked with makehuman/shared/skeleton.skinMesh; units in factory/mh/recipes/",
        "index": indices,
        "rest": [],
        "targets": {},
        "poses": [
            {"id": "rest", "label": "стоя", "key": None},
            {"id": "akimbo", "label": POSE_RECIPES["poseAkimbo"]["label"], "key": "poseAkimbo"},
            {"id": "step", "label": POSE_RECIPES["poseStep"]["label"], "key": "poseStep"},
        ],
    }
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
            deltas.extend([round(dx, 4), round(dy, 4), round(z, 4)])
        packed["targets"][name] = {"s": slots, "d": deltas}
    return packed


def main() -> None:
    data = pack()
    assert data["method"] == "mh-skinmesh-v1"
    assert len(data["poses"]) == 3
    assert len(data["targets"]["poseAkimbo"]["s"]) > 1000
    assert len(data["targets"]["poseStep"]["s"]) > 1000
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(
        f"baked {len(data['poses'])} poses index={len(data['index'])} "
        f"akimbo={len(data['targets']['poseAkimbo']['s'])} "
        f"step={len(data['targets']['poseStep']['s'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
