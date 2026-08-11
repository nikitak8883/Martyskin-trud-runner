#!/usr/bin/env python3
"""Fail-closed structural and behavioral gate for the M03.6 power-up owner."""

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


EFFECT_KEYS = (
    "jumpBoost",
    "dashBoost",
    "armor",
    "magnet",
    "vestBonus",
    "shieldBonus",
    "coffeeBoost",
    "blueprintBonus",
    "passBonus",
    "extraLifeAura",
)


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
    powerup_dir = root / "assets/scripts/gameplay/powerups"
    lifecycle_path = powerup_dir / "PowerUpLifecycle.ts"
    lifecycle_meta_path = powerup_dir / "PowerUpLifecycle.ts.meta"
    directory_meta_path = root / "assets/scripts/gameplay/powerups.meta"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    behavior_path = root / "tools/codex/test-powerup-lifecycle.js"
    web_runtime_path = root / "tools/codex/web_powerup_lifecycle_runtime_function.js"
    android_runtime_path = root / "tools/codex/Run-MtrAndroidPowerUpLifecycleQa.ps1"
    activity_path = root / "native/engine/android/app/src/com/cocos/game/AppActivity.java"
    config_validator_path = root / "tools/validate-mtr-config.ps1"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    errors: list[str] = []

    required_paths = (
        lifecycle_path,
        lifecycle_meta_path,
        directory_meta_path,
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

    lifecycle = lifecycle_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")
    web_runtime = web_runtime_path.read_text(encoding="utf-8")
    android_runtime = android_runtime_path.read_text(encoding="utf-8")
    activity = activity_path.read_text(encoding="utf-8")
    config_validator = config_validator_path.read_text(encoding="utf-8")

    lifecycle_patterns = {
        "class": r"export\s+class\s+PowerUpLifecycle\b",
        "kind_count": r"POWER_UP_KIND_COUNT\s*=\s*9\b",
        "epoch_injection": r"readonly\s+getEpoch\s*:\s*\(\)\s*=>\s*number",
        "tick_injection": r"readonly\s+getTick\s*:\s*\(\)\s*=>\s*number",
        "spawn": r"public\s+spawn\(",
        "collect": r"public\s+collect\(",
        "activate": r"public\s+activate\(",
        "tick": r"public\s+tick\(",
        "expire": r"private\s+expireCompletedInstances\(",
        "cleanup": r"public\s+cleanupSession\(",
        "reset": r"public\s+beginEpoch\(",
        "invalidate": r"public\s+invalidate\(",
        "qa_gate": r"if\s*\(!this\.options\.allowQaMutation\)",
        "raw_subtract": r"this\.effects\[key\]\s*-=\s*dt",
        "stale_reject": r"expectedEpoch\s*!==\s*currentEpoch",
        "immutable_snapshot": r"return\s+Object\.freeze\(\{",
    }
    for label, pattern in lifecycle_patterns.items():
        require(re.search(pattern, lifecycle, re.DOTALL) is not None, f"lifecycle_contract:{label}", errors)
    for key in EFFECT_KEYS:
        require(lifecycle.count(f"'{key}'") >= 1, f"effect_key_missing:{key}", errors)
    for phase in ("spawned", "collected", "active", "expired", "cleaned"):
        require(f"'{phase}'" in lifecycle, f"phase_missing:{phase}", errors)
    for marker in (
        "from 'cc'",
        'from "cc"',
        "localStorage",
        "sessionStorage",
        "fetch(",
        "XMLHttpRequest",
        "Date.",
        "Math.random",
        "setTimeout",
        "setInterval",
        "Promise",
    ):
        require(marker not in lifecycle, f"lifecycle_forbidden:{marker}", errors)

    require(game_root.count("new PowerUpLifecycle(") == 1, "lifecycle_instance_count", errors)
    require(
        "const BONUS_COUNT: typeof POWER_UP_KIND_COUNT = BONUS_LABELS.length;" in game_root,
        "bonus_kind_label_count_contract",
        errors,
    )
    require("interface Bonus { x: number; y: number; type: number; taken: boolean; lifecycleId: string; }" in game_root, "bonus_lifecycle_id", errors)
    require("this.bonuses.push({" not in game_root, "direct_bonus_spawn_writer", errors)
    require(game_root.count("this.createBonus(") >= 6, "spawn_route_count", errors)
    require(game_root.count("this.powerUps.beginEpoch(resetEpoch, reason)") == 1, "reset_owner_count", errors)
    require(game_root.count("this.powerUps.tick(dt)") == 1, "production_tick_owner_count", errors)
    require(game_root.count("this.powerUps.collect(bonus.lifecycleId, event.epoch)") == 1, "collect_owner_count", errors)
    require(game_root.count("this.powerUps.activate(lifecycleId, type, epoch)") == 1, "activate_owner_count", errors)
    require(game_root.count("this.powerUps.consumeArmor(this.devEvents.currentEpoch())") == 1, "armor_owner_count", errors)
    require("this.powerUps.cleanupSession(`transition:${prev}->${next}:${reason}`)" in game_root, "transition_cleanup", errors)
    require("this.powerUps.invalidate(invalidatedEpoch, 'component_destroy')" in game_root, "destroy_cleanup", errors)

    assignment = r"(?:\+\+|--|[+\-*/]?=(?!=))"
    for name in EFFECT_KEYS + ("runBonusCount", "runBonusSeen"):
        pattern = rf"this\.{name}(?:\[[^\]]+\])?\s*{assignment}"
        require(re.search(pattern, game_root) is None, f"legacy_writer:{name}", errors)
    for name in EFFECT_KEYS + ("runBonusCount", "runBonusSeen"):
        require(
            re.search(rf"private\s+get\s+{name}\s*\(", game_root) is not None,
            f"delegating_getter_missing:{name}",
            errors,
        )

    reset_start = game_root.find("private reset(reason: GameRootResetReason): void")
    reset_end = game_root.find("private startLevel", reset_start)
    reset_source = game_root[reset_start:reset_end] if reset_start >= 0 and reset_end > reset_start else ""
    require(reset_source.find("this.devEvents.beginReset") < reset_source.find("this.powerUps.beginEpoch"), "reset_epoch_order", errors)
    require(reset_source.find("this.powerUps.beginEpoch") < reset_source.find("this.generateLevel()"), "reset_generate_order", errors)

    require(game_root.count("params.get('mtr_qa_powerups')") == 1, "web_query_key_count", errors)
    require(activity.count('"mtr_qa_powerups"') == 1, "android_query_key_count", errors)
    require("'mtr_qa_powerups'" in config_validator, "config_query_parity_missing", errors)
    require("mtr_qa_powerups" in web_runtime, "web_runtime_query_missing", errors)
    require("MTR_POWERUP_QA_READY" in web_runtime, "web_runtime_marker_missing", errors)
    require("checks=8\\/8" in web_runtime, "web_runtime_check_assertion", errors)
    require("mtr_qa_powerups" in android_runtime, "android_runtime_query_missing", errors)
    require("MTR_POWERUP_QA_READY" in android_runtime, "android_runtime_marker_missing", errors)
    require("^emulator-\\d+$" in android_runtime, "android_emulator_guard_missing", errors)
    require("ro.kernel.qemu" in android_runtime, "android_qemu_guard_missing", errors)

    directory_uuid = validate_meta(directory_meta_path, "directory", errors)
    lifecycle_uuid = validate_meta(lifecycle_meta_path, "typescript", errors)
    require(directory_uuid != lifecycle_uuid, "powerup_meta_uuid_collision", errors)
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
    lifecycle_steps = [step for step in steps if step.get("id") == "powerup-lifecycle-contracts"]
    require(len(lifecycle_steps) == 1, "static_gate_step_count", errors)
    if lifecycle_steps:
        step = lifecycle_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments") == ["-B", "tools/codex/validate_powerup_lifecycle.py", "--project-root", "."],
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
            require(behavior_result.get("kinds") == 9, "behavioral_test_kind_count", errors)
            require(behavior_result.get("effects") == 10, "behavioral_test_effect_count", errors)
            require(
                behavior_result.get("phaseOrder") == ["spawned", "collected", "activated", "expired", "cleaned"],
                "behavioral_test_phase_order",
                errors,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"behavioral_test_error:{type(exc).__name__}")

    result = {
        "behavioral_groups": behavior_result.get("groups", 0),
        "effect_keys": len(EFFECT_KEYS),
        "errors": sorted(errors),
        "lifecycle_uuid": lifecycle_uuid,
        "powerup_kinds": behavior_result.get("kinds", 0),
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
