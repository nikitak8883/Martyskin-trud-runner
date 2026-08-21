#!/usr/bin/env python3
"""Validate Martyshkin Trud runtime art assets without modifying files.

This script is intentionally non-mutating. It checks PNG readability, matching
`.meta` files, size limits, basic white-matte edge suspects, canonical atlas
manifest source paths, and resource references declared by runtime manifests.
It emits JSON for Codex/QA reports and returns non-zero only for structural
blockers by default.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except Exception as exc:  # pragma: no cover - environment gate
    Image = None  # type: ignore[assignment]
    PIL_IMPORT_ERROR = str(exc)
else:
    PIL_IMPORT_ERROR = ""


OPAQUE_ALPHA_MIN = 250
WHITE_RGB_MIN = 245
WHITE_MATTE_WARN_THRESHOLD = 200
REFERENCE_MISSING_SAMPLE_LIMIT = 50
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
SAFE_ASSET_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:@[0-9a-f]+)?$")
UUID_REFERENCE_RE = re.compile(r'"__uuid__"\s*:\s*"([0-9a-fA-F@-]+)"')
QUARANTINE_SEGMENTS = {"quarantine", "_quarantine", "incoming", "_incoming", "staging", "_staging"}
HIDDEN_REFERENCE_EXTENSIONS = {".scene", ".prefab", ".fire", ".anim", ".json"}

# These ids are deliberately reported by GameRoot.ts telemetry and drawn by
# code, not loaded as `assets/resources/<key>.png`. Keep this list tiny and
# explicit so a genuinely missing PNG still fails validation.
PROCEDURAL_RUNTIME_KEYS = {
    "foreground_safe_area_matte",
    "obstacle_label_component",
    "story_banner_component",
    "themed_platform_contact",
}


@dataclass
class PngInfo:
    path: str
    bytes: int
    width: int | None = None
    height: int | None = None
    mode: str | None = None
    hasAlpha: bool | None = None
    hasMeta: bool = False
    decodeError: str | None = None
    oversize: bool = False
    edgeConnectedOpaqueWhitePixels: int = 0
    whiteMatteSuspect: bool = False
    alphaBBox: list[int] | None = None
    fullyTransparent: bool = False


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def contained_path(root: Path, candidate: Path) -> Path | None:
    """Resolve a path and reject traversal or symlink/junction escape."""

    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_candidate


def has_alpha(image: Image.Image) -> bool:  # type: ignore[name-defined]
    return image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)


def is_opaque_white(pixel: tuple[int, ...]) -> bool:
    if len(pixel) >= 4 and pixel[3] < OPAQUE_ALPHA_MIN:
        return False
    return pixel[0] >= WHITE_RGB_MIN and pixel[1] >= WHITE_RGB_MIN and pixel[2] >= WHITE_RGB_MIN


def edge_connected_opaque_white_count(image: Image.Image, max_pixels: int = 200_000) -> int:  # type: ignore[name-defined]
    """Count opaque near-white pixels connected to the image border.

    This is a conservative artifact heuristic. It is reported as a warning by
    default because intentionally white UI art can be legitimate.
    """

    rgba = image.convert("RGBA")
    width, height = rgba.size
    if width <= 0 or height <= 0:
        return 0

    pixels = rgba.load()
    seen: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def push_if_white(x: int, y: int) -> None:
        if (x, y) in seen:
            return
        if is_opaque_white(pixels[x, y]):
            seen.add((x, y))
            queue.append((x, y))

    for x in range(width):
        push_if_white(x, 0)
        push_if_white(x, height - 1)
    for y in range(height):
        push_if_white(0, y)
        push_if_white(width - 1, y)

    count = 0
    while queue:
        x, y = queue.popleft()
        count += 1
        if count > max_pixels:
            return count
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in seen:
                continue
            if is_opaque_white(pixels[nx, ny]):
                seen.add((nx, ny))
                queue.append((nx, ny))
    return count


def scan_pngs(resources_root: Path, max_edge: int) -> tuple[list[PngInfo], dict[str, dict[str, int]]]:
    if Image is None:
        raise RuntimeError(f"Pillow/PIL is not available: {PIL_IMPORT_ERROR}")

    pngs = sorted(resources_root.rglob("*.png"))
    infos: list[PngInfo] = []
    groups: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "bytes": 0, "alpha": 0, "maxWidth": 0, "maxHeight": 0})

    for path in pngs:
        relative = rel(path, resources_root)
        meta_path = Path(str(path) + ".meta")
        info = PngInfo(
            path=relative,
            bytes=0,
            hasMeta=contained_path(resources_root, meta_path) is not None and meta_path.exists(),
        )
        if contained_path(resources_root, path) is None:
            info.decodeError = "path escapes resources root through traversal or symlink/junction"
            infos.append(info)
            continue
        try:
            info.bytes = path.stat().st_size
            with Image.open(path) as image:
                info.width, info.height = image.size
                info.mode = image.mode
                info.hasAlpha = has_alpha(image)
                info.oversize = image.size[0] > max_edge or image.size[1] > max_edge
                info.edgeConnectedOpaqueWhitePixels = edge_connected_opaque_white_count(image)
                info.whiteMatteSuspect = info.edgeConnectedOpaqueWhitePixels > WHITE_MATTE_WARN_THRESHOLD
                if info.hasAlpha:
                    alpha_bbox = image.convert("RGBA").getchannel("A").getbbox()
                    info.alphaBBox = list(alpha_bbox) if alpha_bbox else None
                    info.fullyTransparent = alpha_bbox is None
        except Exception as exc:
            info.decodeError = str(exc)

        top = info.path.split("/", 1)[0] if info.path else "."
        bucket = groups[top]
        bucket["count"] += 1
        bucket["bytes"] += info.bytes
        if info.hasAlpha:
            bucket["alpha"] += 1
        if info.width:
            bucket["maxWidth"] = max(bucket["maxWidth"], info.width)
        if info.height:
            bucket["maxHeight"] = max(bucket["maxHeight"], info.height)
        infos.append(info)

    return infos, dict(sorted(groups.items()))


def add_blocker(blockers: list[dict[str, Any]], finding_type: str, path: str, **details: Any) -> None:
    blockers.append({"type": finding_type, "path": path, **details})


def safe_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def selector_matches(relative: str, selector: dict[str, Any]) -> bool:
    selector_path = selector.get("path")
    mode = selector.get("match")
    extensions = selector.get("extensions")
    if not isinstance(selector_path, str) or mode not in {"prefix", "exact_file"}:
        return False
    if isinstance(extensions, list) and Path(relative).suffix.lower() not in extensions:
        return False
    if mode == "exact_file":
        return relative == selector_path
    return relative == selector_path or relative.startswith(f"{selector_path}/")


def ownership_matches(relative: str, scope: dict[str, Any]) -> bool:
    scope_path = scope.get("path")
    mode = scope.get("match")
    if not isinstance(scope_path, str) or mode not in {"prefix", "exact_file"}:
        return False
    if mode == "exact_file":
        return relative == scope_path
    return relative == scope_path or relative.startswith(f"{scope_path}/")


def sprite_submeta(meta: dict[str, Any]) -> dict[str, Any] | None:
    sub_metas = meta.get("subMetas")
    if not isinstance(sub_metas, dict):
        return None
    return next(
        (value for value in sub_metas.values() if isinstance(value, dict) and value.get("importer") == "sprite-frame"),
        None,
    )


def texture_submeta(meta: dict[str, Any]) -> dict[str, Any] | None:
    sub_metas = meta.get("subMetas")
    if not isinstance(sub_metas, dict):
        return None
    return next(
        (value for value in sub_metas.values() if isinstance(value, dict) and value.get("importer") == "texture"),
        None,
    )


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def collect_all_meta_uuids(assets_root: Path) -> tuple[set[str], list[Path]]:
    uuids: set[str] = set()
    escaped: list[Path] = []
    for meta_path in sorted(assets_root.rglob("*.meta")):
        if contained_path(assets_root, meta_path) is None:
            escaped.append(meta_path)
            continue
        data, error = safe_json(meta_path)
        if error or not isinstance(data, dict):
            continue
        candidates = [data.get("uuid")]
        sub_metas = data.get("subMetas")
        if isinstance(sub_metas, dict):
            candidates.extend(
                value.get("uuid")
                for value in sub_metas.values()
                if isinstance(value, dict)
            )
        for candidate in candidates:
            if isinstance(candidate, str):
                uuids.add(candidate.lower())
    return uuids, escaped


def validate_hidden_uuid_references(
    project_root: Path,
    assets_root: Path,
    image_uuids: set[str],
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    all_uuids, escaped_meta_paths = collect_all_meta_uuids(assets_root)
    for escaped_path in escaped_meta_paths:
        add_blocker(
            blockers,
            "metadata_path_escape",
            project_rel(escaped_path, project_root),
        )
    resolved_image = 0
    dangling: list[dict[str, str]] = []
    scanned_files = 0
    for source_path in sorted(assets_root.rglob("*")):
        if not source_path.is_file() or source_path.suffix.lower() not in HIDDEN_REFERENCE_EXTENSIONS:
            continue
        if contained_path(assets_root, source_path) is None:
            add_blocker(
                blockers,
                "hidden_reference_path_escape",
                project_rel(source_path, project_root),
            )
            continue
        scanned_files += 1
        try:
            text = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in UUID_REFERENCE_RE.finditer(text):
            uuid = match.group(1).lower()
            if uuid in image_uuids:
                resolved_image += 1
            elif uuid not in all_uuids and UUID_RE.fullmatch(uuid):
                item = {"path": project_rel(source_path, project_root), "uuid": uuid}
                dangling.append(item)
                add_blocker(blockers, "hidden_uuid_reference_dangling", item["path"], uuid=uuid)
    return {
        "checked": True,
        "scannedFileCount": scanned_files,
        "knownUuidCount": len(all_uuids),
        "metadataPathEscapeCount": len(escaped_meta_paths),
        "imageUuidCount": len(image_uuids),
        "resolvedImageReferenceCount": resolved_image,
        "danglingCount": len(dangling),
        "danglingSample": dangling[:REFERENCE_MISSING_SAMPLE_LIMIT],
    }


def validate_bundle_meta(
    project_root: Path,
    resources_root: Path,
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    meta_path = Path(str(resources_root) + ".meta")
    relative = project_rel(meta_path, project_root)
    if contained_path(project_root, meta_path) is None:
        add_blocker(blockers, "bundle_meta_path_escape", relative)
        return {"checked": True, "path": relative, "valid": False, "error": "path_escape"}
    data, error = safe_json(meta_path)
    if error or not isinstance(data, dict):
        add_blocker(blockers, "bundle_meta_invalid", relative, error=error or "not_an_object")
        return {"checked": True, "path": relative, "valid": False, "error": error}
    user_data = data.get("userData") if isinstance(data.get("userData"), dict) else {}
    expected = {"isBundle": True, "bundleName": "resources", "priority": 8}
    actual = {key: user_data.get(key) for key in expected}
    if actual != expected:
        add_blocker(blockers, "bundle_placement_invalid", relative, expected=expected, actual=actual)
    return {
        "checked": True,
        "path": relative,
        "valid": actual == expected,
        "bundleName": user_data.get("bundleName"),
        "priority": user_data.get("priority"),
    }


def validate_image_governance(
    project_root: Path,
    resources_root: Path,
    atlas_data: Any,
    png_infos: list[PngInfo],
    quarantine_root: Path | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate M04-B pre-import rules without changing source assets."""

    blockers: list[dict[str, Any]] = []
    if not isinstance(atlas_data, dict):
        add_blocker(blockers, "atlas_manifest_invalid", "assets/resources/config/atlas_manifest.json")
        return {"checked": True, "status": "FAIL", "blockerCount": len(blockers)}, blockers

    raw_groups = atlas_data.get("atlas_groups")
    raw_scopes = atlas_data.get("ownership_scopes")
    groups = raw_groups if isinstance(raw_groups, list) else []
    scopes = raw_scopes if isinstance(raw_scopes, list) else []
    if not groups:
        add_blocker(blockers, "atlas_groups_invalid", "assets/resources/config/atlas_manifest.json")
    if not scopes:
        add_blocker(blockers, "ownership_scopes_invalid", "assets/resources/config/atlas_manifest.json")
    for index, group in enumerate(groups):
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("atlas_id"), str)
            or not group.get("atlas_id")
            or not isinstance(group.get("source_selectors"), list)
            or not group.get("source_selectors")
        ):
            add_blocker(blockers, "atlas_group_contract_invalid", f"/atlas_groups/{index}")
    for index, scope in enumerate(scopes):
        if (
            not isinstance(scope, dict)
            or not isinstance(scope.get("scope_id"), str)
            or not scope.get("scope_id")
            or scope.get("match") not in {"prefix", "exact_file"}
            or not isinstance(scope.get("path"), str)
        ):
            add_blocker(blockers, "ownership_scope_contract_invalid", f"/ownership_scopes/{index}")
    images = sorted(
        path for path in resources_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    png_by_path = {item.path: item for item in png_infos}
    casefolded: dict[str, str] = {}
    naming_invalid = 0
    naming_collisions = 0
    quarantine_leaks = 0
    ownership_invalid = 0
    atlas_invalid = 0
    provenance_invalid = 0
    metadata_invalid = 0
    trim_invalid = 0
    pivot_invalid = 0
    alpha_invalid = 0
    internal_reference_invalid = 0
    image_uuids: set[str] = set()
    trim_types: dict[str, int] = defaultdict(int)
    pivots: dict[str, int] = defaultdict(int)
    atlas_counts: dict[str, int] = defaultdict(int)
    scope_counts: dict[str, int] = defaultdict(int)

    for image_path in images:
        relative = rel(image_path, resources_root)
        if contained_path(resources_root, image_path) is None:
            metadata_invalid += 1
            add_blocker(blockers, "asset_path_escape", relative)
            continue
        parts = list(Path(relative).parts)
        invalid_segments = [segment for segment in parts[:-1] if not SAFE_ASSET_SEGMENT_RE.fullmatch(segment)]
        stem = image_path.stem
        if not SAFE_ASSET_SEGMENT_RE.fullmatch(stem) or image_path.suffix != image_path.suffix.lower() or invalid_segments:
            naming_invalid += 1
            add_blocker(
                blockers,
                "asset_naming_invalid",
                relative,
                invalidSegments=invalid_segments,
                requiredPattern=SAFE_ASSET_SEGMENT_RE.pattern,
            )
        folded = relative.casefold()
        if folded in casefolded and casefolded[folded] != relative:
            naming_collisions += 1
            add_blocker(blockers, "asset_casefold_collision", relative, other=casefolded[folded])
        else:
            casefolded[folded] = relative

        leaking_segments = sorted({segment.casefold() for segment in parts if segment.casefold() in QUARANTINE_SEGMENTS})
        if leaking_segments:
            quarantine_leaks += 1
            add_blocker(blockers, "runtime_quarantine_leak", relative, segments=leaking_segments)

        matching_scopes = [scope for scope in scopes if isinstance(scope, dict) and ownership_matches(relative, scope)]
        matching_groups = [
            group for group in groups
            if isinstance(group, dict)
            and any(selector_matches(relative, selector) for selector in group.get("source_selectors", []) if isinstance(selector, dict))
        ]
        if len(matching_scopes) != 1:
            ownership_invalid += 1
            add_blocker(
                blockers,
                "asset_ownership_coverage_invalid",
                relative,
                matches=[scope.get("scope_id") for scope in matching_scopes],
            )
        if len(matching_groups) != 1:
            atlas_invalid += 1
            add_blocker(
                blockers,
                "asset_atlas_coverage_invalid",
                relative,
                matches=[group.get("atlas_id") for group in matching_groups],
            )
        scope = matching_scopes[0] if len(matching_scopes) == 1 else None
        group = matching_groups[0] if len(matching_groups) == 1 else None
        if scope:
            scope_counts[str(scope.get("scope_id"))] += 1
        if group:
            atlas_counts[str(group.get("atlas_id"))] += 1

        provenance_paths: set[str] = set()
        for owner in (scope, group):
            if owner is None:
                continue
            if owner.get("bundle_id") != "resources":
                atlas_invalid += 1
                add_blocker(blockers, "asset_bundle_id_invalid", relative, owner=owner.get("scope_id") or owner.get("atlas_id"))
            provenance = owner.get("provenance")
            if not isinstance(provenance, list) or not provenance:
                provenance_invalid += 1
                add_blocker(blockers, "asset_provenance_missing", relative, owner=owner.get("scope_id") or owner.get("atlas_id"))
                continue
            for provenance_path in provenance:
                if not isinstance(provenance_path, str):
                    provenance_invalid += 1
                    add_blocker(blockers, "asset_provenance_invalid", relative, value=provenance_path)
                    continue
                provenance_paths.add(provenance_path)
        for provenance_path in sorted(provenance_paths):
            candidate = contained_path(project_root, project_root / provenance_path)
            if candidate is None or not candidate.is_file():
                provenance_invalid += 1
                add_blocker(blockers, "asset_provenance_unresolved", relative, provenance=provenance_path)

        try:
            with Image.open(image_path) as image:  # type: ignore[union-attr]
                actual_width, actual_height = image.size
                actual_alpha = has_alpha(image)
                alpha_bbox = image.convert("RGBA").getchannel("A").getbbox() if actual_alpha else None
        except Exception:
            # Decode errors are already emitted by the legacy PNG scan. JPEG
            # decode failures are made visible here.
            if image_path.suffix.lower() != ".png":
                metadata_invalid += 1
                add_blocker(blockers, "image_decode_error", relative)
            continue

        meta_path = Path(str(image_path) + ".meta")
        if contained_path(resources_root, meta_path) is None:
            metadata_invalid += 1
            add_blocker(blockers, "image_meta_path_escape", relative)
            continue
        meta, meta_error = safe_json(meta_path)
        if meta_error or not isinstance(meta, dict):
            if image_path.suffix.lower() != ".png" or meta_path.exists():
                metadata_invalid += 1
                add_blocker(blockers, "image_meta_invalid", relative, error=meta_error or "not_an_object")
            continue
        texture = texture_submeta(meta)
        sprite = sprite_submeta(meta)
        if texture is None or sprite is None:
            metadata_invalid += 1
            add_blocker(blockers, "image_meta_submetas_missing", relative)
            continue
        root_uuid = meta.get("uuid")
        texture_uuid = texture.get("uuid")
        sprite_uuid = sprite.get("uuid")
        for uuid in (root_uuid, texture_uuid, sprite_uuid):
            if not isinstance(uuid, str) or not UUID_RE.fullmatch(uuid):
                internal_reference_invalid += 1
                add_blocker(blockers, "image_meta_uuid_invalid", relative, uuid=uuid)
            else:
                image_uuids.add(uuid.lower())

        root_user = meta.get("userData") if isinstance(meta.get("userData"), dict) else {}
        texture_user = texture.get("userData") if isinstance(texture.get("userData"), dict) else {}
        sprite_user = sprite.get("userData") if isinstance(sprite.get("userData"), dict) else {}
        reference_expectations = [
            ("root.redirect", root_user.get("redirect"), texture_uuid),
            ("texture.imageUuidOrDatabaseUri", texture_user.get("imageUuidOrDatabaseUri"), root_uuid),
            ("sprite.imageUuidOrDatabaseUri", sprite_user.get("imageUuidOrDatabaseUri"), texture_uuid),
        ]
        for field, actual, expected in reference_expectations:
            if actual != expected:
                internal_reference_invalid += 1
                add_blocker(blockers, "image_meta_internal_reference_invalid", relative, field=field, expected=expected, actual=actual)

        for owner_name, display_name in (("texture", texture.get("displayName")), ("sprite", sprite.get("displayName"))):
            if display_name != stem:
                metadata_invalid += 1
                add_blocker(blockers, "image_meta_display_name_invalid", relative, owner=owner_name, expected=stem, actual=display_name)

        trim_type = sprite_user.get("trimType")
        trim_types[str(trim_type)] += 1
        numeric_fields = ("trimX", "trimY", "width", "height", "rawWidth", "rawHeight", "offsetX", "offsetY")
        if trim_type not in {"none", "auto"} or any(not finite_number(sprite_user.get(field)) for field in numeric_fields):
            trim_invalid += 1
            add_blocker(blockers, "image_trim_contract_invalid", relative, trimType=trim_type)
        else:
            trim_x = float(sprite_user["trimX"])
            trim_y = float(sprite_user["trimY"])
            width = float(sprite_user["width"])
            height = float(sprite_user["height"])
            raw_width = float(sprite_user["rawWidth"])
            raw_height = float(sprite_user["rawHeight"])
            valid_bounds = (
                raw_width == actual_width
                and raw_height == actual_height
                and width > 0
                and height > 0
                and trim_x >= 0
                and trim_y >= 0
                and trim_x + width <= raw_width
                and trim_y + height <= raw_height
            )
            if trim_type == "none":
                valid_bounds = valid_bounds and (
                    trim_x == 0
                    and trim_y == 0
                    and width == raw_width
                    and height == raw_height
                    and float(sprite_user["offsetX"]) == 0
                    and float(sprite_user["offsetY"]) == 0
                )
            if not valid_bounds:
                trim_invalid += 1
                add_blocker(
                    blockers,
                    "image_trim_bounds_invalid",
                    relative,
                    actual=[actual_width, actual_height],
                    trim=[trim_x, trim_y, width, height, raw_width, raw_height],
                )

        pivot_x = sprite_user.get("pivotX")
        pivot_y = sprite_user.get("pivotY")
        if not finite_number(pivot_x) or not finite_number(pivot_y) or not (0 <= float(pivot_x) <= 1 and 0 <= float(pivot_y) <= 1):
            pivot_invalid += 1
            add_blocker(blockers, "image_pivot_invalid", relative, pivot=[pivot_x, pivot_y])
        else:
            pivots[f"{float(pivot_x):g},{float(pivot_y):g}"] += 1

        packing = group.get("packing") if group and isinstance(group.get("packing"), dict) else {}
        standalone = packing.get("mode") == "standalone_texture"
        if not isinstance(sprite_user.get("packable"), bool):
            metadata_invalid += 1
            add_blocker(blockers, "image_packable_policy_invalid", relative, expected="boolean", actual=sprite_user.get("packable"))
        if sprite_user.get("atlasUuid") not in {"", None}:
            internal_reference_invalid += 1
            add_blocker(blockers, "unexpected_pre_m04_c_atlas_reference", relative, atlasUuid=sprite_user.get("atlasUuid"))

        declared_alpha = root_user.get("hasAlpha")
        expected_alpha = image_path.suffix.lower() == ".png" and not standalone
        if declared_alpha is not actual_alpha or actual_alpha is not expected_alpha:
            alpha_invalid += 1
            add_blocker(
                blockers,
                "image_alpha_contract_invalid",
                relative,
                actual=actual_alpha,
                declared=declared_alpha,
                expected=expected_alpha,
            )
        png_info = png_by_path.get(relative)
        if png_info and png_info.fullyTransparent:
            alpha_invalid += 1
            add_blocker(blockers, "image_null_frame", relative)
        elif actual_alpha and alpha_bbox is None:
            alpha_invalid += 1
            add_blocker(blockers, "image_null_frame", relative)

    quarantine_count = 0
    quarantine_escaped = 0
    quarantine_path_text = None
    if quarantine_root is not None:
        quarantine_path_text = project_rel(quarantine_root, project_root)
        resolved_quarantine = contained_path(project_root, quarantine_root)
        if resolved_quarantine is None:
            add_blocker(blockers, "quarantine_root_escape", quarantine_path_text)
            quarantine_escaped += 1
        elif resolved_quarantine.exists():
            for candidate in resolved_quarantine.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
                    if contained_path(resolved_quarantine, candidate) is None:
                        quarantine_escaped += 1
                        add_blocker(blockers, "quarantine_asset_escape", project_rel(candidate, project_root))
                    else:
                        quarantine_count += 1

    bundle = validate_bundle_meta(project_root, resources_root, blockers)
    hidden_references = validate_hidden_uuid_references(
        project_root,
        project_root / "assets",
        image_uuids,
        blockers,
    )
    report = {
        "checked": True,
        "status": "PASS" if not blockers else "FAIL",
        "policy": {
            "namingPattern": SAFE_ASSET_SEGMENT_RE.pattern,
            "imageExtensions": sorted(IMAGE_EXTENSIONS),
            "quarantineSegments": sorted(QUARANTINE_SEGMENTS),
            "runtimeBundle": "resources",
            "preM04CAtlasUuid": "empty",
            "mutatesFiles": False,
        },
        "summary": {
            "imageCount": len(images),
            "namingInvalidCount": naming_invalid,
            "casefoldCollisionCount": naming_collisions,
            "runtimeQuarantineLeakCount": quarantine_leaks,
            "ownershipInvalidCount": ownership_invalid,
            "atlasPlacementInvalidCount": atlas_invalid,
            "provenanceInvalidCount": provenance_invalid,
            "metadataInvalidCount": metadata_invalid,
            "trimInvalidCount": trim_invalid,
            "pivotInvalidCount": pivot_invalid,
            "alphaInvalidCount": alpha_invalid,
            "internalReferenceInvalidCount": internal_reference_invalid,
            "quarantinedAssetCount": quarantine_count,
            "quarantineEscapeCount": quarantine_escaped,
            "blockerCount": len(blockers),
        },
        "bundle": bundle,
        "trimTypes": dict(sorted(trim_types.items())),
        "pivots": dict(sorted(pivots.items())),
        "atlasCounts": dict(sorted(atlas_counts.items())),
        "ownershipCounts": dict(sorted(scope_counts.items())),
        "quarantine": {"path": quarantine_path_text, "assetCount": quarantine_count, "escapeCount": quarantine_escaped},
        "hiddenReferences": hidden_references,
        "blockerSample": blockers[:REFERENCE_MISSING_SAMPLE_LIMIT],
    }
    return report, blockers


def normalize_resource_key(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    for prefix in ("assets/resources/", "resources/", "./assets/resources/", "./resources/", "./"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    normalized = normalized.strip("/")
    if normalized.endswith(".png"):
        normalized = normalized[:-4]
    return normalized


def resource_key_exists(resources_root: Path, key: str) -> tuple[bool, str, str | None]:
    normalized = normalize_resource_key(key)
    if not normalized:
        return False, normalized, None
    if normalized in PROCEDURAL_RUNTIME_KEYS:
        return True, normalized, "procedural"

    png_path = resources_root / f"{normalized}.png"
    if contained_path(resources_root, png_path) is not None and png_path.exists():
        return True, normalized, rel(png_path, resources_root)
    raw_path = resources_root / normalized
    if contained_path(resources_root, raw_path) is not None and raw_path.exists() and raw_path.is_file():
        return True, normalized, rel(raw_path, resources_root)
    return False, normalized, None


def iter_strings(data: Any, path: str = "$") -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    if isinstance(data, str):
        refs.append({"key": data, "path": path})
    elif isinstance(data, list):
        for index, item in enumerate(data):
            refs.extend(iter_strings(item, f"{path}[{index}]"))
    elif isinstance(data, dict):
        for key, value in data.items():
            refs.extend(iter_strings(value, f"{path}.{key}"))
    return refs


def read_json_manifest(project_root: Path, manifest_path: Path) -> tuple[Any | None, dict[str, Any] | None]:
    if not manifest_path.exists():
        return None, {
            "type": "missing_reference_manifest",
            "path": project_rel(manifest_path, project_root),
        }
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, {
            "type": "invalid_reference_manifest_json",
            "path": project_rel(manifest_path, project_root),
            "error": str(exc),
        }


def make_reference_check(
    project_root: Path,
    resources_root: Path,
    source: str,
    manifest_path: Path,
    references: list[dict[str, str]],
    sample_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    missing: list[dict[str, str]] = []
    procedural: list[dict[str, str]] = []
    resolved: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []
    blockers: list[dict[str, Any]] = []

    seen_keys: set[str] = set()
    for ref in references:
        key = ref.get("key", "")
        ref_path = ref.get("path", "$")
        normalized = normalize_resource_key(key)
        if not normalized:
            invalid.append({"key": key, "path": ref_path, "reason": "empty_resource_key"})
            continue
        seen_keys.add(normalized)
        exists, normalized, resolved_path = resource_key_exists(resources_root, key)
        item = {"key": key, "normalized": normalized, "path": ref_path}
        if exists and resolved_path == "procedural":
            procedural.append(item)
        elif exists and resolved_path:
            resolved.append({**item, "resolved": resolved_path})
        else:
            missing.append(item)
            blockers.append({
                "type": "missing_asset_reference",
                "source": source,
                "manifest": project_rel(manifest_path, project_root),
                "key": key,
                "normalized": normalized,
                "path": ref_path,
            })

    for item in invalid:
        blockers.append({
            "type": "invalid_asset_reference",
            "source": source,
            "manifest": project_rel(manifest_path, project_root),
            **item,
        })

    return {
        "checked": True,
        "exists": True,
        "source": source,
        "path": project_rel(manifest_path, project_root),
        "referenceCount": len(references),
        "uniqueReferenceCount": len(seen_keys),
        "resolvedCount": len(resolved),
        "proceduralCount": len(procedural),
        "missingCount": len(missing),
        "invalidCount": len(invalid),
        "missingSample": missing[:sample_limit],
        "invalidSample": invalid[:sample_limit],
        "proceduralKeys": sorted({item["normalized"] for item in procedural}),
    }, blockers


def collect_player_skin_references(data: Any) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for skin_index, skin in enumerate(data.get("skins", []) if isinstance(data, dict) else []):
        skin_id = str(skin.get("skin_id", skin_index))
        pose_manifest = skin.get("pose_manifest", {})
        if not isinstance(pose_manifest, dict):
            continue
        for pose, variants in pose_manifest.items():
            if not isinstance(variants, dict):
                continue
            for variant, key in variants.items():
                if isinstance(key, str):
                    refs.append({
                        "key": key,
                        "path": f"$.skins[{skin_index}:{skin_id}].pose_manifest.{pose}.{variant}",
                    })
    return refs


def collect_ui_skin_references(data: Any) -> list[dict[str, str]]:
    # UI policy values are also strings, so only keep Cocos-style resource keys.
    return [
        ref for ref in iter_strings(data)
        if "/" in normalize_resource_key(ref["key"]) and ":" not in ref["key"]
    ]


def collect_objective_runtime_references(data: Any) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    required = data.get("requiredRuntimeKeys", {}) if isinstance(data, dict) else {}
    if not isinstance(required, dict):
        return refs
    for category, keys in required.items():
        if not isinstance(keys, list):
            continue
        for index, key in enumerate(keys):
            if isinstance(key, str):
                refs.append({"key": key, "path": f"$.requiredRuntimeKeys.{category}[{index}]"})
    return refs


def collect_last_iteration_references(data: Any) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    entries = data.get("entries", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        return refs
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("runtimeEnabled", True) is False:
            continue
        key = entry.get("runtimeResourceKey")
        if isinstance(key, str):
            refs.append({"key": key, "path": f"$.entries[{index}].runtimeResourceKey"})
    return refs


def validate_manifest_references(project_root: Path, resources_root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if args.skip_reference_checks:
        return {"checked": False, "reason": "skip_reference_checks"}, []

    specs = [
        ("playerSkinsManifest", args.player_skins_manifest, collect_player_skin_references),
        ("uiSkinManifest", args.ui_skin_manifest, collect_ui_skin_references),
        ("objectiveRuntimeUsage", args.objective_runtime_usage, collect_objective_runtime_references),
        ("lastIterationAssetManifest", args.last_iteration_asset_manifest, collect_last_iteration_references),
    ]
    checks: dict[str, Any] = {"checked": True}
    blockers: list[dict[str, Any]] = []

    for source, rel_manifest_path, collector in specs:
        manifest_path = contained_path(project_root, project_root / rel_manifest_path)
        if manifest_path is None:
            error = {
                "type": "reference_manifest_path_escape",
                "path": str(rel_manifest_path),
            }
            checks[source] = {
                "checked": True,
                "exists": False,
                "source": source,
                "path": str(rel_manifest_path),
                "error": error,
            }
            blockers.append(error)
            continue
        data, manifest_error = read_json_manifest(project_root, manifest_path)
        if manifest_error:
            checks[source] = {
                "checked": True,
                "exists": False,
                "source": source,
                "path": project_rel(manifest_path, project_root),
                "error": manifest_error,
            }
            blockers.append(manifest_error)
            continue
        references = collector(data)
        check, check_blockers = make_reference_check(
            project_root,
            resources_root,
            source,
            manifest_path,
            references,
            args.reference_missing_sample_limit,
        )
        checks[source] = check
        blockers.extend(check_blockers)

    checks["proceduralRuntimeKeys"] = sorted(PROCEDURAL_RUNTIME_KEYS)
    checks["blockerCount"] = len(blockers)
    return checks, blockers


def validate_atlas_manifest(
    project_root: Path,
    resources_root: Path,
    manifest_path: Path | None,
    manifest_data: Any | None = None,
) -> dict[str, Any]:
    if manifest_path is None:
        return {"checked": False, "reason": "not_provided", "missingSourceCandidates": []}
    if not manifest_path.exists():
        return {"checked": True, "exists": False, "missingSourceCandidates": [str(manifest_path)]}

    data = manifest_data
    if data is None:
        data, error = safe_json(manifest_path)
        if error or not isinstance(data, dict):
            return {
                "checked": True,
                "exists": True,
                "path": project_rel(manifest_path, project_root),
                "invalidJson": error or "not_an_object",
                "missingSourceCandidates": [],
            }
    missing: list[str] = []
    escaped: list[str] = []
    atlas_groups = data.get("atlas_groups")
    if isinstance(atlas_groups, list):
        for atlas in atlas_groups:
            if not isinstance(atlas, dict):
                continue
            for selector in atlas.get("source_selectors", []):
                if not isinstance(selector, dict):
                    continue
                candidate = selector.get("path")
                if not isinstance(candidate, str):
                    continue
                candidate_path = resources_root / candidate
                if contained_path(resources_root, candidate_path) is None:
                    escaped.append(candidate)
                elif not candidate_path.exists():
                    missing.append(candidate)
        atlas_count = len(atlas_groups)
        contract = data.get("contract")
    else:
        # Historical draft compatibility remains read-only so old audit reports
        # can still be reproduced explicitly with --atlas-manifest.
        atlases = data.get("atlases", [])
        for atlas in atlases:
            if not isinstance(atlas, dict):
                continue
            for candidate in atlas.get("sourceCandidates", []):
                if not isinstance(candidate, str):
                    escaped.append(str(candidate))
                    continue
                candidate_path = resources_root / candidate
                if contained_path(resources_root, candidate_path) is None:
                    escaped.append(str(candidate))
                elif not candidate_path.exists():
                    missing.append(candidate)
        atlas_count = len(atlases)
        contract = data.get("$schema")
    return {
        "checked": True,
        "exists": True,
        "path": str(manifest_path.relative_to(project_root)),
        "contract": contract,
        "atlasCount": atlas_count,
        "missingSourceCandidates": missing,
        "escapedSourceCandidates": escaped,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    resources_root = (project_root / args.resources_root).resolve()
    manifest_path = (project_root / args.atlas_manifest).resolve() if args.atlas_manifest else None
    quarantine_root = (project_root / args.quarantine_root).resolve() if args.quarantine_root else None

    if contained_path(project_root, resources_root) is None:
        raise ValueError(f"resources root escapes project root: {resources_root}")
    if manifest_path is not None and contained_path(project_root, manifest_path) is None:
        raise ValueError(f"atlas manifest escapes project root: {manifest_path}")

    infos, groups = scan_pngs(resources_root, args.max_edge)

    decode_errors = [asdict(info) for info in infos if info.decodeError]
    missing_meta = [asdict(info) for info in infos if not info.hasMeta]
    oversize = [asdict(info) for info in infos if info.oversize]
    white_matte_suspects = [asdict(info) for info in infos if info.whiteMatteSuspect]
    no_alpha = [asdict(info) for info in infos if info.hasAlpha is False]
    null_frames = [asdict(info) for info in infos if info.fullyTransparent]

    atlas_data: Any | None = None
    atlas_error: str | None = None
    if manifest_path is not None and manifest_path.exists():
        atlas_data, atlas_error = safe_json(manifest_path)
    atlas_manifest = validate_atlas_manifest(project_root, resources_root, manifest_path, atlas_data)
    reference_checks, reference_blockers = validate_manifest_references(project_root, resources_root, args)
    pre_import, pre_import_blockers = validate_image_governance(
        project_root,
        resources_root,
        atlas_data,
        infos,
        quarantine_root,
    )
    blockers: list[dict[str, Any]] = []

    for item in decode_errors:
        blockers.append({"type": "png_decode_error", "path": item["path"], "error": item["decodeError"]})
    for item in missing_meta:
        blockers.append({"type": "missing_meta", "path": item["path"]})
    for item in oversize:
        blockers.append({"type": "oversize", "path": item["path"], "width": item["width"], "height": item["height"]})
    for candidate in atlas_manifest.get("missingSourceCandidates", []):
        blockers.append({"type": "missing_atlas_source_candidate", "path": candidate})
    for candidate in atlas_manifest.get("escapedSourceCandidates", []):
        blockers.append({"type": "atlas_source_candidate_path_escape", "path": candidate})
    if atlas_error:
        blockers.append({
            "type": "invalid_atlas_manifest_json",
            "path": project_rel(manifest_path, project_root) if manifest_path else "",
            "error": atlas_error,
        })
    blockers.extend(reference_blockers)
    blockers.extend(pre_import_blockers)
    if args.fail_on_white_matte:
        for item in white_matte_suspects:
            blockers.append({
                "type": "white_matte_suspect",
                "path": item["path"],
                "edgeConnectedOpaqueWhitePixels": item["edgeConnectedOpaqueWhitePixels"],
            })

    return {
        "schema": "mtr.asset_validation.v1",
        "projectRoot": str(project_root),
        "resourcesRoot": str(resources_root),
        "policy": {
            "maxEdge": args.max_edge,
            "whiteMatteWarnThreshold": WHITE_MATTE_WARN_THRESHOLD,
            "failOnWhiteMatte": bool(args.fail_on_white_matte),
            "skipReferenceChecks": bool(args.skip_reference_checks),
            "proceduralRuntimeKeys": sorted(PROCEDURAL_RUNTIME_KEYS),
            "mutatesFiles": False,
        },
        "summary": {
            "pngCount": len(infos),
            "totalBytes": sum(info.bytes for info in infos),
            "alphaCount": sum(1 for info in infos if info.hasAlpha),
            "noAlphaCount": len(no_alpha),
            "decodeErrorCount": len(decode_errors),
            "missingMetaCount": len(missing_meta),
            "oversizeCount": len(oversize),
            "whiteMatteSuspectCount": len(white_matte_suspects),
            "nullFrameCount": len(null_frames),
            "preImportBlockerCount": len(pre_import_blockers),
            "blockerCount": len(blockers),
        },
        "groups": groups,
        "atlasManifest": atlas_manifest,
        "referenceChecks": reference_checks,
        "preImport": pre_import,
        "blockers": blockers,
        "warnings": {
            "noAlpha": no_alpha,
            "whiteMatteSuspects": white_matte_suspects,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--resources-root", default="assets/resources", help="Resources path relative to project root.")
    parser.add_argument(
        "--atlas-manifest",
        default="assets/resources/config/atlas_manifest.json",
        help="Canonical atlas manifest path relative to project root.",
    )
    parser.add_argument(
        "--player-skins-manifest",
        default="docs/skins_integration/manifests/player_skins_manifest.json",
        help="Player skin manifest path relative to project root.",
    )
    parser.add_argument(
        "--ui-skin-manifest",
        default="assets/resources/config/ui_skin_manifest.json",
        help="UI skin manifest path relative to project root.",
    )
    parser.add_argument(
        "--objective-runtime-usage",
        default="assets/resources/config/current_objective_runtime_usage.json",
        help="Objective runtime usage manifest path relative to project root.",
    )
    parser.add_argument(
        "--last-iteration-asset-manifest",
        default="assets/resources/config/last_iteration_asset_manifest.generated.json",
        help="Generated last-iteration asset manifest path relative to project root.",
    )
    parser.add_argument(
        "--quarantine-root",
        default="assets/quarantine",
        help="Non-runtime quarantine path relative to project root; assets here are inventoried but never accepted into resources.",
    )
    parser.add_argument("--max-edge", type=int, default=2048, help="Maximum allowed PNG width/height.")
    parser.add_argument("--report", default="", help="Optional JSON report output path.")
    parser.add_argument("--fail-on-white-matte", action="store_true", help="Treat white matte suspects as blockers.")
    parser.add_argument("--skip-reference-checks", action="store_true", help="Skip manifest resource reference checks.")
    parser.add_argument(
        "--reference-missing-sample-limit",
        type=int,
        default=REFERENCE_MISSING_SAMPLE_LIMIT,
        help="Maximum missing/invalid reference samples retained in the JSON report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    if args.report:
        project_root = Path(args.project_root).resolve()
        requested = Path(args.report)
        out = requested.resolve() if requested.is_absolute() else (project_root / requested).resolve()
        if contained_path(project_root, out) is None:
            print(json.dumps({"ok": False, "error": f"report path escapes project root: {out}"}, ensure_ascii=False))
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        temporary = out.with_name(f".{out.name}.tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(out)

    print(json.dumps({
        "ok": report["summary"]["blockerCount"] == 0,
        "summary": report["summary"],
        "report": args.report or None,
    }, ensure_ascii=False))
    return 0 if report["summary"]["blockerCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
