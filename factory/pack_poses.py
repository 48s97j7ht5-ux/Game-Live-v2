"""Pack hm08 body poses from official MakeHuman modeling targets (CC0).

This is the only supported web pose path: same UniversalModifier deltas as
morph sliders (makehuman/data/targets/...), baked once in CI via pack_poses.py.

Runtime does not skin skeletons or apply body-poseunits quaternions in JS —
that path shredded the hm08 mesh. True skeletal poses need MH/MPFB export
(e.g. glTF) later; see factory/mh/POSES.md.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ = ROOT / "models/base.obj"
TARGETS = ROOT / "factory/mh/targets/armslegs"
OUT = ROOT / "web/data/body-poses.json"
BODY_VERTS = 13380

# Official arms/legs targets @ weight 1.0 (UniversalModifier: weight = |value|).
POSE_RECIPES = {
    "poseAkimbo": {
        "label": "руки в боки",
        "mix": [
            ("l-hand-trans-out.target", 1.0),
            ("r-hand-trans-out.target", 1.0),
            ("l-upperarm-scale-horiz-incr.target", 1.0),
            ("r-upperarm-scale-horiz-incr.target", 1.0),
            ("l-lowerarm-scale-horiz-incr.target", 1.0),
            ("r-lowerarm-scale-horiz-incr.target", 1.0),
        ],
    },
    "poseStep": {
        "label": "шаг",
        "mix": [
            ("l-foot-trans-forward.target", 1.0),
            ("r-foot-trans-backward.target", 1.0),
            ("l-foot-trans-up.target", 0.35),
            ("l-leg-valgus-incr.target", 0.4),
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
        "license": "CC0 MakeHuman arms/legs modeling targets",
        "method": "official-targets-v1",
        "source": "makehumancommunity/makehuman makehuman/data/targets/arms_legs",
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
    assert len(data["poses"]) == 3
    assert data["method"] == "official-targets-v1"
    assert len(data["targets"]["poseAkimbo"]["s"]) > 500
    assert len(data["targets"]["poseStep"]["s"]) > 200
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(
        f"poses {len(data['poses'])} indices {len(data['index'])} "
        f"akimbo {len(data['targets']['poseAkimbo']['s'])} step {len(data['targets']['poseStep']['s'])} -> {OUT}"
    )


if __name__ == "__main__":
    main()
