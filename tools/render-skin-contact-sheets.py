#!/usr/bin/env python3
"""Render non-runtime contact sheets for Martyshkin Trud player skins.

The output is QA evidence only. It never modifies runtime PNGs or Cocos `.meta`
files. Each sheet renders one skin with poses as rows, variants as columns, and
overlays for alpha bbox, current bbox center, current bbox bottom, and base
variant anchor guides.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:  # pragma: no cover - environment gate
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    PIL_IMPORT_ERROR = str(exc)
else:
    PIL_IMPORT_ERROR = ""


CELL_SIZE = 256
LABEL_HEIGHT = 42
ROW_LABEL_WIDTH = 150
HEADER_HEIGHT = 92
MARGIN = 18
GRID_GAP = 10
CHECK_SIZE = 16
OPAQUE_ALPHA_MIN = 250


@dataclass
class FrameOverlay:
    skinId: str
    pose: str
    variant: str
    key: str
    path: str
    alphaBBox: list[int] | None
    bboxCenterX: float | None
    bboxBottom: int | None
    baseCenterX: float | None
    baseBottom: int | None
    centerDriftPx: float | None
    bottomDriftPx: float | None


def project_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:  # type: ignore[name-defined]
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def frame_path(resources_root: Path, key: str) -> Path:
    normalized = key.strip().replace("\\", "/").strip("/")
    if normalized.startswith("assets/resources/"):
        normalized = normalized[len("assets/resources/"):]
    if normalized.endswith(".png"):
        normalized = normalized[:-4]
    return resources_root / f"{normalized}.png"


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:  # type: ignore[name-defined]
    return image.convert("RGBA").getchannel("A").getbbox()


def checkerboard(size: int = CELL_SIZE) -> Image.Image:  # type: ignore[name-defined]
    canvas = Image.new("RGBA", (size, size), (31, 34, 38, 255))
    draw = ImageDraw.Draw(canvas)
    for y in range(0, size, CHECK_SIZE):
        for x in range(0, size, CHECK_SIZE):
            fill = (46, 50, 55, 255) if ((x // CHECK_SIZE + y // CHECK_SIZE) % 2 == 0) else (35, 38, 43, 255)
            draw.rectangle([x, y, x + CHECK_SIZE - 1, y + CHECK_SIZE - 1], fill=fill)
    return canvas


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: Any, fill: tuple[int, int, int, int]) -> None:
    draw.text(xy, text, font=font, fill=fill)


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: Any, fill: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text((left + (right - left - width) / 2, top + (bottom - top - height) / 2), text, font=font, fill=fill)


def draw_dashed_line(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: tuple[int, int, int, int], width: int = 1, dash: int = 8) -> None:
    x1, y1, x2, y2 = xy
    if y1 == y2:
        x = x1
        while x < x2:
            draw.line([x, y1, min(x + dash, x2), y2], fill=fill, width=width)
            x += dash * 2
    elif x1 == x2:
        y = y1
        while y < y2:
            draw.line([x1, y, x2, min(y + dash, y2)], fill=fill, width=width)
            y += dash * 2


def compose_cell(
    frame: Image.Image,  # type: ignore[name-defined]
    bbox: tuple[int, int, int, int] | None,
    base_bbox: tuple[int, int, int, int] | None,
) -> Image.Image:  # type: ignore[name-defined]
    cell = checkerboard(CELL_SIZE)
    rgba = frame.convert("RGBA")
    cell.alpha_composite(rgba)
    draw = ImageDraw.Draw(cell)

    if base_bbox:
        base_center = int(round((base_bbox[0] + base_bbox[2]) / 2))
        base_bottom = base_bbox[3]
        draw_dashed_line(draw, (base_center, 0, base_center, CELL_SIZE), (255, 218, 92, 190), width=1)
        draw_dashed_line(draw, (0, base_bottom, CELL_SIZE, base_bottom), (255, 168, 65, 210), width=1)

    if bbox:
        left, top, right, bottom = bbox
        center = int(round((left + right) / 2))
        draw.rectangle([left, top, right - 1, bottom - 1], outline=(75, 255, 143, 255), width=2)
        draw.line([center, 0, center, CELL_SIZE], fill=(79, 211, 255, 230), width=1)
        draw.line([0, bottom, CELL_SIZE, bottom], fill=(255, 84, 84, 235), width=2)
        draw.ellipse([center - 3, bottom - 3, center + 3, bottom + 3], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))

    draw.rectangle([0, 0, CELL_SIZE - 1, CELL_SIZE - 1], outline=(85, 91, 105, 255), width=1)
    return cell


def build_frame_overlays(
    project_root: Path,
    resources_root: Path,
    skin: dict[str, Any],
    poses: list[str],
    variants: list[str],
) -> tuple[dict[tuple[str, str], Image.Image], dict[tuple[str, str], tuple[int, int, int, int] | None], list[FrameOverlay]]:
    frames: dict[tuple[str, str], Image.Image] = {}
    bboxes: dict[tuple[str, str], tuple[int, int, int, int] | None] = {}
    overlays: list[FrameOverlay] = []
    skin_id = str(skin["skin_id"])
    pose_manifest = skin["pose_manifest"]

    for pose in poses:
        for variant in variants:
            key = pose_manifest[pose][variant]
            path = frame_path(resources_root, key)
            with Image.open(path) as image:
                frame = image.convert("RGBA")
            bbox = alpha_bbox(frame)
            frames[(pose, variant)] = frame
            bboxes[(pose, variant)] = bbox

    for pose in poses:
        base_bbox = bboxes[(pose, "base")]
        base_center = ((base_bbox[0] + base_bbox[2]) / 2) if base_bbox else None
        base_bottom = base_bbox[3] if base_bbox else None
        for variant in variants:
            key = pose_manifest[pose][variant]
            path = frame_path(resources_root, key)
            bbox = bboxes[(pose, variant)]
            center = ((bbox[0] + bbox[2]) / 2) if bbox else None
            bottom = bbox[3] if bbox else None
            overlays.append(FrameOverlay(
                skinId=skin_id,
                pose=pose,
                variant=variant,
                key=key,
                path=project_rel(path, project_root),
                alphaBBox=list(bbox) if bbox else None,
                bboxCenterX=center,
                bboxBottom=bottom,
                baseCenterX=base_center,
                baseBottom=base_bottom,
                centerDriftPx=round(abs(center - base_center), 3) if center is not None and base_center is not None else None,
                bottomDriftPx=round(abs(bottom - base_bottom), 3) if bottom is not None and base_bottom is not None else None,
            ))

    return frames, bboxes, overlays


def render_skin_sheet(
    project_root: Path,
    resources_root: Path,
    output_dir: Path,
    skin: dict[str, Any],
    poses: list[str],
    variants: list[str],
) -> tuple[Path, list[FrameOverlay]]:
    frames, bboxes, overlays = build_frame_overlays(project_root, resources_root, skin, poses, variants)

    title_font = load_font(28, bold=True)
    header_font = load_font(16, bold=True)
    label_font = load_font(15)
    tiny_font = load_font(12)

    width = MARGIN * 2 + ROW_LABEL_WIDTH + GRID_GAP + len(variants) * CELL_SIZE + (len(variants) - 1) * GRID_GAP
    height = MARGIN * 2 + HEADER_HEIGHT + len(poses) * (LABEL_HEIGHT + CELL_SIZE) + (len(poses) - 1) * GRID_GAP
    sheet = Image.new("RGBA", (width, height), (18, 20, 24, 255))
    draw = ImageDraw.Draw(sheet)

    skin_id = str(skin["skin_id"])
    display_name = str(skin.get("display_name") or skin_id)
    draw_text(draw, (MARGIN, MARGIN), f"{display_name} / {skin_id}", title_font, (238, 242, 247, 255))
    legend = "green=bbox, cyan=center, red=bottom, yellow/orange=base variant anchor"
    draw_text(draw, (MARGIN, MARGIN + 38), legend, label_font, (174, 183, 196, 255))

    x0 = MARGIN + ROW_LABEL_WIDTH + GRID_GAP
    y0 = MARGIN + HEADER_HEIGHT

    for col, variant in enumerate(variants):
        x = x0 + col * (CELL_SIZE + GRID_GAP)
        centered_text(draw, (x, MARGIN + 62, x + CELL_SIZE, y0 - 4), variant, header_font, (214, 231, 255, 255))

    for row, pose in enumerate(poses):
        y = y0 + row * (LABEL_HEIGHT + CELL_SIZE + GRID_GAP)
        label_box = (MARGIN, y + LABEL_HEIGHT, MARGIN + ROW_LABEL_WIDTH, y + LABEL_HEIGHT + CELL_SIZE)
        draw.rectangle(label_box, fill=(27, 31, 38, 255), outline=(76, 83, 98, 255), width=1)
        centered_text(draw, label_box, pose, header_font, (233, 237, 245, 255))
        for col, variant in enumerate(variants):
            x = x0 + col * (CELL_SIZE + GRID_GAP)
            draw.rectangle([x, y, x + CELL_SIZE - 1, y + LABEL_HEIGHT - 1], fill=(27, 31, 38, 255), outline=(76, 83, 98, 255))
            bbox = bboxes[(pose, variant)]
            base_bbox = bboxes[(pose, "base")]
            label = ""
            if bbox and base_bbox:
                center = (bbox[0] + bbox[2]) / 2
                base_center = (base_bbox[0] + base_bbox[2]) / 2
                label = f"cx {center-base_center:+.1f} / b {bbox[3]-base_bbox[3]:+d}"
            centered_text(draw, (x, y, x + CELL_SIZE, y + LABEL_HEIGHT), label, tiny_font, (180, 190, 203, 255))
            cell = compose_cell(frames[(pose, variant)], bbox, base_bbox)
            sheet.alpha_composite(cell, (x, y + LABEL_HEIGHT))

    out = output_dir / f"{skin_id}_contact_sheet.png"
    sheet.convert("RGB").save(out, "PNG", optimize=True)
    return out, overlays


def write_html_index(output_dir: Path, generated: list[dict[str, Any]], title: str) -> Path:
    html_path = output_dir / "contact_sheet_index.html"
    cards = []
    for item in generated:
        image = Path(item["sheet"]).name
        cards.append(
            f"<section class=\"card\"><h2>{item['displayName']} <code>{item['skinId']}</code></h2>"
            f"<p>{item['frameCount']} frames, sha256 <code>{item['sha256']}</code></p>"
            f"<img src=\"{image}\" alt=\"Contact sheet for {item['skinId']}\"></section>"
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ margin: 24px; background: #101216; color: #edf2f7; font-family: Arial, sans-serif; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #aeb9c8; margin-bottom: 24px; }}
    .card {{ margin: 0 0 34px; padding: 16px; background: #171b22; border: 1px solid #334052; border-radius: 10px; }}
    img {{ display: block; max-width: 100%; height: auto; border: 1px solid #475367; background: #111; }}
    code {{ color: #9be17d; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">QA evidence only. Runtime assets are not modified.</p>
  {''.join(cards)}
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def render_contact_sheets(args: argparse.Namespace) -> dict[str, Any]:
    if Image is None:
        raise RuntimeError(f"Pillow/PIL is not available: {PIL_IMPORT_ERROR}")

    project_root = Path(args.project_root).resolve()
    resources_root = (project_root / args.resources_root).resolve()
    manifest_path = (project_root / args.manifest).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    poses = [str(item) for item in manifest["poses"]]
    variants = [str(item) for item in manifest["variants"]]

    generated: list[dict[str, Any]] = []
    overlays_all: list[FrameOverlay] = []
    for skin in manifest["skins"]:
        sheet_path, overlays = render_skin_sheet(project_root, resources_root, output_dir, skin, poses, variants)
        overlays_all.extend(overlays)
        generated.append({
            "skinId": skin["skin_id"],
            "displayName": skin.get("display_name") or skin["skin_id"],
            "sheet": project_rel(sheet_path, project_root),
            "sha256": sha256_file(sheet_path),
            "frameCount": len(poses) * len(variants),
        })

    html_path = write_html_index(output_dir, generated, "MTR Module 3 skin/bonus contact sheets")
    manifest_out = {
        "schema": "mtr.skin_contact_sheets.v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(project_root),
        "manifest": project_rel(manifest_path, project_root),
        "policy": {
            "mutatesRuntimeAssets": False,
            "overlay": {
                "alphaBBox": "green rectangle",
                "currentCenter": "cyan vertical line",
                "currentBottom": "red horizontal line",
                "baseVariantCenter": "yellow dashed vertical line",
                "baseVariantBottom": "orange dashed horizontal line",
            },
        },
        "summary": {
            "skinCount": len(generated),
            "poseCount": len(poses),
            "variantCount": len(variants),
            "frameCount": len(overlays_all),
            "sheetCount": len(generated),
        },
        "htmlIndex": project_rel(html_path, project_root),
        "sheets": generated,
        "frames": [asdict(item) for item in overlays_all],
    }
    manifest_json = output_dir / "contact_sheet_manifest.json"
    manifest_json.write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_out["manifestJson"] = project_rel(manifest_json, project_root)
    manifest_json.write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--resources-root", default="assets/resources", help="Resources path relative to project root.")
    parser.add_argument(
        "--manifest",
        default="docs/skins_integration/manifests/player_skins_manifest.json",
        help="Player skin manifest path relative to project root.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/qa/evidence/20260704_module3_contact_sheets",
        help="Output directory relative to project root.",
    )
    return parser.parse_args()


def main() -> int:
    report = render_contact_sheets(parse_args())
    print(json.dumps({
        "ok": True,
        "summary": report["summary"],
        "htmlIndex": report["htmlIndex"],
        "manifestJson": report["manifestJson"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
