"""Pack hm08 body pose recipes from official MakeHuman body-poseunits.json.

Poses are applied at runtime via skeleton + skin weights (web/body-rig.js),
not vertex deltas or modeling targets.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSEUNITS = ROOT / "factory/mh/poseunits/body-poseunits.json"
OUT = ROOT / "web/data/body-poses.json"

# Official unit names in body-poseunits.json (Left definitions; Right mirrored in viewer).
POSE_RECIPES = {
    "poseAkimbo": {
        "label": "руки в боки",
        "units": ["UpperArmDownLeft", "UpperArmRollOutLeft", "LowerArmBend1Left1", "HandDownLeft"],
        "mirror": True,
        "strength": 1.0,
    },
    "poseStep": {
        "label": "шаг",
        "units_left": ["UpperLegForwardLeft", "LowerLegBendLeft1"],
        "units_right": ["UpperLegBackwardLeft"],
        "strength": 1.0,
    },
}


def pack() -> dict:
    meta = json.loads(POSEUNITS.read_text())
    return {
        "mesh": "hm08",
        "license": "CC0 MakeHuman body-poseunits.json",
        "method": "pose-units-v1",
        "poseUnitsSource": "web/data/body-poseunits.json",
        "note": "Requires web/data/body-skeleton.json (default.mhskel + default_weights.mhw)",
        "poses": [
            {"id": "rest", "label": "стоя", "key": None},
            {"id": "akimbo", "label": POSE_RECIPES["poseAkimbo"]["label"], "key": "poseAkimbo"},
            {"id": "step", "label": POSE_RECIPES["poseStep"]["label"], "key": "poseStep"},
        ],
        "recipes": POSE_RECIPES,
        "poseUnitCount": len(meta.get("poses", {})),
    }


def main() -> None:
    data = pack()
    assert data["method"] == "pose-units-v1"
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"poses {len(data['poses'])} units {data['poseUnitCount']} -> {OUT}")


if __name__ == "__main__":
    main()
