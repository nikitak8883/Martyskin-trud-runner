#!/usr/bin/env python3
"""Cross-platform structural validator for the M03.2 session-state contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED_STATES = (
    "menu",
    "playing",
    "paused",
    "clear",
    "over",
    "finished",
    "skins",
    "levels",
    "sound",
    "records",
    "achievements",
    "name",
    "devgate",
    "devpanel",
)

EXPECTED_TARGETS = {
    "menu": ("playing", "clear", "over", "finished", "skins", "levels", "sound", "records", "achievements", "name", "devgate", "devpanel"),
    "playing": ("paused", "clear", "over", "finished"),
    "paused": ("playing", "sound", "menu"),
    "clear": ("playing", "menu"),
    "over": ("playing", "menu"),
    "finished": ("playing", "records"),
    "skins": ("playing", "menu"),
    "levels": ("playing", "menu"),
    "sound": ("playing", "menu"),
    "records": ("playing", "achievements", "menu"),
    "achievements": ("playing", "records", "menu"),
    "name": ("playing", "menu"),
    "devgate": ("playing", "devpanel", "menu"),
    "devpanel": ("playing", "menu"),
}

EXPECTED_MODES = {
    "menu": "MENU",
    "playing": "RUNNING",
    "paused": "PAUSED",
    "clear": "RUNNING",
    "over": "GAME_OVER",
    "finished": "RUNNING",
    "skins": "CHARACTER_SELECT",
    "levels": "LEVEL_SELECT",
    "sound": "PAUSED",
    "records": "ACHIEVEMENTS",
    "achievements": "ACHIEVEMENTS",
    "name": "CHARACTER_SELECT",
    "devgate": "DEV_MODE",
    "devpanel": "DEV_MODE",
}

EXPECTED_PLAYER_STATES = (
    "grounded",
    "jumping",
    "double_jumping",
    "falling",
    "gliding",
    "dashing",
    "hit",
    "victory",
)

REQUIRED_PLAYER_EDGES = {
    ("grounded", "jump", "jumping"),
    ("jumping", "jump", "double_jumping"),
    ("falling", "jump", "double_jumping"),
    ("gliding", "jump", "double_jumping"),
    ("jumping", "jump_apex", "falling"),
    ("double_jumping", "jump_apex", "falling"),
    ("falling", "glide_start", "gliding"),
    ("gliding", "glide_end", "falling"),
    ("grounded", "dash_start", "dashing"),
    ("dashing", "dash_end", "grounded"),
    ("grounded", "damage", "hit"),
    ("hit", "recover", "grounded"),
    ("grounded", "session_complete", "victory"),
    ("victory", "reset", "grounded"),
}


def quoted_values(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"['\"]([^'\"]+)['\"]", text))


def require_match(pattern: str, text: str, label: str, flags: int = 0) -> re.Match[str]:
    match = re.search(pattern, text, flags)
    if not match:
        raise ValueError(f"missing_contract:{label}")
    return match


def parse_contract(source: str) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]], dict[str, str]]:
    state_block = require_match(
        r"export const GAME_SESSION_STATES\s*=\s*Object\.freeze\(\[(.*?)\]\s*as const\)\s*;",
        source,
        "state_list",
        re.DOTALL,
    ).group(1)
    states = quoted_values(state_block)

    target_block = require_match(
        r"export const GAME_SESSION_TRANSITION_TARGETS.*?Object\.freeze\(\{(.*?)\}\)\s*;",
        source,
        "transition_table",
        re.DOTALL,
    ).group(1)
    targets: dict[str, tuple[str, ...]] = {}
    for state in states:
        row = require_match(
            rf"^\s*{re.escape(state)}\s*:\s*frozenTargets\((.*?)\)\s*,?\s*$",
            target_block,
            f"transition_row:{state}",
            re.MULTILINE,
        ).group(1)
        targets[state] = quoted_values(row)

    mode_block = require_match(
        r"const GAME_SESSION_MODE_BY_STATE.*?Object\.freeze\(\{(.*?)\}\)\s*;",
        source,
        "mode_table",
        re.DOTALL,
    ).group(1)
    modes: dict[str, str] = {}
    for state in states:
        value = require_match(
            rf"^\s*{re.escape(state)}\s*:\s*['\"]([^'\"]+)['\"]\s*,?\s*$",
            mode_block,
            f"mode_row:{state}",
            re.MULTILINE,
        ).group(1)
        modes[state] = value

    return states, targets, modes


def validate_player_contract(project_root: Path, errors: list[str]) -> tuple[int, int]:
    player_contract_path = (
        project_root
        / "docs"
        / "global_modernization"
        / "v3"
        / "M03"
        / "player_state_machine.yaml"
    )
    payload = json.loads(player_contract_path.read_text(encoding="utf-8"))
    if set(payload) != {"schemaVersion", "initialState", "states", "transitions"}:
        errors.append("player_contract_topology")
    if payload.get("schemaVersion") != 1:
        errors.append("player_contract_schema_version")
    states = tuple(payload.get("states", ()))
    if states != EXPECTED_PLAYER_STATES:
        errors.append("player_contract_states")
    if payload.get("initialState") != "grounded":
        errors.append("player_contract_initial_state")
    if len(states) != len(set(states)):
        errors.append("player_contract_duplicate_states")

    transitions = payload.get("transitions")
    if not isinstance(transitions, list):
        errors.append("player_contract_transitions_type")
        return len(states), 0

    edges: set[tuple[str, str, str]] = set()
    identities: set[tuple[str, str, str, str]] = set()
    allowed_keys = {"from", "event", "to", "guard", "actions"}
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            errors.append(f"player_transition_type:{index}")
            continue
        if not {"from", "event", "to"}.issubset(transition):
            errors.append(f"player_transition_required:{index}")
            continue
        if not set(transition).issubset(allowed_keys):
            errors.append(f"player_transition_extra_keys:{index}")
        source = transition["from"]
        event = transition["event"]
        target = transition["to"]
        guard = transition.get("guard", "")
        actions = transition.get("actions", [])
        if source not in states or target not in states:
            errors.append(f"player_transition_unknown_state:{index}")
        if not isinstance(event, str) or not event:
            errors.append(f"player_transition_event:{index}")
        if "guard" in transition and not isinstance(guard, str):
            errors.append(f"player_transition_guard:{index}")
        if not isinstance(actions, list) or any(not isinstance(action, str) for action in actions):
            errors.append(f"player_transition_actions:{index}")
        identity = (source, event, target, guard)
        if identity in identities:
            errors.append(f"player_transition_duplicate:{index}")
        identities.add(identity)
        edges.add((source, event, target))

    missing_edges = sorted(REQUIRED_PLAYER_EDGES - edges)
    if missing_edges:
        errors.append(f"player_transition_missing_edges:{missing_edges!r}")
    for state in states:
        if not any(source == state for source, _, _ in edges):
            errors.append(f"player_state_without_outgoing:{state}")
        if state != "grounded" and not any(target == state for _, _, target in edges):
            errors.append(f"player_state_without_incoming:{state}")
    return len(states), len(transitions)


def validate(project_root: Path) -> dict[str, object]:
    contract_path = project_root / "assets" / "scripts" / "gameplay" / "state" / "GameSessionState.ts"
    game_root_path = project_root / "assets" / "scripts" / "GameRoot.ts"
    contract_source = contract_path.read_text(encoding="utf-8")
    game_root_source = game_root_path.read_text(encoding="utf-8")
    states, targets, modes = parse_contract(contract_source)

    errors: list[str] = []
    if states != EXPECTED_STATES:
        errors.append(f"state_list_mismatch:{states!r}")
    if targets != EXPECTED_TARGETS:
        errors.append("transition_table_mismatch")
    if modes != EXPECTED_MODES:
        errors.append("mode_table_mismatch")

    required_contract_patterns = {
        "state_list_freeze": r"GAME_SESSION_STATES\s*=\s*Object\.freeze\(",
        "nested_target_freeze": r"return Object\.freeze\(states\.slice\(\)\)",
        "idempotence": r"return from === to \|\| GAME_SESSION_TRANSITION_TARGETS\[from\]\.indexOf\(to\) >= 0",
        "deterministic_rejection": r"code:\s*['\"]invalid_transition['\"]",
        "changed_result": r"changed:\s*from !== to",
    }
    for label, pattern in required_contract_patterns.items():
        if not re.search(pattern, contract_source):
            errors.append(f"missing_contract:{label}")

    required_integration_patterns = {
        "typed_state_alias": r"type State = GameSessionState\s*;",
        "typed_transition_result": r"private transitionTo\(next: State, reason = 'runtime'\): GameSessionTransitionResult",
        "contract_evaluation": r"evaluateGameSessionTransition\(prev, next, reason\)",
        "deterministic_reject_log": r"MTR_FSM_REJECT code=\$\{transition\.code\}",
    }
    for label, pattern in required_integration_patterns.items():
        if not re.search(pattern, game_root_source):
            errors.append(f"missing_integration:{label}")

    state_writer_count = len(re.findall(r"this\.state\s*=(?!=)", game_root_source))
    if state_writer_count != 1:
        errors.append(f"state_writer_count:{state_writer_count}")

    player_state_count, player_transition_count = validate_player_contract(project_root, errors)

    accepted_transitions = 0
    rejected_transitions = 0
    for source_state in EXPECTED_STATES:
        for target_state in EXPECTED_STATES:
            if source_state == target_state or target_state in EXPECTED_TARGETS[source_state]:
                accepted_transitions += 1
            else:
                rejected_transitions += 1

    return {
        "status": "PASS" if not errors else "FAIL",
        "state_count": len(states),
        "accepted_transitions": accepted_transitions,
        "rejected_transitions": rejected_transitions,
        "idempotent_transitions": len(states),
        "state_writer_count": state_writer_count,
        "player_state_count": player_state_count,
        "player_transition_count": player_transition_count,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    try:
        result = validate(Path(args.project_root).resolve())
    except (OSError, ValueError) as exc:
        result = {
            "status": "FAIL",
            "errors": [f"{type(exc).__name__}:{exc}"],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
