#!/usr/bin/env python3
"""Validate Martyshkin Trud player-skin pose/bonus runtime matrix.

This script is intentionally non-mutating. It checks the manifest-declared
skin x pose x variant matrix, PNG readability, Cocos `.meta` pairing,
transparent-frame hygiene, alpha bounding boxes, baseline stability, and
simple white-chunk heuristics. It writes JSON evidence for Module 3 before any
skin regeneration or runtime patch is attempted.
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


EXPECTED_FRAME_SIZE = 256
OPAQUE_ALPHA_MIN = 250
VISIBLE_ALPHA_MIN = 20
WHITE_RGB_MIN = 245
LOW_SATURATION_MAX_DELTA = 8
WHITE_CHUNK_RATIO_WARN = 0.12
EDGE_WHITE_WARN_THRESHOLD = 100
BASELINE_DRIFT_WARN_PX = 4.0
CENTER_DRIFT_WARN_PX = 12.0


@dataclass
class FrameMetrics:
    skinId: str
    pose: str
    variant: str
    key: str
    path: str
    exists: bool
    hasMeta: bool = False
    width: int | None = None
    height: int | None = None
    mode: str | None = None
    hasAlpha: bool | None = None
    decodeError: str | None = None
    alphaBBox: list[int] | None = None
    bboxWidth: int | None = None
    bboxHeight: int | None = None
    bboxCenterX: float | None = None
    bboxBottom: int | None = None
    alphaCoverageRatio: float | None = None
    borderVisiblePixelCount: int = 0
    nearWhiteOpaqueRatio: float | None = None
    lowSaturationBrightRatio: float | None = None
    edgeConnectedOpaqueWhitePixels: int = 0
    riskFlags: list[str] | None = None


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def has_alpha(image: Image.Image) -> bool:  # type: ignore[name-defined]
    return image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)


def is_opaque_white(pixel: tuple[int, ...]) -> bool:
    if len(pixel) >= 4 and pixel[3] < OPAQUE_ALPHA_MIN:
        return False
    return pixel[0] >= WHITE_RGB_MIN and pixel[1] >= WHITE_RGB_MIN and pixel[2] >= WHITE_RGB_MIN


def is_low_saturation_bright(pixel: tuple[int, ...]) -> bool:
    if len(pixel) >= 4 and pixel[3] < OPAQUE_ALPHA_MIN:
        return False
    channels = pixel[:3]
    return max(channels) >= WHITE_RGB_MIN and (max(channels) - min(channels)) <= LOW_SATURATION_MAX_DELTA


def border_visible_count(rgba: Image.Image) -> int:  # type: ignore[name-defined]
    width, height = rgba.size
    pixels = rgba.load()
    count = 0
    for x in range(width):
        if pixels[x, 0][3] >= VISIBLE_ALPHA_MIN:
            count += 1
        if pixels[x, height - 1][3] >= VISIBLE_ALPHA_MIN:
            count += 1
    for y in range(1, height - 1):
        if pixels[0, y][3] >= VISIBLE_ALPHA_MIN:
            count += 1
        if pixels[width - 1, y][3] >= VISIBLE_ALPHA_MIN:
            count += 1
    return count


def edge_connected_opaque_white_count(rgba: Image.Image, max_pixels: int = 100_000) -> int:  # type: ignore[name-defined]
    width, height = rgba.size
    pixels = rgba.load()
    seen: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        if (x, y) in seen:
            return
        if is_opaque_white(pixels[x, y]):
            seen.add((x, y))
            queue.append((x, y))

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)

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


def count_opaque_white_metrics(rgba: Image.Image) -> tuple[int, int, int]:
    opaque = 0
    near_white = 0
    low_sat = 0
    raw = rgba.tobytes()
    for index in range(0, len(raw), 4):
        r, g, b, a = raw[index], raw[index + 1], raw[index + 2], raw[index + 3]
        if a < OPAQUE_ALPHA_MIN:
            continue
        opaque += 1
        if r >= WHITE_RGB_MIN and g >= WHITE_RGB_MIN and b >= WHITE_RGB_MIN:
            near_white += 1
        if max(r, g, b) >= WHITE_RGB_MIN and (max(r, g, b) - min(r, g, b)) <= LOW_SATURATION_MAX_DELTA:
            low_sat += 1
    return opaque, near_white, low_sat


def frame_path(resources_root: Path, key: str) -> Path:
    normalized = key.strip().replace("\\", "/").strip("/")
    if normalized.startswith("assets/resources/"):
        normalized = normalized[len("assets/resources/"):]
    if normalized.endswith(".png"):
        normalized = normalized[:-4]
    return resources_root / f"{normalized}.png"


def inspect_frame(resources_root: Path, skin_id: str, pose: str, variant: str, key: str, expected_size: int) -> FrameMetrics:
    path = frame_path(resources_root, key)
    metrics = FrameMetrics(
        skinId=skin_id,
        pose=pose,
        variant=variant,
        key=key,
        path=rel(path, resources_root),
        exists=path.exists(),
        hasMeta=Path(str(path) + ".meta").exists(),
        riskFlags=[],
    )
    if not metrics.exists:
        metrics.riskFlags.append("missing_png")
        return metrics
    try:
        with Image.open(path) as image:
            metrics.width, metrics.height = image.size
            metrics.mode = image.mode
            metrics.hasAlpha = has_alpha(image)
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                left, top, right, bottom = bbox
                metrics.alphaBBox = [left, top, right, bottom]
                metrics.bboxWidth = right - left
                metrics.bboxHeight = bottom - top
                metrics.bboxCenterX = (left + right) / 2
                metrics.bboxBottom = bottom
                metrics.alphaCoverageRatio = (metrics.bboxWidth * metrics.bboxHeight) / max(1, image.size[0] * image.size[1])
            metrics.borderVisiblePixelCount = border_visible_count(rgba)
            opaque, near_white, low_sat = count_opaque_white_metrics(rgba)
            metrics.nearWhiteOpaqueRatio = near_white / opaque if opaque else 0.0
            metrics.lowSaturationBrightRatio = low_sat / opaque if opaque else 0.0
            metrics.edgeConnectedOpaqueWhitePixels = edge_connected_opaque_white_count(rgba)
    except Exception as exc:
        metrics.decodeError = str(exc)
        metrics.riskFlags.append("decode_error")
        return metrics

    if metrics.width != expected_size or metrics.height != expected_size:
        metrics.riskFlags.append("unexpected_frame_size")
    if not metrics.hasMeta:
        metrics.riskFlags.append("missing_meta")
    if metrics.hasAlpha is False:
        metrics.riskFlags.append("missing_alpha")
    if metrics.alphaBBox is None:
        metrics.riskFlags.append("empty_alpha_bbox")
    if metrics.borderVisiblePixelCount:
        metrics.riskFlags.append("visible_pixels_touch_canvas_edge")
    if metrics.nearWhiteOpaqueRatio is not None and metrics.nearWhiteOpaqueRatio > WHITE_CHUNK_RATIO_WARN:
        metrics.riskFlags.append("white_chunk_ratio_suspect")
    if metrics.edgeConnectedOpaqueWhitePixels > EDGE_WHITE_WARN_THRESHOLD:
        metrics.riskFlags.append("edge_connected_white_suspect")
    return metrics


def make_matrix_expected(data: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    skin_ids = list(data.get("canonical_skin_ids") or [skin.get("skin_id") for skin in data.get("skins", [])])
    poses = list(data.get("poses") or [])
    variants = list(data.get("variants") or [])
    return [str(item) for item in skin_ids], [str(item) for item in poses], [str(item) for item in variants]


def validate_matrix(data: dict[str, Any], resources_root: Path, expected_size: int) -> tuple[list[FrameMetrics], list[dict[str, Any]], list[dict[str, Any]]]:
    expected_skin_ids, expected_poses, expected_variants = make_matrix_expected(data)
    skins = data.get("skins", [])
    frames: list[FrameMetrics] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    by_skin = {skin.get("skin_id"): skin for skin in skins if isinstance(skin, dict)}
    for skin_id in expected_skin_ids:
        skin = by_skin.get(skin_id)
        if not skin:
            blockers.append({"type": "missing_skin_manifest_entry", "skinId": skin_id})
            continue
        pose_manifest = skin.get("pose_manifest", {})
        for pose in expected_poses:
            pose_entry = pose_manifest.get(pose)
            if not isinstance(pose_entry, dict):
                blockers.append({"type": "missing_pose_manifest_entry", "skinId": skin_id, "pose": pose})
                continue
            for variant in expected_variants:
                key = pose_entry.get(variant)
                if not isinstance(key, str):
                    blockers.append({"type": "missing_variant_manifest_entry", "skinId": skin_id, "pose": pose, "variant": variant})
                    continue
                metrics = inspect_frame(resources_root, skin_id, pose, variant, key, expected_size)
                frames.append(metrics)

                hard_flags = {
                    "missing_png",
                    "decode_error",
                    "unexpected_frame_size",
                    "missing_meta",
                    "missing_alpha",
                    "empty_alpha_bbox",
                }
                for flag in metrics.riskFlags or []:
                    item = {"type": flag, "skinId": skin_id, "pose": pose, "variant": variant, "path": metrics.path}
                    if flag in hard_flags:
                        blockers.append(item)
                    else:
                        warnings.append(item)

    check_baseline_and_variant_drift(frames, warnings)
    return frames, blockers, warnings


def check_baseline_and_variant_drift(frames: list[FrameMetrics], warnings: list[dict[str, Any]]) -> None:
    by_skin_pose: dict[tuple[str, str], dict[str, FrameMetrics]] = defaultdict(dict)
    by_pose: dict[str, list[FrameMetrics]] = defaultdict(list)
    for frame in frames:
        if frame.alphaBBox is None:
            continue
        by_skin_pose[(frame.skinId, frame.pose)][frame.variant] = frame
        by_pose[frame.pose].append(frame)

    for (skin_id, pose), variants in by_skin_pose.items():
        base = variants.get("base")
        if not base or base.bboxCenterX is None or base.bboxBottom is None:
            continue
        for variant, frame in variants.items():
            if variant == "base" or frame.bboxCenterX is None or frame.bboxBottom is None:
                continue
            center_drift = abs(frame.bboxCenterX - base.bboxCenterX)
            bottom_drift = abs(frame.bboxBottom - base.bboxBottom)
            if center_drift > CENTER_DRIFT_WARN_PX:
                warnings.append({
                    "type": "variant_center_drift",
                    "skinId": skin_id,
                    "pose": pose,
                    "variant": variant,
                    "driftPx": round(center_drift, 2),
                    "thresholdPx": CENTER_DRIFT_WARN_PX,
                })
            if bottom_drift > BASELINE_DRIFT_WARN_PX:
                warnings.append({
                    "type": "variant_baseline_drift",
                    "skinId": skin_id,
                    "pose": pose,
                    "variant": variant,
                    "driftPx": round(bottom_drift, 2),
                    "thresholdPx": BASELINE_DRIFT_WARN_PX,
                })

    for pose, pose_frames in by_pose.items():
        bottoms = [frame.bboxBottom for frame in pose_frames if frame.bboxBottom is not None]
        if not bottoms:
            continue
        spread = max(bottoms) - min(bottoms)
        if spread > BASELINE_DRIFT_WARN_PX:
            warnings.append({
                "type": "pose_baseline_spread",
                "pose": pose,
                "spreadPx": spread,
                "thresholdPx": BASELINE_DRIFT_WARN_PX,
            })


def summarize(frames: list[FrameMetrics], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    expected_skin_ids, expected_poses, expected_variants = make_matrix_expected(data)
    size_set = sorted({f"{frame.width}x{frame.height}" for frame in frames if frame.width and frame.height})
    bottom_values = [frame.bboxBottom for frame in frames if frame.bboxBottom is not None]
    near_white_values = [frame.nearWhiteOpaqueRatio for frame in frames if frame.nearWhiteOpaqueRatio is not None]
    return {
        "schema": "mtr.skin_bonus_matrix_validation.v1",
        "summary": {
            "skinCount": len(expected_skin_ids),
            "poseCount": len(expected_poses),
            "variantCount": len(expected_variants),
            "expectedFrameCount": len(expected_skin_ids) * len(expected_poses) * len(expected_variants),
            "checkedFrameCount": len(frames),
            "blockerCount": len(blockers),
            "warningCount": len(warnings),
            "frameSizes": size_set,
            "bboxBottomRange": [min(bottom_values), max(bottom_values)] if bottom_values else None,
            "maxNearWhiteOpaqueRatio": round(max(near_white_values), 6) if near_white_values else None,
        },
        "skinIds": expected_skin_ids,
        "poses": expected_poses,
        "variants": expected_variants,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if Image is None:
        raise RuntimeError(f"Pillow/PIL is not available: {PIL_IMPORT_ERROR}")

    project_root = Path(args.project_root).resolve()
    resources_root = (project_root / args.resources_root).resolve()
    manifest_path = (project_root / args.manifest).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames, blockers, warnings = validate_matrix(data, resources_root, args.expected_frame_size)
    report = summarize(frames, blockers, warnings, data)
    report.update({
        "projectRoot": str(project_root),
        "resourcesRoot": str(resources_root),
        "manifest": rel(manifest_path, project_root),
        "policy": {
            "mutatesFiles": False,
            "expectedFrameSize": args.expected_frame_size,
            "baselineDriftWarnPx": BASELINE_DRIFT_WARN_PX,
            "centerDriftWarnPx": CENTER_DRIFT_WARN_PX,
            "whiteChunkRatioWarn": WHITE_CHUNK_RATIO_WARN,
            "edgeWhiteWarnThreshold": EDGE_WHITE_WARN_THRESHOLD,
            "failOnWarnings": bool(args.fail_on_warnings),
        },
        "blockers": blockers,
        "warnings": warnings,
        "frames": [asdict(frame) for frame in frames],
    })
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--resources-root", default="assets/resources", help="Resources path relative to project root.")
    parser.add_argument(
        "--manifest",
        default="docs/skins_integration/manifests/player_skins_manifest.json",
        help="Player skin manifest path relative to project root.",
    )
    parser.add_argument("--expected-frame-size", type=int, default=EXPECTED_FRAME_SIZE)
    parser.add_argument("--report", default="", help="Optional JSON report output path.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Treat visual heuristic warnings as a non-zero exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = report["summary"]["blockerCount"] == 0 and (not args.fail_on_warnings or report["summary"]["warningCount"] == 0)
    print(json.dumps({
        "ok": ok,
        "summary": report["summary"],
        "report": args.report or None,
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
