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
    assert f"parts/manifest.json?v={CACHE}" in viewer


def test_no_unofficial_morph_hacks() -> None:
    morph = (ROOT / "web/chest-morph.js").read_text()
    assert "gain:" not in morph
    assert "mask:" not in morph


def test_pages_workflow_uses_assemble_script() -> None:
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "factory/assemble_pages.sh" in workflow
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
        rels.update(re.findall(r'from "(\./[^"?]+)"', viewer))
        rels.update(re.findall(r'new URL\("(\./[^"?]+)"', viewer))
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
        if part.get("kind") == "overlay":
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
    assert "tapZones(catalog)" in viewer
    live = [part for part in iter_parts() if part.get("enabled") is not False]
    assert {part["id"] for part in live} >= {"chest", "stomach", "hips", "butt"}
    for part in live:
        if part.get("kind") == "overlay":
            continue
        assert part["floors"]
        assert part["views"]


if __name__ == "__main__":
    test_cache_token_everywhere()
    test_no_unofficial_morph_hacks()
    test_pages_workflow_uses_assemble_script()
    test_assemble_contains_imports()
    test_live_targets_match_packer_and_json()
    test_parts_are_the_zone_source()
    print("ok contract")
