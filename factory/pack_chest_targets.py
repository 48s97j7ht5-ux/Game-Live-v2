"""Pack MakeHuman hm08 body targets into compact JSON for the web viewer.

Source files are CC0 MakeHuman targets (basemesh hm08). Only body vertices
(index < 13380) are kept so helper meshes are ignored.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BODY_VERTS = 13380

TARGET_FILES = {
    "minCupMinFirm": "breast/female-young-averagemuscle-averageweight-mincup-minfirmness.target",
    "minCupMaxFirm": "breast/female-young-averagemuscle-averageweight-mincup-maxfirmness.target",
    "maxCupMinFirm": "breast/female-young-averagemuscle-averageweight-maxcup-minfirmness.target",
    "maxCupMaxFirm": "breast/female-young-averagemuscle-averageweight-maxcup-maxfirmness.target",
    "distDecr": "breast/breast-dist-decr.target",
    "distIncr": "breast/breast-dist-incr.target",
    "pointDecr": "breast/breast-point-decr.target",
    "pointIncr": "breast/breast-point-incr.target",
    "transDown": "breast/breast-trans-down.target",
    "transUp": "breast/breast-trans-up.target",
    "volDown": "breast/breast-volume-vert-down.target",
    "volUp": "breast/breast-volume-vert-up.target",
    "nippleSizeDecr": "breast/nipple-size-decr.target",
    "nippleSizeIncr": "breast/nipple-size-incr.target",
    "nipplePointDecr": "breast/nipple-point-decr.target",
    "nipplePointIncr": "breast/nipple-point-incr.target",
    "stomachToneDecr": "stomach/stomach-tone-decr.target",
    "stomachToneIncr": "stomach/stomach-tone-incr.target",
    "stomachBellyDecr": "stomach/stomach-pregnant-decr.target",
    "stomachBellyIncr": "stomach/stomach-pregnant-incr.target",
    "navelDown": "stomach/stomach-navel-down.target",
    "navelUp": "stomach/stomach-navel-up.target",
    "navelIn": "stomach/stomach-navel-in.target",
    "navelOut": "stomach/stomach-navel-out.target",
    "buttDecr": "buttocks/buttocks-volume-decr.target",
    "buttIncr": "buttocks/buttocks-volume-incr.target",
    "pelvisToneDecr": "pelvis/pelvis-tone-decr.target",
    "pelvisToneIncr": "pelvis/pelvis-tone-incr.target",
    "hipHorizDecr": "hip/hip-scale-horiz-decr.target",
    "hipHorizIncr": "hip/hip-scale-horiz-incr.target",
    "hipDepthDecr": "hip/hip-scale-depth-decr.target",
    "hipDepthIncr": "hip/hip-scale-depth-incr.target",
    "hipVertDecr": "hip/hip-scale-vert-decr.target",
    "hipVertIncr": "hip/hip-scale-vert-incr.target",
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


def pack(obj_path: Path, targets_dir: Path) -> dict:
    verts = parse_obj_verts(obj_path)
    loaded = {name: parse_target(targets_dir / filename) for name, filename in TARGET_FILES.items()}
    indices = sorted({index for target in loaded.values() for index in target})
    packed = {
        "mesh": "hm08",
        "license": "CC0 MakeHuman body targets",
        "index": indices,
        "rest": [],
        "targets": {},
    }
    for index in indices:
        x, y, z = verts[index]
        packed["rest"].extend([round(x, 4), round(y, 4), round(z, 4)])
    for name, target in loaded.items():
        slots = []
        deltas = []
        for slot, index in enumerate(indices):
            dx, dy, dz = target.get(index, (0.0, 0.0, 0.0))
            if dx == 0 and dy == 0 and dz == 0:
                continue
            slots.append(slot)
            deltas.extend([round(dx, 4), round(dy, 4), round(dz, 4)])
        packed["targets"][name] = {"s": slots, "d": deltas}
    return packed


def main() -> None:
    obj_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mh/base.obj")
    targets_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/mh")
    out_path = Path(sys.argv[3] if len(sys.argv) > 3 else "web/data/body-targets.json")
    packed = pack(obj_path, targets_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packed, separators=(",", ":")))
    print(f"wrote {out_path} verts={len(packed['index'])} bytes={out_path.stat().st_size}")


if __name__ == "__main__":
    main()
