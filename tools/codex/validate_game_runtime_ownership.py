#!/usr/bin/env python3
"""Validate the M03.7A UI-intent and runtime-lifecycle ownership seams."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def validate_meta(path: Path, importer: str, errors: list[str]) -> str:
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"invalid_meta:{path.name}:{exc}")
        return ""
    require(payload.get("importer") == importer, f"meta_importer:{path.name}", errors)
    require(payload.get("imported") is True, f"meta_imported:{path.name}", errors)
    require(payload.get("files") == [], f"meta_files:{path.name}", errors)
    require(payload.get("subMetas") == {}, f"meta_submetas:{path.name}", errors)
    require(payload.get("userData") == {}, f"meta_userdata:{path.name}", errors)
    try:
        canonical_uuid = str(uuid.UUID(str(payload.get("uuid"))))
        require(canonical_uuid == payload.get("uuid"), f"meta_uuid_canonical:{path.name}", errors)
        return canonical_uuid
    except (ValueError, TypeError, AttributeError):
        errors.append(f"meta_uuid_invalid:{path.name}")
        return ""


def method_body(source: str, start_marker: str, end_marker: str, errors: list[str]) -> str:
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    require(start >= 0, f"method_start_missing:{start_marker}", errors)
    require(end > start, f"method_end_missing:{end_marker}", errors)
    return source[start:end] if start >= 0 and end > start else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    ui_dir = root / "assets/scripts/gameplay/ui"
    lifecycle_dir = root / "assets/scripts/gameplay/lifecycle"
    ui_path = ui_dir / "GameplayUiIntentAdapter.ts"
    lifecycle_path = lifecycle_dir / "GameRuntimeLifecycleOwner.ts"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    behavior_path = root / "tools/codex/test-game-runtime-ownership.js"
    web_runtime_path = root / "tools/codex/web_runtime_ownership_function.js"
    android_runtime_path = root / "tools/codex/Run-MtrAndroidRuntimeOwnershipQa.ps1"
    activity_path = root / "native/engine/android/app/src/com/cocos/game/AppActivity.java"
    config_validator_path = root / "tools/validate-mtr-config.ps1"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    errors: list[str] = []

    required_paths = (
        ui_path,
        ui_path.with_suffix(".ts.meta"),
        ui_dir.with_suffix(".meta"),
        lifecycle_path,
        lifecycle_path.with_suffix(".ts.meta"),
        lifecycle_dir.with_suffix(".meta"),
        game_root_path,
        behavior_path,
        web_runtime_path,
        android_runtime_path,
        activity_path,
        config_validator_path,
        gate_path,
    )
    for path in required_paths:
        require(path.is_file(), f"missing:{path.relative_to(root)}", errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    ui_source = ui_path.read_text(encoding="utf-8")
    lifecycle_source = lifecycle_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")
    web_runtime = web_runtime_path.read_text(encoding="utf-8")
    android_runtime = android_runtime_path.read_text(encoding="utf-8")
    activity = activity_path.read_text(encoding="utf-8")
    config_validator = config_validator_path.read_text(encoding="utf-8")

    for label, pattern in {
        "ui_class": r"export\s+class\s+GameplayUiIntentAdapter\b",
        "ui_dispatch": r"public\s+dispatch\(",
        "ui_frozen_result": r"return\s+Object\.freeze\(\{",
        "lifecycle_class": r"export\s+class\s+GameRuntimeLifecycleOwner\b",
        "lifecycle_schedule": r"public\s+scheduleOnce\(",
        "lifecycle_listener": r"public\s+registerListener\(",
        "lifecycle_cancel": r"public\s+cancelSession\(",
        "lifecycle_destroy": r"public\s+destroy\(",
        "lifecycle_snapshot": r"public\s+snapshot\(",
        "lifecycle_stale_epoch": r"scope\s*===\s*'session'\s*&&\s*epoch\s*!==\s*this\.options\.getEpoch\(\)",
    }.items():
        source = ui_source if label.startswith("ui_") else lifecycle_source
        require(re.search(pattern, source, re.DOTALL) is not None, f"contract:{label}", errors)

    for action in (
        "navigate",
        "start_level",
        "preview_skin",
        "confirm_skin",
        "open_developer_gate",
        "submit_developer_gate",
    ):
        require(f"'{action}'" in ui_source, f"ui_action_missing:{action}", errors)

    for source_name, source in (("ui", ui_source), ("lifecycle", lifecycle_source)):
        for marker in (
            "from 'cc'",
            'from "cc"',
            "localStorage",
            "sessionStorage",
            "fetch(",
            "XMLHttpRequest",
            "setTimeout",
            "setInterval",
            "Math.random",
        ):
            require(marker not in source, f"{source_name}_forbidden:{marker}", errors)

    require(game_root.count("new GameplayUiIntentAdapter(") == 1, "ui_adapter_instance_count", errors)
    require(game_root.count("new GameRuntimeLifecycleOwner(") == 1, "lifecycle_owner_instance_count", errors)
    require(game_root.count("this.scheduleOnce(") == 1, "direct_schedule_once_count", errors)
    require(game_root.count("scheduleComponentOnce(") == 12, "component_schedule_route_count", errors)
    require(game_root.count("scheduleSessionOnce(") == 11, "session_schedule_route_count", errors)
    require(game_root.count("this.runtimeLifecycle.registerListener(") == 8, "listener_owner_route_count", errors)
    require(game_root.count("this.runtimeLifecycle.cancelSession(") == 2, "session_cleanup_route_count", errors)
    require(game_root.count("this.runtimeLifecycle.destroy(") == 1, "destroy_cleanup_route_count", errors)
    require(game_root.count("input.on(") == 6, "input_listener_register_count", errors)
    require(game_root.count("input.off(") == 6, "input_listener_unregister_count", errors)
    require(game_root.count("view.on('canvas-resize'") == 1, "view_listener_register_count", errors)
    require(game_root.count("view.off('canvas-resize'") == 1, "view_listener_unregister_count", errors)
    require(game_root.count("this.pauseTouchZone.on(") == 1, "pause_listener_register_count", errors)
    require(game_root.count("this.pauseTouchZone.off(") == 1, "pause_listener_unregister_count", errors)
    require(game_root.count("params.get('mtr_qa_ownership')") == 1, "web_query_key_count", errors)
    require(activity.count('"mtr_qa_ownership"') == 1, "android_query_key_count", errors)
    require("'mtr_qa_ownership'" in config_validator, "config_query_parity_missing", errors)
    require("mtr_qa_ownership" in web_runtime, "web_runtime_query_missing", errors)
    require("MTR_OWNERSHIP_QA_READY" in web_runtime, "web_runtime_marker_missing", errors)
    require("mtr_qa_ownership" in android_runtime, "android_runtime_query_missing", errors)
    require("MTR_OWNERSHIP_QA_READY" in android_runtime, "android_runtime_marker_missing", errors)
    require("^emulator-\\d+$" in android_runtime, "android_emulator_guard_missing", errors)

    ownership_qa = method_body(
        game_root,
        "    private runRuntimeOwnershipMatrixForQa(): void",
        "    private runPowerUpLifecycleMatrixForQa(): void",
        errors,
    )
    require(ownership_qa.count("this.gameplayUi.dispatch(") == 2, "runtime_qa_ui_dispatch_count", errors)
    require("this.runtimeLifecycle.snapshot()" in ownership_qa, "runtime_qa_snapshot_missing", errors)
    require("MTR_OWNERSHIP_QA_" in ownership_qa, "runtime_qa_marker_missing", errors)

    draw_menu = method_body(
        game_root,
        "    private drawMenu(): void",
        "    private drawUnifiedMenuChrome",
        errors,
    )
    for label, pattern in {
        "transition": r"this\.transitionTo\(",
        "start_level": r"this\.startLevel\(",
        "skin_assignment": r"this\.pendingSkinSelection\s*=(?!=)",
        "skin_confirm": r"this\.confirmSkinSelection\(",
        "developer_gate_open": r"this\.openDevGate\(",
        "developer_gate_submit": r"this\.tryOpenDeveloperMode\(",
    }.items():
        require(re.search(pattern, draw_menu) is None, f"draw_menu_direct_mutation:{label}", errors)
    for emitter in (
        "emitUiNavigationIntent",
        "emitUiStartLevelIntent",
        "emitUiPreviewSkinIntent",
        "emitUiConfirmSkinIntent",
        "emitUiDeveloperGateIntent",
    ):
        require(emitter in draw_menu, f"draw_menu_emitter_missing:{emitter}", errors)

    draw_player = method_body(
        game_root,
        "    private drawPlayerSkinSprite(",
        "    private drawPlayer",
        errors,
    )
    for field in ("player.x", "player.y", "player.vy", "player.onGround", "player.doubleJump"):
        require(
            re.search(rf"this\.{re.escape(field)}\s*=(?!=)", draw_player) is None,
            f"skin_render_physics_writer:{field}",
            errors,
        )

    meta_uuids = {
        validate_meta(ui_dir.with_suffix(".meta"), "directory", errors),
        validate_meta(ui_path.with_suffix(".ts.meta"), "typescript", errors),
        validate_meta(lifecycle_dir.with_suffix(".meta"), "directory", errors),
        validate_meta(lifecycle_path.with_suffix(".ts.meta"), "typescript", errors),
    }
    require("" not in meta_uuids, "ownership_meta_uuid_missing", errors)
    require(len(meta_uuids) == 4, "ownership_meta_uuid_collision", errors)

    gate = load_json(gate_path)
    steps = gate.get("steps", [])
    ownership_steps = [step for step in steps if step.get("id") == "game-runtime-ownership-contracts"]
    require(len(ownership_steps) == 1, "static_gate_step_count", errors)
    if ownership_steps:
        step = ownership_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments") == ["-B", "tools/codex/validate_game_runtime_ownership.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

    behavior_result: dict[str, Any] = {}
    node = shutil.which("node")
    require(node is not None, "node_not_found", errors)
    if node is not None:
        try:
            syntax = subprocess.run(
                [node, "--check", str(web_runtime_path)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
            require(syntax.returncode == 0, f"web_runtime_syntax_exit:{syntax.returncode}", errors)
            completed = subprocess.run(
                [node, str(behavior_path)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            require(completed.returncode == 0, f"behavioral_test_exit:{completed.returncode}", errors)
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            require(bool(lines), "behavioral_test_no_output", errors)
            if lines:
                try:
                    behavior_result = json.loads(lines[-1])
                except json.JSONDecodeError:
                    errors.append("behavioral_test_invalid_json")
            require(behavior_result.get("status") == "PASS", "behavioral_test_status", errors)
            require(behavior_result.get("groups") == 14, "behavioral_test_group_count", errors)
            require(behavior_result.get("uiActions") == 6, "behavioral_test_ui_action_count", errors)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"behavioral_test_error:{type(exc).__name__}")

    result = {
        "behavioral_groups": behavior_result.get("groups", 0),
        "component_schedule_routes": game_root.count("scheduleComponentOnce("),
        "errors": sorted(errors),
        "listener_routes": game_root.count("this.runtimeLifecycle.registerListener("),
        "session_schedule_routes": game_root.count("scheduleSessionOnce("),
        "status": "PASS" if not errors else "FAIL",
        "ui_actions": behavior_result.get("uiActions", 0),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
