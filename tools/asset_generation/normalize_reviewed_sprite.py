"""Normalize an imagegen-approved cutout; never synthesize or remove pixels here."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def normalize(source: Path, target: Path, canvas: tuple[int, int], box: tuple[int, int, int, int]) -> None:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("Empty source alpha")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= canvas[0] and 0 <= y0 < y1 <= canvas[1]):
        raise ValueError("Invalid target bounds")
    # Deliberate matching of the existing Cocos trim rectangle and raw canvas.
    sprite = rgba.crop(bounds).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    # Low-alpha fringes can disappear on downsampling. Re-trim only fully
    # transparent pixels and refit so the existing import rectangle remains valid.
    for _ in range(3):
        resized_bounds = sprite.getchannel("A").getbbox()
        if resized_bounds == (0, 0, sprite.width, sprite.height):
            break
        if resized_bounds is None:
            raise ValueError("Source lost all alpha during normalization")
        sprite = sprite.crop(resized_bounds).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    if sprite.getchannel("A").getbbox() != (0, 0, sprite.width, sprite.height):
        raise ValueError("Cannot fit stable alpha bounds")
    normalized = Image.new("RGBA", canvas, (0, 0, 0, 0))
    normalized.paste(sprite, (x0, y0))
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized.save(target, optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--canvas", type=int, nargs=2, required=True)
    parser.add_argument("--box", type=int, nargs=4, required=True)
    args = parser.parse_args()
    normalize(args.source, args.target, tuple(args.canvas), tuple(args.box))
