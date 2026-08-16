"""Pack hm08 pose deltas from official MakeHuman arms/legs targets.

Poses are fixed recipes (not sliders): each pose merges CC0 .target files at
set weights, then stores one sparse delta blob keyed like body-targets.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ = ROOT / "models/base.obj"
TARGETS = ROOT / "factory/mh/targets/armslegs"
OUT = ROOT / "web/data/body-poses.json"
BODY_VERTS = 13380

POSE_RECIPES = {
    "poseAkimbo": {
        "label": "руки в боки",
        "mix": [
            ("l-hand-trans-out.target", 0.92),
            ("r-hand-trans-out.target", 0.92),
            ("l-upperarm-scale-horiz-incr.target", 0.35),
            ("r-upperarm-scale-horiz-incr.target", 0.35),
        ],
    },
    "poseStep": {
        "label": "шаг",
        "mix": [
            ("l-foot-trans-forward.target", 0.75),
            ("r-foot-trans-backward.target", 0.65),
            ("l-leg-valgus-incr.target", 0.25),
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


def parse_target(path: Path) -> dict[int, tuple[float, float, float]]:
    out: dict[int, tuple[float, float, float]] = {}
    for line in path.read_text().splitlines():
        if not line or line[0] == "#":
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        index = int(parts[0])
        if index >= BODY_VERTS:
            continue
        out[index] = (float(parts[1]), float(parts[2]), float(parts[3]))
    return out


def merge_recipe(mix: list[tuple[str, float]]) -> dict[int, tuple[float, float, float]]:
    merged: dict[int, tuple[float, float, float]] = {}
    for filename, weight in mix:
        path = TARGETS / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
        for index, (dx, dy, dz) in parse_target(path).items():
            ox, oy, oz = merged.get(index, (0.0, 0.0, 0.0))
            merged[index] = (ox + dx * weight, oy + dy * weight, oz + dz * weight)
    return merged


def pack() -> dict:
    verts = parse_obj_verts(OBJ)
    loaded = {key: merge_recipe(rec["mix"]) for key, rec in POSE_RECIPES.items()}
    indices = sorted({index for pose in loaded.values() for index in pose})
    packed = {
        "mesh": "hm08",
        "license": "CC0 MakeHuman arms/legs targets",
        "index": indices,
        "rest": [],
        "targets": {},
        "poses": [{"id": "rest", "label": "стоя", "key": None}]
        + [{"id": key.replace("pose", "").lower() or "rest", "label": rec["label"], "key": key} for key, rec in POSE_RECIPES.items()],
    }
    # Fix pose ids to be readable
    packed["poses"] = [
        {"id": "rest", "label": "стоя", "key": None},
        {"id": "akimbo", "label": POSE_RECIPES["poseAkimbo"]["label"], "key": "poseAkimbo"},
        {"id": "step", "label": POSE_RECIPES["poseStep"]["label"], "key": "poseStep"},
    ]
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
    assert data["targets"]["poseAkimbo"]["s"]
    assert data["targets"]["poseStep"]["s"]
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"poses {len(data['poses'])} indices {len(data['index'])} -> {OUT}")


if __name__ == "__main__":
    main()
