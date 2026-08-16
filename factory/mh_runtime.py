"""Minimal MakeHuman Python runtime for factory bake (AGPL code, CC0 data only)."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MH_REPO = ROOT / "vendor/makehuman"
MH = MH_REPO / "makehuman"
FACTORY_RIG = ROOT / "factory/mh/rigs"


def ensure_makehuman_repo() -> Path:
    if MH.is_dir() and (MH / "shared/skeleton.py").is_file():
        return MH_REPO
    raise FileNotFoundError(
        "Run: python3 factory/fetch_makehuman.py (vendors makehumancommunity/makehuman for skeleton.skinMesh)"
    )


def bootstrap():
    if getattr(bootstrap, "_done", False):
        return
    ensure_makehuman_repo()
    sys.path.insert(0, str(MH))
    sys.path.insert(0, str(MH / "lib"))

    def load_mod(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    load_mod("transformations", MH / "core/transformations.py")
    load_mod("matrix", MH / "lib/matrix.py")
    log = types.SimpleNamespace(
        message=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    sys.modules["log"] = log
    progress = types.SimpleNamespace(
        __call__=lambda *a, **k: types.SimpleNamespace(step=lambda *a, **k: None),
    )
    sys.modules["progress"] = progress

    lic = types.SimpleNamespace(
        fromJson=lambda *a, **k: None,
        copy=lambda: types.SimpleNamespace(),
        asDict=lambda: {},
    )
    mh = types.ModuleType("makehuman")
    mh.getAssetLicense = lambda: lic
    mh.isRelease = lambda: True
    sys.modules["makehuman"] = mh

    def thoroughFindFile(filename, searchPaths=None, searchDefaultPaths=True):
        searchPaths = searchPaths or []
        name = Path(filename).name
        if name == "default_weights.mhw":
            return str(FACTORY_RIG / name)
        for base in searchPaths:
            candidate = Path(base) / filename
            if candidate.is_file():
                return str(candidate)
        local = FACTORY_RIG / name
        if local.is_file():
            return str(local)
        return filename

    getpath = types.ModuleType("getpath")
    getpath.thoroughFindFile = thoroughFindFile
    getpath.canonicalPath = lambda p: str(Path(p).resolve())
    getpath.getSysDataPath = lambda sub="": str(MH / "data" / sub)
    sys.modules["getpath"] = getpath

    load_mod("animation", MH / "shared/animation.py")
    load_mod("skeleton", MH / "shared/skeleton.py")

    bootstrap._done = True


def make_human_mesh(obj_path: Path):
    import numpy as np

    coords = []
    for line in obj_path.read_text().splitlines():
        if line.startswith("v "):
            coords.append([float(x) for x in line.split()[1:4]])
    coords = np.array(coords, dtype=np.float32)

    class Mesh:
        def getVertexCount(self):
            return len(coords)

        def getCoords(self, idx):
            return coords[idx]

        def getRestposeCoordinates(self):
            return coords

    class Human:
        meshData = Mesh()

        def getRestposeCoordinates(self):
            return coords

    core = types.ModuleType("core")
    core.G = types.SimpleNamespace(app=types.SimpleNamespace(selectedHuman=Human()))
    sys.modules["core"] = core
    return Human(), coords


def load_default_skeleton(obj_path: Path):
    """Load official default.mhskel + weights against hm08 rest mesh."""
    bootstrap()
    import skeleton

    human, _coords = make_human_mesh(obj_path)
    skel_path = FACTORY_RIG / "default.mhskel"
    skel = skeleton.Skeleton("default")
    skel.fromFile(str(skel_path), mesh=human.meshData)
    return skel, human


bootstrap._done = False
