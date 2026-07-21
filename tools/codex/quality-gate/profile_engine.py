#!/usr/bin/env python3
"""Semantic profile catalog validation and explicit scope resolution for M01.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EXPECTED_PROFILES = {"D4", "P4", "M2_PLUS", "QA7", "RC2"}
EXPECTED_PROFILE_SHAPES = {
    "D4": {"cycles": ("d4",), "slots": 4, "conditions": frozenset()},
    "P4": {"cycles": ("p4",), "slots": 4, "conditions": frozenset()},
    "M2_PLUS": {
        "cycles": ("pass_a", "pass_b", "focused_recovery"),
        "slots": 12,
        "conditions": frozenset({"high_risk_recovery"}),
    },
    "QA7": {"cycles": ("qa7",), "slots": 7, "conditions": frozenset()},
    "RC2": {
        "cycles": ("rc1", "rc2", "parity"),
        "slots": 20,
        "conditions": frozenset({"play_store_target", "physical_device_authorized"}),
    },
}


class ProfileError(ValueError):
    """Typed, user-actionable profile configuration error."""

    def __init__(self, code: str, field: str, expected: Any, actual: Any, suggested_fix: str) -> None:
        super().__init__(f"{code}: {field}: expected {expected!r}, got {actual!r}")
        self.code = code
        self.field = field
        self.expected = expected
        self.actual = actual
        self.suggested_fix = suggested_fix

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True)
class ResolvedSlot:
    id: str
    gate_id: str
    cycle_id: str
    domain: str
    requirement: str
    effective_mandatory: bool
    required_target_platforms: tuple[str, ...]
    applicability: dict[str, Any]
    report_path: str | None


@dataclass(frozen=True)
class ProfileResolution:
    profile_id: str
    description: str
    cycle_order: tuple[str, ...]
    slots: tuple[ResolvedSlot, ...]


def _unique_by(items: list[dict[str, Any]], key: str, field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        value = item[key]
        if value in result:
            raise ProfileError(
                "DUPLICATE_PROFILE_VALUE",
                field,
                f"unique {key} values",
                value,
                f"Remove or rename the duplicate {key}.",
            )
        result[value] = item
    return result


def validate_catalog(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate semantic invariants that JSON Schema cannot express."""

    profiles = _unique_by(document["profiles"], "id", "profiles.id")
    actual_profiles = set(profiles)
    if actual_profiles != EXPECTED_PROFILES:
        raise ProfileError(
            "PROFILE_SET_MISMATCH",
            "profiles.id",
            sorted(EXPECTED_PROFILES),
            sorted(actual_profiles),
            "Declare exactly D4, P4, M2_PLUS, QA7 and RC2.",
        )

    global_gate_ids: set[str] = set()
    for profile_id, profile in profiles.items():
        expected = EXPECTED_PROFILE_SHAPES[profile_id]
        cycles = tuple(profile["cycle_order"])
        if cycles != expected["cycles"]:
            raise ProfileError(
                "PROFILE_CYCLE_ORDER_MISMATCH",
                f"profiles.{profile_id}.cycle_order",
                list(expected["cycles"]),
                list(cycles),
                "Restore the canonical independent-cycle order.",
            )
        if len(profile["slots"]) != expected["slots"]:
            raise ProfileError(
                "PROFILE_SLOT_COUNT_MISMATCH",
                f"profiles.{profile_id}.slots",
                expected["slots"],
                len(profile["slots"]),
                "Restore every canonical gate/domain slot; do not silently weaken the profile.",
            )
        slots = _unique_by(profile["slots"], "id", f"profiles.{profile_id}.slots.id")
        profile_gate_ids = _unique_by(profile["slots"], "gate_id", f"profiles.{profile_id}.slots.gate_id")
        overlap = global_gate_ids.intersection(profile_gate_ids)
        if overlap:
            raise ProfileError(
                "GATE_ID_REUSED_ACROSS_PROFILES",
                f"profiles.{profile_id}.slots.gate_id",
                "globally unique child gate IDs",
                sorted(overlap),
                "Give every profile/cycle slot its own child gate identity.",
            )
        global_gate_ids.update(profile_gate_ids)
        used_cycles = {slot["cycle_id"] for slot in slots.values()}
        if used_cycles != set(cycles):
            raise ProfileError(
                "PROFILE_CYCLE_COVERAGE_MISMATCH",
                f"profiles.{profile_id}.slots.cycle_id",
                list(cycles),
                sorted(used_cycles),
                "Use every declared cycle exactly as part of the canonical profile.",
            )

        condition_ids: set[str] = set()
        for slot in slots.values():
            requirement = slot["requirement"]
            condition_id = slot.get("condition_id")
            if requirement == "conditional":
                condition_ids.add(condition_id)
            elif condition_id is not None:
                raise ProfileError(
                    "UNEXPECTED_CONDITION",
                    f"profiles.{profile_id}.slots.{slot['id']}.condition_id",
                    "condition only on a conditional slot",
                    condition_id,
                    "Remove the condition or mark the slot conditional.",
                )
            if "android-device" in slot["required_target_platforms"] and not (
                requirement == "conditional" and condition_id == "physical_device_authorized"
            ):
                raise ProfileError(
                    "PHYSICAL_DEVICE_POLICY_VIOLATION",
                    f"profiles.{profile_id}.slots.{slot['id']}.required_target_platforms",
                    "android-device only behind physical_device_authorized",
                    slot["required_target_platforms"],
                    "Use android-emulator by default or guard the device slot explicitly.",
                )
        if frozenset(condition_ids) != expected["conditions"]:
            raise ProfileError(
                "PROFILE_CONDITION_SET_MISMATCH",
                f"profiles.{profile_id}.slots.condition_id",
                sorted(expected["conditions"]),
                sorted(condition_ids),
                "Restore the canonical high-risk, Play-target and physical-device conditions.",
            )
    return profiles


def resolve_profile(
    config: dict[str, Any],
    scope: dict[str, Any],
    *,
    config_sha256: str,
    allow_physical_device: bool,
) -> ProfileResolution:
    """Resolve conditional applicability without treating N/A as an ordinary skip."""

    profiles = validate_catalog(config)
    profile_id = scope["profile_id"]
    profile = profiles[profile_id]
    if scope["profile_config_sha256"] != config_sha256:
        raise ProfileError(
            "PROFILE_CONFIG_HASH_MISMATCH",
            "scope.profile_config_sha256",
            config_sha256,
            scope["profile_config_sha256"],
            "Regenerate the invocation scope against the current canonical profile catalog.",
        )

    decisions = _unique_by(scope["condition_decisions"], "condition_id", "scope.condition_decisions.condition_id")
    bindings = _unique_by(scope["evidence_bindings"], "slot_id", "scope.evidence_bindings.slot_id")
    slots = _unique_by(profile["slots"], "id", f"profiles.{profile_id}.slots.id")
    expected_conditions = {
        slot["condition_id"] for slot in slots.values() if slot["requirement"] == "conditional"
    }
    if set(decisions) != expected_conditions:
        raise ProfileError(
            "CONDITION_DECISION_SET_MISMATCH",
            "scope.condition_decisions",
            sorted(expected_conditions),
            sorted(decisions),
            "Provide exactly one explicit decision for every conditional profile gate.",
        )
    unknown_bindings = set(bindings).difference(slots)
    if unknown_bindings:
        raise ProfileError(
            "UNKNOWN_EVIDENCE_SLOT",
            "scope.evidence_bindings.slot_id",
            sorted(slots),
            sorted(unknown_bindings),
            "Remove bindings that are not part of the selected profile.",
        )
    bound_paths: dict[str, str] = {}
    resolved: list[ResolvedSlot] = []
    for raw in profile["slots"]:
        slot_id = raw["id"]
        requirement = raw["requirement"]
        binding = bindings.get(slot_id)
        condition_id = raw.get("condition_id")
        if requirement == "conditional":
            decision = decisions[condition_id]
            if decision["applicable"]:
                if condition_id == "physical_device_authorized" and not allow_physical_device:
                    raise ProfileError(
                        "PHYSICAL_DEVICE_NOT_AUTHORIZED",
                        f"scope.condition_decisions.{condition_id}",
                        "explicit CLI authorization together with applicable=true",
                        False,
                        "Use emulator evidence or pass the explicit physical-device authorization switch.",
                    )
                applicability = {"status": "applicable", "condition_id": condition_id}
                effective_mandatory = True
                if binding is None:
                    report_path = None
                else:
                    report_path = binding["report_path"]
            else:
                if binding is not None:
                    raise ProfileError(
                        "NOT_APPLICABLE_SLOT_HAS_EVIDENCE",
                        f"scope.evidence_bindings.{slot_id}",
                        "no evidence binding for an explicitly N/A slot",
                        binding["report_path"],
                        "Remove the binding or mark the condition applicable.",
                    )
                applicability = {
                    "status": "not_applicable",
                    "condition_id": condition_id,
                    "reason_code": decision["reason_code"],
                    "reason": decision["reason"],
                }
                effective_mandatory = False
                report_path = None
        else:
            applicability = {"status": "applicable"}
            effective_mandatory = requirement == "mandatory"
            report_path = binding["report_path"] if binding is not None else None

        if report_path is not None:
            previous = bound_paths.get(report_path.casefold())
            if previous is not None:
                raise ProfileError(
                    "EVIDENCE_REPORT_PATH_REUSED",
                    f"scope.evidence_bindings.{slot_id}.report_path",
                    "a unique child report path per profile slot",
                    {"path": report_path, "already_bound_to": previous},
                    "Generate independent child evidence for each cycle and slot.",
                )
            bound_paths[report_path.casefold()] = slot_id

        resolved.append(
            ResolvedSlot(
                id=slot_id,
                gate_id=raw["gate_id"],
                cycle_id=raw["cycle_id"],
                domain=raw["domain"],
                requirement=requirement,
                effective_mandatory=effective_mandatory,
                required_target_platforms=tuple(raw["required_target_platforms"]),
                applicability=applicability,
                report_path=report_path,
            )
        )

    return ProfileResolution(
        profile_id=profile_id,
        description=profile["description"],
        cycle_order=tuple(profile["cycle_order"]),
        slots=tuple(resolved),
    )
