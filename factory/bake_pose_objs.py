"""Official MakeHuman body poses → posed OBJ (factory only).

Pipeline (makehuman/shared/skeleton.py):
  default.mhskel + default_weights.mhw + body-poseunits.json
  → blend units → setPose → skinMesh(rest)

Writes models/poses/<id>.obj (same v order as models/base.obj, basemesh only deformed).
Viewer swaps basemesh coordinates by vertex index — no runtime skeleton.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from factory.mh_pose_bake import PoseUnitSpec, bake_pose_vertices, load_body_pose_json

BASE_OBJ = ROOT / "models/base.obj"
POSE_DIR = ROOT / "models/poses"
CATALOG = ROOT / "web/data/body-poses.json"
BODY_VERTS = 13380

POSE_RECIPES: dict[str, dict] = {
    "poseAkimbo": {
        "label": "руки в боки",
        "file": "akimbo.obj",
        "units": [
            ("UpperArmRollOutLeft", 1.0, True),
            ("UpperArmDownLeft", 0.65, True),
            ("LowerArmBend1Left1", 0.85, True),
            ("HandBendOutLeft", 0.45, True),
        ],
    },
    "poseStep": {
        "label": "шаг",
        "file": "step.obj",
        "units": [
            ("UpperLegForwardLeft", 1.0, False),
            ("UpperLegBackwardLeft", 0.85, True),
            ("LowerLegBendLeft1", 0.35, False),
            ("FootUpLeft", 0.25, False),
        ],
    },
}


def read_base_lines() -> list[str]:
    return BASE_OBJ.read_text(encoding="utf-8").splitlines()


def write_posed_obj(lines: list[str], posed: np.ndarray, dest: Path) -> None:
    vi = 0
    out: list[str] = []
    for line in lines:
        if line.startswith("v "):
            if vi < BODY_VERTS:
                x, y, z = float(posed[vi, 0]), float(posed[vi, 1]), float(posed[vi, 2])
                out.append(f"v {x:.4f} {y:.4f} {z:.4f}")
            else:
                out.append(line)
            vi += 1
        else:
            out.append(line)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")


def validate_pose(rest: np.ndarray, posed: np.ndarray, name: str) -> None:
    d = np.linalg.norm(posed[:BODY_VERTS] - rest[:BODY_VERTS], axis=1)
    if float(d.max()) > 3.5:
        raise ValueError(f"{name}: suspicious max displacement {d.max()}")
    if int((d > 1e-4).sum()) < 500:
        raise ValueError(f"{name}: pose moves too few basemesh verts")


def main() -> None:
    load_body_pose_json()
    lines = read_base_lines()
    vcount = sum(1 for ln in lines if ln.startswith("v "))
    if vcount < BODY_VERTS:
        raise ValueError(f"base.obj has {vcount} verts, need {BODY_VERTS}")

    from factory.mh_runtime import bootstrap, load_default_skeleton

    bootstrap()
    skel, human = load_default_skeleton(BASE_OBJ)
    rest = human.getRestposeCoordinates()[:BODY_VERTS]

    catalog_poses = [{"id": "rest", "label": "стоя", "key": None, "obj": None}]
    for key, rec in POSE_RECIPES.items():
        posed = bake_pose_vertices(rec["units"])
        validate_pose(rest, posed, key)
        out_path = POSE_DIR / rec["file"]
        write_posed_obj(lines, posed, out_path)
        pose_id = "akimbo" if key == "poseAkimbo" else "step"
        catalog_poses.append(
            {"id": pose_id, "label": rec["label"], "key": key, "obj": f"./models/poses/{rec['file']}"}
        )
        print(f"{key} -> {out_path}")

    catalog = {
        "mesh": "hm08",
        "method": "mh-posed-obj-v1",
        "license": "CC0 MakeHuman body-poseunits + default rig (skinMesh factory bake)",
        "vertexCount": BODY_VERTS,
        "poses": catalog_poses,
    }
    CATALOG.write_text(json.dumps(catalog, separators=(",", ":")), encoding="utf-8")
    print(f"catalog -> {CATALOG}")


if __name__ == "__main__":
    main()
