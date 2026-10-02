"""Normalize an imagegen-approved cutout; no color-based matte removal.

An explicit reviewed frame may isolate tool-generated alpha=1 margin residue.
It must retain every source pixel with alpha >= 2; never clip visible artwork.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PIL import Image

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from tools.asset_generation.canonical_png import encode_png


def normalize(source: Path, target: Path, canvas: tuple[int, int], box: tuple[int, int, int, int],
              *, source_box: tuple[int, int, int, int] | None = None) -> None:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
    if source_box is not None:
        sx0, sy0, sx1, sy1 = source_box
        if not (0 <= sx0 < sx1 <= rgba.width and 0 <= sy0 < sy1 <= rgba.height):
            raise ValueError("Invalid reviewed source bounds")
        visible = rgba.getchannel("A").point(lambda alpha: 255 if alpha >= 2 else 0).getbbox()
        if visible is None or not (sx0 <= visible[0] and sy0 <= visible[1]
                                  and sx1 >= visible[2] and sy1 >= visible[3]):
            raise ValueError("Reviewed source frame would clip visible artwork")
        rgba = rgba.crop(source_box)
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
    payload = encode_png(normalized, optimize=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--canvas", type=int, nargs=2, required=True)
    parser.add_argument("--box", type=int, nargs=4, required=True)
    parser.add_argument("--source-box", type=int, nargs=4,
                        help="Reviewed frame: may exclude only alpha<=1 margin residue")
    args = parser.parse_args()
    normalize(args.source, args.target, tuple(args.canvas), tuple(args.box),
              source_box=tuple(args.source_box) if args.source_box is not None else None)
