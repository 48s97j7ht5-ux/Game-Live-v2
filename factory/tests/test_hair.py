from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAIR = ROOT / "models/hair"


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


def test_bob_maps_cover_obj_verts() -> None:
    obj = (HAIR / "bob01/bob01.obj").read_text()
    verts = [line for line in obj.splitlines() if line.startswith("v ")]
    maps = _maps((HAIR / "bob01/bob01.mhclo").read_text())
    assert maps == len(verts), (maps, len(verts))


def test_mhclo_indices_fit_hm08() -> None:
    proxy = (HAIR / "bob01/bob01.mhclo").read_text()
    for line in proxy.splitlines():
        parts = line.split()
        if len(parts) >= 9 and parts[0].lstrip("-").isdigit() and "." not in parts[0]:
            for index in parts[:3]:
                assert 0 <= int(index) < 19158
            break


if __name__ == "__main__":
    test_bob_maps_cover_obj_verts()
    test_mhclo_indices_fit_hm08()
    print("ok hair")
