from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAIR = ROOT / "models/hair"


def test_mhclo_triples_match_obj_vert_count() -> None:
    for name in ("short", "bob", "long", "bangs_brow", "bangs_face"):
        obj = (HAIR / f"{name}.obj").read_text().splitlines()
        verts = [line for line in obj if line.startswith("v ")]
        proxy = (HAIR / f"{name}.mhclo").read_text().splitlines()
        triples = [line for line in proxy if line.startswith("  ")]
        assert len(triples) == len(verts), (name, len(triples), len(verts))
        parts = triples[0].split()
        assert len(parts) == 9
        i0, i1, i2 = map(int, parts[:3])
        assert i0 != i1 or i1 != i2


def test_pack_script_mentions_official_rules() -> None:
    pack = (ROOT / "factory/hair/pack.py").read_text()
    assert "ProxyRefVert.fromTriple" in pack
    assert "helper-hair" in pack
    assert "is_face_skin" in pack
