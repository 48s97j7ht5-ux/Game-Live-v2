"""Downscale a Blender render to ~200px height and quantize to 48 colors."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


TARGET_HEIGHT = 200
PALETTE_COLORS = 48
FILL_RATIO = 0.9


def content_bbox(image: Image.Image, threshold: int = 24) -> tuple[int, int, int, int]:
    bg = image.getpixel((0, 0))
    width, height = image.size
    pixels = image.load()
    min_x, min_y, max_x, max_y = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if abs(pixel[0] - bg[0]) + abs(pixel[1] - bg[1]) + abs(pixel[2] - bg[2]) > threshold:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < 0:
        return (0, 0, width, height)
    return (min_x, min_y, max_x + 1, max_y + 1)


def center_character(image: Image.Image) -> Image.Image:
    bg = image.getpixel((0, 0))
    left, top, right, bottom = content_bbox(image)
    cropped = image.crop((left, top, right, bottom))
    target_h = max(1, round(TARGET_HEIGHT * FILL_RATIO))
    scale = target_h / cropped.height
    size = (max(1, round(cropped.width * scale)), target_h)
    sprite = cropped.resize(size, Image.Resampling.BOX)
    canvas_w = max(sprite.width + 8, round(TARGET_HEIGHT * image.width / image.height))
    canvas = Image.new("RGB", (canvas_w, TARGET_HEIGHT), bg)
    x = (canvas.width - sprite.width) // 2
    y = (canvas.height - sprite.height) // 2
    canvas.paste(sprite, (x, y))
    return canvas


def pixelize(src: Path, dst: Path) -> None:
    image = Image.open(src).convert("RGB")
    pixel = center_character(image)
    quantized = pixel.quantize(colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    dst.parent.mkdir(parents=True, exist_ok=True)
    quantized.convert("RGB").save(dst)
    print(f"wrote {dst} {pixel.size[0]}x{pixel.size[1]} {PALETTE_COLORS} colors")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="factory/out/render.png")
    parser.add_argument("--dst", default="factory/out/character.png")
    args = parser.parse_args()
    pixelize(Path(args.src), Path(args.dst))


if __name__ == "__main__":
    main()
