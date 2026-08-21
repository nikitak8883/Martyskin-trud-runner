#!/usr/bin/env python3
"""Generate deterministic, manifest-linked M04-B contact sheets.

The generated PNG/HTML files are local QA evidence. Runtime assets and Cocos
metadata are never modified. The canonical JSON index is source-controlled and
can be checked byte-for-byte without materializing the sheet files.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, __version__ as PILLOW_VERSION
except Exception as exc:  # pragma: no cover - environment gate
    Image = ImageDraw = ImageFont = ImageOps = None  # type: ignore[assignment]
    PILLOW_VERSION = "unavailable"
    PIL_IMPORT_ERROR = str(exc)
else:
    PIL_IMPORT_ERROR = ""


GENERATOR_VERSION = "m04-b-contact-sheets.v1"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
CATEGORY_ORDER = ["hud", "menu", "runner", "bonuses", "obstacles", "backgrounds", "vfx"]
CATEGORY_LABELS = {
    "hud": "HUD",
    "menu": "Menu",
    "runner": "Runner",
    "bonuses": "Bonuses",
    "obstacles": "Obstacles and platforms",
    "backgrounds": "Backgrounds and previews",
    "vfx": "VFX textures",
}
PAGE_COLUMNS = 8
PAGE_ROWS = 8
ASSETS_PER_PAGE = PAGE_COLUMNS * PAGE_ROWS
CELL_WIDTH = 176
CELL_HEIGHT = 174
PREVIEW_WIDTH = 156
PREVIEW_HEIGHT = 124
PAGE_HEADER_HEIGHT = 48
MARGIN = 12


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def contained_path(root: Path, candidate: Path) -> Path | None:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_candidate


def project_rel(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_controlled_artifact_name(name: str) -> bool:
    return (
        (name.startswith("m04b_") and (name.endswith(".png") or name == "m04b_contact_sheet_index.html"))
        or (name.startswith(".m04b_") and name.endswith(".tmp"))
    )


def remove_stale_artifacts(output_root: Path, expected_names: set[str]) -> list[str]:
    """Delete only stale generator-owned files directly under the bounded output root."""

    removed: list[str] = []
    if not output_root.exists():
        return removed
    for candidate in sorted(output_root.iterdir()):
        if not candidate.is_file() or not is_controlled_artifact_name(candidate.name):
            continue
        if candidate.name in expected_names:
            continue
        if contained_path(output_root, candidate) is None:
            raise ValueError(f"refusing to remove stale artifact outside output root: {candidate}")
        candidate.unlink()
        removed.append(candidate.name)
    return removed


def selector_matches(relative: str, selector: dict[str, Any]) -> bool:
    path = selector.get("path")
    mode = selector.get("match")
    extensions = selector.get("extensions")
    if not isinstance(path, str) or mode not in {"prefix", "exact_file"}:
        return False
    if isinstance(extensions, list) and Path(relative).suffix.lower() not in extensions:
        return False
    return relative == path if mode == "exact_file" else relative == path or relative.startswith(f"{path}/")


def ownership_matches(relative: str, scope: dict[str, Any]) -> bool:
    path = scope.get("path")
    mode = scope.get("match")
    if not isinstance(path, str) or mode not in {"prefix", "exact_file"}:
        return False
    return relative == path if mode == "exact_file" else relative == path or relative.startswith(f"{path}/")


def classify(relative: str) -> str:
    """Assign every governed image to exactly one required M04.4 category."""

    if relative.startswith("characters/player_skins/"):
        return "runner" if "/base/" in relative else "bonuses"
    if relative.startswith(("objectives/bonuses/", "objectives/equipment/")):
        return "bonuses"
    if relative.startswith("objectives/collectibles/"):
        return "vfx" if "_glow_" in Path(relative).stem else "runner"
    if relative.startswith("objectives/npc/"):
        return "obstacles"
    if relative.startswith("objectives/themed/last_iteration/ui/"):
        return "menu"
    if relative.startswith("objectives/themed/last_iteration/"):
        return "obstacles"
    if relative.startswith("objectives/ui/"):
        return "hud"
    if relative.startswith("ui/main_menu_background/"):
        return "backgrounds"
    if relative.startswith("ui/shared/cards/hud_"):
        return "hud"
    if relative.startswith("ui/"):
        return "menu"
    if relative.startswith(("backgrounds/", "backgrounds_preview/")):
        return "backgrounds"
    raise ValueError(f"unclassified runtime image: {relative}")


def checkerboard(size: tuple[int, int], block: int = 12) -> Image.Image:  # type: ignore[name-defined]
    canvas = Image.new("RGBA", size, (32, 36, 42, 255))
    draw = ImageDraw.Draw(canvas)
    colors = ((50, 55, 63, 255), (72, 77, 86, 255))
    for y in range(0, size[1], block):
        for x in range(0, size[0], block):
            draw.rectangle(
                [x, y, min(size[0] - 1, x + block - 1), min(size[1] - 1, y + block - 1)],
                fill=colors[((x // block) + (y // block)) % 2],
            )
    return canvas


def fit_preview(image: Image.Image) -> Image.Image:  # type: ignore[name-defined]
    rgba = image.convert("RGBA")
    fitted = ImageOps.contain(rgba, (PREVIEW_WIDTH, PREVIEW_HEIGHT), method=Image.Resampling.LANCZOS)
    preview = checkerboard((PREVIEW_WIDTH, PREVIEW_HEIGHT))
    x = (PREVIEW_WIDTH - fitted.width) // 2
    y = (PREVIEW_HEIGHT - fitted.height) // 2
    preview.alpha_composite(fitted, (x, y))
    return preview


def render_page(category: str, page_number: int, assets: list[dict[str, Any]], resources_root: Path) -> bytes:
    page_width = MARGIN * 2 + PAGE_COLUMNS * CELL_WIDTH
    page_height = MARGIN * 2 + PAGE_HEADER_HEIGHT + PAGE_ROWS * CELL_HEIGHT
    page = Image.new("RGB", (page_width, page_height), (10, 13, 17))
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    title = f"MTR M04-B / {CATEGORY_LABELS[category]} / page {page_number}"
    draw.text((MARGIN, MARGIN), title, fill=(170, 255, 190), font=font)
    draw.text((MARGIN, MARGIN + 18), "checkerboard = transparency; source assets are not modified", fill=(150, 165, 180), font=font)

    for index, asset in enumerate(assets):
        column = index % PAGE_COLUMNS
        row = index // PAGE_COLUMNS
        x = MARGIN + column * CELL_WIDTH
        y = MARGIN + PAGE_HEADER_HEIGHT + row * CELL_HEIGHT
        draw.rectangle([x, y, x + CELL_WIDTH - 3, y + CELL_HEIGHT - 3], fill=(22, 27, 34), outline=(63, 76, 91))
        with Image.open(resources_root / asset["path"]) as source:
            preview = fit_preview(source)
        page.paste(preview.convert("RGB"), (x + 8, y + 7))
        basename = Path(asset["path"]).name
        if len(basename) > 25:
            basename = f"{basename[:22]}..."
        draw.text((x + 8, y + 134), basename, fill=(230, 235, 241), font=font)
        details = f"{asset['width']}x{asset['height']} {asset['atlasId']}"
        if len(details) > 27:
            details = f"{details[:24]}..."
        draw.text((x + 8, y + 150), details, fill=(145, 184, 255), font=font)

    buffer = io.BytesIO()
    page.save(buffer, format="PNG", compress_level=9, optimize=False)
    return buffer.getvalue()


def html_bytes(categories: list[dict[str, Any]]) -> bytes:
    sections: list[str] = []
    for category in categories:
        images = "".join(
            f'<figure><img src="{Path(sheet["path"]).name}" alt="{category["id"]} {sheet["id"]}">'
            f'<figcaption>{sheet["id"]} · {sheet["assetCount"]} assets · {sheet["sha256"]}</figcaption></figure>'
            for sheet in category["sheets"]
        )
        sections.append(
            f'<section><h2>{CATEGORY_LABELS[category["id"]]}</h2>'
            f'<p>{category["assetCount"]} assets; atlas links: {", ".join(category["atlasIds"])}</p>{images}</section>'
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MTR M04-B contact sheets</title>
  <style>
    body {{ margin: 24px; background: #080b0e; color: #d9ffe2; font-family: Consolas, monospace; }}
    section {{ margin: 28px 0; padding: 16px; border: 1px solid #245d35; background: #0d1410; }}
    figure {{ margin: 18px 0; }} img {{ display: block; max-width: 100%; height: auto; border: 1px solid #3b7650; }}
    figcaption, p {{ color: #94bda0; overflow-wrap: anywhere; }}
  </style>
</head>
<body><h1>MTR M04-B manifest-linked contact sheets</h1>
<p>Local QA evidence only. Regenerate from the canonical source tree; no runtime image is changed.</p>
{''.join(sections)}
</body></html>
"""
    return html.encode("utf-8")


def collect_assets(project_root: Path, resources_root: Path, atlas: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups = atlas.get("atlas_groups") if isinstance(atlas.get("atlas_groups"), list) else []
    scopes = atlas.get("ownership_scopes") if isinstance(atlas.get("ownership_scopes"), list) else []
    categories: dict[str, list[dict[str, Any]]] = {category: [] for category in CATEGORY_ORDER}
    for path in sorted(resources_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if contained_path(resources_root, path) is None:
            raise ValueError(f"runtime image escapes resources root: {path}")
        relative = path.relative_to(resources_root).as_posix()
        group_matches = [
            (index, group)
            for index, group in enumerate(groups)
            if isinstance(group, dict)
            and any(selector_matches(relative, selector) for selector in group.get("source_selectors", []) if isinstance(selector, dict))
        ]
        scope_matches = [
            (index, scope)
            for index, scope in enumerate(scopes)
            if isinstance(scope, dict) and ownership_matches(relative, scope)
        ]
        if len(group_matches) != 1 or len(scope_matches) != 1:
            raise ValueError(
                f"manifest ownership must be exactly one atlas and one scope for {relative}: "
                f"groups={len(group_matches)} scopes={len(scope_matches)}"
            )
        group_index, group = group_matches[0]
        scope_index, scope = scope_matches[0]
        provenance = sorted(set(group.get("provenance", [])) | set(scope.get("provenance", [])))
        if not provenance or any(
            not isinstance(item, str)
            or contained_path(project_root, project_root / item) is None
            or not (project_root / item).is_file()
            for item in provenance
        ):
            raise ValueError(f"unresolved provenance for {relative}: {provenance}")
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
            alpha = image.convert("RGBA").getchannel("A") if "A" in image.getbands() or "transparency" in image.info else None
            bbox = alpha.getbbox() if alpha is not None else None
        category = classify(relative)
        categories[category].append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "width": width,
                "height": height,
                "mode": mode,
                "hasAlpha": alpha is not None,
                "alphaBBox": list(bbox) if bbox else None,
                "atlasId": group["atlas_id"],
                "atlasManifestPointer": f"/atlas_groups/{group_index}",
                "ownershipScope": scope["scope_id"],
                "ownershipManifestPointer": f"/ownership_scopes/{scope_index}",
                "provenance": provenance,
            }
        )
    return categories


def build_index(
    project_root: Path,
    resources_root: Path,
    atlas_path: Path,
    output_root: Path,
    write_artifacts: bool,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    if Image is None:
        raise RuntimeError(f"Pillow/PIL is not available: {PIL_IMPORT_ERROR}")
    atlas = load_json(atlas_path)
    by_category = collect_assets(project_root, resources_root, atlas)
    artifacts: dict[str, bytes] = {}
    category_records: list[dict[str, Any]] = []
    total_assets = 0
    total_sheets = 0

    for category in CATEGORY_ORDER:
        assets = by_category[category]
        if not assets:
            raise ValueError(f"required contact-sheet category is empty: {category}")
        sheet_records: list[dict[str, Any]] = []
        for page_index, start in enumerate(range(0, len(assets), ASSETS_PER_PAGE), start=1):
            page_assets = assets[start : start + ASSETS_PER_PAGE]
            sheet_id = f"{category}-{page_index:02d}"
            output_path = output_root / f"m04b_{sheet_id}.png"
            payload = render_page(category, page_index, page_assets, resources_root)
            relative_output = project_rel(output_path, project_root)
            artifacts[relative_output] = payload
            for cell_index, asset in enumerate(page_assets):
                asset["sheetId"] = sheet_id
                asset["cellIndex"] = cell_index
            with Image.open(io.BytesIO(payload)) as rendered:
                rendered_width, rendered_height = rendered.size
            sheet_records.append(
                {
                    "id": sheet_id,
                    "path": relative_output,
                    "sha256": sha256_bytes(payload),
                    "bytes": len(payload),
                    "width": rendered_width,
                    "height": rendered_height,
                    "assetCount": len(page_assets),
                }
            )
        source_digest = hashlib.sha256()
        for asset in assets:
            source_digest.update(f"{asset['path']}\0{asset['sha256']}\n".encode("utf-8"))
        category_records.append(
            {
                "id": category,
                "label": CATEGORY_LABELS[category],
                "assetCount": len(assets),
                "sheetCount": len(sheet_records),
                "sourceDigest": source_digest.hexdigest().upper(),
                "atlasIds": sorted({asset["atlasId"] for asset in assets}),
                "ownershipScopes": sorted({asset["ownershipScope"] for asset in assets}),
                "provenance": sorted({item for asset in assets for item in asset["provenance"]}),
                "sheets": sheet_records,
                "assets": assets,
            }
        )
        total_assets += len(assets)
        total_sheets += len(sheet_records)

    html_path = output_root / "m04b_contact_sheet_index.html"
    html = html_bytes(category_records)
    artifacts[project_rel(html_path, project_root)] = html
    content_identity = atlas.get("content_identity", {})
    inventory = atlas.get("inventory", {})
    index = {
        "schema": "mtr.asset_contact_sheets.v1",
        "schemaPath": "docs/global_modernization/v3/M04/schemas/contact_sheet_index.schema.json",
        "generator": {
            "id": GENERATOR_VERSION,
            "path": "tools/codex/render_m04_b_contact_sheets.py",
            "pillowVersion": PILLOW_VERSION,
            "deterministic": True,
            "runtimeAssetsMutated": False,
            "runtimeMetadataMutated": False,
        },
        "source": {
            "atlasManifest": project_rel(atlas_path, project_root),
            "atlasManifestSha256": sha256_file(atlas_path),
            "contentIdentity": content_identity.get("path"),
            "logicalContentVersion": content_identity.get("logical_content_version"),
            "sourcePayloadSha256": inventory.get("source_payload", {}).get("sha256"),
        },
        "materialization": {
            "policy": "local_qa_evidence_not_runtime_not_committed",
            "outputRoot": project_rel(output_root, project_root),
            "regenerateCommand": "python -B tools/codex/render_m04_b_contact_sheets.py --project-root .",
            "checkCommand": "python -B tools/codex/render_m04_b_contact_sheets.py --project-root . --check",
            "html": {
                "path": project_rel(html_path, project_root),
                "sha256": sha256_bytes(html),
                "bytes": len(html),
            },
        },
        "classificationPolicy": {
            "version": 1,
            "requiredCategories": CATEGORY_ORDER,
            "coverage": "every governed PNG/JPG exactly once",
            "vfxRule": "collectible filename contains _glow_",
            "hudRule": "shared hud cards plus objective UI",
            "menuRule": "remaining shared/themed UI",
            "runnerRule": "base skin poses plus non-glow collectibles",
            "bonusesRule": "skin bonus variants plus objective bonuses/equipment",
            "obstaclesRule": "NPC plus non-UI themed gameplay art",
            "backgroundsRule": "level backgrounds/previews plus main-menu scenic bitmap",
        },
        "summary": {
            "categoryCount": len(category_records),
            "assetCount": total_assets,
            "sheetCount": total_sheets,
            "unclassifiedCount": 0,
            "duplicateClassificationCount": 0,
        },
        "categories": category_records,
    }

    if write_artifacts:
        output_root.mkdir(parents=True, exist_ok=True)
        remove_stale_artifacts(output_root, {Path(relative).name for relative in artifacts})
        for relative, payload in artifacts.items():
            destination = project_root / relative
            if contained_path(output_root, destination) is None:
                raise ValueError(f"generated artifact escapes output root: {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_bytes(payload)
            temporary.replace(destination)
    return index, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--resources-root", default="assets/resources")
    parser.add_argument("--atlas-manifest", default="assets/resources/config/atlas_manifest.json")
    parser.add_argument("--output-root", default="temp/m04-b-contact-sheets")
    parser.add_argument("--index", default="docs/global_modernization/v3/M04/contact_sheet_index.json")
    parser.add_argument("--check", action="store_true", help="Recompute in memory and compare the canonical index; write nothing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = Path(args.project_root).resolve()
        resources_root = contained_path(project_root, project_root / args.resources_root)
        atlas_path = contained_path(project_root, project_root / args.atlas_manifest)
        output_root = contained_path(project_root, project_root / args.output_root)
        index_path = contained_path(project_root, project_root / args.index)
        if resources_root is None or atlas_path is None or output_root is None or index_path is None:
            raise ValueError("resources, manifest, output and index paths must stay inside project root")
        if not resources_root.is_dir() or not atlas_path.is_file():
            raise ValueError("resources root or atlas manifest is missing")
        index, _ = build_index(project_root, resources_root, atlas_path, output_root, not args.check)
        payload = canonical_json(index)
        if args.check:
            if not index_path.is_file():
                raise ValueError(f"canonical contact-sheet index is missing: {index_path}")
            actual = index_path.read_bytes()
            if actual != payload:
                raise ValueError(
                    f"canonical contact-sheet index is stale: expected={sha256_bytes(payload)} actual={sha256_bytes(actual)}"
                )
        else:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = index_path.with_name(f".{index_path.name}.tmp")
            temporary.write_bytes(payload)
            temporary.replace(index_path)
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "check" if args.check else "generate",
                    "summary": index["summary"],
                    "index": project_rel(index_path, project_root),
                    "indexSha256": sha256_bytes(payload),
                    "outputRoot": project_rel(output_root, project_root),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
