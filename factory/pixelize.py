"""Downscale a Blender render to ~200px height and quantize to 48 colors."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


TARGET_HEIGHT = 200
PALETTE_COLORS = 48


def pixelize(src: Path, dst: Path) -> None:
    image = Image.open(src).convert("RGB")
    width, height = image.size
    scale = TARGET_HEIGHT / height
    size = (max(1, round(width * scale)), TARGET_HEIGHT)
    pixel = image.resize(size, Image.Resampling.BOX)
    quantized = pixel.quantize(colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    dst.parent.mkdir(parents=True, exist_ok=True)
    quantized.convert("RGB").save(dst)
    print(f"wrote {dst} {size[0]}x{size[1]} {PALETTE_COLORS} colors")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="factory/out/render.png")
    parser.add_argument("--dst", default="factory/out/character.png")
    args = parser.parse_args()
    pixelize(Path(args.src), Path(args.dst))


if __name__ == "__main__":
    main()
