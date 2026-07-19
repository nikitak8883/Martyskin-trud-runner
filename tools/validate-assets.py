#!/usr/bin/env python3
"""Validate Martyshkin Trud runtime art assets without modifying files.

This script is intentionally non-mutating. It checks PNG readability, matching
`.meta` files, size limits, basic white-matte edge suspects, draft atlas
manifest source paths, and resource references declared by runtime manifests.
It emits JSON for Codex/QA reports and returns non-zero only for structural
blockers by default.
"""

from __future__ import annotations

import argparse
import json
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


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


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
        info = PngInfo(
            path=rel(path, resources_root),
            bytes=path.stat().st_size,
            hasMeta=Path(str(path) + ".meta").exists(),
        )
        try:
            with Image.open(path) as image:
                info.width, info.height = image.size
                info.mode = image.mode
                info.hasAlpha = has_alpha(image)
                info.oversize = image.size[0] > max_edge or image.size[1] > max_edge
                info.edgeConnectedOpaqueWhitePixels = edge_connected_opaque_white_count(image)
                info.whiteMatteSuspect = info.edgeConnectedOpaqueWhitePixels > WHITE_MATTE_WARN_THRESHOLD
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
    if png_path.exists():
        return True, normalized, rel(png_path, resources_root)
    raw_path = resources_root / normalized
    if raw_path.exists() and raw_path.is_file():
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
        manifest_path = (project_root / rel_manifest_path).resolve()
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


def validate_atlas_manifest(project_root: Path, resources_root: Path, manifest_path: Path | None) -> dict[str, Any]:
    if manifest_path is None:
        return {"checked": False, "reason": "not_provided", "missingSourceCandidates": []}
    if not manifest_path.exists():
        return {"checked": True, "exists": False, "missingSourceCandidates": [str(manifest_path)]}

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    atlases = data.get("atlases", [])
    for atlas in atlases:
        for candidate in atlas.get("sourceCandidates", []):
            candidate_path = resources_root / candidate
            if not candidate_path.exists():
                missing.append(candidate)
    return {
        "checked": True,
        "exists": True,
        "path": str(manifest_path.relative_to(project_root)),
        "atlasCount": len(atlases),
        "missingSourceCandidates": missing,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    resources_root = (project_root / args.resources_root).resolve()
    manifest_path = (project_root / args.atlas_manifest).resolve() if args.atlas_manifest else None

    infos, groups = scan_pngs(resources_root, args.max_edge)

    decode_errors = [asdict(info) for info in infos if info.decodeError]
    missing_meta = [asdict(info) for info in infos if not info.hasMeta]
    oversize = [asdict(info) for info in infos if info.oversize]
    white_matte_suspects = [asdict(info) for info in infos if info.whiteMatteSuspect]
    no_alpha = [asdict(info) for info in infos if info.hasAlpha is False]

    atlas_manifest = validate_atlas_manifest(project_root, resources_root, manifest_path)
    reference_checks, reference_blockers = validate_manifest_references(project_root, resources_root, args)
    blockers: list[dict[str, Any]] = []

    for item in decode_errors:
        blockers.append({"type": "png_decode_error", "path": item["path"], "error": item["decodeError"]})
    for item in missing_meta:
        blockers.append({"type": "missing_meta", "path": item["path"]})
    for item in oversize:
        blockers.append({"type": "oversize", "path": item["path"], "width": item["width"], "height": item["height"]})
    for candidate in atlas_manifest.get("missingSourceCandidates", []):
        blockers.append({"type": "missing_atlas_source_candidate", "path": candidate})
    blockers.extend(reference_blockers)
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
            "blockerCount": len(blockers),
        },
        "groups": groups,
        "atlasManifest": atlas_manifest,
        "referenceChecks": reference_checks,
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
        default="docs/global_modernization/manifests/atlas_manifest.draft.json",
        help="Draft atlas manifest path relative to project root.",
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
    report = build_report(args)

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ok": report["summary"]["blockerCount"] == 0,
        "summary": report["summary"],
        "report": args.report or None,
    }, ensure_ascii=False))
    return 0 if report["summary"]["blockerCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
