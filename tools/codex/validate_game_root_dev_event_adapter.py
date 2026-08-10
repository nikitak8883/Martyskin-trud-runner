#!/usr/bin/env python3
"""Cross-platform structural gate for the M03.3C GameRoot diagnostics seam."""

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
    adapter_path = root / "assets/scripts/qa/GameRootDevEventAdapter.ts"
    meta_path = root / "assets/scripts/qa/GameRootDevEventAdapter.ts.meta"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    state_path = root / "assets/scripts/gameplay/state/GameSessionState.ts"
    activity_path = root / "native/engine/android/app/src/com/cocos/game/AppActivity.java"
    config_validator_path = root / "tools/validate-mtr-config.ps1"
    behavioral_test_path = root / "tools/codex/test-game-root-dev-event-adapter.js"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    web_config_path = root / "build-web-mobile.json"
    emulator_config_path = root / "build-android-emulator.json"
    errors: list[str] = []

    required_paths = (
        adapter_path,
        meta_path,
        game_root_path,
        state_path,
        activity_path,
        config_validator_path,
        behavioral_test_path,
        gate_path,
        web_config_path,
        emulator_config_path,
    )
    for path in required_paths:
        require(path.is_file(), f"missing:{path.relative_to(root)}", errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    adapter = adapter_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")
    state_source = state_path.read_text(encoding="utf-8")
    activity = activity_path.read_text(encoding="utf-8")
    config_validator = config_validator_path.read_text(encoding="utf-8")
    behavioral_test = behavioral_test_path.read_text(encoding="utf-8")

    adapter_patterns = {
        "class": r"export\s+class\s+GameRootDevEventAdapter\b",
        "capacity": r"GAME_ROOT_DEV_EVENT_CAPACITY\s*=\s*128\b",
        "export_bound": r"GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES\s*=\s*32768\b",
        "single_log": r"private\s+readonly\s+events\s*:\s*DevEventLog",
        "single_epoch": r"private\s+readonly\s+lifecycle\s*=\s*new\s+LifecycleEpoch\(\)",
        "release_switch": r"enabled\s*:\s*options\.eventsEnabled",
        "sink_disabled": r"this\.onEvent\s*=\s*options\.eventsEnabled\s*\?\s*options\.onEvent\s*:\s*undefined",
        "transition": r"recordTransition\s*\(\s*transition\s*:\s*GameSessionTransitionResult",
        "reset_begin": r"beginReset\s*\(\s*state\s*:\s*GameSessionState",
        "reset_end": r"endReset\s*\(\s*epoch\s*:\s*number",
        "epoch_advance": r"const\s+epoch\s*=\s*this\.lifecycle\.advance\(\)",
        "epoch_event": r"code\s*:\s*'session\.epoch\.changed'",
        "reset_begin_event": r"code\s*:\s*'session\.reset\.begin'",
        "reset_end_event": r"code\s*:\s*'session\.reset\.end'",
        "guard": r"guardSessionCallback<[^>]+>",
        "bounded_export": r"return\s+this\.events\.exportJson\(maxEvents,\s*maxBytes\)",
        "sink_isolation": r"try\s*\{\s*this\.onEvent\(event\);\s*\}\s*catch\s*\{",
    }
    for label, pattern in adapter_patterns.items():
        require(re.search(pattern, adapter, re.DOTALL) is not None, f"adapter_contract:{label}", errors)

    for marker in (
        "from 'cc'",
        'from "cc"',
        "from 'cc/env'",
        'from "cc/env"',
        "console.",
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "Date.",
        "Math.random",
        "scheduleOnce",
        "setTimeout",
        "setInterval",
    ):
        require(marker not in adapter, f"adapter_forbidden:{marker}", errors)

    require("import { DEBUG } from 'cc/env';" in game_root, "game_root_missing_debug_macro", errors)
    require(game_root.count("new GameRootDevEventAdapter(") == 1, "adapter_instance_count", errors)
    require("eventsEnabled: DEBUG" in game_root, "adapter_not_bound_to_debug", errors)
    require(
        "onEvent: DEBUG ? logGameRootDevEvent : undefined" in game_root,
        "event_sink_not_bound_to_debug",
        errors,
    )
    require("new DevEventLog(" not in game_root, "second_dev_event_log_owner", errors)
    require("new LifecycleEpoch(" not in game_root, "second_lifecycle_epoch_owner", errors)
    require(len(re.findall(r"this\.state\s*=\s*next\b", game_root)) == 1, "state_writer_count", errors)
    require(len(re.findall(r"this\.devEvents\.recordTransition\(", game_root)) == 3, "transition_branch_observer_count", errors)
    require(len(re.findall(r"this\.devEvents\.beginReset\(", game_root)) == 1, "reset_begin_wiring_count", errors)
    require(len(re.findall(r"this\.devEvents\.endReset\(", game_root)) == 1, "reset_end_wiring_count", errors)
    require(len(re.findall(r"guardSessionCallback\(", game_root)) == 4, "session_guard_wiring_count", errors)

    reset_reasons = {
        "boot": 1,
        "start_level": 1,
        "qa_end_state": 1,
        "qa_reset_loop": 1,
    }
    for reason, expected_count in reset_reasons.items():
        require(
            len(re.findall(rf"this\.reset\('{re.escape(reason)}'\)", game_root)) == expected_count,
            f"reset_reason_count:{reason}",
            errors,
        )
    require(
        re.search(r"private\s+reset\s*\(\s*reason\s*:\s*GameRootResetReason\s*\)", game_root) is not None,
        "reset_reason_not_typed",
        errors,
    )
    require("if (!DEBUG) return;" in game_root, "qa_probe_not_debug_guarded", errors)
    require("params.get('mtr_qa_reset_loops')" in game_root, "qa_reset_query_missing", errors)
    require(
        "if (!/^(?:[1-9]|10)$/.test(rawLoops))" in game_root,
        "qa_reset_loop_not_canonical_decimal",
        errors,
    )
    require("loops > 10" in game_root, "qa_reset_loop_not_bounded", errors)
    require("MTR_DEV_EVENT_QA_" in game_root, "qa_summary_marker_missing", errors)
    require("exportBound=${GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES}" in game_root, "qa_export_bound_marker_missing", errors)
    require(activity.count('"mtr_qa_reset_loops"') == 1, "android_query_key_count", errors)
    require("'mtr_qa_reset_loops'" in config_validator, "config_query_parity_missing", errors)

    require(
        len(re.findall(r"GAME_SESSION_TRANSITION_TARGETS", state_source)) >= 2,
        "state_contract_missing",
        errors,
    )
    for marker in (
        "release_disabled_log_still_advances_epoch",
        "transition_events_are_unique_and_do_not_write_state",
        "reset_pairing_rejects_nested_and_stale_end",
        "guard_suppresses_work_after_next_reset",
        "ten_loop_runtime_contract_is_exact",
        "ring_and_export_remain_bounded",
        "compilerTarget: 'ES2015'",
    ):
        require(marker in behavioral_test, f"behavioral_test_missing:{marker}", errors)

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
        adapter_uuid = str(uuid.UUID(str(meta.get("uuid"))))
        require(adapter_uuid == meta.get("uuid"), "meta_uuid_canonical", errors)
    except (ValueError, TypeError, AttributeError):
        adapter_uuid = ""
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

    web_config = load_json(web_config_path)
    emulator_config = load_json(emulator_config_path)
    require(web_config.get("debug") is False, "release_web_debug_enabled", errors)
    require(emulator_config.get("debug") is True, "emulator_debug_disabled", errors)
    require(
        emulator_config.get("packages", {}).get("android", {}).get("appABIs") == ["x86_64"],
        "emulator_abi_contract",
        errors,
    )

    gate = load_json(gate_path)
    steps = gate.get("steps", [])
    adapter_steps = [step for step in steps if step.get("id") == "game-root-dev-event-adapter-contracts"]
    require(len(adapter_steps) == 1, "static_gate_step_count", errors)
    if adapter_steps:
        step = adapter_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments")
            == ["-B", "tools/codex/validate_game_root_dev_event_adapter.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

    result = {
        "adapter_uuid": adapter_uuid,
        "errors": sorted(errors),
        "event_capacity": 128,
        "max_export_bytes": 32768,
        "release_web_events_enabled": web_config.get("debug"),
        "reset_reasons": sorted(reset_reasons),
        "session_guard_wiring_count": len(re.findall(r"guardSessionCallback\(", game_root)),
        "state_writer_count": len(re.findall(r"this\.state\s*=\s*next\b", game_root)),
        "static_gate_steps": len(steps),
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
