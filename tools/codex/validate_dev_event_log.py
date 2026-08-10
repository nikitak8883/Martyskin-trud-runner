#!/usr/bin/env python3
"""Cross-platform structural validator for the pure M03.3A DevEvent contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any


EXPECTED_CODES = (
    "session.transition.accepted",
    "session.transition.rejected",
    "session.reset.begin",
    "session.reset.end",
    "session.epoch.changed",
    "input.action",
    "collision.event",
    "powerup.event",
    "asset.load.start",
    "asset.load.complete",
    "asset.load.error",
    "qa.marker",
)

EXPECTED_DEFAULTS: dict[str, bool | int] = {
    "enabled": False,
    "capacity": 256,
    "maxStateLength": 64,
    "maxReasonLength": 96,
    "maxStringLength": 256,
    "maxArrayLength": 24,
    "maxObjectKeys": 24,
    "maxDepth": 4,
    "maxPayloadNodes": 512,
    "maxPayloadBytes": 16384,
    "maxExportBytes": 65536,
}

EXPECTED_LIMITS: dict[str, tuple[int, int]] = {
    "capacity": (0, 4096),
    "maxStateLength": (0, 256),
    "maxReasonLength": (0, 512),
    "maxStringLength": (0, 4096),
    "maxArrayLength": (0, 256),
    "maxObjectKeys": (0, 256),
    "maxDepth": (0, 16),
    "maxPayloadNodes": (1, 4096),
    "maxPayloadBytes": (2, 262144),
    "maxExportBytes": (2, 1048576),
}

CAMEL_TO_SCHEMA = {
    "capacity": "capacity",
    "maxStateLength": "max_state_length",
    "maxReasonLength": "max_reason_length",
    "maxStringLength": "max_string_length",
    "maxArrayLength": "max_array_length",
    "maxObjectKeys": "max_object_keys",
    "maxDepth": "max_depth",
    "maxPayloadNodes": "max_payload_nodes",
    "maxPayloadBytes": "max_payload_bytes",
    "maxExportBytes": "max_export_bytes",
}


def require_match(pattern: str, text: str, label: str, flags: int = 0) -> re.Match[str]:
    match = re.search(pattern, text, flags)
    if not match:
        raise ValueError(f"missing_contract:{label}")
    return match


def quoted_values(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"['\"]([^'\"]+)['\"]", text))


def parse_defaults(source: str) -> dict[str, bool | int]:
    block = require_match(
        r"DEFAULT_DEV_EVENT_LOG_CONFIG\s*:\s*DevEventLogConfig\s*=\s*Object\.freeze\(\{(.*?)\}\)\s*;",
        source,
        "default_config",
        re.DOTALL,
    ).group(1)
    result: dict[str, bool | int] = {}
    for key, raw_value in re.findall(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*:\s*(true|false|[0-9]+)\s*,\s*$", block, re.MULTILINE):
        if raw_value == "true":
            result[key] = True
        elif raw_value == "false":
            result[key] = False
        else:
            result[key] = int(raw_value)
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_meta(project_root: Path, errors: list[str]) -> int:
    expected = {
        project_root / "assets" / "scripts" / "qa.meta": ("1.2.0", "directory"),
        project_root / "assets" / "scripts" / "qa" / "DevEventTypes.ts.meta": ("4.0.24", "typescript"),
        project_root / "assets" / "scripts" / "qa" / "DevEventLog.ts.meta": ("4.0.24", "typescript"),
    }
    target_uuids: dict[str, Path] = {}
    for path, (version, importer) in expected.items():
        try:
            document = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"meta_read:{path.relative_to(project_root).as_posix()}:{type(exc).__name__}")
            continue
        if document.get("ver") != version:
            errors.append(f"meta_version:{path.relative_to(project_root).as_posix()}")
        if document.get("importer") != importer:
            errors.append(f"meta_importer:{path.relative_to(project_root).as_posix()}")
        if document.get("imported") is not True:
            errors.append(f"meta_imported:{path.relative_to(project_root).as_posix()}")
        raw_uuid = document.get("uuid")
        try:
            normalized = str(uuid.UUID(raw_uuid))
        except (AttributeError, TypeError, ValueError):
            errors.append(f"meta_uuid:{path.relative_to(project_root).as_posix()}")
            continue
        target_uuids[normalized] = path

    occurrences: dict[str, list[Path]] = {value: [] for value in target_uuids}
    for path in (project_root / "assets").rglob("*.meta"):
        try:
            raw_uuid = load_json(path).get("uuid")
            normalized = str(uuid.UUID(raw_uuid))
        except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
            continue
        if normalized in occurrences:
            occurrences[normalized].append(path)
    for normalized, paths in occurrences.items():
        if len(paths) != 1:
            rendered = ",".join(path.relative_to(project_root).as_posix() for path in paths)
            errors.append(f"meta_uuid_occurrences:{normalized}:{rendered}")
    if len(target_uuids) != len(expected):
        errors.append("meta_uuid_targets_not_unique")
    return len(expected)


def validate(project_root: Path) -> dict[str, object]:
    types_path = project_root / "assets" / "scripts" / "qa" / "DevEventTypes.ts"
    log_path = project_root / "assets" / "scripts" / "qa" / "DevEventLog.ts"
    test_path = project_root / "tools" / "codex" / "test-dev-event-log.js"
    game_root_path = project_root / "assets" / "scripts" / "GameRoot.ts"
    static_gate_path = project_root / "tools" / "codex" / "quality-gate" / "static-gates.json"
    event_schema_path = project_root / "docs" / "global_modernization" / "v4" / "library" / "schemas" / "dev_event.schema.json"
    config_schema_path = project_root / "docs" / "global_modernization" / "v4" / "library" / "schemas" / "dev_event_log_config.schema.json"

    types_source = types_path.read_text(encoding="utf-8")
    log_source = log_path.read_text(encoding="utf-8")
    test_source = test_path.read_text(encoding="utf-8")
    game_root_source = game_root_path.read_text(encoding="utf-8")
    static_gate = load_json(static_gate_path)
    event_schema = load_json(event_schema_path)
    config_schema = load_json(config_schema_path)
    errors: list[str] = []

    code_block = require_match(
        r"DEV_EVENT_CODES\s*=\s*Object\.freeze\(\[(.*?)\]\s*as const\)\s*;",
        types_source,
        "event_codes",
        re.DOTALL,
    ).group(1)
    codes = quoted_values(code_block)
    if codes != EXPECTED_CODES:
        errors.append(f"event_codes:{codes!r}")
    if tuple(event_schema["properties"]["code"]["enum"]) != EXPECTED_CODES:
        errors.append("event_schema_code_parity")

    defaults = parse_defaults(types_source)
    if defaults != EXPECTED_DEFAULTS:
        errors.append(f"default_config:{defaults!r}")

    event_properties = event_schema["properties"]
    expected_schema_defaults = {
        "maxStateLength": event_properties["state"]["maxLength"],
        "maxReasonLength": event_properties["reason"]["maxLength"],
        "maxStringLength": event_schema["$defs"]["jsonValue"]["oneOf"][1]["maxLength"],
        "maxArrayLength": event_schema["$defs"]["jsonValue"]["oneOf"][2]["maxItems"],
        "maxObjectKeys": event_schema["$defs"]["jsonValue"]["oneOf"][3]["maxProperties"],
        "maxDepth": event_schema["x-mtr-runtime-max-depth"],
        "maxPayloadNodes": event_schema["x-mtr-runtime-max-payload-nodes"],
        "maxPayloadBytes": event_schema["x-mtr-runtime-max-payload-bytes"],
        "maxExportBytes": event_schema["x-mtr-runtime-max-export-bytes"],
    }
    for key, actual in expected_schema_defaults.items():
        if defaults.get(key) != actual:
            errors.append(f"event_schema_default:{key}:{actual!r}")

    config_properties = config_schema["properties"]
    for key, (minimum, maximum) in EXPECTED_LIMITS.items():
        schema_key = CAMEL_TO_SCHEMA[key]
        schema_property = config_properties[schema_key]
        if schema_property.get("minimum") != minimum or schema_property.get("maximum") != maximum:
            errors.append(f"config_schema_limit:{schema_key}")
        pattern = (
            rf"{re.escape(key)}\s*:\s*Object\.freeze\(\["
            rf"{minimum}\s*,\s*{maximum}\]\s*as const\)"
        )
        if not re.search(pattern, log_source):
            errors.append(f"runtime_config_limit:{key}")

    required_type_patterns = {
        "record": r"export interface DevEventRecord",
        "input": r"export interface DevEventInput",
        "config": r"export interface DevEventLogConfig",
        "json_value": r"export type DevJsonValue",
        "code_guard": r"export function isDevEventCode\(value: unknown\): value is DevEventCode",
        "default_disabled": r"enabled\s*:\s*false",
    }
    required_log_patterns = {
        "config_plain_object": r"DevEventLog config must be a plain object",
        "descriptor_helper": r"function ownPropertyDescriptors\(value: object\): PropertyDescriptorMap",
        "descriptor_names": r"Object\.getOwnPropertyNames\(value\)",
        "descriptor_read": r"Object\.getOwnPropertyDescriptor\(value, key\)",
        "config_descriptors": r"descriptors = ownPropertyDescriptors\(input\)",
        "config_unknown_key": r"Unknown DevEventLog config key",
        "input_plain_object": r"DevEvent input must be a plain object",
        "input_descriptors": r"descriptors = ownPropertyDescriptors\(input\)",
        "input_unknown_key": r"Unknown DevEvent input key",
        "input_required_own_fields": r"DevEvent input requires own data property",
        "finite_numbers": r"Number\.isFinite\(value\)",
        "safe_integers": r"Number\.isSafeInteger\(value\)",
        "plain_object_guard": r"prototype !== Object\.prototype && prototype !== null",
        "payload_descriptors": r"descriptors = ownPropertyDescriptors\(value\)",
        "enumerable_only": r"descriptors\[key\]\?\.enumerable === true",
        "null_prototype": r"Object\.create\(null\)",
        "depth_budget": r"depth >= config\.maxDepth",
        "node_budget": r"remainingNodes: config\.maxPayloadNodes",
        "payload_byte_budget": r"maxPayloadBytes",
        "utf8_counter": r"function utf8ByteLength\(value: string\): number",
        "minimum_byte_fallback": r"JSON\.stringify\(''\) is exactly two UTF-8 bytes",
        "ring_buffer": r"private readonly buffer: Array<DevEventRecord \| undefined>",
        "ring_allocation": r"new Array<DevEventRecord \| undefined>\(this\.config\.capacity\)",
        "ring_eviction": r"this\.start = \(this\.start \+ 1\) % this\.config\.capacity",
        "immutable_event": r"const event: DevEventRecord = Object\.freeze\(\{",
        "immutable_snapshot": r"return Object\.freeze\(result\)",
        "clear_preserves_sequence": r"public clear\(\): void \{\s*this\.buffer\.fill\(undefined\);\s*this\.start = 0;\s*this\.length = 0;\s*\}",
        "event_bound": r"Math\.min\(maxEvents, snapshot\.length\)",
        "export_byte_bound": r"bytes \+ addition > maxBytes",
        "stable_object_keys": r"Object\.keys\(descriptors\).*?\.sort\(\)",
        "disabled_short_circuit": r"if \(!this\.config\.enabled \|\| this\.config\.capacity === 0\) return undefined",
    }
    for label, pattern in required_type_patterns.items():
        if not re.search(pattern, types_source, re.DOTALL):
            errors.append(f"missing_types_contract:{label}")
    for label, pattern in required_log_patterns.items():
        if not re.search(pattern, log_source, re.DOTALL):
            errors.append(f"missing_log_contract:{label}")

    forbidden_patterns = {
        "cocos": r"from\s+['\"]cc['\"]|require\s*\(\s*['\"]cc['\"]\s*\)",
        "console": r"\bconsole\s*\.",
        "clock": r"\bDate\s*\.|\bperformance\s*\.",
        "random": r"\bMath\.random\s*\(",
        "storage": r"\b(?:localStorage|sessionStorage)\b",
        "network": r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b",
        "node": r"from\s+['\"](?:fs|path|node:)|require\s*\(",
        "linear_ring_mutation": r"\.shift\s*\(|\.splice\s*\(",
    }
    combined_source = types_source + "\n" + log_source
    for label, pattern in forbidden_patterns.items():
        if re.search(pattern, combined_source):
            errors.append(f"forbidden_runtime_dependency:{label}")
    direct_wiring = re.search(
        r"new\s+DevEventLog\b|new\s+LifecycleEpoch\b|\./qa/(?:DevEventLog|DevEventTypes|LifecycleEpoch)",
        game_root_source,
    )
    if direct_wiring:
        errors.append("game_root_direct_runtime_wiring")
    if len(re.findall(r"new\s+GameRootDevEventAdapter\s*\(", game_root_source)) != 1:
        errors.append("game_root_adapter_count")
    if re.search(r"eventsEnabled:\s*DEBUG\b", game_root_source) is None:
        errors.append("game_root_adapter_not_debug_bound")

    required_test_markers = (
        "strictTypeScript",
        "disabled_and_zero_capacity",
        "config_boundaries",
        "input accessors must never execute",
        "ring_order_and_eviction",
        "clear_and_sequence",
        "immutable_snapshot_and_copy",
        "accessors_and_enumerability",
        "payload_utf8_byte_bound",
        "stable_serialization",
        "export_event_and_byte_bounds",
        "gameRootWired: 'M03.3C_ADAPTER_ONLY'",
    )
    for marker in required_test_markers:
        if marker not in test_source:
            errors.append(f"missing_behavioral_test:{marker}")

    matching_steps = [step for step in static_gate.get("steps", []) if step.get("id") == "dev-event-log-contracts"]
    expected_step = {
        "id": "dev-event-log-contracts",
        "mandatory": True,
        "enabled": True,
        "executable": "python",
        "arguments": ["-B", "tools/codex/validate_dev_event_log.py", "--project-root", "."],
        "working_directory": ".",
        "timeout_seconds": 60,
        "expected_exit_codes": [0],
    }
    if matching_steps != [expected_step]:
        errors.append("static_gate_registration")

    meta_count = validate_meta(project_root, errors)
    return {
        "status": "PASS" if not errors else "FAIL",
        "event_code_count": len(codes),
        "default_capacity": defaults.get("capacity"),
        "static_gate_steps": len(static_gate.get("steps", [])),
        "meta_contracts": meta_count,
        "game_root_wiring": "M03.3C_ADAPTER_ONLY" if not direct_wiring else "DIRECT_REJECTED",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    try:
        result = validate(Path(args.project_root).resolve())
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        result = {
            "status": "FAIL",
            "errors": [f"{type(exc).__name__}:{exc}"],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
