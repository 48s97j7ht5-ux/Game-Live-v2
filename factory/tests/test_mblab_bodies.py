"""MB-Lab dummies must be real template meshes, not a convex hull."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MBLAB = ROOT / "models" / "mblab"

EXPECTED = {
    "f_an01.obj": (13995, 13806),
    "f_an02.obj": (13995, 13806),
    "m_an01.obj": (13687, 13498),
}


def _counts(path: Path) -> tuple[int, int]:
    verts = 0
    faces = 0
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            verts += 1
        elif line.startswith("f "):
            faces += 1
            corners = line.split()[1:]
            assert len(corners) >= 3
    return verts, faces


def test_mblab_dummies_match_library() -> None:
    assert (MBLAB / "NOTICE").is_file()
    for name, expected in EXPECTED.items():
        path = MBLAB / name
        assert path.is_file(), name
        assert _counts(path) == expected, name
        text = path.read_text()
        assert "\no body\n" in text
        assert "\ng body\n" in text
        assert "convex" not in text.lower()


if __name__ == "__main__":
    test_mblab_dummies_match_library()
    print("ok mblab")
