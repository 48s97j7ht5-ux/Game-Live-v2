"""Find lip and cheek vertex indices on the clay hm08 body by position.

base.obj has no named lip/cheek group (only "g body" for the whole face),
so we pick vertices geometrically, the same way viewer.js finds "head" and
"face" vertices for the camera crop. Indices are into the raw v-line order
of models/base.obj (index < BODY_VERTS is guaranteed body, not a helper).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_OBJ = ROOT / "models/base.obj"
OUT = ROOT / "web/data/makeup-zones.json"
BODY_VERTS = 13380

MOUTH_Y = (6.42, 6.78)
MOUTH_X_ABS = 0.36
MOUTH_Z_MIN = 0.85

CHEEK_Y = (6.55, 7.15)
CHEEK_X_ABS = (0.45, 1.05)
CHEEK_Z_MIN = 0.4


def load_verts() -> list[tuple[float, float, float]]:
    verts = []
    for line in BASE_OBJ.read_text().splitlines():
        if line.startswith("v "):
            x, y, z = (float(v) for v in line.split()[1:4])
            verts.append((x, y, z))
    return verts


def find_zones() -> dict[str, list[int]]:
    verts = load_verts()[:BODY_VERTS]
    lips = [
        i
        for i, (x, y, z) in enumerate(verts)
        if MOUTH_Y[0] <= y <= MOUTH_Y[1] and abs(x) <= MOUTH_X_ABS and z >= MOUTH_Z_MIN
    ]
    cheeks = [
        i
        for i, (x, y, z) in enumerate(verts)
        if CHEEK_Y[0] <= y <= CHEEK_Y[1] and CHEEK_X_ABS[0] <= abs(x) <= CHEEK_X_ABS[1] and z >= CHEEK_Z_MIN
    ]
    return {"lips": lips, "cheeks": cheeks}


def main() -> None:
    zones = find_zones()
    assert 200 <= len(zones["lips"]) <= 900, len(zones["lips"])
    assert 200 <= len(zones["cheeks"]) <= 900, len(zones["cheeks"])
    OUT.write_text(json.dumps(zones))
    print(f"lips {len(zones['lips'])} cheeks {len(zones['cheeks'])} -> {OUT}")


if __name__ == "__main__":
    main()
