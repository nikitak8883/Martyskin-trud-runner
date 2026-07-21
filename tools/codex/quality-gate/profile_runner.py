#!/usr/bin/env python3
"""Fail-closed M01.4 profile evaluator over M01.3 quality-gate reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import runner
from profile_engine import ProfileError, ProfileResolution, ResolvedSlot, resolve_profile
from schema_engine import SchemaEngine, SchemaValidationError


PROFILE_CONFIG_SCHEMA = "quality_profile_config.schema.json"
PROFILE_SCOPE_SCHEMA = "quality_profile_scope.schema.json"
PROFILE_REPORT_SCHEMA = "quality_profile_report.schema.json"
CHILD_REPORT_SCHEMA = "quality_gate_report.schema.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_time(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProfileError(
            "INVALID_TIMESTAMP",
            field,
            "ISO-8601 timestamp with timezone",
            value,
            "Use an explicit UTC or offset-aware timestamp.",
        ) from exc
    if parsed.tzinfo is None:
        raise ProfileError(
            "INVALID_TIMESTAMP",
            field,
            "timezone-aware ISO-8601 timestamp",
            value,
            "Include Z or an explicit UTC offset.",
        )
    return parsed.astimezone(timezone.utc)


def _finding(
    code: str,
    severity: str,
    blocking: bool,
    slot_id: str | None,
    path: str,
    field: str,
    expected: Any,
    actual: Any,
    suggested_fix: str,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "blocking": blocking,
        "slot_id": slot_id,
        "path": path,
        "field": field,
        "expected": expected,
        "actual": actual,
        "suggested_fix": suggested_fix,
    }


def _record_snapshot(
    snapshots: dict[Path, tuple[str, runner.FileIdentity]],
    path: Path,
    label: str,
) -> runner.FileIdentity:
    resolved = path.resolve(strict=True)
    identity = runner._identity(resolved)
    if identity is None:
        raise runner.GateError(
            "PROTECTED_INPUT_MISSING",
            label,
            "existing immutable file",
            str(resolved),
            "Restore the profile input and rerun the complete evaluation.",
        )
    previous = snapshots.get(resolved)
    if previous is not None and previous[1] != identity:
        raise runner.GateError(
            "PROTECTED_INPUT_CHANGED_DURING_DISCOVERY",
            label,
            previous[1].sha256,
            identity.sha256,
            "Stop concurrent writers and rerun from the beginning.",
        )
    snapshots[resolved] = (label, identity)
    return identity


def _load_json_snapshot(
    snapshots: dict[Path, tuple[str, runner.FileIdentity]],
    path: Path,
    label: str,
    field: str,
) -> tuple[dict[str, Any], runner.FileIdentity]:
    """Read, identify, and parse one immutable JSON input from the same bytes."""

    resolved = path.resolve(strict=True)
    try:
        with resolved.open("rb") as handle:
            before = os.fstat(handle.fileno())
            payload = handle.read()
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise runner.GateError(
            "PROTECTED_INPUT_MISSING",
            label,
            "readable immutable JSON file",
            str(exc),
            "Restore the profile input and rerun the complete evaluation.",
        ) from exc

    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    changed_during_read = any(getattr(before, name, None) != getattr(after, name, None) for name in stable_fields)
    if changed_during_read or len(payload) != after.st_size:
        raise runner.GateError(
            "PROTECTED_INPUT_CHANGED_DURING_READ",
            label,
            "stable file identity while reading",
            {
                "before": {name: getattr(before, name, None) for name in stable_fields},
                "after": {name: getattr(after, name, None) for name in stable_fields},
                "bytes_read": len(payload),
            },
            "Stop concurrent writers and rerun from the beginning.",
        )

    identity = runner.FileIdentity(
        sha256=hashlib.sha256(payload).hexdigest().upper(),
        bytes=len(payload),
        modified_ns=after.st_mtime_ns,
    )
    previous = snapshots.get(resolved)
    if previous is not None and previous[1] != identity:
        raise runner.GateError(
            "PROTECTED_INPUT_CHANGED_DURING_DISCOVERY",
            label,
            previous[1].sha256,
            identity.sha256,
            "Stop concurrent writers and rerun from the beginning.",
        )
    snapshots[resolved] = (label, identity)

    try:
        document = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise runner.GateError(
            "MALFORMED_JSON",
            field,
            "readable UTF-8 JSON object",
            str(exc),
            "Repair or regenerate the JSON file.",
        ) from exc
    if not isinstance(document, dict):
        raise runner.GateError(
            "MALFORMED_JSON",
            field,
            "top-level JSON object",
            type(document).__name__,
            "Emit a JSON object.",
        )
    return document, identity


def _slot_base(slot: ResolvedSlot) -> dict[str, Any]:
    return {
        "id": slot.id,
        "gate_id": slot.gate_id,
        "cycle_id": slot.cycle_id,
        "domain": slot.domain,
        "requirement": slot.requirement,
        "effective_mandatory": slot.effective_mandatory,
        "applicability": slot.applicability,
    }


def _blocked_slot(slot: ResolvedSlot, finding: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        **_slot_base(slot),
        "status": "BLOCKED",
        "evidence": None,
        "findings": [finding],
        "decision_reasons": [reason],
    }


def _evaluate_slot(
    *,
    project_root: Path,
    slot: ResolvedSlot,
    scope: dict[str, Any],
    scope_started_at: datetime,
    now: datetime,
    future_skew_seconds: int,
    expected_source_dirty: bool,
    allow_dirty_source: bool,
    schema_engine: SchemaEngine,
    snapshots: dict[Path, tuple[str, runner.FileIdentity]],
    output_path: Path,
    run_owners: dict[str, str],
    report_hash_owners: dict[str, str],
    artifact_owners: dict[Path, str],
) -> tuple[dict[str, Any], dict[str, Any] | None, datetime | None]:
    if slot.applicability["status"] == "not_applicable":
        return (
            {
                **_slot_base(slot),
                "status": "NOT_APPLICABLE",
                "evidence": None,
                "findings": [],
                "decision_reasons": [
                    f"Condition {slot.applicability['condition_id']} was explicitly resolved as not applicable: "
                    f"{slot.applicability['reason_code']}."
                ],
            },
            None,
            None,
        )

    if slot.report_path is None:
        if slot.effective_mandatory:
            finding = _finding(
                "MANDATORY_EVIDENCE_MISSING",
                "BLOCKER",
                True,
                slot.id,
                "",
                "scope.evidence_bindings",
                f"fresh {slot.gate_id} report",
                "missing",
                "Run the child M01.3 gate and bind its report before evaluating this profile.",
            )
            return _blocked_slot(slot, finding, "A mandatory applicable profile slot has no evidence binding."), None, None
        return (
            {
                **_slot_base(slot),
                "status": "SKIPPED",
                "evidence": None,
                "findings": [
                    _finding(
                        "OPTIONAL_EVIDENCE_SKIPPED",
                        "INFO",
                        False,
                        slot.id,
                        "",
                        "scope.evidence_bindings",
                        "optional evidence or an explicit omission",
                        "missing",
                        "Bind the optional child report when that additional evidence is available.",
                    )
                ],
                "decision_reasons": ["Optional evidence was not supplied."],
            },
            None,
            None,
        )

    try:
        report_path = runner.resolve_project_path(
            project_root,
            slot.report_path,
            f"scope.evidence_bindings.{slot.id}.report_path",
            must_exist=True,
        )
    except runner.GateError as exc:
        finding = _finding(
            exc.code,
            "BLOCKER",
            True,
            slot.id,
            slot.report_path,
            exc.field,
            exc.expected,
            exc.actual,
            exc.suggested_fix,
        )
        return _blocked_slot(slot, finding, "The bound child report path is unavailable or unsafe."), None, None
    if report_path == output_path:
        raise ProfileError(
            "PROFILE_OUTPUT_INPUT_COLLISION",
            "output_path",
            "path distinct from every child report",
            slot.report_path,
            "Choose a dedicated aggregate report path.",
        )

    findings: list[dict[str, Any]] = []
    try:
        document, report_identity = _load_json_snapshot(
            snapshots,
            report_path,
            f"child report for {slot.id}",
            f"profile.slots.{slot.id}.report",
        )
        schema_engine.validate(CHILD_REPORT_SCHEMA, document)
    except runner.GateError as exc:
        findings.append(
            _finding(exc.code, "BLOCKER", True, slot.id, slot.report_path, exc.field, exc.expected, exc.actual, exc.suggested_fix)
        )
        return _blocked_slot(slot, findings[0], "The child report is not readable canonical JSON."), None, None
    except SchemaValidationError as exc:
        finding = _finding(
            "CHILD_REPORT_SCHEMA_UNKNOWN_OR_INVALID",
            "BLOCKER",
            True,
            slot.id,
            slot.report_path,
            "child_report",
            "canonical mtr.quality_gate_report v1",
            exc.as_dict(),
            "Regenerate the report with the accepted M01.3 runner and schema set.",
        )
        return _blocked_slot(slot, finding, "Unknown or malformed child evidence fails closed."), None, None

    run_id = document["run_id"]
    prior_run_owner = run_owners.get(run_id)
    if prior_run_owner is not None:
        findings.append(
            _finding(
                "CHILD_RUN_ID_REUSED",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.run_id",
                "unique run ID per slot/cycle",
                {"run_id": run_id, "already_used_by": prior_run_owner},
                "Rerun the child gate independently for this slot.",
            )
        )
    else:
        run_owners[run_id] = slot.id
    prior_hash_owner = report_hash_owners.get(report_identity.sha256)
    if prior_hash_owner is not None:
        findings.append(
            _finding(
                "CHILD_REPORT_REUSED",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.sha256",
                "unique report bytes per slot/cycle",
                {"sha256": report_identity.sha256, "already_used_by": prior_hash_owner},
                "Generate fresh independent evidence instead of copying a prior report.",
            )
        )
    else:
        report_hash_owners[report_identity.sha256] = slot.id

    if document["gate_id"] != slot.gate_id:
        findings.append(
            _finding(
                "CHILD_GATE_ID_MISMATCH",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.gate_id",
                slot.gate_id,
                document["gate_id"],
                "Bind the report produced for this exact profile slot.",
            )
        )

    child_source = document["source"]
    expected_source = {
        "commit": scope["source_commit"],
        "content_version": scope["content_version"],
    }
    actual_source = {
        "commit": child_source["commit"],
        "expected_commit": child_source["expected_commit"],
        "content_version": child_source["content_version"],
        "matches_expected": child_source["matches_expected"],
        "stable_during_run": child_source["stable_during_run"],
        "dirty": child_source["dirty"],
        "dirty_authorized": child_source["dirty_authorized"],
    }
    if not (
        child_source["commit"] == scope["source_commit"]
        and child_source["expected_commit"] == scope["source_commit"]
        and child_source["content_version"] == scope["content_version"]
        and child_source["matches_expected"]
        and child_source["stable_during_run"]
        and child_source["dirty"] == expected_source_dirty
        and (not child_source["dirty"] or (allow_dirty_source and child_source["dirty_authorized"]))
    ):
        findings.append(
            _finding(
                "CHILD_SOURCE_IDENTITY_MISMATCH",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.source",
                expected_source,
                actual_source,
                "Rerun the child gate against the exact profile source/content identity.",
            )
        )

    try:
        generated_at = _parse_time(document["generated_at"], f"slots.{slot.id}.generated_at")
    except ProfileError as exc:
        generated_at = None
        findings.append(
            _finding(exc.code, "BLOCKER", True, slot.id, slot.report_path, exc.field, exc.expected, exc.actual, exc.suggested_fix)
        )
    if generated_at is not None:
        if generated_at < scope_started_at:
            findings.append(
                _finding(
                    "STALE_PROFILE_EVIDENCE",
                    "BLOCKER",
                    True,
                    slot.id,
                    slot.report_path,
                    "child_report.generated_at",
                    f">= {_iso(scope_started_at)}",
                    document["generated_at"],
                    "Rerun the child gate after the profile scope starts.",
                )
            )
        if generated_at > now + timedelta(seconds=future_skew_seconds):
            findings.append(
                _finding(
                    "CHILD_REPORT_FROM_FUTURE",
                    "BLOCKER",
                    True,
                    slot.id,
                    slot.report_path,
                    "child_report.generated_at",
                    f"<= {_iso(now + timedelta(seconds=future_skew_seconds))}",
                    document["generated_at"],
                    "Correct the system clock and rerun the child gate.",
                )
            )

    child_config_path: Path | None = None
    try:
        child_config_path = runner.resolve_project_path(
            project_root,
            document["config"]["relative_path"],
            f"slots.{slot.id}.child_config",
            must_exist=True,
        )
        if child_config_path == output_path:
            raise ProfileError(
                "PROFILE_OUTPUT_INPUT_COLLISION",
                "output_path",
                "path distinct from every child config",
                document["config"]["relative_path"],
                "Choose a dedicated aggregate report path.",
            )
        child_config_identity = _record_snapshot(snapshots, child_config_path, f"child config for {slot.id}")
        if child_config_identity.sha256 != document["config"]["sha256"]:
            findings.append(
                _finding(
                    "CHILD_CONFIG_CHANGED",
                    "BLOCKER",
                    True,
                    slot.id,
                    document["config"]["relative_path"],
                    "child_report.config.sha256",
                    document["config"]["sha256"],
                    child_config_identity.sha256,
                    "Restore the executed child config or rerun the gate with its current bytes.",
                )
            )
    except runner.GateError as exc:
        findings.append(
            _finding(exc.code, "BLOCKER", True, slot.id, document["config"]["relative_path"], exc.field, exc.expected, exc.actual, exc.suggested_fix)
        )

    for artifact in document["artifacts"]:
        try:
            artifact_path = runner.resolve_project_path(
                project_root,
                artifact["relative_path"],
                f"slots.{slot.id}.artifacts",
                must_exist=True,
            )
            if artifact_path == output_path:
                raise ProfileError(
                    "PROFILE_OUTPUT_INPUT_COLLISION",
                    "output_path",
                    "path distinct from every child artifact",
                    artifact["relative_path"],
                    "Choose a dedicated aggregate report path.",
                )
            artifact_identity = _record_snapshot(snapshots, artifact_path, f"child artifact for {slot.id}")
            owner = artifact_owners.get(artifact_path)
            if owner is not None and owner != slot.id:
                findings.append(
                    _finding(
                        "CHILD_ARTIFACT_REUSED",
                        "BLOCKER",
                        True,
                        slot.id,
                        artifact["relative_path"],
                        "child_report.artifacts.relative_path",
                        "unique artifact path per slot/cycle",
                        {"already_used_by": owner},
                        "Use a distinct artifact directory for every child run.",
                    )
                )
            else:
                artifact_owners[artifact_path] = slot.id
            if artifact_identity.sha256 != artifact["sha256"] or artifact_identity.bytes != artifact["bytes"]:
                findings.append(
                    _finding(
                        "CHILD_ARTIFACT_CHANGED",
                        "BLOCKER",
                        True,
                        slot.id,
                        artifact["relative_path"],
                        "child_report.artifacts",
                        {"sha256": artifact["sha256"], "bytes": artifact["bytes"]},
                        {"sha256": artifact_identity.sha256, "bytes": artifact_identity.bytes},
                        "Restore the exact artifact or rerun the child gate.",
                    )
                )
        except runner.GateError as exc:
            findings.append(
                _finding(exc.code, "BLOCKER", True, slot.id, artifact["relative_path"], exc.field, exc.expected, exc.actual, exc.suggested_fix)
            )

    target_platforms = sorted(
        {
            envelope["target"]["platform"]
            for step in document["steps"]
            for envelope in [step["evidence_envelope"]]
            if envelope is not None
            and envelope["status"] == "PASS"
            and envelope["fresh"]
            and envelope["applicable"]
        }
    )
    missing_platforms = sorted(set(slot.required_target_platforms).difference(target_platforms))
    if missing_platforms:
        findings.append(
            _finding(
                "REQUIRED_TARGET_EVIDENCE_MISSING",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.steps.evidence_envelope.target.platform",
                list(slot.required_target_platforms),
                target_platforms,
                "Run fresh accepted evidence for every platform required by this slot.",
            )
        )

    evidence = {
        "relative_path": runner.project_relative(project_root, report_path),
        "sha256": report_identity.sha256,
        "run_id": document["run_id"],
        "gate_id": document["gate_id"],
        "generated_at": document["generated_at"],
        "status": document["status"],
        "config_relative_path": document["config"]["relative_path"],
        "config_sha256": document["config"]["sha256"],
        "target_platforms": target_platforms,
    }
    aggregate_artifact = {
        "kind": "quality_gate_report",
        "relative_path": evidence["relative_path"],
        "sha256": report_identity.sha256,
        "bytes": report_identity.bytes,
        "slot_id": slot.id,
    }
    if findings:
        result = {
            **_slot_base(slot),
            "status": "BLOCKED",
            "evidence": evidence,
            "findings": findings,
            "decision_reasons": ["Child evidence failed provenance, freshness, identity or platform validation."],
        }
        return result, aggregate_artifact, generated_at

    child_status = document["status"]
    child_findings: list[dict[str, Any]] = []
    if child_status == "FAIL":
        child_findings.append(
            _finding(
                "CHILD_GATE_FAILED",
                "ERROR",
                True,
                slot.id,
                slot.report_path,
                "child_report.status",
                "PASS",
                "FAIL",
                "Fix the child gate failure and rerun this slot.",
            )
        )
    elif child_status == "BLOCKED":
        child_findings.append(
            _finding(
                "CHILD_GATE_BLOCKED",
                "BLOCKER",
                True,
                slot.id,
                slot.report_path,
                "child_report.status",
                "PASS",
                "BLOCKED",
                "Resolve the child gate blocker and regenerate fresh evidence.",
            )
        )
    result = {
        **_slot_base(slot),
        "status": child_status,
        "evidence": evidence,
        "findings": child_findings,
        "decision_reasons": [
            "Fresh child gate report passed all profile provenance checks."
            if child_status == "PASS"
            else f"Child gate reported {child_status}."
        ],
    }
    return result, aggregate_artifact, generated_at


def _cycle_order_findings(
    resolution: ProfileResolution,
    slot_results: list[dict[str, Any]],
    generated_times: dict[str, datetime],
) -> list[dict[str, Any]]:
    times_by_cycle: dict[str, list[datetime]] = {cycle: [] for cycle in resolution.cycle_order}
    for result in slot_results:
        generated = generated_times.get(result["id"])
        if generated is not None:
            times_by_cycle[result["cycle_id"]].append(generated)
    findings: list[dict[str, Any]] = []
    previous_cycle: str | None = None
    previous_latest: datetime | None = None
    for cycle in resolution.cycle_order:
        values = times_by_cycle[cycle]
        if not values:
            continue
        earliest = min(values)
        latest = max(values)
        if previous_latest is not None and earliest <= previous_latest:
            findings.append(
                _finding(
                    "PROFILE_CYCLE_ORDER_INVALID",
                    "BLOCKER",
                    True,
                    None,
                    "",
                    "profile.cycle_order",
                    f"all {cycle} evidence generated after {previous_cycle}",
                    {"previous_latest": _iso(previous_latest), "current_earliest": _iso(earliest)},
                    "Run profile cycles sequentially and generate independent evidence after the prior cycle finishes.",
                )
            )
        previous_cycle = cycle
        previous_latest = latest
    return findings


def semantic_projection(report: dict[str, Any]) -> dict[str, Any]:
    """Deterministic comparison surface excluding clocks, hashes and run IDs."""

    return {
        "profile_id": report["profile"]["id"],
        "status": report["status"],
        "source_matches": report["source"]["matches_scope"],
        "source_stable": report["source"]["stable_during_run"],
        "slots": [
            {
                "id": slot["id"],
                "requirement": slot["requirement"],
                "effective_mandatory": slot["effective_mandatory"],
                "applicability": slot["applicability"],
                "status": slot["status"],
                "finding_codes": [finding["code"] for finding in slot["findings"]],
            }
            for slot in report["slots"]
        ],
        "finding_codes": [finding["code"] for finding in report["findings"]],
    }


def run_profile(
    *,
    project_root: Path,
    config_path: Path,
    scope_path: Path,
    output_path: Path,
    allow_physical_device: bool = False,
    allow_dirty_source: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = project_root.resolve(strict=True)
    config_path = runner._ensure_contained(root, config_path, "config_path")
    scope_path = runner._ensure_contained(root, scope_path, "scope_path")
    output_path = runner._ensure_contained(root, output_path, "output_path")
    if not config_path.is_file() or not scope_path.is_file():
        raise ProfileError(
            "PROFILE_INPUT_MISSING",
            "config_path/scope_path",
            "existing contained JSON files",
            {"config": str(config_path), "scope": str(scope_path)},
            "Create the canonical catalog and one explicit invocation scope.",
        )
    if output_path in {config_path, scope_path} or output_path.suffix.lower() != ".json":
        raise ProfileError(
            "INVALID_PROFILE_OUTPUT",
            "output_path",
            "dedicated .json path distinct from inputs",
            str(output_path),
            "Choose a separate contained JSON report path.",
        )

    snapshots: dict[Path, tuple[str, runner.FileIdentity]] = {}
    config, config_identity = _load_json_snapshot(snapshots, config_path, "profile catalog", "config_path")
    scope, scope_identity = _load_json_snapshot(snapshots, scope_path, "profile scope", "scope_path")
    for schema_path in sorted((root / runner.SCHEMA_DIRECTORY_RELATIVE).glob("*.schema.json")):
        _record_snapshot(snapshots, schema_path, f"canonical schema {schema_path.name}")
    for protected_path, label in (
        (Path(__file__), "profile runner"),
        (Path(__file__).with_name("profile_engine.py"), "profile engine"),
        (Path(__file__).with_name("runner.py"), "M01.3 runner"),
        (runner.REQUIREMENTS_LOCK, "validator lock"),
    ):
        _record_snapshot(snapshots, protected_path, label)
    if output_path.resolve(strict=False) in snapshots:
        raise ProfileError(
            "PROFILE_OUTPUT_INPUT_COLLISION",
            "output_path",
            "path distinct from every canonical profile input",
            str(output_path),
            "Choose a dedicated aggregate report path.",
        )

    schema_engine = SchemaEngine(root / runner.SCHEMA_DIRECTORY_RELATIVE, runner.REQUIREMENTS_LOCK)
    engine_identity = schema_engine.assert_isolated_runtime()
    try:
        schema_engine.validate(PROFILE_CONFIG_SCHEMA, config)
        schema_engine.validate(PROFILE_SCOPE_SCHEMA, scope)
    except SchemaValidationError as exc:
        raise ProfileError(
            "PROFILE_SCHEMA_INVALID",
            exc.schema_name,
            "canonical Draft 2020-12 document",
            exc.as_dict(),
            "Fix every schema issue before profile evaluation.",
        ) from exc

    config_hash = config_identity.sha256
    resolution = resolve_profile(
        config,
        scope,
        config_sha256=config_hash,
        allow_physical_device=allow_physical_device,
    )
    if resolution.profile_id == "RC2" and allow_dirty_source:
        raise ProfileError(
            "RC2_DIRTY_OVERRIDE_REJECTED",
            "allow_dirty_source",
            False,
            True,
            "Commit the release candidate and run RC2 without a development override.",
        )

    current_time = (now or _utc_now()).astimezone(timezone.utc)
    scope_started_at = _parse_time(scope["started_at"], "scope.started_at")
    policy = config["policy"]
    if scope_started_at > current_time + timedelta(seconds=policy["future_clock_skew_seconds"]):
        raise ProfileError(
            "PROFILE_SCOPE_FROM_FUTURE",
            "scope.started_at",
            f"<= {_iso(current_time + timedelta(seconds=policy['future_clock_skew_seconds']))}",
            scope["started_at"],
            "Correct the system clock and regenerate the scope.",
        )
    if current_time - scope_started_at > timedelta(seconds=policy["max_run_age_seconds"]):
        raise ProfileError(
            "PROFILE_SCOPE_EXPIRED",
            "scope.started_at",
            f"age <= {policy['max_run_age_seconds']} seconds",
            scope["started_at"],
            "Start a new profile cycle and regenerate every child report.",
        )

    source_probe_error: runner.GateError | None = None
    try:
        initial_head = runner._git_output(root, ["rev-parse", "HEAD"]).lower()
        initial_dirty = bool(runner._git_output(root, ["status", "--porcelain", "--untracked-files=normal", "--", "."]))
    except runner.GateError as exc:
        source_probe_error = exc
        initial_head = "0" * 40
        initial_dirty = True
    source_matches = initial_head == scope["source_commit"]
    dirty_allowed = not initial_dirty or allow_dirty_source

    started_monotonic = time.monotonic_ns()
    run_owners: dict[str, str] = {}
    report_hash_owners: dict[str, str] = {}
    artifact_owners: dict[Path, str] = {}
    slot_results: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    generated_times: dict[str, datetime] = {}
    for slot in resolution.slots:
        result, artifact, generated = _evaluate_slot(
            project_root=root,
            slot=slot,
            scope=scope,
            scope_started_at=scope_started_at,
            now=current_time,
            future_skew_seconds=policy["future_clock_skew_seconds"],
            expected_source_dirty=initial_dirty,
            allow_dirty_source=allow_dirty_source,
            schema_engine=schema_engine,
            snapshots=snapshots,
            output_path=output_path,
            run_owners=run_owners,
            report_hash_owners=report_hash_owners,
            artifact_owners=artifact_owners,
        )
        slot_results.append(result)
        if artifact is not None:
            artifacts.append(artifact)
        if generated is not None:
            generated_times[slot.id] = generated

    global_findings = _cycle_order_findings(resolution, slot_results, generated_times)
    try:
        final_head = runner._git_output(root, ["rev-parse", "HEAD"]).lower()
        final_dirty = bool(runner._git_output(root, ["status", "--porcelain", "--untracked-files=normal", "--", "."]))
        source_stable = final_head == initial_head and final_dirty == initial_dirty
    except runner.GateError as exc:
        source_stable = False
        source_probe_error = source_probe_error or exc
        final_head = None
        final_dirty = None

    if source_probe_error is not None:
        global_findings.append(
            _finding(
                "PROFILE_SOURCE_PROBE_FAILED",
                "BLOCKER",
                True,
                None,
                "",
                "source",
                "bounded Git source identity",
                source_probe_error.as_dict(),
                "Restore Git availability and rerun the complete profile.",
            )
        )
    if not source_matches:
        global_findings.append(
            _finding(
                "PROFILE_SOURCE_COMMIT_MISMATCH",
                "BLOCKER",
                True,
                None,
                "",
                "source.commit",
                scope["source_commit"],
                initial_head,
                "Run against the exact scope commit or regenerate the scope and all evidence.",
            )
        )
    if initial_dirty and not allow_dirty_source:
        global_findings.append(
            _finding(
                "PROFILE_DIRTY_SOURCE_NOT_AUTHORIZED",
                "BLOCKER",
                True,
                None,
                "",
                "source.dirty",
                False,
                True,
                "Commit or revert project changes before profile acceptance.",
            )
        )
    if not source_stable:
        global_findings.append(
            _finding(
                "PROFILE_SOURCE_CHANGED_DURING_RUN",
                "BLOCKER",
                True,
                None,
                "",
                "source.stable_during_run",
                {"commit": initial_head, "dirty": initial_dirty},
                {"commit": final_head, "dirty": final_dirty},
                "Discard this evaluation and rerun against a stable worktree.",
            )
        )

    changed_inputs: list[dict[str, Any]] = []
    for path, (label, before) in snapshots.items():
        after = runner._identity(path)
        if after != before:
            changed_inputs.append(
                {
                    "label": label,
                    "path": str(path),
                    "before": before.sha256,
                    "after": after.sha256 if after is not None else None,
                }
            )
    for changed in changed_inputs:
        try:
            changed_path = runner.project_relative(root, Path(changed["path"]))
        except ValueError:
            changed_path = changed["path"]
        global_findings.append(
            _finding(
                "PROFILE_INPUT_CHANGED_DURING_RUN",
                "BLOCKER",
                True,
                None,
                changed_path,
                "protected_inputs",
                {"label": changed["label"], "sha256": changed["before"]},
                {"sha256": changed["after"]},
                "Restore the exact input and rerun the complete profile.",
            )
        )

    top_findings = list(global_findings)
    for result in slot_results:
        for item in result["findings"]:
            promoted = dict(item)
            promoted["blocking"] = bool(item["blocking"] and result["effective_mandatory"])
            top_findings.append(promoted)

    globally_blocked = bool(global_findings) or not source_matches or not dirty_allowed or not source_stable or bool(changed_inputs)
    mandatory_results = [result for result in slot_results if result["effective_mandatory"]]
    if globally_blocked or any(result["status"] in {"BLOCKED", "SKIPPED", "NOT_APPLICABLE"} for result in mandatory_results):
        overall = "BLOCKED"
        decision_reasons = [
            "Profile blocked on missing, stale, reused, source-drifted, cycle-invalid or otherwise untrusted mandatory evidence."
        ]
    elif any(result["status"] == "FAIL" for result in mandatory_results):
        overall = "FAIL"
        decision_reasons = ["At least one applicable mandatory child gate reported a validated product or QA failure."]
    else:
        overall = "PASS"
        decision_reasons = [
            "Every applicable mandatory slot has a fresh independent PASS report; conditional exclusions are explicit NOT_APPLICABLE decisions."
        ]

    report = {
        "schema_version": 1,
        "contract": "mtr.quality_profile_report",
        "run_id": scope["run_id"],
        "generated_at": _iso(_utc_now()),
        "status": overall,
        "source": {
            "commit": initial_head,
            "content_version": scope["content_version"],
            "matches_scope": source_matches,
            "dirty": initial_dirty,
            "dirty_authorized": bool(allow_dirty_source),
            "stable_during_run": source_stable,
        },
        "profile": {
            "id": resolution.profile_id,
            "catalog_id": config["catalog_id"],
            "config_relative_path": runner.project_relative(root, config_path),
            "config_sha256": config_identity.sha256,
            "scope_relative_path": runner.project_relative(root, scope_path),
            "scope_sha256": scope_identity.sha256,
            "started_at": scope["started_at"],
            "cycle_order": list(resolution.cycle_order),
        },
        "schema_engine": engine_identity,
        "duration_ms": max(0, (time.monotonic_ns() - started_monotonic) // 1_000_000),
        "slots": slot_results,
        "artifacts": artifacts,
        "findings": top_findings,
        "decision_reasons": decision_reasons,
    }
    try:
        schema_engine.validate(PROFILE_REPORT_SCHEMA, report)
    except SchemaValidationError as exc:
        raise ProfileError(
            "PROFILE_REPORT_SCHEMA_INVALID",
            "profile_report",
            "canonical aggregate report",
            exc.as_dict(),
            "Fix the evaluator/schema invariant before replacing any prior report.",
        ) from exc
    runner.atomic_write_json(output_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-physical-device", action="store_true")
    parser.add_argument("--allow-dirty-source", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve(strict=True)
        config_path = runner.resolve_cli_path(root, args.config, "config_path", must_exist=True)
        scope_path = runner.resolve_cli_path(root, args.scope, "scope_path", must_exist=True)
        output_path = runner.resolve_cli_path(root, args.output, "output_path")
        report = run_profile(
            project_root=root,
            config_path=config_path,
            scope_path=scope_path,
            output_path=output_path,
            allow_physical_device=args.allow_physical_device,
            allow_dirty_source=args.allow_dirty_source,
        )
    except (ProfileError, runner.GateError, RuntimeError, OSError) as exc:
        if isinstance(exc, (ProfileError, runner.GateError)):
            detail = exc.as_dict()
        else:
            detail = {
                "code": "PROFILE_INTERNAL_BLOCK",
                "field": "profile_runner",
                "expected": "successful bounded evaluation",
                "actual": str(exc),
                "suggested_fix": "Inspect the isolated evaluator environment and retry after correcting the explicit error.",
            }
        print(json.dumps({"status": "BLOCKED", "error": detail}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 3
    print(json.dumps({"status": report["status"], "report": str(output_path)}, ensure_ascii=False, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
