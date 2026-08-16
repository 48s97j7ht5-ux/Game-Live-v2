# MakeHuman poses — what the official repo actually ships

Sources: `makehumancommunity/makehuman` (AGPL/CC0 data).

## Face pose units (wired in the app)

- `makehuman/data/poseunits/face-poseunits.json` — **framemapping** + metadata
- `makehuman/data/poseunits/face-poseunits.bvh` — **animation_file** (one frame per unit)
- Loaded in `makehuman/plugins/2_posing_expression.py`: BVH → `animation.PoseUnit` → `skeleton.setPose()` → **`skeleton.skinMesh()`**

Face JSON alone is **not** enough; it points at the BVH.

## Body pose units (data only in core MH)

- `makehuman/data/poseunits/body-poseunits.json` — bone name → quaternion per unit name
- **No** `animation_file`, **no** `framemapping`, **no** matching `body-poseunits.bvh` in the repo
- **No** Python plugin references `body-poseunits.json` (grep the tree)

External tools (e.g. MPFB) may consume it; this repo applies it in the **factory** only.

## Official deformation pipeline (mesh)

1. Rest coordinates (basemesh / hm08 OBJ)
2. Modeling `.target` deltas (UniversalModifier) — morph sliders
3. Skeleton pose as **4×4 matrices per bone** (breadth-first), from pose units or BVH
4. **`Skeleton.skinMesh()`** with `VertexBoneWeights` from `default_weights.mhw`

Rig files: `factory/mh/rigs/default.mhskel` + `default_weights.mhw` (CC0, from MH data).

## hm08 web viewer (this repo)

**Shipping method:** `mh-skinmesh-v1`

- CI clones MakeHuman (`factory/fetch_makehuman.py`) and runs `factory/bake_body_poses.py`.
- Recipes blend official **body-poseunits** (see `factory/mh/recipes/*.json`) with L→R mirror where documented.
- Output is packed vertex deltas in `web/data/body-poses.json` (same wire format as morph targets).
- Runtime applies deltas only — **no** Three.js `SkinnedMesh` / hand-rolled bind matrices (`web/body-rig.js` stays off).

**Legacy:** `official-targets-v1` (`factory/pack_poses.py`) used modeling `.target` files; kept for reference, not used in CI.

**Not official for web:** applying body-poseunits quaternions directly in JavaScript without MH `skinMesh()`.
