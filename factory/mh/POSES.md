# MakeHuman poses — foundation (Game-Live-v2)

## What runs in CI and on Pages

**`official-targets-v1`** only.

1. `factory/fetch_pose_targets.py` — sync **all** `makehuman/data/targets/armslegs/*.target` (CC0) into `factory/mh/targets/armslegs/`.
2. `factory/pack_poses.py` — blend official targets into `web/data/body-poses.json` (same format as chest morphs).
3. Viewer — `bindMorph` + `applyBody`; **no skeleton**, **no posed OBJ**, **no body-poseunits in JS**.

Pose recipes are versioned in `pack_poses.py` (UniversalModifier: weight = |value|).

## Why not body-poseunits + skinMesh here

MakeHuman ships **face** pose units with BVH; **body** JSON has no BVH and no app plugin. We tried factory `skinMesh()` + posed OBJ (`mh-posed-obj-v1`): mesh stayed intact but poses looked like **arms out (A-pose)**, not «руки в боки» — wrong recipe / hm08 vs bind, not acceptable for this product.

Until **glTF** (mesh + skin + clips) is exported from MakeHuman or MPFB, web poses stay **official modeling targets** for arms/legs — the same data class as slider morphs, baked once in the factory.

## Runtime files not used for poses

- `web/body-rig.js`
- `web/data/body-skeleton.json` (reference only)
- `factory/archive/*` — old bake attempts

## Next official step

Export hm08 with default or MPFB **game_engine** rig to **glTF**; load one `SkinnedMesh` + animation clips in Three.js.
