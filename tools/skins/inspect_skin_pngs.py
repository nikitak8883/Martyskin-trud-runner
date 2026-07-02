#!/usr/bin/env python3
"""Inventory and alpha-QA for staged Martyskin source skin packs.

This script intentionally uses only the Python standard library. It is meant to
run in a freshly restarted Codex/Cocos environment without installing Pillow or
other image dependencies. It does not cut sprites, modify runtime configs, or
move source files; it only writes audit manifests and markdown reports.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import math
import re
import struct
import subprocess
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COLOR_TYPES = {
    0: "GRAY",
    2: "RGB",
    3: "INDEXED",
    4: "GRAY_ALPHA",
    6: "RGBA",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_if_exists(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def run_git_status(project_root: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(project_root),
            text=True,
            capture_output=True,
            timeout=12,
            check=False,
        )
        return {
            "exitCode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"exitCode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def read_png_chunks(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Not a PNG file")
    pos = len(PNG_SIGNATURE)
    chunks: list[tuple[str, bytes]] = []
    idat = bytearray()
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8].decode("ascii", errors="replace")
        chunk_data = data[pos + 8 : pos + 8 + length]
        chunks.append((ctype, chunk_data))
        if ctype == "IDAT":
            idat.extend(chunk_data)
        pos += 12 + length
        if ctype == "IEND":
            break
    ihdr = next((chunk for ctype, chunk in chunks if ctype == "IHDR"), None)
    if not ihdr or len(ihdr) != 13:
        raise ValueError("PNG IHDR is missing or invalid")
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", ihdr)
    plte = next((chunk for ctype, chunk in chunks if ctype == "PLTE"), b"")
    trns = next((chunk for ctype, chunk in chunks if ctype == "tRNS"), b"")
    return {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "mode": COLOR_TYPES.get(color_type, f"UNKNOWN_{color_type}"),
        "compression": compression,
        "filterMethod": filter_method,
        "interlace": interlace,
        "hasTRNS": bool(trns),
        "plte": plte,
        "trns": trns,
        "idat": bytes(idat),
        "chunkTypes": [ctype for ctype, _ in chunks],
    }


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def unfilter_png_rows(raw: bytes, width: int, height: int, bit_depth: int, color_type: int) -> list[bytes]:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"Unsupported PNG color type {color_type}")
    bits_per_pixel = channels * bit_depth
    row_bytes = math.ceil(width * bits_per_pixel / 8)
    bpp = max(1, math.ceil(bits_per_pixel / 8))
    rows: list[bytes] = []
    prev = bytes(row_bytes)
    pos = 0
    for _ in range(height):
        if pos >= len(raw):
            raise ValueError("PNG scanline data ended early")
        filter_type = raw[pos]
        pos += 1
        scan = bytearray(raw[pos : pos + row_bytes])
        pos += row_bytes
        recon = bytearray(row_bytes)
        for i, value in enumerate(scan):
            left = recon[i - bpp] if i >= bpp else 0
            up = prev[i] if i < len(prev) else 0
            up_left = prev[i - bpp] if i >= bpp and i - bpp < len(prev) else 0
            if filter_type == 0:
                recon[i] = value
            elif filter_type == 1:
                recon[i] = (value + left) & 0xFF
            elif filter_type == 2:
                recon[i] = (value + up) & 0xFF
            elif filter_type == 3:
                recon[i] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                recon[i] = (value + paeth(left, up, up_left)) & 0xFF
            else:
                raise ValueError(f"Unsupported PNG filter {filter_type}")
        rows.append(bytes(recon))
        prev = bytes(recon)
    return rows


def decode_palette(plte: bytes) -> list[tuple[int, int, int]]:
    colors = []
    for i in range(0, len(plte) - 2, 3):
        colors.append((plte[i], plte[i + 1], plte[i + 2]))
    return colors


def transparency_sample_value(trns: bytes, offset: int = 0) -> int | None:
    if len(trns) < offset + 2:
        return None
    return struct.unpack(">H", trns[offset : offset + 2])[0]


def analyze_png_alpha(path: Path) -> dict[str, Any]:
    meta = read_png_chunks(path)
    width = meta["width"]
    height = meta["height"]
    bit_depth = meta["bitDepth"]
    color_type = meta["colorType"]
    has_alpha_channel = color_type in (4, 6)
    has_alpha = has_alpha_channel or meta["hasTRNS"]
    base = {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "mode": meta["mode"],
        "hasAlpha": has_alpha,
        "hasAlphaChannel": has_alpha_channel,
        "hasTRNS": meta["hasTRNS"],
        "interlace": meta["interlace"],
        "detailedAlphaDecoded": False,
        "alphaMin": None,
        "alphaMax": None,
        "transparentPixels": None,
        "translucentPixels": None,
        "opaquePixels": None,
        "transparentRatio": None,
        "translucentRatio": None,
        "opaqueRatio": None,
        "nonEmptyBBox": None,
        "bboxCoverageRatio": None,
        "possibleCheckerboardPattern": False,
        "riskFlags": [],
    }
    if meta["interlace"] != 0:
        base["riskFlags"].append("interlaced_png_no_detailed_alpha")
        return base
    if bit_depth != 8:
        base["riskFlags"].append(f"bit_depth_{bit_depth}_no_detailed_alpha")
        if not has_alpha:
            base["riskFlags"].append("no_alpha_channel")
        return base

    raw = zlib.decompress(meta["idat"])
    rows = unfilter_png_rows(raw, width, height, bit_depth, color_type)
    palette = decode_palette(meta["plte"])
    trns = meta["trns"]
    trns_gray = transparency_sample_value(trns)
    trns_rgb = (
        transparency_sample_value(trns, 0),
        transparency_sample_value(trns, 2),
        transparency_sample_value(trns, 4),
    ) if len(trns) >= 6 else None
    total = width * height
    transparent = 0
    translucent = 0
    opaque = 0
    alpha_min = 255
    alpha_max = 0
    bbox_min_x = width
    bbox_min_y = height
    bbox_max_x = -1
    bbox_max_y = -1
    corner_colors: Counter[tuple[int, int, int]] = Counter()
    corner_span = min(18, max(2, width // 10), max(2, height // 10))

    def pixel_alpha_and_rgb(row: bytes, x: int) -> tuple[int, tuple[int, int, int]]:
        if color_type == 6:
            idx = x * 4
            return row[idx + 3], (row[idx], row[idx + 1], row[idx + 2])
        if color_type == 4:
            idx = x * 2
            gray = row[idx]
            return row[idx + 1], (gray, gray, gray)
        if color_type == 3:
            index = row[x]
            alpha = trns[index] if index < len(trns) else 255
            rgb = palette[index] if index < len(palette) else (0, 0, 0)
            return alpha, rgb
        if color_type == 2:
            idx = x * 3
            rgb = (row[idx], row[idx + 1], row[idx + 2])
            alpha = 0 if trns_rgb and rgb == trns_rgb else 255
            return alpha, rgb
        if color_type == 0:
            gray = row[x]
            alpha = 0 if trns_gray is not None and gray == trns_gray else 255
            return alpha, (gray, gray, gray)
        return 255, (0, 0, 0)

    for y, row in enumerate(rows):
        for x in range(width):
            alpha, rgb = pixel_alpha_and_rgb(row, x)
            alpha_min = min(alpha_min, alpha)
            alpha_max = max(alpha_max, alpha)
            if alpha <= 0:
                transparent += 1
            elif alpha >= 255:
                opaque += 1
            else:
                translucent += 1
            if alpha > 8:
                bbox_min_x = min(bbox_min_x, x)
                bbox_min_y = min(bbox_min_y, y)
                bbox_max_x = max(bbox_max_x, x)
                bbox_max_y = max(bbox_max_y, y)
            in_corner = (
                (x < corner_span and y < corner_span)
                or (x >= width - corner_span and y < corner_span)
                or (x < corner_span and y >= height - corner_span)
                or (x >= width - corner_span and y >= height - corner_span)
            )
            if in_corner and alpha > 8:
                corner_colors[rgb] += 1

    if bbox_max_x >= bbox_min_x and bbox_max_y >= bbox_min_y:
        bbox = [bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y]
        bbox_area = (bbox_max_x - bbox_min_x + 1) * (bbox_max_y - bbox_min_y + 1)
    else:
        bbox = None
        bbox_area = 0

    top_colors = corner_colors.most_common(5)
    grayish_corner_colors = [
        color for color, count in top_colors
        if count >= 4 and max(color) - min(color) <= 18 and 110 <= (sum(color) / 3) <= 245
    ]
    possible_checkerboard = bool(len(grayish_corner_colors) >= 2 and transparent == 0)
    transparent_ratio = transparent / total if total else 0
    translucent_ratio = translucent / total if total else 0
    opaque_ratio = opaque / total if total else 0
    coverage_ratio = bbox_area / total if total else 0

    base.update(
        {
            "detailedAlphaDecoded": True,
            "alphaMin": alpha_min,
            "alphaMax": alpha_max,
            "transparentPixels": transparent,
            "translucentPixels": translucent,
            "opaquePixels": opaque,
            "transparentRatio": round(transparent_ratio, 6),
            "translucentRatio": round(translucent_ratio, 6),
            "opaqueRatio": round(opaque_ratio, 6),
            "nonEmptyBBox": bbox,
            "bboxCoverageRatio": round(coverage_ratio, 6),
            "possibleCheckerboardPattern": possible_checkerboard,
        }
    )
    if not has_alpha:
        base["riskFlags"].append("no_alpha_channel")
    if transparent_ratio < 0.005:
        base["riskFlags"].append("almost_no_transparency")
    if coverage_ratio > 0.985:
        base["riskFlags"].append("content_bbox_fills_canvas")
    if possible_checkerboard:
        base["riskFlags"].append("possible_baked_checkerboard")
    return base


def source_group_for(path: Path) -> tuple[str, str]:
    stem = path.stem
    variant_match = re.search(r"\s+\((\d+)\)$", stem)
    variant = variant_match.group(1) if variant_match else "base"
    group_stem = re.sub(r"\s+\(\d+\)$", "", stem)
    safe_group = re.sub(r"[^a-zA-Z0-9]+", "_", group_stem).strip("_").lower()
    return safe_group or "source_group", variant


def load_active_skin_manifest(project_root: Path) -> dict[str, Any]:
    manifest_path = project_root / "docs" / "skins_integration" / "manifests" / "player_skins_manifest.json"
    if not manifest_path.exists():
        return {"path": str(manifest_path), "exists": False}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["path"] = str(manifest_path)
        data["exists"] = True
        return data
    except Exception as exc:
        return {"path": str(manifest_path), "exists": True, "error": f"{type(exc).__name__}: {exc}"}


def active_skin_ids(active_manifest: dict[str, Any]) -> list[str]:
    for key in ("canonical_skin_ids", "selectedSkins", "skins"):
        value = active_manifest.get(key)
        if isinstance(value, list):
            ids = [str(item) for item in value if str(item).strip()]
            if ids:
                return ids
    skin_map = active_manifest.get("skin_mapping")
    if isinstance(skin_map, dict):
        return sorted(str(key) for key in skin_map if str(key).strip())
    return []


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def write_contact_sheet_html(path: Path, files: list[dict[str, Any]], source_root: Path) -> None:
    cards = []
    for item in files:
        image_path = Path(item["path"])
        try:
            uri = image_path.resolve().as_uri()
        except ValueError:
            uri = str(image_path)
        cards.append(
            f"""
            <article class="card">
              <img src="{html.escape(uri)}" alt="{html.escape(image_path.name)}" />
              <h2>{html.escape(item["candidateGroupId"])} / variant {html.escape(item["sourceVariant"])}</h2>
              <p>{html.escape(image_path.name)}</p>
              <p>{item["width"]}×{item["height"]} · {html.escape(item["mode"])} · alpha={item["hasAlpha"]}</p>
              <p>bbox={html.escape(str(item["nonEmptyBBox"]))}</p>
              <p>risks={html.escape(", ".join(item["riskFlags"]) or "none")}</p>
            </article>
            """
        )
    html_doc = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>Martyskin source skin-pack contact sheet</title>
  <style>
    body {{ margin: 24px; background: #17120d; color: #f6e9c0; font: 14px/1.4 system-ui, sans-serif; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }}
    .card {{ background: #251b12; border: 1px solid #76592d; border-radius: 14px; padding: 12px; }}
    img {{ width: 100%; height: 220px; object-fit: contain; background:
      linear-gradient(45deg, #777 25%, transparent 25%),
      linear-gradient(-45deg, #777 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #777 75%),
      linear-gradient(-45deg, transparent 75%, #777 75%);
      background-size: 24px 24px; background-position: 0 0, 0 12px, 12px -12px, -12px 0; }}
    h1, h2 {{ color: #ffd86a; }}
    h2 {{ font-size: 15px; }}
    p {{ margin: 5px 0; }}
  </style>
</head>
<body>
  <h1>Martyskin source skin-pack contact sheet</h1>
  <p>Source root: {html.escape(str(source_root))}</p>
  <section class="grid">
    {''.join(cards)}
  </section>
</body>
</html>
"""
    path.write_text(html_doc, encoding="utf-8")


def write_reports(args: argparse.Namespace, inventory: dict[str, Any]) -> None:
    project_root = Path(args.project_root).resolve()
    docs_dir = project_root / "docs" / "skins_integration"
    manifest_dir = project_root / "assets" / "resources" / "characters" / "player_skins" / "_shared" / "manifests"
    contact_dir = project_root / "assets" / "resources" / "characters" / "player_skins" / "_shared" / "debug_contact_sheets"
    docs_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    contact_dir.mkdir(parents=True, exist_ok=True)

    files = inventory["files"]
    quarantine = [item for item in files if item["riskFlags"]]
    source_inventory_json = manifest_dir / "source_inventory.json"
    alpha_json = manifest_dir / "png_alpha_validation.json"
    quarantine_json = manifest_dir / "quarantine_candidates.json"
    mapping_json = manifest_dir / "source_file_mapping_candidates.json"
    contact_html = contact_dir / "skin_pack_inventory_contact_sheet.html"
    write_contact_sheet_html(contact_html, files, Path(args.source_dir).resolve())

    source_inventory_json.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    alpha_json.write_text(json.dumps({"schemaVersion": 1, "generatedAt": inventory["generatedAt"], "files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    quarantine_json.write_text(json.dumps({"schemaVersion": 1, "generatedAt": inventory["generatedAt"], "files": quarantine}, ensure_ascii=False, indent=2), encoding="utf-8")
    mapping_json.write_text(json.dumps(inventory["mappingCandidates"], ensure_ascii=False, indent=2), encoding="utf-8")

    git = inventory["safety"]["gitStatus"]
    safety_lines = [
        "# Skin-pack safety checkpoint",
        "",
        f"- Generated: `{inventory['generatedAt']}`",
        f"- Project root: `{project_root}`",
        f"- Source dir: `{Path(args.source_dir).resolve()}`",
        f"- Prompt: `{Path(args.prompt).resolve() if args.prompt else ''}`",
        f"- Prompt SHA verified: `{inventory['prompt']['sha256Verified']}`",
        f"- Hermes checkpoint: `{inventory['safety'].get('hermesCheckpoint') or 'not provided'}`",
        f"- Git status exit: `{git['exitCode']}`",
        f"- Git status stderr: `{git['stderr'] or 'none'}`",
        "",
        "No destructive operations were used. This checkpoint intentionally stops before sprite cutting, runtime manifest replacement, or asset migration.",
        "",
        "## Git status stdout",
        "",
        "```text",
        git["stdout"] or "(empty)",
        "```",
    ]
    (docs_dir / "00_safety_checkpoint.md").write_text("\n".join(safety_lines) + "\n", encoding="utf-8")

    rows = []
    for item in files:
        rows.append(
            [
                item["candidateGroupId"],
                item["sourceVariant"],
                f"`{item['name']}`",
                f"{item['width']}×{item['height']}",
                item["mode"],
                str(item["hasAlpha"]),
                f"{item['transparentRatio']:.4f}" if isinstance(item["transparentRatio"], float) else "n/a",
                item["sha256"][:12],
                ", ".join(item["riskFlags"]) or "none",
            ]
        )
    inventory_lines = [
        "# Source skin-pack inventory",
        "",
        f"- PNG files found: `{len(files)}`",
        f"- Candidate source groups: `{len(inventory['mappingCandidates']['groups'])}`",
        f"- Recognized skin IDs from filenames: `{', '.join(inventory['recognizedSkinIds']) or 'none'}`",
        f"- Active runtime skin namespace: `assets/resources/characters/player_skins`",
        f"- Existing selected skins: `{', '.join(active_skin_ids(inventory['activeSkinManifest']))}`",
        f"- Contact sheet: `{contact_html}`",
        "",
        markdown_table(["group", "variant", "file", "size", "mode", "alpha", "transparent", "sha", "risks"], rows),
        "",
        "## Manual confirmations required before cutting",
        "",
    ]
    inventory_lines.extend(f"- {item}" for item in inventory["manualConfirmationsRequired"])
    (docs_dir / "01_source_inventory.md").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")

    alpha_rows = []
    for item in files:
        alpha_rows.append(
            [
                item["candidateGroupId"],
                f"`{item['name']}`",
                str(item["hasAlpha"]),
                str(item["nonEmptyBBox"]),
                f"{item['bboxCoverageRatio']:.4f}" if isinstance(item["bboxCoverageRatio"], float) else "n/a",
                str(item["possibleCheckerboardPattern"]),
                ", ".join(item["riskFlags"]) or "pass",
            ]
        )
    alpha_lines = [
        "# PNG alpha validation",
        "",
        f"- Decoded files: `{len(files)}`",
        f"- Files with risk flags: `{len(quarantine)}`",
        f"- Quarantine candidates JSON: `{quarantine_json}`",
        "",
        markdown_table(["group", "file", "alpha", "bbox", "bbox coverage", "checkerboard risk", "status"], alpha_rows),
        "",
        "A risk flag does not mean the asset is unusable; it means cutting should wait for visual confirmation or masking rules.",
    ]
    (docs_dir / "02_png_alpha_validation.md").write_text("\n".join(alpha_lines) + "\n", encoding="utf-8")

    plan_lines = [
        "# Skin-pack extraction and integration plan",
        "",
        "Current phase completed: safety checkpoint, source inventory, and alpha validation.",
        "",
        "Next phase is intentionally gated because source filenames are generic ChatGPT export names and do not encode canonical skin IDs or poses.",
        "",
        "## Proposed next steps",
        "",
        "1. Confirm whether each timestamp group is one skin, one pose sheet, or an A/B visual variant.",
        "2. Confirm target skin IDs and ordering. Existing active skin IDs are listed in `source_inventory.json`.",
        "3. For each accepted source, define cut boxes or sheet layout before any generated sprite replacement.",
        "4. Generate into a staging namespace first, then wire runtime manifests only after Web and Android screenshot QA.",
        "5. Keep only the code-level `player_skins_v2` compatibility redirect until Web and Android screenshot QA pass; the active asset namespace is `assets/resources/characters/player_skins`.",
        "",
        "## Candidate mapping JSON",
        "",
        f"`{mapping_json}`",
    ]
    (docs_dir / "03_extraction_plan.md").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")


def build_inventory(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    source_dir = Path(args.source_dir).resolve()
    prompt_path = Path(args.prompt).resolve() if args.prompt else None
    prompt_sha_path = Path(args.prompt_sha_file).resolve() if args.prompt_sha_file else None
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    prompt_sha = sha256_file(prompt_path) if prompt_path and prompt_path.exists() else ""
    prompt_sha_text = read_text_if_exists(prompt_sha_path).strip()
    prompt_sha_verified = bool(prompt_sha and prompt_sha_text and prompt_sha_text.startswith(prompt_sha))
    active_manifest = load_active_skin_manifest(project_root)
    pngs = sorted(source_dir.rglob("*.png"), key=lambda item: item.name.lower())
    group_stems: dict[str, str] = {}
    group_counter = 0
    files: list[dict[str, Any]] = []
    recognized_skin_ids: set[str] = set()
    existing_skins = set(active_skin_ids(active_manifest))

    for path in pngs:
        raw_group, variant = source_group_for(path)
        if raw_group not in group_stems:
            group_counter += 1
            group_stems[raw_group] = f"source_group_{group_counter:02d}"
        group_id = group_stems[raw_group]
        analysis = analyze_png_alpha(path)
        sha = sha256_file(path)
        name_lc = path.stem.lower()
        matched = sorted(skin_id for skin_id in existing_skins if skin_id.lower() in name_lc)
        recognized_skin_ids.update(matched)
        files.append(
            {
                "path": str(path),
                "name": path.name,
                "sizeBytes": path.stat().st_size,
                "sha256": sha,
                "rawGroupKey": raw_group,
                "candidateGroupId": group_id,
                "sourceVariant": variant,
                "recognizedSkinIds": matched,
                **analysis,
            }
        )

    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {"files": [], "candidateSkinId": None, "confidence": "manual"})
    for item in files:
        groups[item["candidateGroupId"]]["files"].append({"path": item["path"], "variant": item["sourceVariant"], "sha256": item["sha256"]})
    mapping_candidates = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "needsManualMapping": True,
        "reason": "Source filenames are generic export names and do not encode canonical skin ID, pose, or variant.",
        "groups": dict(groups),
    }
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "projectRoot": str(project_root),
        "sourceDir": str(source_dir),
        "prompt": {
            "path": str(prompt_path) if prompt_path else None,
            "sha256": prompt_sha,
            "sha256File": str(prompt_sha_path) if prompt_sha_path else None,
            "sha256FileText": prompt_sha_text,
            "sha256Verified": prompt_sha_verified,
        },
        "safety": {
            "gitStatus": run_git_status(project_root),
            "hermesCheckpoint": args.hermes_checkpoint,
            "destructiveOperationsUsed": False,
            "runtimeAssetsModified": False,
        },
        "activeSkinManifest": active_manifest,
        "recognizedSkinIds": sorted(recognized_skin_ids),
        "files": files,
        "mappingCandidates": mapping_candidates,
        "manualConfirmationsRequired": [
            "Map each source_group_NN to a canonical or new skin_id.",
            "Confirm whether paired `(1)` and `(2)` files are A/B variants, pose sheets, or separate skins.",
            "Confirm accepted transparent background/masking policy for files flagged as almost opaque or checkerboard risk.",
            "Confirm whether the canonical `assets/resources/characters/player_skins` target needs any project-specific override.",
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory and alpha-validate source skin PNGs.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-sha-file")
    parser.add_argument("--hermes-checkpoint", default="")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    inventory = build_inventory(args)
    write_reports(args, inventory)
    risk_count = sum(1 for item in inventory["files"] if item["riskFlags"])
    print(json.dumps({
        "pngFiles": len(inventory["files"]),
        "candidateGroups": len(inventory["mappingCandidates"]["groups"]),
        "riskFiles": risk_count,
        "promptShaVerified": inventory["prompt"]["sha256Verified"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
