"""Guardrails so the workbench cannot ship without morphs or drift from MakeHuman."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / "factory/mh_contract.json").read_text())
MANIFEST = json.loads((ROOT / "web/parts/manifest.json").read_text())
CACHE = MANIFEST["cache"]
PARTS_DIR = ROOT / "web/parts"


def iter_parts():
    for part_id in MANIFEST["parts"]:
        yield json.loads((PARTS_DIR / f"{part_id}.json").read_text())


def test_cache_token_everywhere() -> None:
    assert CONTRACT["cache"] == CACHE
    index = (ROOT / "index.html").read_text()
    viewer = (ROOT / "web/viewer.js").read_text()
    assert f"viewer.css?v={CACHE}" in index
    assert f"viewer.js?v={CACHE}" in index
    assert f"chest-morph.js?v={CACHE}" in viewer
    assert f"registry.js?v={CACHE}" in viewer
    assert f"hair.js?v={CACHE}" in viewer
    assert f"eye-wear.js?v={CACHE}" in viewer
    assert f"makeup.js?v={CACHE}" in viewer
    assert f"pose.js?v={CACHE}" in viewer
    hair = (ROOT / "web/hair.js").read_text()
    catalog_js = (ROOT / "web/hair-catalog.js").read_text()
    assert f"hair-catalog.js?v={CACHE}" in hair
    assert f"hair-wear.js?v={CACHE}" in hair
    assert f'HAIR_CACHE = "{CACHE}"' in catalog_js
    assert f"parts/manifest.json?v={CACHE}" in viewer


def test_no_unofficial_morph_hacks() -> None:
    morph = (ROOT / "web/chest-morph.js").read_text()
    assert "gain:" not in morph
    assert "mask:" not in morph


def test_pages_workflow_uses_assemble_script() -> None:
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "factory/assemble_pages.sh" in workflow
    assert "fetch_community_hair.py" in workflow
    assert "cp web/viewer.css web/viewer.js" not in workflow


def test_assemble_contains_imports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "dist"
        subprocess.run(
            ["bash", str(ROOT / "factory/assemble_pages.sh"), str(dest)],
            check=True,
        )
        viewer = (dest / "web/viewer.js").read_text()
        html = (dest / "index.html").read_text()
        rels = set(re.findall(r'(?:src|href)="(\./[^"?]+|web/[^"?]+)"', html))
        for name in ("viewer.js", "hair.js", "hair-catalog.js", "hair-wear.js", "eye-wear.js"):
            text = (dest / "web" / name).read_text()
            rels.update(re.findall(r'from "(\./[^"?]+)"', text))
            rels.update(re.findall(r'new URL\("(\./[^"?]+)"', text))
        rels.update(
            [
                "web/vendor/three.module.js",
                "web/vendor/loaders/OBJLoader.js",
                "web/parts/manifest.json",
                "web/registry.js",
            ]
        )
        for part_id in MANIFEST["parts"]:
            rels.add(f"web/parts/{part_id}.json")
        missing = []
        for rel in sorted(rels):
            path = rel[2:] if rel.startswith("./") else rel
            if path.startswith("web/") or path.startswith("models/"):
                candidate = dest / path
            else:
                candidate = dest / "web" / path
            if not candidate.is_file():
                missing.append(f"{rel} -> {candidate}")
        assert not missing, missing


def test_live_targets_match_packer_and_json() -> None:
    packer = (ROOT / "factory/pack_chest_targets.py").read_text()
    packed = json.loads((ROOT / "web/data/body-targets.json").read_text())
    needed = list(CONTRACT["packed_not_in_ui"])
    for part in iter_parts():
        if part.get("kind") in ("overlay", "body", "hair", "makeup"):
            continue
        if part.get("macro", {}).get("corners"):
            needed.extend(part["macro"]["corners"])
        for floor in part.get("floors") or []:
            if floor.get("decr"):
                needed.append(floor["decr"])
            if floor.get("incr"):
                needed.append(floor["incr"])
    for name in needed:
        assert f'"{name}"' in packer, name
        assert name in packed["targets"], name


def test_parts_are_the_zone_source() -> None:
    viewer = (ROOT / "web/viewer.js").read_text()
    assert "tapZones(catalog, currentBody, focusMode)" in viewer
    live = [part for part in iter_parts() if part.get("enabled") is not False]
    assert {part["id"] for part in live} >= {"chest", "stomach", "hips", "butt", "clay"}
    for part in live:
        if part.get("kind") in ("overlay", "body", "hair", "makeup"):
            continue
        assert part["floors"]
        assert part["views"]
        assert "clay" in (part.get("bodies") or ["clay"])


def test_clay_is_the_only_body() -> None:
    clay = json.loads((PARTS_DIR / "clay.json").read_text())
    assert clay["kind"] == "body"
    assert clay["model"] == "./models/base.obj"
    assert not (PARTS_DIR / "anime.json").exists()
    assert not (ROOT / "models/mblab").exists()
    viewer = (ROOT / "web/viewer.js").read_text()
    assert "setFocus" in viewer
    assert 'id="focus"' not in (ROOT / "index.html").read_text()
    assert 'data-focus="head"' not in (ROOT / "index.html").read_text()
    bodies = [part for part in iter_parts() if part.get("kind") == "body"]
    assert [part["id"] for part in bodies] == ["clay"]


def test_hair_is_three_head_modules() -> None:
    assert not (PARTS_DIR / "hair.json").exists()
    color = json.loads((PARTS_DIR / "hair-color.json").read_text())
    style = json.loads((PARTS_DIR / "hair-style.json").read_text())
    shelf = json.loads((PARTS_DIR / "hair-shelf.json").read_text())
    for part in (color, style, shelf):
        assert part["kind"] == "hair"
        assert part["focus"] == "head"
        assert part["yFrac"]
        assert len(part["floors"]) == 1
    assert color["yFrac"] > style["yFrac"] > shelf["yFrac"]
    viewer = (ROOT / "web/viewer.js").read_text()
    studio = (ROOT / "web/hair.js").read_text()
    catalog = (ROOT / "web/hair-catalog.js").read_text()
    wear = (ROOT / "web/hair-wear.js").read_text()
    assert "createHairStudio" in viewer
    assert "floorsFor" in viewer
    assert "isHairZone" in viewer
    assert "HAIR_HEAD_IDS" in viewer
    assert "openHairStudio" in viewer
    assert "HAIR_HEAD_IDS.flatMap" in viewer
    assert '((i + 1) / (count + 1)) * height' in viewer
    assert 'setEditZone("hair-style")' not in viewer
    assert "editZone === \"hair\"" not in viewer
    assert "zoneById(editZone).yFrac" not in viewer
    assert "helper-hair" in studio
    assert "dye(" in wear
    assert "cycleColor" in studio
    notice = (ROOT / "models/hair/NOTICE").read_text()
    assert (ROOT / "models/hair/scalp.obj").is_file()
    scalp = (ROOT / "models/hair/scalp.obj").read_text()
    assert "g scalp" in scalp[:200]
    assert "hair-scalp" in wear
    assert sum(1 for line in scalp.splitlines() if line.startswith("v ")) >= 180
    assert "helper-hair" in notice
    for name in style["styles"]:
        obj = ROOT / "models/hair" / name / f"{name}.obj"
        mhclo = ROOT / "models/hair" / name / f"{name}.mhclo"
        assert obj.is_file(), name
        assert mhclo.is_file(), name
        proxy = mhclo.read_text()
        assert "basemesh hm08" in proxy
        assert "verts 0" in proxy
        assert "CC0" in obj.read_text()[:800]
        assert f'id: "{name}"' in catalog
    assert len(style["styles"]) >= 10
    assert "loadCommunity" in catalog
    assert "общая" in catalog
    fetch = (ROOT / "factory/fetch_community_hair.py").read_text()
    assert "learning_anime_hair" in fetch
    assert "hair01_cc0.zip" in fetch


def test_head_focus_keeps_camera_crop() -> None:
    viewer = (ROOT / "web/viewer.js").read_text()
    html = (ROOT / "index.html").read_text()
    assert "FOCUS" in viewer
    assert "head:" in viewer
    assert "face:" in viewer
    assert "HEAD_Y_FRAC" in viewer
    assert "hitDummy" in viewer
    assert "isHeadHit" in viewer
    assert 'setFocus("head")' in viewer
    assert 'setFocus("face")' in viewer
    assert 'setFocus("body")' in viewer
    assert "span: 0.16" in viewer
    assert "span: 0.46" in viewer
    assert 'id="focus"' not in html
    assert 'data-focus="head"' not in html


def test_eyes_are_official_clothes() -> None:
    viewer = (ROOT / "web/viewer.js").read_text()
    wear = (ROOT / "web/eye-wear.js").read_text()
    assert "createEyes" in viewer
    assert "eyes.wear" in viewer
    assert "eyes.refit" in viewer
    assert 'name === "eyes"' in viewer
    assert "helper-l-eye" in wear
    assert (ROOT / "models/eyes/high-poly.obj").is_file()
    assert (ROOT / "models/eyes/high-poly.mhclo").is_file()
    assert (ROOT / "models/eyes/brown_eye.png").is_file()


def test_makeup_is_two_face_modules() -> None:
    lips = json.loads((PARTS_DIR / "makeup-lips.json").read_text())
    cheeks = json.loads((PARTS_DIR / "makeup-cheeks.json").read_text())
    for part in (lips, cheeks):
        assert part["kind"] == "makeup"
        assert part["focus"] == "face"
        assert part["yFrac"]
        assert len(part["floors"]) == 1
    viewer = (ROOT / "web/viewer.js").read_text()
    studio = (ROOT / "web/makeup.js").read_text()
    assert "createMakeupStudio" in viewer
    assert "makeupStudio" in viewer
    assert "MAKEUP_FACE_IDS" in viewer
    assert "MAKEUP_FACE_IDS.flatMap" in viewer
    assert "openMakeupStudio" in viewer
    assert "isMakeupZone" in viewer
    assert "vertexColors" not in viewer
    assert "bodyMesh" in viewer
    assert "cycleLip" in studio
    assert "cycleCheek" in studio
    assert "SKIN_HEX" in studio
    assert "makeup-zones.json" in studio
    assert "CanvasTexture" in studio
    zones = json.loads((ROOT / "web/data/makeup-zones.json").read_text())
    assert 130 <= len(zones["lips"]) <= 200
    assert 120 <= len(zones["cheeks"]) <= 250
    assert 180 <= len(zones["lipUv"]) <= 700
    assert 20 <= len(zones["cheekUv"]) <= 400
    assert len(zones["lipBox"]) == 4
    assert len(zones["cheekBoxes"]) == 2
    assert "mouth-upperlip-volume" in json.dumps(zones["source"])
    packer = (ROOT / "factory/pack_makeup_zones.py").read_text()
    assert "MOUTH_Y" not in packer
    assert "mouth-upperlip-volume-incr.target" in packer
    assert "mouth-lowerlip-width-incr.target" in packer
    assert "mouth-angles-up.target" in packer
    assert (ROOT / "factory/mh/targets/mouth/mouth-upperlip-volume-incr.target").is_file()
    assert (ROOT / "factory/mh/targets/mouth/mouth-lowerlip-width-incr.target").is_file()
    assert (ROOT / "factory/mh/targets/mouth/mouth-angles-up.target").is_file()


def test_poses_on_body_screen() -> None:
    part = json.loads((PARTS_DIR / "poses.json").read_text())
    assert part["kind"] == "pose"
    assert part["focus"] == "body"
    viewer = (ROOT / "web/viewer.js").read_text()
    pose = (ROOT / "web/pose.js").read_text()
    assert "createPoseStudio" in viewer
    assert "poseStudio" in viewer
    assert "POSE_Y_FRAC" in viewer
    assert "syncBodySideBars" in viewer
    assert "applyBody" in viewer
    assert "createPoseStudio" in pose
    assert "cycle" in pose
    packed = json.loads((ROOT / "web/data/body-poses.json").read_text())
    assert len(packed["poses"]) == 3
    assert packed["targets"]["poseAkimbo"]["s"]
    assert (ROOT / "factory/pack_poses.py").is_file()
    assert (ROOT / "factory/mh/targets/armslegs/l-hand-trans-out.target").stat().st_size > 1000


if __name__ == "__main__":
    test_cache_token_everywhere()
    test_no_unofficial_morph_hacks()
    test_pages_workflow_uses_assemble_script()
    test_assemble_contains_imports()
    test_live_targets_match_packer_and_json()
    test_parts_are_the_zone_source()
    test_clay_is_the_only_body()
    test_hair_is_three_head_modules()
    test_head_focus_keeps_camera_crop()
    test_eyes_are_official_clothes()
    test_makeup_is_two_face_modules()
    test_poses_on_body_screen()
    print("ok contract")
