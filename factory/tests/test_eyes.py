from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EYES = ROOT / "models/eyes"


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


def test_official_eyes_cover_obj() -> None:
    obj = (EYES / "high-poly.obj").read_text()
    mhclo = (EYES / "high-poly.mhclo").read_text()
    verts = [line for line in obj.splitlines() if line.startswith("v ")]
    uvs = [line for line in obj.splitlines() if line.startswith("vt ")]
    maps = _maps(mhclo)
    assert "basemesh hm08" in mhclo
    assert "CC0" in obj[:800]
    assert "HighPolyEyes" in mhclo
    assert maps >= len(verts), (maps, len(verts))
    assert len(verts) >= 1000
    assert len(uvs) >= 800
    assert (EYES / "brown_eye.png").is_file()
    png = (EYES / "brown_eye.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert png[:8] and (EYES / "brown_eye.png").stat().st_size > 10000
    notice = (EYES / "NOTICE").read_text()
    assert "helper-l-eye" in notice
    wear = (ROOT / "web/eye-wear.js").read_text()
    viewer = (ROOT / "web/viewer.js").read_text()
    mhclo_js = (ROOT / "web/mhclo.js").read_text()
    assert "createEyes" in wear
    assert "parseObjTextured" in wear
    assert "parseObjTextured" in mhclo_js
    assert "createEyes" in viewer
    assert 'name === "eyes"' in viewer
    assert 'mesh.name = "eyes"' in wear
    assert "helper-l-eye" in wear
    found = False
    for line in mhclo.splitlines():
        parts = line.split()
        if len(parts) >= 9 and parts[0].lstrip("-").isdigit() and "." not in parts[0]:
            for index in parts[:3]:
                assert 0 <= int(index) < 19158, index
            found = True
            break
    assert found


if __name__ == "__main__":
    test_official_eyes_cover_obj()
    print("ok eyes")
