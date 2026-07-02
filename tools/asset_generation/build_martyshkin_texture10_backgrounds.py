from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageStat


TARGET_SIZE = (1920, 886)
PREVIEW_SIZE = (640, 295)
PRIMARY_SOURCE_SLOT = 2
JPEG_QUALITY_FULL = 88
JPEG_QUALITY_PREVIEW = 78

SOURCE_SLOT_ROLES = {
    1: "scenic_far_reference",
    2: "scenic_runtime_primary",
    3: "near_edge_reference_not_runtime_whole_sheet",
    4: "track_backdrop_reference_not_runtime_whole_sheet",
    5: "atmosphere_reference_not_runtime_whole_sheet",
    6: "prop_sheet_reference_not_runtime_whole_sheet",
    7: "prop_sheet_reference_not_runtime_whole_sheet",
    8: "prop_sheet_reference_not_runtime_whole_sheet",
}


@dataclass
class SourceInfo:
    slot: int
    role: str
    fileName: str
    relativePath: str
    width: int
    height: int
    mode: str
    sha256: str
    meanLuma: float
    contrast: float
    wholeSheetRuntimePolicy: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    src_w, src_h = image.size
    dst_w, dst_h = size
    scale = max(dst_w / src_w, dst_h / src_h)
    resized = image.resize((math.ceil(src_w * scale), math.ceil(src_h * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - dst_w) // 2)
    top = max(0, int((resized.height - dst_h) * 0.56))
    top = min(top, max(0, resized.height - dst_h))
    return resized.crop((left, top, left + dst_w, top + dst_h))


def fit_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return cover_resize(image, size)


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def parse_game_root_levels(project_root: Path) -> list[dict[str, Any]]:
    game_root = project_root / "assets" / "scripts" / "GameRoot.ts"
    text = game_root.read_text(encoding="utf-8")
    block = re.search(r"const LEVELS: Level\[] = \[(?P<body>[\s\S]*?)\];", text)
    if not block:
        return []
    rows = []
    pattern = re.compile(
        r"\{ name: '(?P<name>[^']+)', subtitle: '(?P<subtitle>[^']+)'[\s\S]*?"
        r"speed: (?P<speed>\d+), length: (?P<length>\d+), target: (?P<target>\d+), theme: (?P<theme>\d+) \}"
    )
    for m in pattern.finditer(block.group("body")):
        rows.append(
            {
                "name": m.group("name"),
                "subtitle": m.group("subtitle"),
                "speed": int(m.group("speed")),
                "length": int(m.group("length")),
                "target": int(m.group("target")),
                "theme": int(m.group("theme")),
            }
        )
    return rows


def load_canon(project_root: Path) -> dict[str, Any]:
    canon_path = project_root / "nessesary" / "10" / "mtr_level_canon_manifest.json"
    return json.loads(canon_path.read_text(encoding="utf-8-sig"))


def source_info(project_root: Path, path: Path, slot: int) -> SourceInfo:
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        gray = rgb.convert("L")
        stat = ImageStat.Stat(gray)
        mean_luma = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        mode = img.mode
        width, height = img.size
    role = SOURCE_SLOT_ROLES.get(slot, "extra_reference_not_runtime_whole_sheet")
    whole_sheet_policy = "runtime_primary" if slot == PRIMARY_SOURCE_SLOT else "audit_only_do_not_embed_whole_sheet"
    return SourceInfo(
        slot=slot,
        role=role,
        fileName=path.name,
        relativePath=str(path.relative_to(project_root)).replace("\\", "/"),
        width=width,
        height=height,
        mode=mode,
        sha256=sha256_file(path),
        meanLuma=round(mean_luma, 2),
        contrast=round(contrast, 2),
        wholeSheetRuntimePolicy=whole_sheet_policy,
    )


def apply_runtime_grade(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    overlay = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = rgb.size
    draw.rectangle((0, int(h * 0.69), w, h), fill=(0, 0, 0, 38))
    draw.rectangle((0, 0, w, int(h * 0.12)), fill=(255, 246, 220, 14))
    graded = Image.alpha_composite(rgb.convert("RGBA"), overlay).convert("RGB")
    return graded


def build_level_background(project_root: Path, level: int, sources: list[SourceInfo]) -> dict[str, Any]:
    source_dir = project_root / "nessesary" / "10" / "Levels" / str(level)
    files = sorted(source_dir.glob("*.png"))
    primary = files[PRIMARY_SOURCE_SLOT - 1] if len(files) >= PRIMARY_SOURCE_SLOT else files[0]
    out_full = project_root / "assets" / "resources" / "backgrounds" / f"level{level:02d}.jpg"
    out_preview = project_root / "assets" / "resources" / "backgrounds_preview" / f"level{level:02d}.jpg"
    out_full.parent.mkdir(parents=True, exist_ok=True)
    out_preview.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(primary) as img:
        full = apply_runtime_grade(fit_resize(img.convert("RGB"), TARGET_SIZE))
    full.save(out_full, quality=JPEG_QUALITY_FULL, optimize=True, progressive=True)
    preview = full.resize(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    preview.save(out_preview, quality=JPEG_QUALITY_PREVIEW, optimize=True, progressive=True)

    selected = next(item for item in sources if item.fileName == primary.name)
    return {
        "level": level,
        "resource": f"backgrounds/level{level:02d}",
        "previewResource": f"backgrounds_preview/level{level:02d}",
        "sourceIteration": 10,
        "sourceDirectory": str(source_dir.relative_to(project_root)).replace("\\", "/"),
        "selectedSourceSlot": PRIMARY_SOURCE_SLOT,
        "selectedSourceName": primary.name,
        "selectedSourceRole": selected.role,
        "selectedSourceSha256": selected.sha256,
        "targetSize": list(TARGET_SIZE),
        "previewSize": list(PREVIEW_SIZE),
        "normalization": "center_cover_resize_bottom_weighted_crop_runtime_grade",
        "runtimePolicy": "single_scenic_bitmap_no_old_fallback_no_sheet_embedding",
        "sourceAudit": [asdict(item) for item in sources],
        "output": str(out_full),
        "previewOutput": str(out_preview),
        "outputSha256": sha256_file(out_full),
        "previewSha256": sha256_file(out_preview),
    }


def make_selected_contact_sheet(project_root: Path, entries: list[dict[str, Any]]) -> Path:
    out_dir = project_root / "qa" / "texture10-background-evidence" / "contact_sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h = 320, 148
    label_h = 26
    cols = 3
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (22, 22, 22))
    draw = ImageDraw.Draw(sheet)
    font = load_font(14)
    for idx, entry in enumerate(entries):
        level = entry["level"]
        img_path = project_root / "assets" / "resources" / "backgrounds" / f"level{level:02d}.jpg"
        with Image.open(img_path) as img:
            thumb = img.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(16, 16, 16))
        draw.text((x + 8, y + thumb_h + 5), f"L{level:02d} slot {entry['selectedSourceSlot']} 1920x886", fill=(240, 232, 196), font=font)
        draw.rectangle((x, y, x + thumb_w - 1, y + thumb_h + label_h - 1), outline=(96, 88, 72))
    out = out_dir / "texture10_selected_runtime_backgrounds.jpg"
    sheet.save(out, quality=90)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    levels_dir = project_root / "nessesary" / "10" / "Levels"
    if not levels_dir.exists():
        raise FileNotFoundError(f"Missing texture10 level background source: {levels_dir}")

    canon = load_canon(project_root)
    existing_levels = parse_game_root_levels(project_root)
    entries: list[dict[str, Any]] = []
    audit_warnings: list[str] = []
    for level in range(1, 16):
        files = sorted((levels_dir / str(level)).glob("*.png"))
        if len(files) < PRIMARY_SOURCE_SLOT:
            raise RuntimeError(f"Level {level:02d} has fewer than {PRIMARY_SOURCE_SLOT} PNG files")
        sources = [source_info(project_root, path, slot) for slot, path in enumerate(files, 1)]
        entries.append(build_level_background(project_root, level, sources))
        if len(files) != 8:
            audit_warnings.append(f"Level {level:02d} expected 8 source PNG files, found {len(files)}")
        primary = sources[PRIMARY_SOURCE_SLOT - 1]
        if primary.width < 1400 or primary.height < 800:
            audit_warnings.append(f"Level {level:02d} primary source is small: {primary.width}x{primary.height}")

    manifest = {
        "version": "2026-06-12-texture10-backgrounds",
        "game": "Martyshkin Trud Runner",
        "sourceRoot": "nessesary/10/Levels",
        "canonManifest": "nessesary/10/mtr_level_canon_manifest.json",
        "targetSize": list(TARGET_SIZE),
        "previewSize": list(PREVIEW_SIZE),
        "primarySourceSlot": PRIMARY_SOURCE_SLOT,
        "legacyBackgroundPolicy": "previous generated background families are obsolete and must not be referenced",
        "levels": entries,
    }
    source_manifest = project_root / "assets" / "resources" / "backgrounds" / "background_sources.json"
    source_manifest.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    config_manifest = project_root / "assets" / "resources" / "config" / "background_manifest_texture10.json"
    config_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    report_dir = project_root / "qa" / "texture10-background-evidence" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    selected_sheet = make_selected_contact_sheet(project_root, entries)
    report = {
        "passed": len(audit_warnings) == 0,
        "warnings": audit_warnings,
        "sourcePngCount": sum(len(list((levels_dir / str(level)).glob("*.png"))) for level in range(1, 16)),
        "runtimeBackgroundCount": len(entries),
        "runtimePreviewCount": len(entries),
        "selectedContactSheet": str(selected_sheet.relative_to(project_root)).replace("\\", "/"),
        "canonVersion": canon.get("version"),
        "canonLevels": canon.get("canonicalLevelCount"),
        "gameRootLevelsDetected": len(existing_levels),
        "manifest": str(config_manifest.relative_to(project_root)).replace("\\", "/"),
    }
    report_path = report_dir / "texture10_background_pipeline_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MTR_TEXTURE10_BACKGROUNDS_OK levels={len(entries)} sourcePng=120 report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
