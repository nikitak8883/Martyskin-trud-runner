from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GAMEPLAY_DIRS = [
    "characters/player_skins",
    "objectives/equipment",
    "objectives/collectibles",
    "objectives/hazards",
    "objectives/platforms",
    "objectives/labels_signage",
    "objectives/npc_decor",
    "objectives/ui_achievements",
    "objectives/foreground_decor",
]

EDGE_CONNECTED_WHITE_SUSPECT_MIN_PIXELS = 12
ALPHA_EDGE_WHITE_HALO_SUSPECT_MIN_PIXELS = 320


def near_white(pixel: tuple[int, int, int, int], threshold: int = 238) -> bool:
    r, g, b, _ = pixel
    return r >= threshold and g >= threshold and b >= threshold


def edge_connected_white_mask(img: Image.Image) -> set[tuple[int, int]]:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    visited: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()

    def add_if_candidate(x: int, y: int) -> None:
        if (x, y) in visited:
            return
        r, g, b, a = pixels[x, y]
        if a > 220 and r > 238 and g > 238 and b > 238:
            visited.add((x, y))
            q.append((x, y))

    for x in range(w):
        add_if_candidate(x, 0)
        add_if_candidate(x, h - 1)
    for y in range(h):
        add_if_candidate(0, y)
        add_if_candidate(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                add_if_candidate(nx, ny)
    return visited


def alpha_edge_white_halo_count(img: Image.Image) -> int:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    count = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = pixels[x, y]
            if not (20 < a < 245 and r > 235 and g > 235 and b > 235):
                continue
            near_transparent = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if pixels[nx, ny][3] <= 8:
                    near_transparent = True
                    break
            if near_transparent:
                count += 1
    return count


def trim_transparent(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return rgba
    # Keep a small transparent gutter so Cocos filtering does not bleed against edges.
    left = max(0, bbox[0] - 2)
    top = max(0, bbox[1] - 2)
    right = min(rgba.width, bbox[2] + 2)
    bottom = min(rgba.height, bbox[3] + 2)
    cropped = rgba.crop((left, top, right, bottom))
    canvas = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    canvas.alpha_composite(cropped, (left, top))
    return canvas


def clean_connected_white(img: Image.Image) -> tuple[Image.Image, int]:
    rgba = img.convert("RGBA")
    mask = edge_connected_white_mask(rgba)
    low_alpha_removed = 0
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if 0 < a <= 18:
                pixels[x, y] = (0, 0, 0, 0)
                low_alpha_removed += 1
    if not mask:
        return trim_transparent(rgba), low_alpha_removed
    for x, y in mask:
        pixels[x, y] = (0, 0, 0, 0)
    return trim_transparent(rgba), len(mask) + low_alpha_removed


def analyze(path: Path) -> dict:
    img = Image.open(path).convert("RGBA")
    alpha = img.getchannel("A")
    amin, amax = alpha.getextrema()
    connected = edge_connected_white_mask(img)
    halo = alpha_edge_white_halo_count(img)
    corners = [img.getpixel((0, 0)), img.getpixel((img.width - 1, 0)), img.getpixel((0, img.height - 1)), img.getpixel((img.width - 1, img.height - 1))]
    opaque_white_corners = sum(1 for px in corners if px[3] > 220 and near_white(px))
    reasons: list[str] = []
    if len(connected) > EDGE_CONNECTED_WHITE_SUSPECT_MIN_PIXELS:
        reasons.append("edge-connected opaque white")
    if halo >= ALPHA_EDGE_WHITE_HALO_SUSPECT_MIN_PIXELS:
        reasons.append("large alpha-edge white halo")
    if opaque_white_corners > 0:
        reasons.append("opaque white corner")
    return {
        "file": str(path),
        "size": [img.width, img.height],
        "alphaMin": amin,
        "alphaMax": amax,
        "edgeConnectedOpaqueWhite": len(connected),
        "alphaEdgeWhiteHalo": halo,
        "opaqueWhiteCorners": opaque_white_corners,
        "reasons": reasons,
        "status": "suspect" if reasons else "ok",
    }


def checkerboard(size: tuple[int, int], tile: int = 12) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", size, (34, 34, 34, 255))
    draw = ImageDraw.Draw(im)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            color = (68, 68, 68, 255) if ((x // tile) + (y // tile)) % 2 else (30, 30, 30, 255)
            draw.rectangle([x, y, x + tile - 1, y + tile - 1], fill=color)
    return im


def contact_sheet(paths: list[Path], out_path: Path) -> None:
    if not paths:
        if out_path.exists():
            out_path.unlink()
        return
    tile_w, tile_h = 192, 176
    cols = 4
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tile_w, rows * tile_h), (18, 18, 18, 255))
    font = ImageFont.load_default()
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGBA")
        bg = checkerboard((tile_w, tile_h - 24))
        img.thumbnail((tile_w - 20, tile_h - 42), Image.Resampling.LANCZOS)
        bg.alpha_composite(img, ((tile_w - img.width) // 2, (tile_h - 24 - img.height) // 2))
        x = (i % cols) * tile_w
        y = (i // cols) * tile_h
        sheet.alpha_composite(bg, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + tile_h - 21), path.name[:28], fill=(245, 230, 180, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="assets/resources")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--report", default="qa/20260528_asset_cutout_scan_strict.json")
    parser.add_argument("--contact-sheet", default="qa/20260528_cutout_suspects_contact_sheet.png")
    args = parser.parse_args()

    root = Path(args.root)
    checked: list[dict] = []
    fixed: list[dict] = []

    for rel in GAMEPLAY_DIRS:
        folder = root / rel
        if not folder.exists():
            checked.append({"category": rel, "status": "missing"})
            continue
        for path in sorted(folder.rglob("*.png")):
            info = analyze(path)
            info["category"] = rel
            checked.append(info)
            if args.fix and info["edgeConnectedOpaqueWhite"] > EDGE_CONNECTED_WHITE_SUSPECT_MIN_PIXELS:
                original = Image.open(path).convert("RGBA")
                cleaned, removed = clean_connected_white(original)
                if removed > 0:
                    cleaned.save(path)
                    info_after = analyze(path)
                    fixed.append({"file": str(path), "removedPixels": removed, "after": info_after})

    suspects = [Path(item["file"]) for item in checked if item.get("status") == "suspect" and "file" in item]
    report = {
        "checkedCount": sum(1 for item in checked if "file" in item),
        "suspectCount": len(suspects),
        "fixedCount": len(fixed),
        "thresholds": {
            "edgeConnectedOpaqueWhite": EDGE_CONNECTED_WHITE_SUSPECT_MIN_PIXELS,
            "alphaEdgeWhiteHalo": ALPHA_EDGE_WHITE_HALO_SUSPECT_MIN_PIXELS,
        },
        "suspects": [item for item in checked if item.get("status") == "suspect"],
        "fixed": fixed,
        "checked": checked,
    }
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    contact_sheet(suspects[:64], Path(args.contact_sheet))
    print(json.dumps({k: report[k] for k in ("checkedCount", "suspectCount", "fixedCount")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
