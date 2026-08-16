import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAIR = ROOT / "models/hair"
STYLES = json.loads((ROOT / "web/parts/hair.json").read_text())["styles"]


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
    studio = (ROOT / "web/hair.js").read_text()
    assert 'id: "bob01", label: "каре"' in studio
    assert "style: 5" in studio
    for name in STYLES:
        obj = (HAIR / name / f"{name}.obj").read_text()
        verts = [line for line in obj.splitlines() if line.startswith("v ")]
        maps = _maps((HAIR / name / f"{name}.mhclo").read_text())
        assert maps >= len(verts), (name, maps, len(verts))
        assert f'id: "{name}"' in studio, name


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


if __name__ == "__main__":
    test_maps_cover_obj_verts()
    test_mhclo_indices_fit_hm08()
    test_scalp_is_a_crown_cap()
    print("ok hair")
