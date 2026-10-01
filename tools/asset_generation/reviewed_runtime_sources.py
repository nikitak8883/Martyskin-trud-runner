"""Pinned source replacements: validate all inputs before applying any target."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


CONFIG = Path("tools/asset_generation/reviewed_runtime_sources.json")
MANIFEST = Path("assets/resources/config/last_iteration_asset_manifest.generated.json")
SOURCE_ROOT = Path("tools/asset_generation/source_assets")
RUNTIME_PREFIX = "objectives/themed/last_iteration/"


def contained(root: Path, relative: str, allowed: Path) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to((root / allowed).resolve()):
        raise ValueError(f"Path escapes allowed scope: {relative}")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate_image(path: Path, record: dict[str, Any]) -> None:
    with Image.open(path) as image:
        if image.mode != "RGBA" or list(image.size) != record["dimensions"]:
            raise ValueError(f"RGBA/dimension mismatch: {path}")
        alpha = image.getchannel("A")
        if list(alpha.getbbox() or ()) != record["alpha_bbox"]:
            raise ValueError(f"Alpha bbox mismatch: {path}")
        for box in record["transparent_boxes"]:
            x0, y0, x1, y1 = box
            if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
                raise ValueError("Transparent region outside image")
            if alpha.crop(tuple(box)).getextrema()[1] != 0:
                raise ValueError(f"Opaque pixels in reviewed transparent region: {path}")


def apply_sources(
    project_root: Path,
    entries: list[dict[str, Any]],
    *,
    apply: bool = False,
    validate_runtime: bool = True,
    config: Path = CONFIG,
) -> dict[str, Any]:
    root = project_root.resolve()
    document = json.loads((root / config).read_text(encoding="utf-8-sig"))
    if document.get("schema_version") != 1 or not document.get("entries"):
        raise ValueError("Unsupported or empty reviewed source contract")
    prepared = []
    keys: set[str] = set()
    for record in document["entries"]:
        key = record["runtime_resource_key"]
        if key in keys or not key.startswith(RUNTIME_PREFIX) or key.endswith(".png"):
            raise ValueError("Duplicate or invalid runtime key")
        keys.add(key)
        source = contained(root, record["source"], SOURCE_ROOT)
        meta_source = contained(root, record["meta_source"], SOURCE_ROOT)
        target = contained(root, f"assets/resources/{key}.png", Path("assets/resources") / RUNTIME_PREFIX)
        meta_target = contained(root, f"assets/resources/{key}.png.meta", Path("assets/resources") / RUNTIME_PREFIX)
        generated = contained(root, record["provenance"]["generated_source"], SOURCE_ROOT)
        for path, expected in ((source, record["source_sha256"]), (meta_source, record["meta_sha256"]), (generated, record["provenance"]["generated_sha256"])):
            if digest(path) != expected:
                raise ValueError(f"Pinned source hash mismatch: {path}")
        validate_image(source, record)
        source_payload = source.read_bytes()
        meta_payload = meta_source.read_bytes()
        if hashlib.sha256(source_payload).hexdigest().upper() != record["source_sha256"] or hashlib.sha256(meta_payload).hexdigest().upper() != record["meta_sha256"]:
            raise ValueError("Pinned source changed during validation")
        meta = json.loads(meta_source.read_text(encoding="utf-8-sig"))
        data = meta["subMetas"]["f9941"]["userData"]
        if (meta["uuid"] != record["uuid"] or
                meta["subMetas"]["f9941"]["uuid"] != record["uuid"] + "@f9941" or
                [data["rawWidth"], data["rawHeight"]] != record["dimensions"] or
                [data["trimX"], data["trimY"], data["trimX"] + data["width"], data["trimY"] + data["height"]] != record["alpha_bbox"] or
                data["pivotX"] != 0.5 or data["pivotY"] != 0.5):
            raise ValueError("Pinned metadata contract mismatch")
        matched = [entry for entry in entries if entry.get("runtimeResourceKey") == key]
        if len(matched) != 1:
            raise ValueError(f"Expected exactly one manifest entry for {key}")
        entry = matched[0]
        provenance = {"schema_version": 1, "source": record["source"], "source_sha256": record["source_sha256"], "meta_sha256": record["meta_sha256"], "generator": record["provenance"]["generator"]}
        if not apply and validate_runtime:
            if digest(target) != record["source_sha256"] or digest(meta_target) != record["meta_sha256"]:
                raise ValueError(f"Runtime source/metadata drift: {key}")
            validate_image(target, record)
            if entry.get("runtimeSha256") != record["source_sha256"] or entry.get("reviewedSourceOverride") != provenance:
                raise ValueError(f"Manifest provenance drift: {key}")
        prepared.append((record, source_payload, meta_payload, target, meta_target, entry, provenance))
    # No filesystem mutation before every hash, path, alpha, and entry passes.
    for record, source_payload, meta_payload, target, meta_target, entry, provenance in prepared:
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_payload)
            meta_target.write_bytes(meta_payload)
            entry["runtimeSha256"] = record["source_sha256"]
            entry["sourceCutoutMethod"] = "reviewed_generated_transparent_source:v1"
            entry["reviewedSourceOverride"] = provenance
        # Preserve original sheet/source/bounds as immutable lineage.
    return {"status": "PASS", "mode": "apply" if apply else "check", "reviewed_source_count": len(prepared), "keys": sorted(keys)}


def preflight_sources(project_root: Path) -> dict[str, Any]:
    document = json.loads((project_root / CONFIG).read_text(encoding="utf-8-sig"))
    entries = [{"runtimeResourceKey": record["runtime_resource_key"]} for record in document["entries"]]
    return apply_sources(project_root, entries, validate_runtime=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--apply", action="store_true", help="Explicitly restore pinned runtime PNG, metadata and manifest lineage")
    args = parser.parse_args()
    manifest_path = args.project_root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    report = apply_sources(args.project_root, manifest["entries"], apply=args.apply)
    if args.apply:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
