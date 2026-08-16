"""Factory pose bake (MakeHuman skinMesh → models/poses/*.obj)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pose_obj_bake_runs() -> None:
    subprocess.run(["python3", str(ROOT / "factory/fetch_makehuman.py")], check=True)
    subprocess.run(["python3", str(ROOT / "factory/bake_pose_objs.py")], check=True)


def test_pose_catalog_and_objs() -> None:
    catalog = json.loads((ROOT / "web/data/body-poses.json").read_text())
    assert catalog["method"] == "mh-posed-obj-v1"
    assert len(catalog["poses"]) == 3
    for name in ("akimbo.obj", "step.obj"):
        path = ROOT / "models/poses" / name
        assert path.is_file(), name
        assert path.stat().st_size > 1_000_000


if __name__ == "__main__":
    test_pose_obj_bake_runs()
    test_pose_catalog_and_objs()
    print("ok pose bake")
