import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAIR = ROOT / "models/hair"
STYLES = json.loads((ROOT / "web/parts/hair-style.json").read_text())["styles"]


def _maps(text: str) -> int:
    count = 0
    started = False
    for line in text.splitlines():
        if line.strip().startswith("verts "):
            started = True
            continue
        if not started:
            continue
        parts = line.split()
        if len(parts) >= 9 and parts[0].lstrip("-").replace(".", "", 1).isdigit():
            count += 1
    return count


def test_maps_cover_obj_verts() -> None:
    catalog = (ROOT / "web/hair-catalog.js").read_text()
    studio = (ROOT / "web/hair.js").read_text()
    assert 'id: "bob01", label: "каре"' in catalog
    assert "DEFAULT_OFFICIAL_STYLE = 5" in catalog
    assert "floorsFor" in studio
    assert "cycleColor" in studio
    assert 'cycle("style", styles, dir)' not in studio
    for name in STYLES:
        obj = (HAIR / name / f"{name}.obj").read_text()
        verts = [line for line in obj.splitlines() if line.startswith("v ")]
        maps = _maps((HAIR / name / f"{name}.mhclo").read_text())
        assert maps >= len(verts), (name, maps, len(verts))
        assert f'id: "{name}"' in catalog, name


def test_scalp_is_a_crown_cap() -> None:
    text = (HAIR / "scalp.obj").read_text()
    verts = [line for line in text.splitlines() if line.startswith("v ")]
    faces = [line for line in text.splitlines() if line.startswith("f ")]
    assert "g scalp" in text
    assert len(verts) >= 180
    assert len(faces) >= 140
    ys = [float(line.split()[2]) for line in verts]
    zs = [float(line.split()[3]) for line in verts]
    assert max(ys) > 8.4
    assert min(ys) > 7.3
    assert max(zs) < 1.35


def test_mhclo_indices_fit_hm08() -> None:
    for name in STYLES:
        proxy = (HAIR / name / f"{name}.mhclo").read_text()
        found = False
        for line in proxy.splitlines():
            parts = line.split()
            if len(parts) >= 9 and parts[0].lstrip("-").isdigit() and "." not in parts[0]:
                for index in parts[:3]:
                    assert 0 <= int(index) < 19158, (name, index)
                found = True
                break
        assert found, name


def test_community_catalog_if_present() -> None:
    catalog = ROOT / "web/parts/hair-community.json"
    if not catalog.is_file():
        return
    data = json.loads(catalog.read_text())
    assert len(data["styles"]) >= 50
    catalog_js = (ROOT / "web/hair-catalog.js").read_text()
    studio = (ROOT / "web/hair.js").read_text()
    wear = (ROOT / "web/hair-wear.js").read_text()
    assert "loadCommunity" in catalog_js
    assert "floorsFor" in studio
    assert "cycleColor" in studio
    assert "dye(" in wear
    assert 'cycle("style", styles, dir)' not in studio
    for item in data["styles"]:
        name = item["id"]
        assert name != "learning_anime_hair"
        obj = HAIR / name / f"{name}.obj"
        mhclo = HAIR / name / f"{name}.mhclo"
        assert obj.is_file(), name
        assert mhclo.is_file(), name
        proxy = mhclo.read_text()
        assert "basemesh hm08" in proxy
        maps = _maps(proxy)
        verts = [line for line in obj.read_text().splitlines() if line.startswith("v ")]
        assert maps >= len(verts), (name, maps, len(verts))


if __name__ == "__main__":
    test_maps_cover_obj_verts()
    test_mhclo_indices_fit_hm08()
    test_scalp_is_a_crown_cap()
    test_community_catalog_if_present()
    print("ok hair")
