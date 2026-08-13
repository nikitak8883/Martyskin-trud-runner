#!/usr/bin/env python3
"""Validate the minimal epoch value object after M03.7B callback-owner cleanup."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    source_path = root / "assets/scripts/qa/LifecycleEpoch.ts"
    meta_path = root / "assets/scripts/qa/LifecycleEpoch.ts.meta"
    test_path = root / "tools/codex/test-lifecycle-epoch.js"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    errors: list[str] = []

    for path, code in (
        (source_path, "missing_source"),
        (meta_path, "missing_meta"),
        (test_path, "missing_behavioral_test"),
        (game_root_path, "missing_game_root"),
        (gate_path, "missing_static_gate"),
    ):
        require(path.is_file(), code, errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    source = source_path.read_text(encoding="utf-8")
    test_source = test_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")

    required_patterns = {
        "class_export": r"export\s+class\s+LifecycleEpoch\b",
        "constructor": r"constructor\s*\(\s*initialValue\s*=\s*0\s*\)",
        "safe_initial": r"Number\.isSafeInteger\(initialValue\)",
        "current": r"public\s+current\s*\(\s*\)\s*:\s*number",
        "is_current": r"public\s+isCurrent\s*\(\s*epoch\s*:\s*number\s*\)\s*:\s*boolean",
        "advance": r"public\s+advance\s*\(\s*\)\s*:\s*number",
        "overflow_guard": r"this\.value\s*>=\s*Number\.MAX_SAFE_INTEGER",
    }
    for label, pattern in required_patterns.items():
        require(re.search(pattern, source, re.DOTALL) is not None, f"missing_contract:{label}", errors)

    forbidden_markers = (
        "from 'cc'",
        'from "cc"',
        "Date.",
        "Math.random",
        "console.",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "scheduleOnce",
        "setTimeout",
        "setInterval",
    )
    require(re.search(r"^\s*import\s", source, re.MULTILINE) is None, "source_has_import", errors)
    for marker in forbidden_markers:
        require(marker not in source, f"forbidden_source_marker:{marker}", errors)
    require(re.search(r"public\s+capture\s*\(", source) is None, "legacy_capture_present", errors)
    require(re.search(r"public\s+guard(?:<|\s*\()", source) is None, "legacy_guard_present", errors)
    require(
        re.search(r"\bcallback\s*(?::|\()", source, re.IGNORECASE) is None,
        "callback_ownership_present",
        errors,
    )
    require("this.value = 1" not in source, "overflow_wrap_to_one", errors)
    require("LifecycleEpoch" not in game_root, "game_root_wired", errors)

    for marker in (
        "current_is_stable",
        "is_current_tracks_monotonic_identity",
        "public_surface_excludes_callback_ownership",
        "overflow_fails_before_mutation",
        "Symbol('epoch')",
        "legacyCallbackHelpers: false",
        "callbackOwnership: 'GAME_RUNTIME_LIFECYCLE_OWNER'",
        "compilerTarget: 'ES2015'",
    ):
        require(marker in test_source, f"missing_test_marker:{marker}", errors)

    try:
        meta = load_json(meta_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid_meta:{exc}")
        meta = {}
    require(meta.get("ver") == "4.0.24", "meta_version", errors)
    require(meta.get("importer") == "typescript", "meta_importer", errors)
    require(meta.get("imported") is True, "meta_imported", errors)
    require(meta.get("files") == [], "meta_files", errors)
    require(meta.get("subMetas") == {}, "meta_submetas", errors)
    require(meta.get("userData") == {}, "meta_userdata", errors)
    try:
        lifecycle_uuid = str(uuid.UUID(str(meta.get("uuid"))))
        require(lifecycle_uuid == meta.get("uuid"), "meta_uuid_canonical", errors)
    except (ValueError, TypeError, AttributeError):
        lifecycle_uuid = ""
        errors.append("meta_uuid_invalid")

    seen_uuids: dict[str, Path] = {}
    duplicate_uuids: list[str] = []
    for candidate in (root / "assets").rglob("*.meta"):
        try:
            payload = load_json(candidate)
        except (OSError, json.JSONDecodeError):
            continue
        candidate_uuid = payload.get("uuid")
        if not isinstance(candidate_uuid, str):
            continue
        if candidate_uuid in seen_uuids:
            duplicate_uuids.append(candidate_uuid)
        else:
            seen_uuids[candidate_uuid] = candidate
    require(not duplicate_uuids, "duplicate_meta_uuid", errors)

    try:
        gate = load_json(gate_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid_static_gate:{exc}")
        gate = {"steps": []}
    steps = gate.get("steps", [])
    lifecycle_steps = [step for step in steps if step.get("id") == "lifecycle-epoch-contracts"]
    require(len(lifecycle_steps) == 1, "static_gate_step_count", errors)
    if lifecycle_steps:
        step = lifecycle_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments")
            == ["-B", "tools/codex/validate_lifecycle_epoch.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

    result = {
        "errors": sorted(errors),
        "game_root_wired": "LifecycleEpoch" in game_root,
        "legacy_callback_helpers": bool(
            re.search(r"public\s+(?:capture\s*\(|guard(?:<|\s*\())", source)
        ),
        "meta_uuid": lifecycle_uuid,
        "static_gate_steps": len(steps),
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
