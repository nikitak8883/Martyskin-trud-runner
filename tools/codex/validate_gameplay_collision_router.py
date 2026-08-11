#!/usr/bin/env python3
"""Fail-closed structural and recorded-order gate for the M03.5 collision seam."""

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


COLLISION_KINDS = (
    "platform_land",
    "ground_clamp",
    "collectible_pickup",
    "bonus_pickup",
    "obstacle_hit",
    "npc_stomp",
    "npc_hit",
    "level_finish",
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


def ordered_markers(source: str, markers: tuple[str, ...], code: str, errors: list[str]) -> None:
    previous = -1
    for marker in markers:
        current = source.find(marker)
        require(current > previous, f"{code}:{marker}", errors)
        previous = current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    collision_dir = root / "assets/scripts/gameplay/collision"
    router_path = collision_dir / "GameplayCollisionRouter.ts"
    router_meta_path = collision_dir / "GameplayCollisionRouter.ts.meta"
    collision_meta_path = root / "assets/scripts/gameplay/collision.meta"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    behavior_path = root / "tools/codex/test-gameplay-collision-router.js"
    web_runtime_path = root / "tools/codex/web_collision_router_runtime_function.js"
    android_runtime_path = root / "tools/codex/Run-MtrAndroidCollisionRouterQa.ps1"
    activity_path = root / "native/engine/android/app/src/com/cocos/game/AppActivity.java"
    config_validator_path = root / "tools/validate-mtr-config.ps1"
    web_release_config_path = root / "build-web-mobile.json"
    web_qa_config_path = root / "build-web-mobile-qa.json"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    errors: list[str] = []

    for path in (
        router_path,
        router_meta_path,
        collision_meta_path,
        game_root_path,
        behavior_path,
        web_runtime_path,
        android_runtime_path,
        activity_path,
        config_validator_path,
        web_release_config_path,
        web_qa_config_path,
        gate_path,
    ):
        require(path.is_file(), f"missing:{path.relative_to(root)}", errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    router = router_path.read_text(encoding="utf-8")
    game_root = game_root_path.read_text(encoding="utf-8")
    behavior = behavior_path.read_text(encoding="utf-8")
    web_runtime = web_runtime_path.read_text(encoding="utf-8")
    android_runtime = android_runtime_path.read_text(encoding="utf-8")
    activity = activity_path.read_text(encoding="utf-8")
    config_validator = config_validator_path.read_text(encoding="utf-8")
    web_release_config = load_json(web_release_config_path)
    web_qa_config = load_json(web_qa_config_path)

    router_patterns = {
        "class": r"export\s+class\s+GameplayCollisionRouter\b",
        "kind_constant": r"export\s+const\s+GAMEPLAY_COLLISION_KINDS\s*=\s*Object\.freeze",
        "typed_union": r"export\s+type\s+GameplayCollisionIntent\s*=",
        "sequence": r"readonly\s+sequence\s*:\s*number",
        "epoch": r"readonly\s+epoch\s*:\s*number",
        "tick": r"readonly\s+tick\s*:\s*number",
        "single_callback": r"readonly\s+onEvent\s*:\s*\(event:\s*GameplayCollisionEvent\)\s*=>\s*void",
        "reentrant_guard": r"if\s*\(this\.dispatching\)",
        "sync_callback": r"this\.options\.onEvent\(event\)",
        "finally_release": r"finally\s*\{\s*this\.dispatching\s*=\s*false;\s*\}",
        "payload_freeze": r"Object\.freeze\(\{\s*\.\.\.intent\.payload\s*\}\)",
    }
    for label, pattern in router_patterns.items():
        require(re.search(pattern, router, re.DOTALL) is not None, f"router_contract:{label}", errors)

    for kind in COLLISION_KINDS:
        require(router.count(f"'{kind}'") >= 2, f"router_kind_missing:{kind}", errors)
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
        "Promise",
    ):
        require(marker not in router, f"router_forbidden:{marker}", errors)

    require(game_root.count("new GameplayCollisionRouter(") == 1, "router_instance_count", errors)
    require(game_root.count("this.applyCollisionEvent(event)") == 1, "router_callback_count", errors)
    require(game_root.count("private applyCollisionEvent(event: GameplayCollisionEvent)") == 1, "effect_callback_count", errors)

    update_start = game_root.find("private updateGame(dt: number): void")
    callback_start = game_root.find("private applyCollisionEvent(event: GameplayCollisionEvent)")
    callback_end = game_root.find("private applyJumpInput(): void", callback_start)
    require(update_start >= 0 and callback_start > update_start and callback_end > callback_start, "method_boundaries", errors)
    update = game_root[update_start:callback_start] if update_start >= 0 and callback_start > update_start else ""
    callback = game_root[callback_start:callback_end] if callback_start >= 0 and callback_end > callback_start else ""
    qa_start = game_root.find("private runCollisionRouterMatrixForQa(): void")
    qa_end = game_root.find("private enableDeveloperMode(): void", qa_start)
    qa_matrix = game_root[qa_start:qa_end] if qa_start >= 0 and qa_end > qa_start else ""
    require(update.count("this.gameplayCollisions.route(") == len(COLLISION_KINDS), "production_route_count", errors)
    require(qa_matrix.count("this.gameplayCollisions.route(") == len(COLLISION_KINDS), "qa_route_count", errors)
    require(
        game_root.count("this.gameplayCollisions.route(") == len(COLLISION_KINDS) * 2,
        "total_route_count",
        errors,
    )

    ordered_markers(
        update,
        tuple(f"kind: '{kind}'" for kind in COLLISION_KINDS) + ("this.updateParticles(dt)",),
        "legacy_detection_order",
        errors,
    )
    for kind in COLLISION_KINDS:
        require(callback.count(f"case '{kind}'") == 1, f"callback_case_count:{kind}", errors)
    require("this.gameplayCollisions.route(" not in callback, "callback_reentrant_route", errors)
    require("const unhandledEvent: never = event" in callback, "callback_not_exhaustive", errors)

    direct_legacy_markers = (
        "b.taken = true",
        "bonus.taken = true",
        "o.dead = true",
        "npc.dead = true",
        "this.transitionTo(nextState, 'level_end')",
    )
    for marker in direct_legacy_markers:
        require(marker not in update, f"direct_legacy_effect:{marker}", errors)

    callback_orders = {
        "platform_land": (
            "this.player.y = event.payload.targetY",
            "this.player.vy = 0",
            "this.player.onGround = true",
            "this.player.doubleJump = true",
            "this.secondJumpPoseTimer = 0",
        ),
        "collectible_pickup": (
            "collectible.taken = true",
            "const gain = Math.max(1, collectible.value || 1)",
            "this.bananasCollected += gain",
            "this.score +=",
            "this.emit(",
            "this.checkAchievementProgress(",
        ),
        "bonus_pickup": (
            "bonus.taken = true",
            "this.activateBonus(event.payload.bonusType)",
            "this.emit(event.payload.screenX",
            "this.playFirst(['bonus', 'clear']",
        ),
        "obstacle_hit": ("obstacle.dead = true", "this.damage("),
        "npc_stomp": (
            "npc.dead = true",
            "this.player.vy = -520",
            "this.bananasCollected += gain",
            "this.score += 90 + gain * 8",
            "this.bannerText =",
            "this.bannerTimer = 1.35",
            "this.emit(",
            "this.playFirst(",
            "this.playVoice('banana'",
            "this.checkAchievementProgress('npc_stomp')",
        ),
        "level_finish": (
            "this.transitionTo(event.payload.nextState, 'level_end')",
            "this.unlockedLevel = Math.max(",
            "this.saveSettings()",
            "this.unlockAchievement('level_clear'",
            "this.saveRecord()",
            "this.playFirst(this.state === 'over'",
        ),
    }
    for label, markers in callback_orders.items():
        case_marker = f"case '{label}'"
        case_start = callback.find(case_marker)
        next_case = callback.find("case '", case_start + len(case_marker)) if case_start >= 0 else -1
        case_end = next_case if next_case >= 0 else len(callback)
        case_source = callback[case_start:case_end] if case_start >= 0 else ""
        ordered_markers(case_source, markers, f"side_effect_order:{label}", errors)

    ordered_markers(
        qa_matrix,
        tuple(f"kind: '{kind}'" for kind in COLLISION_KINDS),
        "qa_runtime_order",
        errors,
    )
    for marker in (
        "if (!DEBUG || !this.developerMode || this.state !== 'playing')",
        "MTR_COLLISION_QA_",
        "sequence=${contiguousSequence ? 'contiguous' : 'invalid'}",
        "effects=${effectPassCount}/${GAMEPLAY_COLLISION_KINDS.length}",
        "this.collisionQaEvents = null",
    ):
        require(marker in qa_matrix, f"qa_runtime_contract:{marker}", errors)

    require(game_root.count("params.get('mtr_qa_collisions')") == 1, "web_query_key_count", errors)
    require(activity.count('"mtr_qa_collisions"') == 1, "android_query_key_count", errors)
    require("'mtr_qa_collisions'" in config_validator, "config_query_parity_missing", errors)
    require("mtr_qa_collisions" in web_runtime, "web_runtime_query_missing", errors)
    require("MTR_COLLISION_QA_READY" in web_runtime, "web_runtime_ready_marker_missing", errors)
    require("effects=8\\/8" in web_runtime, "web_runtime_effect_assertion_missing", errors)
    require("mtr_qa_collisions" in android_runtime, "android_runtime_query_missing", errors)
    require("MTR_COLLISION_QA_READY" in android_runtime, "android_runtime_ready_marker_missing", errors)
    require("^emulator-\\d+$" in android_runtime, "android_emulator_guard_missing", errors)
    require("ro.kernel.qemu" in android_runtime, "android_qemu_guard_missing", errors)
    require(web_release_config.get("platform") == "web-mobile", "web_release_platform", errors)
    require(web_release_config.get("debug") is False, "web_release_debug_not_off", errors)
    require(web_release_config.get("outputName") == "web-mobile", "web_release_output", errors)
    require(web_qa_config.get("platform") == "web-mobile", "web_qa_platform", errors)
    require(web_qa_config.get("debug") is True, "web_qa_debug_not_on", errors)
    require(web_qa_config.get("outputName") == "web-mobile-qa", "web_qa_output", errors)

    for marker in (
        "recorded_order_is_synchronous_and_monotonic",
        "event_and_payload_are_immutable_snapshots",
        "epoch_and_tick_are_sampled_per_route",
        "reentrant_routing_is_rejected_and_guard_recovers",
        "callback_failure_propagates_without_poisoning_router",
        "game_root_routes_detection_in_legacy_order",
        "side_effects_live_only_in_exhaustive_game_root_callback",
        "compilerOptions",
    ):
        require(marker in behavior, f"behavioral_test_missing:{marker}", errors)

    directory_uuid = validate_meta(collision_meta_path, "directory", errors)
    router_uuid = validate_meta(router_meta_path, "typescript", errors)
    require(directory_uuid != router_uuid, "collision_meta_uuid_collision", errors)

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
    router_steps = [step for step in steps if step.get("id") == "gameplay-collision-router-contracts"]
    require(len(router_steps) == 1, "static_gate_step_count", errors)
    if router_steps:
        gate_step = router_steps[0]
        require(gate_step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(gate_step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(gate_step.get("executable") == "python", "static_gate_executable", errors)
        require(
            gate_step.get("arguments")
            == ["-B", "tools/codex/validate_gameplay_collision_router.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(gate_step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

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
            require(behavior_result.get("passed_groups") == 10, "behavioral_test_group_count", errors)
            require(behavior_result.get("collision_kinds") == len(COLLISION_KINDS), "behavioral_test_kind_count", errors)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"behavioral_test_error:{type(exc).__name__}")

    result = {
        "behavioral_groups": behavior_result.get("passed_groups", 0),
        "collision_kinds": behavior_result.get("collision_kinds", 0),
        "errors": sorted(errors),
        "legacy_order_slots": len(COLLISION_KINDS),
        "production_route_count": update.count("this.gameplayCollisions.route("),
        "qa_route_count": qa_matrix.count("this.gameplayCollisions.route("),
        "router_uuid": router_uuid,
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
