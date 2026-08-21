#!/usr/bin/env python3
"""Compare deterministic M04-C atlas-pilot screenshots inside frozen content ROIs."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat


def resolve_contained(project_root: Path, value: str, label: str) -> Path:
    candidate = (project_root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes project root: {candidate}") from exc
    return candidate


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def normalized_roi(size: tuple[int, int], roi: dict[str, Any]) -> tuple[int, int, int, int]:
    width, height = size
    box = (
        round(width * float(roi["left"])),
        round(height * float(roi["top"])),
        round(width * float(roi["right"])),
        round(height * float(roi["bottom"])),
    )
    left, top, right, bottom = box
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(f"Invalid normalized ROI {roi} for image size {size}.")
    return box


def compare_images(
    baseline_path: Path,
    candidate_path: Path,
    roi: dict[str, Any],
    channel_delta_threshold: int,
    maximum_mean_absolute_error: float,
    maximum_changed_pixel_fraction: float,
) -> dict[str, Any]:
    with Image.open(baseline_path) as baseline_source, Image.open(candidate_path) as candidate_source:
        baseline = baseline_source.convert("RGB")
        candidate = candidate_source.convert("RGB")
    if baseline.size != candidate.size:
        return {
            "status": "fail",
            "reason": "dimension_mismatch",
            "baselineDimensions": list(baseline.size),
            "candidateDimensions": list(candidate.size),
        }

    box = normalized_roi(baseline.size, roi)
    baseline_crop = baseline.crop(box)
    candidate_crop = candidate.crop(box)
    difference = ImageChops.difference(baseline_crop, candidate_crop)
    channel_means = ImageStat.Stat(difference).mean
    mean_absolute_error = sum(channel_means) / len(channel_means)
    changed = 0
    pixels = difference.get_flattened_data() if hasattr(difference, "get_flattened_data") else difference.getdata()
    for red, green, blue in pixels:
        if max(red, green, blue) > channel_delta_threshold:
            changed += 1
    pixel_count = difference.width * difference.height
    changed_fraction = changed / pixel_count if pixel_count else 1.0
    passed = (
        mean_absolute_error <= maximum_mean_absolute_error
        and changed_fraction <= maximum_changed_pixel_fraction
    )
    return {
        "status": "pass" if passed else "fail",
        "baselineDimensions": list(baseline.size),
        "candidateDimensions": list(candidate.size),
        "contentRoiPixels": list(box),
        "contentPixelCount": pixel_count,
        "meanAbsoluteError": round(mean_absolute_error, 6),
        "changedPixelCount": changed,
        "changedPixelFraction": round(changed_fraction, 9),
        "thresholds": {
            "channelDelta": channel_delta_threshold,
            "maximumMeanAbsoluteError": maximum_mean_absolute_error,
            "maximumChangedPixelFraction": maximum_changed_pixel_fraction,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--contract", default="docs/global_modernization/v3/M04/M04_C_PILOT_CONTRACT.json")
    parser.add_argument("--baseline-root", default="temp/m04-c-pilot/baseline")
    parser.add_argument("--candidate-root", default="temp/m04-c-pilot/candidate")
    parser.add_argument("--output", default="temp/m04-c-pilot/comparison/visual-parity.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    contract = load_json(resolve_contained(project_root, args.contract, "--contract"))
    baseline_root = resolve_contained(project_root, args.baseline_root, "--baseline-root")
    candidate_root = resolve_contained(project_root, args.candidate_root, "--candidate-root")
    output = resolve_contained(project_root, args.output, "--output")
    visual = contract["acceptance"]["visual"]["automated_parity"]
    screenshot_filename = str(
        contract.get("measurement_protocol", {}).get("screenshot_filename", "atlas-pilot.png")
    )
    if (
        not screenshot_filename
        or screenshot_filename != Path(screenshot_filename).name
        or "/" in screenshot_filename
        or "\\" in screenshot_filename
        or not screenshot_filename.lower().endswith(".png")
    ):
        raise ValueError(f"Unsafe screenshot filename in contract: {screenshot_filename!r}")
    comparisons: dict[str, Any] = {}
    for platform, directory in (("web", "web"), ("android_emulator", "android")):
        comparisons[platform] = compare_images(
            baseline_root / directory / screenshot_filename,
            candidate_root / directory / screenshot_filename,
            visual["content_roi_by_platform"][platform],
            int(visual["channel_delta_threshold"]),
            float(visual["maximum_mean_absolute_error"]),
            float(visual["maximum_changed_pixel_fraction"]),
        )
    report = {
        "schema": "mtr.atlas_pilot_visual_parity.v1",
        "status": "pass" if all(item["status"] == "pass" for item in comparisons.values()) else "fail",
        "contractStatus": contract["status"],
        "screenshotFilename": screenshot_filename,
        "comparisons": comparisons,
    }
    atomic_write_json(output, report)
    print(json.dumps({"status": report["status"], "output": output.relative_to(project_root).as_posix()}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
