#!/usr/bin/env python3
"""Validate Martyshkin Trud UI IR manifests without modifying runtime files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_CANVAS_FIT_MODES = {"fit_width", "fit_height", "fixed_height", "fixed_width", "auto"}
ALLOWED_NODE_TYPES = {
    "panel",
    "sprite",
    "label",
    "button",
    "list",
    "grid",
    "progress",
    "badge",
    "icon_slot",
    "slider",
    "toggle",
    "modal",
    "spacer",
    "editbox",
}
ALLOWED_TEXT_STRATEGIES = {
    "runtime_label",
    "baked_png_atomic",
    "hidden_editbox_runtime_mirror",
    "decorative_none",
}
TOUCH_TARGET_MIN_PX = 64
EXPECTED_SCREEN_IDS = {
    "menu",
    "name",
    "levels",
    "playing_hud",
    "devgate",
    "sound",
    "skins",
    "devpanel",
    "achievements",
    "records",
    "paused",
    "clear",
    "over",
    "finished",
}
RUNTIME_BUTTON_CALL_RE = re.compile(
    r"this\.button\(\s*([^,\r\n]+)\s*,\s*([^,\r\n]+)\s*,\s*([^,\r\n]+)\s*,\s*([^,\r\n]+)\s*,",
)
NUMERIC_LITERAL_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


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


def resource_exists(resources_root: Path, key: str) -> bool:
    normalized = normalize_resource_key(key)
    if not normalized:
        return False
    return (resources_root / f"{normalized}.png").exists()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def exception_labels(ui_skin_manifest: dict[str, Any]) -> dict[str, set[str]]:
    labels_by_screen: dict[str, set[str]] = {}
    exceptions = ui_skin_manifest.get("policy", {}).get("atomicBakedInteractiveExceptions", [])
    if not isinstance(exceptions, list):
        return labels_by_screen
    for item in exceptions:
        if not isinstance(item, dict):
            continue
        screen = str(item.get("screen", "")).strip()
        labels = item.get("labels", [])
        if not screen or not isinstance(labels, list):
            continue
        labels_by_screen.setdefault(screen, set()).update(str(label) for label in labels)
    return labels_by_screen


def validate_runtime_button_literals(project_root: Path, runtime_file: str = "assets/scripts/GameRoot.ts") -> dict[str, Any]:
    path = (project_root / runtime_file).resolve()
    problems: list[dict[str, Any]] = []
    checked = 0
    if not path.exists():
        return {
            "path": runtime_file,
            "checkedLiteralButtonCount": 0,
            "problems": [{"type": "missing_runtime_file", "path": runtime_file}],
        }
    text = path.read_text(encoding="utf-8")
    for match in RUNTIME_BUTTON_CALL_RE.finditer(text):
        width_expr = match.group(3).strip()
        height_expr = match.group(4).strip()
        if not NUMERIC_LITERAL_RE.fullmatch(width_expr) or not NUMERIC_LITERAL_RE.fullmatch(height_expr):
            continue
        checked += 1
        width = float(width_expr)
        height = float(height_expr)
        if width >= TOUCH_TARGET_MIN_PX and height >= TOUCH_TARGET_MIN_PX:
            continue
        line = text.count("\n", 0, match.start()) + 1
        problems.append({
            "type": "runtime_touch_target_too_small",
            "path": runtime_file,
            "line": line,
            "width": width,
            "height": height,
            "minimum": TOUCH_TARGET_MIN_PX,
        })
    return {
        "path": runtime_file,
        "checkedLiteralButtonCount": checked,
        "problems": problems,
    }


def validate_ir(path: Path, project_root: Path, resources_root: Path, baked_exceptions: dict[str, set[str]]) -> dict[str, Any]:
    problems: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    data = load_json(path)

    if data.get("schema") != "mtr.ui_ir.screen.v1":
        problems.append({"type": "invalid_schema", "expected": "mtr.ui_ir.screen.v1", "actual": data.get("schema")})

    screen = data.get("screen")
    if not isinstance(screen, dict):
        return {
            "path": path.relative_to(project_root).as_posix(),
            "ok": False,
            "screenId": None,
            "nodeCount": 0,
            "problems": [{"type": "missing_screen"}],
            "warnings": warnings,
        }

    screen_id = str(screen.get("id", "")).strip()
    if not screen_id:
        problems.append({"type": "missing_screen_id"})
    if screen.get("root_safe_area") is not True:
        problems.append({"type": "root_safe_area_required", "screen": screen_id})
    if screen.get("canvas_fit_mode") not in ALLOWED_CANVAS_FIT_MODES:
        problems.append({"type": "invalid_canvas_fit_mode", "screen": screen_id, "actual": screen.get("canvas_fit_mode")})

    nodes = screen.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        problems.append({"type": "nodes_required", "screen": screen_id})
        nodes = []

    baked_allowed = baked_exceptions.get(screen_id, set())
    button_count = 0
    baked_button_count = 0
    runtime_label_count = 0
    asset_count = 0
    seen_node_ids: set[str] = set()

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            problems.append({"type": "invalid_node", "screen": screen_id, "index": index})
            continue
        node_id = str(node.get("id", f"node_{index}"))
        if node_id in seen_node_ids:
            problems.append({"type": "duplicate_node_id", "screen": screen_id, "node": node_id})
        seen_node_ids.add(node_id)
        node_type = node.get("type")
        if node_type not in ALLOWED_NODE_TYPES:
            problems.append({"type": "invalid_node_type", "screen": screen_id, "node": node_id, "actual": node_type})
        text_strategy = node.get("text_strategy", "decorative_none")
        if text_strategy not in ALLOWED_TEXT_STRATEGIES:
            problems.append({"type": "invalid_text_strategy", "screen": screen_id, "node": node_id, "actual": text_strategy})

        asset_key = node.get("asset_key")
        if isinstance(asset_key, str) and asset_key:
            asset_count += 1
            if not resource_exists(resources_root, asset_key):
                problems.append({"type": "missing_asset", "screen": screen_id, "node": node_id, "asset_key": asset_key})

        bounds = node.get("bounds")
        width = height = None
        if isinstance(bounds, dict):
            width = bounds.get("w")
            height = bounds.get("h")

        if node_type == "button":
            button_count += 1
            if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
                problems.append({"type": "button_bounds_required", "screen": screen_id, "node": node_id})
            elif width < TOUCH_TARGET_MIN_PX or height < TOUCH_TARGET_MIN_PX:
                problems.append({
                    "type": "touch_target_too_small",
                    "screen": screen_id,
                    "node": node_id,
                    "width": width,
                    "height": height,
                    "minimum": TOUCH_TARGET_MIN_PX,
                })

            label = str(node.get("label", "")).strip()
            if text_strategy == "baked_png_atomic":
                baked_button_count += 1
                if label not in baked_allowed:
                    problems.append({"type": "undocumented_baked_button_label", "screen": screen_id, "node": node_id, "label": label})
                if node.get("runtime_label_drawn") is not False:
                    problems.append({"type": "baked_button_must_not_draw_runtime_label", "screen": screen_id, "node": node_id, "label": label})
            elif text_strategy == "runtime_label":
                runtime_label_count += 1
                if not node.get("text_key") and not label:
                    problems.append({"type": "runtime_label_missing_text", "screen": screen_id, "node": node_id})

        if node_type == "editbox" and text_strategy != "hidden_editbox_runtime_mirror":
            warnings.append({"type": "editbox_should_hide_native_visual_label", "screen": screen_id, "node": node_id})

    return {
        "path": path.relative_to(project_root).as_posix(),
        "ok": not problems,
        "screenId": screen_id,
        "nodeCount": len(nodes),
        "buttonCount": button_count,
        "bakedButtonCount": baked_button_count,
        "runtimeLabelButtonCount": runtime_label_count,
        "assetReferenceCount": asset_count,
        "problems": problems,
        "warnings": warnings,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    resources_root = (project_root / args.resources_root).resolve()
    ir_dir = (project_root / args.ir_dir).resolve()
    ui_skin_manifest_path = (project_root / args.ui_skin_manifest).resolve()
    ui_skin_manifest = load_json(ui_skin_manifest_path)
    baked_exceptions = exception_labels(ui_skin_manifest)
    files = sorted(ir_dir.glob("*.json")) if ir_dir.exists() else []
    checks = [validate_ir(path, project_root, resources_root, baked_exceptions) for path in files]
    runtime_button_contract = validate_runtime_button_literals(project_root)
    screen_ids = [check["screenId"] for check in checks if check["screenId"]]
    duplicate_screen_ids = sorted({screen_id for screen_id in screen_ids if screen_ids.count(screen_id) > 1})
    missing_screen_ids = sorted(EXPECTED_SCREEN_IDS.difference(screen_ids))
    coverage_problems: list[dict[str, Any]] = [
        {"type": "missing_screen_manifest", "screen": screen_id}
        for screen_id in missing_screen_ids
    ]
    coverage_problems.extend(
        {"type": "duplicate_screen_manifest", "screen": screen_id}
        for screen_id in duplicate_screen_ids
    )
    problems = coverage_problems + runtime_button_contract["problems"] + [problem for check in checks for problem in check["problems"]]
    warnings = [warning for check in checks for warning in check["warnings"]]
    return {
        "schema": "mtr.ui_ir_validation.v1",
        "projectRoot": str(project_root),
        "irDir": ir_dir.relative_to(project_root).as_posix() if ir_dir.exists() else args.ir_dir,
        "uiSkinManifest": ui_skin_manifest_path.relative_to(project_root).as_posix(),
        "policy": {
            "touchTargetMinPx": TOUCH_TARGET_MIN_PX,
            "mutatesFiles": False,
            "bakedExceptionScreens": sorted(baked_exceptions.keys()),
            "expectedScreenIds": sorted(EXPECTED_SCREEN_IDS),
        },
        "coverage": {
            "expectedScreenCount": len(EXPECTED_SCREEN_IDS),
            "observedScreenIds": sorted(screen_ids),
            "missingScreenIds": missing_screen_ids,
            "duplicateScreenIds": duplicate_screen_ids,
        },
        "runtimeButtonContract": runtime_button_contract,
        "summary": {
            "screenCount": len(checks),
            "expectedScreenCount": len(EXPECTED_SCREEN_IDS),
            "okCount": sum(1 for check in checks if check["ok"]),
            "nodeCount": sum(check["nodeCount"] for check in checks),
            "buttonCount": sum(check["buttonCount"] for check in checks),
            "bakedButtonCount": sum(check["bakedButtonCount"] for check in checks),
            "assetReferenceCount": sum(check["assetReferenceCount"] for check in checks),
            "runtimeLiteralButtonCount": runtime_button_contract["checkedLiteralButtonCount"],
            "problemCount": len(problems),
            "warningCount": len(warnings),
        },
        "checks": checks,
        "problems": problems,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--resources-root", default="assets/resources", help="Resources path relative to project root.")
    parser.add_argument("--ir-dir", default="docs/global_modernization/manifests/ui_ir", help="UI IR directory relative to project root.")
    parser.add_argument("--ui-skin-manifest", default="assets/resources/config/ui_skin_manifest.json", help="UI skin manifest path relative to project root.")
    parser.add_argument("--report", default="", help="Optional JSON report output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": report["summary"]["problemCount"] == 0,
        "summary": report["summary"],
        "report": args.report or None,
    }, ensure_ascii=False))
    return 0 if report["summary"]["problemCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
