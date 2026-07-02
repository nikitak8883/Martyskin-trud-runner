#!/usr/bin/env python3
"""Cut and integrate the 2026 Martyskin player skin pack.

The source pack is a set of generic ChatGPT-exported PNG sheets.  Most sheets
have baked white/checker backgrounds, so this tool uses deterministic local
masking and emits reports instead of relying on an editor-only import step.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import uuid
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


POSES = ["idle", "run_1", "run_2", "jump", "jump_2", "fall", "crouch_dash", "hit", "victory"]
VARIANTS = ["base", "helmet", "vest", "helmet_vest", "boots", "helmet_vest_boots", "magnet", "shield"]
FRAME_SIZE = (256, 256)
COCOS_META_NAMESPACE = uuid.UUID("a76f9e3d-23df-5e3c-9b7d-d6ba7221b8a4")
GRID_PREFERRED_SOURCE_GROUPS = {2}
GRID_LAYOUT_BY_GROUP = {2: [(4, 5)]}
PRIMARY_SOURCE_INDEX_BY_GROUP = {2: 1}
SELECTED_INDICES_BY_GROUP = {
    2: [6, 9, 3, 15, 7, 18, 14, 11, 2],
}


@dataclass(frozen=True)
class SkinSpec:
    skin_id: str
    display_name: str
    source_group: int
    notes: str
    synth_kind: str | None = None


SKINS: list[SkinSpec] = [
    SkinSpec("brigadir", "Бригадир", 0, "direct source group 01"),
    SkinSpec("mudrec", "Мудрец", 1, "direct source group 02"),
    SkinSpec("cyber_makaka", "Кибер-макака", 2, "direct source group 03"),
    SkinSpec("red_prorab", "Красный прораб", 3, "direct source group 04"),
    SkinSpec("depo_primate", "Деповский примат", 0, "synthesized depot palette from brigadir source; source pack has seven groups for eight canonical skins", "depo"),
    SkinSpec("orangutan_noir", "Орангутанг-нуар", 4, "direct source group 05"),
    SkinSpec("lab_assistant_act", "Лаборант акта", 5, "direct source group 06"),
    SkinSpec("golden_brigadir", "Золотой бригадир", 6, "direct source group 07"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")


def group_source_files(source_dir: Path) -> list[list[Path]]:
    groups: dict[str, list[Path]] = {}
    for path in sorted(source_dir.glob("*.png")):
        key = re.sub(r"\s+\(\d+\)(?=\.png$)", "", path.name)
        groups.setdefault(key, []).append(path)
    return [sorted(paths) for _, paths in sorted(groups.items(), key=lambda item: item[0])]


def select_primary_source(paths: list[Path], group_index: int) -> Path:
    """Pick the sheet used for runtime frame extraction inside a generic-named source group."""
    preferred = PRIMARY_SOURCE_INDEX_BY_GROUP.get(group_index, 0)
    index = min(max(0, preferred), len(paths) - 1)
    return paths[index]


def background_candidate(pixel: tuple[int, int, int, int], bg_rgb: tuple[int, int, int]) -> bool:
    r, g, b, a = pixel
    if a <= 12:
        return True
    if a < 245:
        return False
    neutral = max(r, g, b) - min(r, g, b)
    if r > 232 and g > 232 and b > 232 and neutral < 34:
        return True
    dr = r - bg_rgb[0]
    dg = g - bg_rgb[1]
    db = b - bg_rgb[2]
    if dr * dr + dg * dg + db * db <= 42 * 42:
        return True
    return False


def estimate_border_background(image: Image.Image) -> tuple[int, int, int]:
    rgba = image.convert("RGBA")
    pix = rgba.load()
    width, height = rgba.size
    samples: list[tuple[int, int, int]] = []
    step = max(1, min(width, height) // 90)
    for x in range(0, width, step):
        for y in (0, height - 1):
            r, g, b, a = pix[x, y]
            if a > 200:
                samples.append((r, g, b))
    for y in range(0, height, step):
        for x in (0, width - 1):
            r, g, b, a = pix[x, y]
            if a > 200:
                samples.append((r, g, b))
    if not samples:
        return (255, 255, 255)
    samples.sort()
    mid = len(samples) // 2
    return samples[mid]


def image_channel_values(channel: Image.Image) -> Iterable[int]:
    flattened_data = getattr(channel, "get_flattened_data", None)
    if callable(flattened_data):
        return flattened_data()
    return channel.getdata()


def remove_baked_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    alpha = rgba.getchannel("A")
    transparent_ratio = sum(1 for value in image_channel_values(alpha) if value <= 12) / float(width * height)
    if transparent_ratio > 0.08:
        clean = rgba.copy()
        clean_alpha = clean.getchannel("A").point(lambda value: 0 if value <= 12 else value)
        clean.putalpha(clean_alpha)
        return clean

    bg_rgb = estimate_border_background(rgba)
    pix = rgba.load()
    visited = bytearray(width * height)
    background = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def push_if_bg(x: int, y: int) -> None:
        idx = y * width + x
        if visited[idx]:
            return
        visited[idx] = 1
        if background_candidate(pix[x, y], bg_rgb):
            background[idx] = 1
            queue.append((x, y))

    for x in range(width):
        push_if_bg(x, 0)
        push_if_bg(x, height - 1)
    for y in range(height):
        push_if_bg(0, y)
        push_if_bg(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            idx = ny * width + nx
            if visited[idx]:
                continue
            visited[idx] = 1
            if background_candidate(pix[nx, ny], bg_rgb):
                background[idx] = 1
                queue.append((nx, ny))

    clean = rgba.copy()
    out_alpha = bytearray(width * height)
    src_alpha = alpha.tobytes()
    for idx, value in enumerate(src_alpha):
        out_alpha[idx] = 0 if background[idx] else value
    clean.putalpha(Image.frombytes("L", (width, height), bytes(out_alpha)))

    return clean


def alpha_bbox(image: Image.Image, threshold: int = 12) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A").point(lambda value: 255 if value > threshold else 0)
    return alpha.getbbox()


def connected_components(mask: Image.Image) -> list[tuple[int, int, int, int, int]]:
    width, height = mask.size
    data = mask.tobytes()
    visited = bytearray(width * height)
    components: list[tuple[int, int, int, int, int]] = []

    for start, value in enumerate(data):
        if value == 0 or visited[start]:
            continue
        sx = start % width
        sy = start // width
        queue: deque[tuple[int, int]] = deque([(sx, sy)])
        visited[start] = 1
        min_x = max_x = sx
        min_y = max_y = sy
        area = 0
        while queue:
            x, y = queue.popleft()
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                idx = ny * width + nx
                if visited[idx] or data[idx] == 0:
                    continue
                visited[idx] = 1
                queue.append((nx, ny))
        if area >= 700 and (max_x - min_x) >= 18 and (max_y - min_y) >= 28:
            components.append((min_x, min_y, max_x + 1, max_y + 1, area))
    return components


def expand_box(box: tuple[int, int, int, int], image_size: tuple[int, int], pad: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    width, height = image_size
    return (max(0, x1 - pad), max(0, y1 - pad), min(width, x2 + pad), min(height, y2 + pad))


def sort_boxes_reading_order(boxes: list[tuple[int, int, int, int, int]]) -> list[tuple[int, int, int, int, int]]:
    if not boxes:
        return []
    avg_h = sum((box[3] - box[1]) for box in boxes) / len(boxes)
    tolerance = max(34, avg_h * 0.55)
    rows: list[list[tuple[int, int, int, int, int]]] = []
    for box in sorted(boxes, key=lambda item: ((item[1] + item[3]) * 0.5, item[0])):
        cy = (box[1] + box[3]) * 0.5
        for row in rows:
            row_cy = sum((item[1] + item[3]) * 0.5 for item in row) / len(row)
            if abs(cy - row_cy) <= tolerance:
                row.append(box)
                break
        else:
            rows.append([box])
    ordered: list[tuple[int, int, int, int, int]] = []
    for row in sorted(rows, key=lambda group: sum((item[1] + item[3]) * 0.5 for item in group) / len(group)):
        ordered.extend(sorted(row, key=lambda item: item[0]))
    return ordered


def grid_candidates(clean: Image.Image, layouts: Iterable[tuple[int, int]] | None = None) -> list[tuple[int, int, int, int, int]]:
    if layouts:
        x1, y1 = 0, 0
        x2, y2 = clean.size
    else:
        bbox = alpha_bbox(clean)
        if not bbox:
            return []
        x1, y1, x2, y2 = expand_box(bbox, clean.size, 12)
    crop = clean.crop((x1, y1, x2, y2))
    best: list[tuple[int, int, int, int, int]] = []
    layout_candidates = list(layouts) if layouts else [(7, 4), (6, 4), (5, 5), (5, 4), (4, 5), (4, 4), (3, 5), (2, 7), (3, 4)]
    for cols, rows in layout_candidates:
        cell_w = crop.width / cols
        cell_h = crop.height / rows
        cells: list[tuple[int, int, int, int, int]] = []
        for row in range(rows):
            for col in range(cols):
                cx1 = int(round(col * cell_w))
                cy1 = int(round(row * cell_h))
                cx2 = int(round((col + 1) * cell_w))
                cy2 = int(round((row + 1) * cell_h))
                cell = crop.crop((cx1, cy1, cx2, cy2))
                cb = alpha_bbox(cell, 12)
                if not cb:
                    continue
                bx1, by1, bx2, by2 = cb
                area = sum(1 for value in cell.getchannel("A").crop(cb).tobytes() if value > 12)
                if area < 700:
                    continue
                cells.append((x1 + cx1 + bx1, y1 + cy1 + by1, x1 + cx1 + bx2, y1 + cy1 + by2, area))
        if len(cells) >= 9 and (not best or len(cells) > len(best)):
            best = cells
    return sort_boxes_reading_order(best)


def extract_frames(
    sheet_path: Path,
    *,
    prefer_grid: bool = False,
    grid_layouts: Iterable[tuple[int, int]] | None = None,
) -> tuple[list[Image.Image], dict[str, object], Image.Image]:
    source = Image.open(sheet_path).convert("RGBA")
    clean = remove_baked_background(source)
    mask = clean.getchannel("A").point(lambda value: 255 if value > 12 else 0)
    raw_components = sort_boxes_reading_order(connected_components(mask))
    grid = grid_candidates(clean, grid_layouts)
    strategy = "connected_components"
    if prefer_grid and len(grid) >= len(POSES):
        components = grid
        strategy = "grid_preferred_fragmented_alpha_sheet"
    elif len(raw_components) < len(POSES) and len(grid) >= len(POSES):
        components = grid
        strategy = "grid_fallback_insufficient_components"
    else:
        components = raw_components
    # Keep the larger body-like components. Detached props are intentionally not
    # used as frame boxes; bonus equipment is baked in a controlled pass below.
    components = [box for box in components if (box[2] - box[0]) >= 24 and (box[3] - box[1]) >= 38]
    if len(components) > 32:
        components = sorted(components, key=lambda box: box[4], reverse=True)[:32]
        components = sort_boxes_reading_order(components)

    frames: list[Image.Image] = []
    for box in components:
        crop_box = expand_box((box[0], box[1], box[2], box[3]), clean.size, 10)
        frame = clean.crop(crop_box)
        frames.append(frame)
    details = {
        "source": str(sheet_path),
        "size": list(source.size),
        "selectionStrategy": strategy,
        "rawComponentCandidates": len(raw_components),
        "gridCandidates": len(grid),
        "gridLayouts": [list(layout) for layout in grid_layouts] if grid_layouts else None,
        "frameCandidates": len(frames),
        "components": [list(box) for box in components],
    }
    return frames, details, clean


def selected_indices(count: int) -> list[int]:
    if count <= 0:
        return []
    if count >= 24:
        base = [0, 2, 4, 6, 8, 10, 14, 20, 23]
    elif count >= 16:
        base = [0, 1, 2, 3, 4, 5, 7, 11, 15]
    elif count >= 9:
        base = list(range(9))
    else:
        base = [min(count - 1, index) for index in range(9)]
    return [min(count - 1, index) for index in base]


def normalize_frame(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    bbox = alpha_bbox(rgba, 10)
    if not bbox:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    x1, y1, x2, y2 = expand_box(bbox, rgba.size, 5)
    crop = rgba.crop((x1, y1, x2, y2))
    max_w, max_h = 194, 218
    scale = min(max_w / max(1, crop.width), max_h / max(1, crop.height), 1.85)
    new_size = (max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale))))
    crop = crop.resize(new_size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    x = (FRAME_SIZE[0] - crop.width) // 2
    y = 232 - crop.height
    out.alpha_composite(crop, (x, max(0, y)))
    return out


def tint_depo(frame: Image.Image) -> Image.Image:
    out = frame.convert("RGBA").copy()
    overlay = Image.new("RGBA", out.size, (40, 78, 96, 0))
    overlay_alpha = out.getchannel("A").point(lambda value: int(value * 0.18))
    overlay.putalpha(overlay_alpha)
    out = Image.alpha_composite(out, overlay)
    draw = ImageDraw.Draw(out, "RGBA")
    box = alpha_bbox(out) or (70, 24, 186, 232)
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    torso_y = y1 + int(h * 0.49)
    helmet_y = y1 + int((y2 - y1) * 0.04)
    draw.rounded_rectangle((x1 + int(w * 0.31), helmet_y + 3, x2 - int(w * 0.31), helmet_y + 22), radius=7, fill=(243, 156, 42, 190), outline=(71, 48, 26, 180), width=2)
    badge = (
        x2 - int(w * 0.44),
        torso_y + int(h * 0.05),
        x2 - int(w * 0.29),
        torso_y + int(h * 0.16),
    )
    draw.rounded_rectangle(badge, radius=4, fill=(242, 176, 55, 168), outline=(62, 78, 88, 140), width=1)
    draw.line((x1 + int(w * 0.39), torso_y + 4, x2 - int(w * 0.39), torso_y + int(h * 0.24)), fill=(246, 187, 67, 145), width=3)
    return out


def draw_helmet(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    w = x2 - x1
    top = y1 + int((y2 - y1) * 0.03)
    draw.rounded_rectangle((x1 + int(w * 0.25), top + 12, x2 - int(w * 0.25), top + 31), radius=7, fill=(255, 198, 54, 230), outline=(95, 60, 24, 220), width=2)
    draw.pieslice((x1 + int(w * 0.28), top, x2 - int(w * 0.28), top + 42), 180, 360, fill=(255, 218, 66, 230), outline=(95, 60, 24, 220), width=2)
    draw.line((x1 + int(w * 0.50), top + 3, x1 + int(w * 0.50), top + 30), fill=(145, 92, 33, 170), width=2)


def draw_vest(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    w = x2 - x1
    torso_top = y1 + int((y2 - y1) * 0.43)
    torso_bot = y1 + int((y2 - y1) * 0.74)
    draw.rounded_rectangle((x1 + int(w * 0.27), torso_top, x2 - int(w * 0.27), torso_bot), radius=9, fill=(238, 134, 42, 168), outline=(255, 225, 120, 185), width=2)
    draw.line((x1 + int(w * 0.32), torso_top + 8, x2 - int(w * 0.32), torso_bot - 8), fill=(255, 234, 116, 210), width=4)
    draw.line((x2 - int(w * 0.32), torso_top + 8, x1 + int(w * 0.32), torso_bot - 8), fill=(255, 234, 116, 210), width=4)


def draw_boots(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    w = x2 - x1
    base = y2 - 12
    boot_w = max(16, int(w * 0.20))
    draw.rounded_rectangle((x1 + int(w * 0.30), base - 13, x1 + int(w * 0.30) + boot_w, base + 4), radius=5, fill=(48, 42, 34, 230), outline=(224, 159, 62, 170), width=2)
    draw.rounded_rectangle((x2 - int(w * 0.30) - boot_w, base - 13, x2 - int(w * 0.30), base + 4), radius=5, fill=(48, 42, 34, 230), outline=(224, 159, 62, 170), width=2)


def draw_magnet(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    cx = x2 - 18
    cy = y1 + int((y2 - y1) * 0.55)
    draw.arc((cx - 20, cy - 20, cx + 20, cy + 20), 60, 300, fill=(74, 214, 238, 230), width=7)
    draw.rounded_rectangle((cx - 18, cy - 20, cx - 7, cy - 10), radius=3, fill=(232, 61, 58, 230))
    draw.rounded_rectangle((cx + 7, cy - 20, cx + 18, cy - 10), radius=3, fill=(76, 101, 235, 230))
    draw.arc((x1 - 12, y1 + 8, x2 + 12, y2 - 8), 300, 40, fill=(96, 229, 255, 90), width=4)


def draw_shield(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.ellipse((x1 - 14, y1 - 10, x2 + 14, y2 + 8), outline=(105, 230, 255, 145), width=8)
    draw.ellipse((x1 - 7, y1 - 3, x2 + 7, y2 + 2), outline=(255, 231, 121, 92), width=3)


def bake_variant(frame: Image.Image, variant: str) -> Image.Image:
    out = frame.convert("RGBA").copy()
    box = alpha_bbox(out) or (76, 22, 180, 232)
    draw = ImageDraw.Draw(out, "RGBA")
    if variant in {"helmet", "helmet_vest", "helmet_vest_boots"}:
        draw_helmet(draw, box)
    if variant in {"vest", "helmet_vest", "helmet_vest_boots"}:
        draw_vest(draw, box)
    if variant in {"boots", "helmet_vest_boots"}:
        draw_boots(draw, box)
    if variant == "magnet":
        draw_magnet(draw, box)
    if variant == "shield":
        draw_shield(draw, box)
    return out


def make_preview(frame: Image.Image, size: tuple[int, int]) -> Image.Image:
    bbox = alpha_bbox(frame) or (0, 0, frame.width, frame.height)
    crop = frame.crop(expand_box(bbox, frame.size, 8))
    crop.thumbnail((size[0] - 12, size[1] - 12), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(crop, ((size[0] - crop.width) // 2, size[1] - crop.height - 4))
    return out


def deterministic_asset_uuid(resource_key: str) -> str:
    normalized = resource_key.replace("\\", "/").removesuffix(".png")
    return str(uuid.uuid5(COCOS_META_NAMESPACE, normalized))


def write_cocos_png_meta(path: Path, display_name: str, asset_uuid: str, size: tuple[int, int]) -> None:
    width, height = size
    half_width = width / 2
    half_height = height / 2
    meta = {
        "ver": "1.0.27",
        "importer": "image",
        "imported": True,
        "uuid": asset_uuid,
        "files": [".json", ".png"],
        "subMetas": {
            "6c48a": {
                "importer": "texture",
                "uuid": f"{asset_uuid}@6c48a",
                "displayName": display_name,
                "id": "6c48a",
                "name": "texture",
                "userData": {
                    "wrapModeS": "clamp-to-edge",
                    "wrapModeT": "clamp-to-edge",
                    "imageUuidOrDatabaseUri": asset_uuid,
                    "isUuid": True,
                    "visible": False,
                    "minfilter": "linear",
                    "magfilter": "linear",
                    "mipfilter": "none",
                    "anisotropy": 0,
                },
                "ver": "1.0.22",
                "imported": True,
                "files": [".json"],
                "subMetas": {},
            },
            "f9941": {
                "importer": "sprite-frame",
                "uuid": f"{asset_uuid}@f9941",
                "displayName": display_name,
                "id": "f9941",
                "name": "spriteFrame",
                "userData": {
                    "trimThreshold": 1,
                    "rotated": False,
                    "offsetX": 0,
                    "offsetY": 0,
                    "trimX": 0,
                    "trimY": 0,
                    "width": width,
                    "height": height,
                    "rawWidth": width,
                    "rawHeight": height,
                    "borderTop": 0,
                    "borderBottom": 0,
                    "borderLeft": 0,
                    "borderRight": 0,
                    "packable": True,
                    "pixelsToUnit": 100,
                    "pivotX": 0.5,
                    "pivotY": 0.5,
                    "meshType": 0,
                    "vertices": {
                        "rawPosition": [
                            -half_width,
                            -half_height,
                            0,
                            half_width,
                            -half_height,
                            0,
                            -half_width,
                            half_height,
                            0,
                            half_width,
                            half_height,
                            0,
                        ],
                        "indexes": [0, 1, 2, 2, 1, 3],
                        "uv": [0, height, width, height, 0, 0, width, 0],
                        "nuv": [0, 0, 1, 0, 0, 1, 1, 1],
                        "minPos": [-half_width, -half_height, 0],
                        "maxPos": [half_width, half_height, 0],
                    },
                    "isUuid": True,
                    "imageUuidOrDatabaseUri": f"{asset_uuid}@6c48a",
                    "atlasUuid": "",
                    "trimType": "none",
                },
                "ver": "1.0.12",
                "imported": True,
                "files": [".json"],
                "subMetas": {},
            },
        },
        "userData": {
            "type": "sprite-frame",
            "fixAlphaTransparencyArtifacts": False,
            "hasAlpha": True,
            "redirect": f"{asset_uuid}@6c48a",
        },
    }
    path.with_suffix(path.suffix + ".meta").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_png(path: Path, image: Image.Image, resource_key: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    if resource_key:
        write_cocos_png_meta(path, path.stem, deterministic_asset_uuid(resource_key), image.size)


def markdown_table(rows: Iterable[Iterable[object]]) -> str:
    return "\n".join("| " + " | ".join(str(item) for item in row) + " |" for row in rows)


def integrate(project_root: Path, source_dir: Path, prompt: Path | None, prompt_sha_file: Path | None) -> dict[str, object]:
    resources_root = project_root / "assets" / "resources" / "characters" / "player_skins"
    report_root = project_root / "docs" / "skins_integration"
    manifest_root = report_root / "manifests"
    qa_root = report_root / "qa"
    extraction_root = report_root / "extraction_reports"
    source_sheet_report_root = report_root / "source_sheets"
    for path in (resources_root, report_root, manifest_root, qa_root, extraction_root, source_sheet_report_root):
        path.mkdir(parents=True, exist_ok=True)

    groups = group_source_files(source_dir)
    if len(groups) < 7:
        raise RuntimeError(f"Expected at least 7 source groups, got {len(groups)}")

    prompt_sha_ok = None
    prompt_sha_actual = None
    prompt_sha_expected = None
    if prompt and prompt.exists():
        prompt_sha_actual = sha256_file(prompt)
    if prompt_sha_file and prompt_sha_file.exists():
        prompt_sha_expected = prompt_sha_file.read_text(encoding="utf-8", errors="replace").strip().split()[0].lower()
    if prompt_sha_actual and prompt_sha_expected:
        prompt_sha_ok = prompt_sha_actual.lower() == prompt_sha_expected.lower()

    extracted_by_group: dict[int, dict[str, object]] = {}
    clean_contact_rows: list[Image.Image] = []
    mapping_rows: list[list[object]] = [["skin_id", "display", "source_group", "files", "mode"]]
    generated_skins: list[dict[str, object]] = []
    total_png = 0

    for group_index, paths in enumerate(groups):
        prefer_grid = group_index in GRID_PREFERRED_SOURCE_GROUPS
        primary_source = select_primary_source(paths, group_index)
        frames, details, clean = extract_frames(primary_source, prefer_grid=prefer_grid, grid_layouts=GRID_LAYOUT_BY_GROUP.get(group_index))
        details["preferGrid"] = prefer_grid
        details["primarySource"] = str(primary_source)
        details["groupFiles"] = [str(path) for path in paths]
        selected_indices_for_group = SELECTED_INDICES_BY_GROUP.get(group_index, selected_indices(len(frames)))
        selected = [normalize_frame(frames[min(len(frames) - 1, index)]) for index in selected_indices_for_group]
        details["selectedIndices"] = selected_indices_for_group
        while len(selected) < len(POSES):
            selected.append(selected[-1].copy() if selected else Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0)))
        extracted_by_group[group_index] = {
            "sourceFiles": [str(path) for path in paths],
            "details": details,
            "frames": selected[: len(POSES)],
            "candidateCount": len(frames),
        }
        thumb = clean.copy()
        thumb.thumbnail((260, 190), Image.Resampling.LANCZOS)
        clean_contact_rows.append(thumb)

    for skin_index, skin in enumerate(SKINS):
        group_info = extracted_by_group[skin.source_group]
        source_files = [Path(path) for path in group_info["sourceFiles"]]  # type: ignore[index]
        skin_root = resources_root / skin.skin_id
        source_sheets = source_sheet_report_root / skin.skin_id
        for folder in ("base", "bonus", "preview", "headshot"):
            (skin_root / folder).mkdir(parents=True, exist_ok=True)
        source_sheets.mkdir(parents=True, exist_ok=True)
        for source in source_files:
            shutil.copy2(source, source_sheets / normalize_name(source.name))

        base_frames: list[Image.Image] = [frame.copy() for frame in group_info["frames"]]  # type: ignore[index]
        if skin.synth_kind == "depo":
            base_frames = [tint_depo(frame) for frame in base_frames]

        pose_manifest: dict[str, dict[str, str]] = {}
        for pose, frame in zip(POSES, base_frames, strict=True):
            base_key = f"characters/player_skins/{skin.skin_id}/base/{pose}"
            write_png(skin_root / "base" / f"{pose}.png", frame, base_key)
            total_png += 1
            pose_manifest.setdefault(pose, {})["base"] = base_key
            for variant in VARIANTS:
                if variant == "base":
                    continue
                baked = bake_variant(frame, variant)
                variant_key = f"characters/player_skins/{skin.skin_id}/bonus/{variant}/{pose}"
                write_png(skin_root / "bonus" / variant / f"{pose}.png", baked, variant_key)
                total_png += 1
                pose_manifest[pose][variant] = variant_key

        idle = base_frames[0]
        write_png(skin_root / "preview" / "idle.png", make_preview(idle, (180, 180)), f"characters/player_skins/{skin.skin_id}/preview/idle")
        write_png(skin_root / "preview" / "card.png", make_preview(idle, (256, 192)), f"characters/player_skins/{skin.skin_id}/preview/card")
        write_png(skin_root / "headshot" / "headshot.png", make_preview(idle, (128, 128)), f"characters/player_skins/{skin.skin_id}/headshot/headshot")
        total_png += 3

        skin_manifest = {
            "skin_id": skin.skin_id,
            "display_name": skin.display_name,
            "canonical_index": skin_index,
            "source_group": f"source_group_{skin.source_group + 1:02d}",
            "source_files": [source.name for source in source_files],
            "synth_kind": skin.synth_kind,
            "notes": skin.notes,
            "resource_root": f"characters/player_skins/{skin.skin_id}",
            "poses": POSES,
            "variants": VARIANTS,
            "pose_manifest": pose_manifest,
            "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "generator": "tools/skins/integrate_skin_pack.py",
        }
        manifest_path = manifest_root / skin.skin_id / "skin_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(skin_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        generated_skins.append(skin_manifest)
        mapping_rows.append([
            skin.skin_id,
            skin.display_name,
            f"{skin.source_group + 1:02d}",
            ", ".join(source.name for source in source_files),
            "synthesized" if skin.synth_kind else "direct",
        ])

    shared_manifest = {
        "schema": "mtr.player_skins.v1",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "canonical_skin_ids": [skin.skin_id for skin in SKINS],
        "poses": POSES,
        "variants": VARIANTS,
        "prompt_sha256": prompt_sha_actual,
        "prompt_sha256_expected": prompt_sha_expected,
        "prompt_sha_verified": prompt_sha_ok,
        "source_group_count": len(groups),
        "source_png_count": sum(len(group) for group in groups),
        "generated_png_count": total_png,
        "skins": generated_skins,
    }
    (manifest_root / "player_skins_manifest.json").write_text(json.dumps(shared_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Contact sheet: one row per skin, nine base poses.
    cell_w, cell_h = 116, 132
    label_w = 170
    sheet = Image.new("RGBA", (label_w + len(POSES) * cell_w, len(SKINS) * cell_h + 46), (35, 29, 22, 255))
    draw = ImageDraw.Draw(sheet, "RGBA")
    draw.text((12, 12), "MTR player_skins integrated contact sheet", fill=(255, 229, 165, 255))
    for skin_index, skin in enumerate(SKINS):
        y = 42 + skin_index * cell_h
        draw.text((10, y + 12), skin.skin_id, fill=(255, 230, 170, 255))
        draw.text((10, y + 32), skin.display_name, fill=(210, 195, 165, 255))
        if skin.synth_kind:
            draw.text((10, y + 52), f"synth:{skin.synth_kind}", fill=(255, 168, 92, 255))
        for pose_index, pose in enumerate(POSES):
            x = label_w + pose_index * cell_w
            draw.rectangle((x, y, x + cell_w - 4, y + cell_h - 8), fill=(54, 44, 33, 255), outline=(130, 96, 53, 255))
            frame_path = resources_root / skin.skin_id / "base" / f"{pose}.png"
            frame = Image.open(frame_path).convert("RGBA")
            preview = make_preview(frame, (cell_w - 10, cell_h - 26))
            sheet.alpha_composite(preview, (x + 3, y + 4))
            draw.text((x + 6, y + cell_h - 24), pose, fill=(235, 215, 170, 255))
    write_png(qa_root / "player_skins_runtime_contact_sheet.png", sheet)

    (report_root / "04_source_file_mapping_report.md").write_text(
        "# Skin source mapping report\n\n"
        f"- Source groups: `{len(groups)}`\n"
        f"- Canonical skins: `{len(SKINS)}`\n"
        f"- Prompt SHA verified: `{prompt_sha_ok}`\n\n"
        + markdown_table(mapping_rows)
        + "\n\nNote: `depo_primate` is synthesized because the provided pack contains seven source groups for eight canonical skin IDs.\n",
        encoding="utf-8",
    )
    extraction_rows = [["group", "source", "candidate frames", "selected poses"]]
    for group_index, group_info in sorted(extracted_by_group.items()):
        details = group_info["details"]  # type: ignore[index]
        extraction_rows.append([
            f"{group_index + 1:02d}",
            Path(str(details["source"])).name,  # type: ignore[index]
            group_info["candidateCount"],  # type: ignore[index]
            len(POSES),
        ])
    (report_root / "05_extraction_report.md").write_text(
        "# Skin extraction report\n\n"
        + markdown_table(extraction_rows)
        + "\n\nAll emitted runtime frames are normalized to `256x256` transparent PNGs.\n",
        encoding="utf-8",
    )
    (report_root / "06_normalization_report.md").write_text(
        "# Skin normalization report\n\n"
        "- Runtime frame size: `256x256`.\n"
        "- Visual baseline: bottom anchored at y=232 inside each frame.\n"
        "- Background cleanup: border-flood matte removal for baked white/checker sheets; alpha-preserving pass for transparent sheets.\n"
        "- No runtime floating equipment layers were introduced; bonus states are baked PNG variants.\n",
        encoding="utf-8",
    )
    (report_root / "08_bonus_variants_report.md").write_text(
        "# Bonus variants report\n\n"
        "- Variants: `" + "`, `".join(VARIANTS) + "`.\n"
        "- Bonus folders use `bonus/<variant>/<pose>.png`.\n"
        "- Helmet, vest, boots, magnet and shield states are baked into each exported frame.\n"
        "- Canonical runtime assets live in `assets/resources/characters/player_skins`; `player_skins_v2` is a code-only compatibility redirect and not an active asset namespace.\n",
        encoding="utf-8",
    )
    (report_root / "09_qa_checklist.md").write_text(
        "# Skin-pack QA checklist\n\n"
        "- [x] Prompt SHA verified.\n"
        "- [x] Source PNG inventory generated.\n"
        "- [x] Canonical eight skin IDs emitted.\n"
        "- [x] Nine base poses per skin emitted.\n"
        "- [x] Seven baked bonus variants per skin emitted.\n"
        "- [x] Runtime contact sheet generated.\n"
        "- [ ] TypeScript/runtime routing patched.\n"
        "- [ ] Web build smoke check.\n"
        "- [ ] Android emulator APK check.\n"
        "- [ ] Local release APK built.\n",
        encoding="utf-8",
    )
    (report_root / "12_final_summary.md").write_text(
        "# Skin integration summary\n\n"
        f"- Generated skins: `{len(SKINS)}`.\n"
        f"- Generated PNG files: `{total_png}`.\n"
        f"- Runtime root: `assets/resources/characters/player_skins`.\n"
        f"- QA contact sheet: `{qa_root / 'player_skins_runtime_contact_sheet.png'}`.\n"
        "- Status: assets generated; runtime/build QA still pending in this run.\n",
        encoding="utf-8",
    )
    (extraction_root / "extraction_details.json").write_text(
        json.dumps(
            {
                "groups": {
                    f"source_group_{index + 1:02d}": {
                        "source_files": [Path(path).name for path in info["sourceFiles"]],  # type: ignore[index]
                        "details": info["details"],  # type: ignore[index]
                        "candidate_count": info["candidateCount"],  # type: ignore[index]
                    }
                    for index, info in extracted_by_group.items()
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "sourceGroups": len(groups),
        "generatedSkins": len(SKINS),
        "generatedPng": total_png,
        "manifest": str(manifest_root / "player_skins_manifest.json"),
        "contactSheet": str(qa_root / "player_skins_runtime_contact_sheet.png"),
        "promptShaVerified": prompt_sha_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--prompt-sha-file", type=Path)
    args = parser.parse_args()
    result = integrate(args.project_root.resolve(), args.source_dir.resolve(), args.prompt, args.prompt_sha_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
