# Deprecated pose experiments (not used in CI)

- `bake_pose_objs.py` — MH skinMesh → OBJ; wrong visuals on hm08 (A-pose, not hands on hips).
- `bake_body_poses.py` — sparse delta pack; shredded mesh in browser.
- `test_pose_bake.py` — tests for the above.

**Production:** `../fetch_pose_targets.py` + `../pack_poses.py` → `official-targets-v1`.

True skeletal poses: glTF export from MakeHuman/MPFB (see `../mh/POSES.md`).
