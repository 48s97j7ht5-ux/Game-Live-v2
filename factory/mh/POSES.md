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

So the official desktop app does **not** document a “apply this JSON directly in JS” path for body. External tools (e.g. MPFB) may consume it.

## Official deformation pipeline (mesh)

1. Rest coordinates (basemesh)
2. Modeling `.target` deltas (UniversalModifier) — what hm08 morphs use
3. Skeleton pose as **4×4 matrices per bone** (breadth-first), via `AnimationTrack` / BVH
4. **`Skeleton.skinMesh()`** with `VertexBoneWeights` from `default_weights.mhw`

Rig files: `makehuman/data/rigs/default.mhskel` + `default_weights.mhw`.

## hm08 web viewer (this repo)

Until we run step 3–4 through MakeHuman (or Collada/FBX export from MH), **runtime Three.js skinning + raw body-poseunits quaternions is not an official path** and has produced broken binds.

**Current shipping method:** `official-targets-v1` — same as modeling sliders (`pack_poses.py`), documented in `factory/mh/SOURCE.txt`.

**Next official step:** factory bake using `shared.skeleton` + `skinMesh()` (or MH Collada export), then optional glTF for Three.js — not hand-rolled bind matrices.
