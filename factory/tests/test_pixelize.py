import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pixelize import PALETTE_COLORS, TARGET_HEIGHT, pixelize

src = Path("/tmp/factory-src.png")
dst = Path("/tmp/factory-dst.png")
Image.new("RGB", (500, 800), (40, 42, 48)).save(src)
pixelize(src, dst)
out = Image.open(dst)
assert out.size[1] == TARGET_HEIGHT
assert out.mode == "RGB"
print("ok", out.size, PALETTE_COLORS)
