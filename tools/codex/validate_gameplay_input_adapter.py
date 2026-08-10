#!/usr/bin/env python3
"""Fail-closed structural and behavioral gate for the M03.4 input seam."""

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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def validate_meta(path: Path, importer: str, errors: list[str]) -> str:
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    input_dir = root / "assets/scripts/gameplay/input"
    adapter_path = input_dir / "GameplayInputAdapter.ts"
    adapter_meta_path = input_dir / "GameplayInputAdapter.ts.meta"
    input_meta_path = root / "assets/scripts/gameplay/input.meta"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    behavior_path = root / "tools/codex/test-gameplay-input-adapter.js"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    errors: list[str] = []

    required_paths = (
        adapter_path,
        adapter_meta_path,
        input_meta_path,
        game_root_path,
        behavior_path,
        gate_path,
    )
    for path in required_paths:
        require(path.is_file(), f"missing:{path.relative_to(root)}", errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    adapter = adapter_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")
    behavior = behavior_path.read_text(encoding="utf-8")

    adapter_patterns = {
        "class": r"export\s+class\s+GameplayInputAdapter\b",
        "actions": r"GameplayInputAction\s*=\s*'jump'\s*\|\s*'glide'\s*\|\s*'dash'\s*\|\s*'pause'",
        "pause_debounce": r"GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS\s*=\s*220\b",
        "clock_injection": r"readonly\s+nowMs\s*:\s*\(\)\s*=>\s*number",
        "state_injection": r"readonly\s+getSessionState\s*:\s*\(\)\s*=>\s*GameSessionState",
        "single_pause_clock": r"private\s+lastAcceptedPauseMs\s*:\s*number\s*\|\s*null\s*=\s*null",
        "pause_count": r"private\s+acceptedPauseCount\s*=\s*0",
        "phase_guard": r"if\s*\(!this\.hasValidPhase\(intent\)\)",
        "clock_guard": r"if\s*\(!Number\.isFinite\(nowMs\)\)",
        "playing_guard": r"sessionState\s*!==\s*'playing'",
        "release_glide": r"releaseGlide\(source:\s*'global_touch'\s*\|\s*'keyboard'\s*\|\s*'session_reset'\)",
    }
    for label, pattern in adapter_patterns.items():
        require(re.search(pattern, adapter, re.DOTALL) is not None, f"adapter_contract:{label}", errors)

    for marker in (
        "from 'cc'",
        'from "cc"',
        "console.",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "Date.",
        "Math.random",
        "setTimeout",
        "setInterval",
        "input.on(",
        "input.off(",
    ):
        require(marker not in adapter, f"adapter_forbidden:{marker}", errors)

    require(game_root.count("new GameplayInputAdapter(") == 1, "adapter_instance_count", errors)
    require(game_root.count("this.gliding =") == 1, "glide_writer_count", errors)
    require(game_root.count("this.applyJumpInput()") == 1, "jump_effect_route_count", errors)
    require(game_root.count("this.applyDashInput()") == 1, "dash_effect_route_count", errors)
    require(game_root.count("this.applyPauseInput(context)") == 1, "pause_effect_route_count", errors)
    for legacy in ("togglePauseFromInput", "lastPauseToggleMs", "pauseTapAccepted"):
        require(legacy not in game_root, f"legacy_route_present:{legacy}", errors)
    require(re.search(r"private\s+(?:jump|dash)\s*\(", game_root) is None, "legacy_effect_method_present", errors)

    listener_pairs = (
        ("TOUCH_START", "onTouchStart"),
        ("TOUCH_MOVE", "onTouchMove"),
        ("TOUCH_END", "onTouchEnd"),
        ("TOUCH_CANCEL", "onTouchEnd"),
        ("KEY_DOWN", "onKeyDown"),
        ("KEY_UP", "onKeyUp"),
    )
    for event, handler in listener_pairs:
        on_pattern = rf"input\.on\(Input\.EventType\.{event},\s*this\.{handler},\s*this\);"
        off_pattern = rf"input\.off\(Input\.EventType\.{event},\s*this\.{handler},\s*this\);"
        require(len(re.findall(on_pattern, game_root)) == 1, f"listener_on_count:{event}:{handler}", errors)
        require(len(re.findall(off_pattern, game_root)) == 1, f"listener_off_count:{event}:{handler}", errors)
    require(
        game_root.count("this.pauseTouchZone.on(Input.EventType.TOUCH_END, this.onPauseTouchZoneTap, this);") == 1,
        "pause_zone_listener_on_count",
        errors,
    )
    require(
        game_root.count("this.pauseTouchZone.off(Input.EventType.TOUCH_END, this.onPauseTouchZoneTap, this);") == 1,
        "pause_zone_listener_off_count",
        errors,
    )

    for source in ("keyboard", "global_touch", "hud_button", "pause_zone", "qa", "session_reset"):
        require(f"'{source}'" in game_root, f"missing_input_source:{source}", errors)
    require(game_root.count("this.gameplayInput.dispatch(") == 14, "dispatch_route_count", errors)
    require(game_root.count("this.gameplayInput.releaseGlide(") == 3, "release_glide_route_count", errors)

    for marker in (
        "pause_debounce_accepts_first_and_exact_boundary",
        "overlapping_pause_routes_share_one_debounce_owner",
        "clock_rollback_fails_closed_until_boundary_recovers",
        "invalid_clock_does_not_poison_pause_state",
        "invalid_action_phases_have_no_side_effects",
        "game_root_listener_and_routing_parity",
        "compilerOptions",
    ):
        require(marker in behavior, f"behavioral_test_missing:{marker}", errors)

    input_uuid = validate_meta(input_meta_path, "directory", errors)
    adapter_uuid = validate_meta(adapter_meta_path, "typescript", errors)
    require(input_uuid != adapter_uuid, "input_meta_uuid_collision", errors)

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

    gate = load_json(gate_path)
    steps = gate.get("steps", [])
    adapter_steps = [step for step in steps if step.get("id") == "gameplay-input-adapter-contracts"]
    require(len(adapter_steps) == 1, "static_gate_step_count", errors)
    if adapter_steps:
        step = adapter_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments")
            == ["-B", "tools/codex/validate_gameplay_input_adapter.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

    behavior_result: dict[str, Any] = {}
    node = shutil.which("node")
    require(node is not None, "node_not_found", errors)
    if node is not None:
        try:
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
            require(behavior_result.get("passed_groups") == 10, "behavioral_test_group_count", errors)
            require(behavior_result.get("debounce_ms") == 220, "behavioral_test_debounce", errors)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"behavioral_test_error:{type(exc).__name__}")

    result = {
        "adapter_uuid": adapter_uuid,
        "behavioral_groups": behavior_result.get("passed_groups", 0),
        "debounce_ms": behavior_result.get("debounce_ms", 0),
        "dispatch_routes": game_root.count("this.gameplayInput.dispatch("),
        "errors": sorted(errors),
        "global_listener_pairs": len(listener_pairs),
        "release_glide_routes": game_root.count("this.gameplayInput.releaseGlide("),
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
