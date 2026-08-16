# MakeHuman poses — hm08 web (Game-Live-v2)

Official data: `makehumancommunity/makehuman` (CC0 targets, AGPL app code).

## What ships on GitHub Pages

**Method: `official-targets-v1`** — factory `pack_poses.py` only.

- Poses are **pre-baked vertex deltas** from official **arms/legs modeling `.target`** files (`factory/mh/targets/armslegs/`), same rules as chest/hip morphs (`UniversalModifier`, weight = |value|).
- CI runs `python3 factory/pack_poses.py` before contract tests and Pages deploy.
- The viewer applies deltas through `bindMorph` / `applyBody` — **no runtime skeleton**, no `body-poseunits.json` in JS.

This is official MakeHuman **geometry** (targets), not a hand-rolled hack. It is **not** full skeletal pose units; akimbo/step are recipes of modeling sliders at 1.0.

## What we tried and removed from production

| Attempt | Why it failed |
|--------|----------------|
| Vertex rotation around joints | Not official; breaks normals |
| Three.js `SkinnedMesh` + body-poseunits quaternions | Wrong bind for hm08; mesh collapsed |
| Factory `skinMesh()` bake → sparse deltas | hm08 OBJ + default weights ≠ reliable posed bake for web; shredded mesh even with basemesh-index fix |

Scripts `bake_body_poses.py`, `mh_runtime.py`, `fetch_makehuman.py` remain for a future **glTF/Collada export** path, not used in CI.

## True skeletal poses (later)

1. Pose in MakeHuman or MPFB with **game_engine** / default rig on basemesh  
2. Export **glTF** (mesh + skin + one animation per pose) or Collada  
3. Load in Three.js `SkinnedMesh` — no manual bind matrices in this repo  

Reference data kept for tooling: `factory/mh/rigs/`, `factory/mh/poseunits/body-poseunits.json`, `web/data/body-skeleton.json` (not loaded by viewer).
