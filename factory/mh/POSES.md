# MakeHuman body poses — official factory path

Sources (CC0 data + AGPL app code): `makehumancommunity/makehuman`.

## Production pipeline (`mh-posed-obj-v1`)

1. **Rig:** `factory/mh/rigs/default.mhskel` + `default_weights.mhw` (from MH `makehuman/data/rigs/`).
2. **Pose units:** `factory/mh/poseunits/body-poseunits.json` blended per `factory/mh/recipes/*.json`.
3. **Deform:** vendored `makehuman/shared/skeleton.py` → `setPose()` → **`skinMesh()`** (headless via `factory/mh_runtime.py`).
4. **Output:** `models/poses/akimbo.obj`, `models/poses/step.obj` — same vertex order as `models/base.obj`, basemesh indices `0..13379` updated.
5. **Catalog:** `web/data/body-poses.json` lists poses and OBJ paths.
6. **Viewer:** loads posed OBJ, sets body mesh corners by **basemesh vertex index** (from rest OBJ), then applies morph sliders on top.

CI: `fetch_makehuman.py` + `bake_pose_objs.py` (checks + Pages).

No runtime JavaScript skeleton. No modeling `.target` files pretending to be poses.

## Face vs body in core MakeHuman

Face pose units ship with matching **BVH**; body JSON has **no BVH** in the upstream repo. This factory uses the same **skinMesh** path the desktop app uses for face, applied to official body unit quaternions.

## Not used on Pages

- `factory/pack_poses.py` (modeling targets only — legacy)
- `web/body-rig.js` (runtime SkinnedMesh experiment)
- `factory/bake_body_poses.py` (sparse delta pack — mapping fragile)

## Later: glTF

Export skin + animation clips from MakeHuman/MPFB once; until then, posed OBJ bake is the supported official deform path.
