#!/usr/bin/env python3
"""Validate the MTR v4 execution DAG against the canonical 95-package ledger."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict, deque
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
  import yaml
except ImportError as exc:  # pragma: no cover - canonical bootstrap supplies PyYAML
    raise SystemExit("PyYAML is required through the pinned MTR quality-gate environment") from exc

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - canonical bootstrap supplies jsonschema
    raise SystemExit("jsonschema is required through the pinned MTR quality-gate environment") from exc


VALID_UNIT_STATUSES = {"complete", "ready", "planned", "blocked", "conditional"}
INFRASTRUCTURE_UNITS = {"RDX-01", "TC-01"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_SCHEMA = PROJECT_ROOT / "docs" / "global_modernization" / "v4" / "library" / "schemas" / "execution_unit_index.schema.json"


def add_finding(findings: list[dict[str, Any]], code: str, field: str, expected: Any, actual: Any) -> None:
    findings.append({"code": code, "field": field, "expected": expected, "actual": actual})


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_source_ledger(path: Path) -> dict[str, dict[str, Any]]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("modules"), dict):
        raise ValueError("source work-package ledger must contain a modules object")
    packages: dict[str, dict[str, Any]] = {}
    for module_id, module in value["modules"].items():
        if not isinstance(module, dict) or not isinstance(module.get("work_packages"), list):
            raise ValueError(f"module {module_id} must contain a work_packages array")
        for package in module["work_packages"]:
            if not isinstance(package, dict):
                raise ValueError(f"invalid package object in {module_id}")
            package_id = package.get("id")
            if not isinstance(package_id, str):
                raise ValueError(f"invalid package id in {module_id}")
            if package_id in packages:
                raise ValueError(f"duplicate source package id: {package_id}")
            if package.get("status") not in {"complete", "pending", "blocked", "conditional"}:
                raise ValueError(f"invalid source package status: {package_id}")
            packages[package_id] = {"module": module_id, **package}
    return packages


def plan_schema_findings(plan: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    findings: list[dict[str, Any]] = []
    for error in sorted(validator.iter_errors(plan), key=lambda item: [str(part) for part in item.absolute_path]):
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        add_finding(findings, "PLAN_SCHEMA_VIOLATION", path, error.validator, error.message)
    return findings


def dependency_cycle(units: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {unit_id: 0 for unit_id in units}
    for unit_id, unit in units.items():
        for dependency in [*unit.get("depends_on", []), *unit.get("optional_dependencies", [])]:
            if dependency not in units:
                continue
            outgoing[dependency].append(unit_id)
            indegree[unit_id] += 1
    queue = deque(sorted(unit_id for unit_id, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for follower in sorted(outgoing[current]):
            indegree[follower] -= 1
            if indegree[follower] == 0:
                queue.append(follower)
    cyclic = sorted(unit_id for unit_id, degree in indegree.items() if degree > 0)
    return order, cyclic


def validate(
    plan: dict[str, Any],
    source_packages: dict[str, dict[str, Any]],
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings = plan_schema_findings(plan, schema or load_json(DEFAULT_PLAN_SCHEMA))
    if findings:
        return {
            "schema_version": 1,
            "status": "FAIL",
            "counts": {"source_packages": len(source_packages), "execution_units": 0, "dependency_cycles": 0, "findings": len(findings)},
            "topological_order": [],
            "findings": findings,
        }
    raw_units = plan.get("units")
    if not isinstance(raw_units, list):
        return {"status": "FAIL", "findings": [{"code": "UNITS_NOT_ARRAY", "field": "units", "expected": "array", "actual": type(raw_units).__name__}]}

    units: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for index, unit in enumerate(raw_units):
        if not isinstance(unit, dict):
            add_finding(findings, "UNIT_NOT_OBJECT", f"units[{index}]", "object", type(unit).__name__)
            continue
        unit_id = unit.get("id")
        if not isinstance(unit_id, str) or not unit_id:
            add_finding(findings, "INVALID_UNIT_ID", f"units[{index}].id", "non-empty string", unit_id)
            continue
        if unit_id in units:
            duplicate_ids.append(unit_id)
        else:
            units[unit_id] = unit
    for unit_id in sorted(set(duplicate_ids)):
        add_finding(findings, "DUPLICATE_UNIT_ID", "units.id", "unique", unit_id)

    decision_ids: set[str] = set()
    for item in plan["decisions"]:
        decision_id = item["id"]
        if decision_id in decision_ids:
            add_finding(findings, "DUPLICATE_DECISION_ID", "decisions.id", "unique", decision_id)
        decision_ids.add(decision_id)
    if set(plan["status_values"]) != VALID_UNIT_STATUSES:
        add_finding(findings, "STATUS_VALUES_MISMATCH", "status_values", sorted(VALID_UNIT_STATUSES), plan["status_values"])
    coverage: dict[str, list[str]] = defaultdict(list)
    for unit_id, unit in units.items():
        status = unit.get("status")
        if status not in VALID_UNIT_STATUSES:
            add_finding(findings, "INVALID_UNIT_STATUS", f"units.{unit_id}.status", sorted(VALID_UNIT_STATUSES), status)
        dependencies = unit.get("depends_on", [])
        optional = unit.get("optional_dependencies", [])
        for label, values in (("depends_on", dependencies), ("optional_dependencies", optional)):
            if not isinstance(values, list):
                add_finding(findings, "DEPENDENCIES_NOT_ARRAY", f"units.{unit_id}.{label}", "array", type(values).__name__)
                continue
            for dependency in values:
                if dependency == unit_id:
                    add_finding(findings, "SELF_DEPENDENCY", f"units.{unit_id}.{label}", "different unit", dependency)
                elif dependency not in units:
                    add_finding(findings, "UNKNOWN_DEPENDENCY", f"units.{unit_id}.{label}", "known unit id", dependency)
        blockers = unit.get("blockers", [])
        if status == "blocked" and not blockers:
            add_finding(findings, "BLOCKED_WITHOUT_BLOCKER", f"units.{unit_id}.blockers", "non-empty", blockers)
        for blocker in blockers:
            if blocker not in decision_ids:
                add_finding(findings, "UNKNOWN_BLOCKER", f"units.{unit_id}.blockers", "known decision id", blocker)
        if status == "conditional" and not unit.get("condition"):
            add_finding(findings, "CONDITIONAL_WITHOUT_CONDITION", f"units.{unit_id}.condition", "non-empty", unit.get("condition"))
        if status == "ready":
            unresolved = [dependency for dependency in dependencies if units.get(dependency, {}).get("status") != "complete"]
            if unresolved:
                add_finding(findings, "READY_WITH_UNRESOLVED_DEPENDENCY", f"units.{unit_id}.depends_on", "all complete", unresolved)

        package_ids = unit.get("source_packages", [])
        if not isinstance(package_ids, list):
            add_finding(findings, "SOURCE_PACKAGES_NOT_ARRAY", f"units.{unit_id}.source_packages", "array", type(package_ids).__name__)
            continue
        if not package_ids and unit_id not in INFRASTRUCTURE_UNITS:
            add_finding(findings, "SOURCELESS_NON_INFRASTRUCTURE_UNIT", f"units.{unit_id}.source_packages", "non-empty", package_ids)
        for package_id in package_ids:
            source = source_packages.get(package_id)
            if source is None:
                add_finding(findings, "UNKNOWN_SOURCE_PACKAGE", f"units.{unit_id}.source_packages", "known source package", package_id)
                continue
            coverage[package_id].append(unit_id)
            source_status = source.get("status")
            if source_status == "complete":
                add_finding(findings, "COMPLETE_SOURCE_REPLANNED", f"units.{unit_id}.source_packages", "remaining package", package_id)
            if status == "conditional" and source_status != "conditional":
                add_finding(findings, "CONDITIONAL_UNIT_HAS_MANDATORY_SOURCE", f"units.{unit_id}.source_packages", "conditional source", package_id)
            if status != "conditional" and source_status == "conditional":
                add_finding(findings, "MANDATORY_UNIT_HAS_CONDITIONAL_SOURCE", f"units.{unit_id}.source_packages", "mandatory source", package_id)

    for package_id, unit_ids in sorted(coverage.items()):
        if len(unit_ids) > 1:
            without_slice = [unit_id for unit_id in unit_ids if not units[unit_id].get("source_slice")]
            if without_slice:
                add_finding(findings, "DUPLICATE_COVERAGE_WITHOUT_SLICE", f"source.{package_id}", "source_slice on every unit", without_slice)

    mandatory_remaining = {package_id for package_id, item in source_packages.items() if item.get("status") in {"pending", "blocked"}}
    conditional_remaining = {package_id for package_id, item in source_packages.items() if item.get("status") == "conditional"}
    missing_mandatory = sorted(mandatory_remaining - coverage.keys())
    missing_conditional = sorted(conditional_remaining - coverage.keys())
    if missing_mandatory:
        add_finding(findings, "MISSING_MANDATORY_SOURCE_COVERAGE", "source_coverage", sorted(mandatory_remaining), missing_mandatory)
    if missing_conditional:
        add_finding(findings, "MISSING_CONDITIONAL_SOURCE_COVERAGE", "source_coverage", sorted(conditional_remaining), missing_conditional)

    source_counts = Counter(str(item.get("status")) for item in source_packages.values())
    expected_source_ledger = {
        "total": len(source_packages),
        "complete": source_counts["complete"],
        "pending": source_counts["pending"],
        "blocked": source_counts["blocked"],
        "conditional": source_counts["conditional"],
        "mandatory_total": len(source_packages) - source_counts["conditional"],
        "mandatory_remaining": len(mandatory_remaining),
    }
    if plan.get("source_ledger") != expected_source_ledger:
        add_finding(findings, "SOURCE_LEDGER_COUNT_MISMATCH", "source_ledger", expected_source_ledger, plan.get("source_ledger"))

    unit_counts = Counter(str(unit.get("status")) for unit in units.values())
    mandatory_total = len(units) - unit_counts["conditional"]
    expected_execution_ledger = {
        "mandatory_units_total": mandatory_total,
        "complete": unit_counts["complete"],
        "ready": unit_counts["ready"],
        "planned": unit_counts["planned"],
        "blocked": unit_counts["blocked"],
        "mandatory_remaining": mandatory_total - unit_counts["complete"],
        "conditional_units_total": unit_counts["conditional"],
    }
    if plan.get("execution_ledger") != expected_execution_ledger:
        add_finding(findings, "EXECUTION_LEDGER_COUNT_MISMATCH", "execution_ledger", expected_execution_ledger, plan.get("execution_ledger"))

    topological_order, cyclic = dependency_cycle(units)
    if cyclic:
        add_finding(findings, "DEPENDENCY_CYCLE", "units.depends_on", "acyclic", cyclic)

    return {
        "schema_version": 1,
        "status": "PASS" if not findings else "FAIL",
        "counts": {
            "source_packages": len(source_packages),
            "mandatory_source_covered": len(mandatory_remaining & coverage.keys()),
            "conditional_source_covered": len(conditional_remaining & coverage.keys()),
            "execution_units": len(units),
            "dependency_cycles": 1 if cyclic else 0,
            "findings": len(findings),
        },
        "topological_order": topological_order,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--work-packages", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=DEFAULT_PLAN_SCHEMA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate(
            load_json(args.plan.resolve()),
            load_source_ledger(args.work_packages.resolve()),
            load_json(args.schema.resolve()),
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        report = {"schema_version": 1, "status": "FAIL", "counts": {"findings": 1}, "findings": [{"code": "VALIDATOR_INPUT_ERROR", "detail": f"{type(exc).__name__}:{exc}"}]}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
