#!/usr/bin/env python3
"""Reference adapters for current MTR quality reports.

This module is deliberately project-library code, not an active gate runner.  It
normalizes already-produced reports into the canonical v1 evidence envelope and
fails closed on unsupported, malformed, stale, or mis-targeted evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable


ADAPTER_VERSION = "1.0.0"
CONTRACT = "mtr.quality_evidence_envelope"
HEX_40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")


class AdapterError(ValueError):
    """A deterministic, machine-readable adapter rejection."""

    def __init__(
        self,
        code: str,
        field: str,
        expected: Any,
        actual: Any,
        suggested_fix: str,
    ) -> None:
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


def _is_type(value: Any, expected_type: type | tuple[type, ...]) -> bool:
    if expected_type is bool:
        return type(value) is bool
    if expected_type is int:
        return type(value) is int
    return isinstance(value, expected_type)


def _require_path(
    document: dict[str, Any],
    dotted_path: str,
    expected_type: type | tuple[type, ...],
    *,
    error_code: str = "MALFORMED_SOURCE",
    suggested_fix: str = "Regenerate the native report with the owning validator.",
) -> Any:
    current: Any = document
    traversed: list[str] = []
    for part in dotted_path.split("."):
        traversed.append(part)
        if not isinstance(current, dict) or part not in current:
            raise AdapterError(
                error_code,
                ".".join(traversed),
                getattr(expected_type, "__name__", str(expected_type)),
                "missing",
                suggested_fix,
            )
        current = current[part]
    if not _is_type(current, expected_type):
        raise AdapterError(
            error_code,
            dotted_path,
            getattr(expected_type, "__name__", str(expected_type)),
            type(current).__name__,
            suggested_fix,
        )
    return current


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterError("PATH_OUTSIDE_SCOPE", field, "non-empty relative path", value, "Use a project-relative path.")
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        raise AdapterError("PATH_OUTSIDE_SCOPE", field, "project-relative path", value, "Remove the absolute path prefix.")
    raw_parts = normalized.split("/")
    if "\x00" in normalized or any(part in ("", ".", "..") or ":" in part for part in raw_parts):
        raise AdapterError("PATH_OUTSIDE_SCOPE", field, "contained path without empty/dot/traversal/ADS segments", value, "Remove empty, dot, parent, NUL, or alternate-data-stream segments.")
    path = PurePosixPath(*raw_parts)
    return str(path)


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise AdapterError("INVALID_CONTEXT", field, "RFC3339 timestamp", value, "Provide a timezone-aware timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdapterError("INVALID_CONTEXT", field, "RFC3339 timestamp", value, "Provide a valid timestamp.") from exc
    if parsed.tzinfo is None:
        raise AdapterError("INVALID_CONTEXT", field, "timezone-aware timestamp", value, "Include Z or an explicit UTC offset.")
    return parsed


def _finding(
    code: str,
    severity: str,
    blocking: bool,
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
        "path": path,
        "field": field,
        "expected": expected,
        "actual": actual,
        "suggested_fix": suggested_fix,
    }


def _result(
    status: str,
    metrics: dict[str, Any],
    findings: list[dict[str, Any]],
    reasons: list[str],
) -> dict[str, Any]:
    return {"status": status, "metrics": metrics, "findings": findings, "reasons": reasons}


def _strict_flag_findings(context: dict[str, Any], required_flag: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    tool = context["tool"]
    if not tool["strict"]:
        findings.append(
            _finding(
                "STRICT_INVOCATION_REQUIRED",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "tool.strict",
                True,
                False,
                "Run the validator through the strict quality-gate profile.",
            )
        )
    if required_flag not in tool["flags"]:
        findings.append(
            _finding(
                "STRICT_FLAG_MISSING",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "tool.flags",
                required_flag,
                tool["flags"],
                f"Regenerate the report with {required_flag}.",
            )
        )
    return findings


def adapt_asset_validation(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    blocker_count = _require_path(report, "summary.blockerCount", int)
    white_count = _require_path(report, "summary.whiteMatteSuspectCount", int)
    reference_blockers = _require_path(report, "referenceChecks.blockerCount", int)
    fail_on_white = _require_path(report, "policy.failOnWhiteMatte", bool)
    skip_references = _require_path(report, "policy.skipReferenceChecks", bool)
    findings = _strict_flag_findings(context, "--fail-on-white-matte")
    if not fail_on_white or skip_references:
        findings.append(
            _finding(
                "UNSAFE_REPORT_POLICY",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "policy",
                {"failOnWhiteMatte": True, "skipReferenceChecks": False},
                {"failOnWhiteMatte": fail_on_white, "skipReferenceChecks": skip_references},
                "Regenerate the report with strict matte and reference checks enabled.",
            )
        )
    if findings:
        status = "BLOCKED"
    elif blocker_count > 0 or reference_blockers > 0 or white_count > 0:
        status = "FAIL"
        findings.append(
            _finding(
                "ASSET_BLOCKERS_PRESENT",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "summary.blockerCount",
                0,
                blocker_count,
                "Resolve asset, reference, decode, size, metadata, and white-matte blockers; then rerun the strict validator.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {
            "blocker_count": blocker_count,
            "reference_blocker_count": reference_blockers,
            "white_matte_suspect_count": white_count,
            "png_count": _require_path(report, "summary.pngCount", int),
        },
        findings,
        ["Strict asset policy accepted." if status == "PASS" else "Asset evidence did not satisfy the strict acceptance rule."],
    )


def adapt_skin_bonus_matrix(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    blocker_count = _require_path(report, "summary.blockerCount", int)
    warning_count = _require_path(report, "summary.warningCount", int)
    expected_count = _require_path(report, "summary.expectedFrameCount", int)
    checked_count = _require_path(report, "summary.checkedFrameCount", int)
    fail_on_warnings = _require_path(report, "policy.failOnWarnings", bool)
    findings = _strict_flag_findings(context, "--fail-on-warnings")
    if not fail_on_warnings:
        findings.append(
            _finding(
                "UNSAFE_REPORT_POLICY",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "policy.failOnWarnings",
                True,
                fail_on_warnings,
                "Regenerate the report with warning promotion enabled.",
            )
        )
    if findings:
        status = "BLOCKED"
    elif blocker_count > 0 or warning_count > 0 or checked_count != expected_count:
        status = "FAIL"
        findings.append(
            _finding(
                "SKIN_MATRIX_NOT_CLEAN",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "summary",
                {"blockerCount": 0, "warningCount": 0, "checkedFrameCount": expected_count},
                {"blockerCount": blocker_count, "warningCount": warning_count, "checkedFrameCount": checked_count},
                "Repair missing, malformed, misaligned, or white-matte frames and rerun the strict matrix.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "expected_frame_count": expected_count,
            "checked_frame_count": checked_count,
        },
        findings,
        ["Strict skin matrix accepted." if status == "PASS" else "Skin matrix evidence did not satisfy the strict acceptance rule."],
    )


def adapt_ui_ir_validation(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    problem_count = _require_path(report, "summary.problemCount", int)
    warning_count = _require_path(report, "summary.warningCount", int)
    screen_count = _require_path(report, "summary.screenCount", int)
    expected_screen_count = _require_path(report, "summary.expectedScreenCount", int)
    findings: list[dict[str, Any]] = []
    if warning_count > 0:
        findings.append(
            _finding(
                "UI_IR_WARNINGS_PRESENT",
                "WARNING",
                False,
                context["source_report"]["relative_path"],
                "summary.warningCount",
                0,
                warning_count,
                "Review warnings or promote them in the future quality profile when required.",
            )
        )
    if problem_count > 0 or screen_count != expected_screen_count:
        status = "FAIL"
        findings.append(
            _finding(
                "UI_IR_PROBLEMS_PRESENT",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "summary",
                {"problemCount": 0, "screenCount": expected_screen_count},
                {"problemCount": problem_count, "screenCount": screen_count},
                "Repair UI IR contract or coverage failures and rerun validation.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {
            "problem_count": problem_count,
            "warning_count": warning_count,
            "screen_count": screen_count,
            "expected_screen_count": expected_screen_count,
        },
        findings,
        ["UI IR native pass semantics accepted." if status == "PASS" else "UI IR contains blocking problems or coverage drift."],
    )


def adapt_android_toolchain_status(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    ready = _require_path(report, "qaReady", bool)
    blockers = _require_path(report, "blockers", list)
    policy = _require_path(report, "androidQaTargetPolicy", str)
    findings = _strict_flag_findings(context, "-FailOnNotReady")
    boot_serial = report.get("bootCompletedSerial")
    if isinstance(boot_serial, str) and boot_serial and boot_serial != context["target"]["identity"]:
        findings.append(
            _finding(
                "TARGET_IDENTITY_MISMATCH",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "target.identity",
                boot_serial,
                context["target"]["identity"],
                "Bind the evidence envelope to the emulator recorded by the toolchain report.",
            )
        )
    if policy != "emulator-only-default":
        findings.append(
            _finding(
                "TARGET_POLICY_VIOLATION",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "androidQaTargetPolicy",
                "emulator-only-default",
                policy,
                "Regenerate toolchain evidence under the emulator-only default policy.",
            )
        )
    if findings:
        status = "BLOCKED"
    elif not ready or blockers:
        status = "FAIL"
        findings.append(
            _finding(
                "ANDROID_TOOLCHAIN_NOT_READY",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "qaReady",
                True,
                ready,
                "Resolve the reported toolchain blockers and rerun with -FailOnNotReady.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"qa_ready": ready, "blocker_count": len(blockers)},
        findings,
        ["Strict Android toolchain evidence accepted." if status == "PASS" else "Android toolchain evidence is not release-safe."],
    )


def adapt_android_emulator_matrix(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    serial = _require_path(report, "serial", str)
    native_status = _require_path(report, "status", str)
    case_count = _require_path(report, "case_count", int)
    pass_count = _require_path(report, "pass_count", int)
    fail_count = _require_path(report, "fail_count", int)
    cases = _require_path(report, "cases", list)
    findings: list[dict[str, Any]] = []
    if not serial.startswith("emulator-") or context["target"]["identity"] != serial:
        findings.append(
            _finding(
                "TARGET_POLICY_VIOLATION",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "serial",
                {"serial": "emulator-*", "target_identity": serial},
                {"serial": serial, "target_identity": context["target"]["identity"]},
                "Run Android QA on one emulator and bind the envelope to that exact serial.",
            )
        )
        status = "BLOCKED"
    else:
        bad_cases = sum(1 for case in cases if not isinstance(case, dict) or str(case.get("status", "")).lower() != "pass")
        if native_status.lower() != "pass" or fail_count != 0 or pass_count != case_count or len(cases) != case_count or bad_cases:
            status = "FAIL"
            findings.append(
                _finding(
                    "ANDROID_MATRIX_FAILED",
                    "ERROR",
                    True,
                    context["source_report"]["relative_path"],
                    "matrix",
                    {"status": "pass", "pass_count": case_count, "fail_count": 0, "case_records": case_count},
                    {"status": native_status, "pass_count": pass_count, "fail_count": fail_count, "case_records": len(cases)},
                    "Fix failing or missing emulator matrix cases and rerun the full matrix.",
                )
            )
        else:
            status = "PASS"
    return _result(
        status,
        {"case_count": case_count, "pass_count": pass_count, "fail_count": fail_count},
        findings,
        ["Android emulator matrix accepted." if status == "PASS" else "Android matrix or target policy is not acceptable."],
    )


def adapt_android_emulator_interaction(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    serial = _require_path(report, "serial", str)
    guard = _require_path(report, "emulator_only_guard", bool)
    native_status = _require_path(report, "status", str)
    subpaths = ("touch_flow.status", "name_entry.status", "restart_loop.status", "soak.status")
    substatuses = {path: _require_path(report, path, str) for path in subpaths}
    restart_requested = _require_path(report, "restart_loop.requested_iterations", int)
    restart_pass = _require_path(report, "restart_loop.pass_count", int)
    restart_fail = _require_path(report, "restart_loop.fail_count", int)
    requested_seconds = _require_path(report, "soak.requested_seconds", int)
    actual_seconds = _require_path(report, "soak.actual_seconds", (int, float))
    process_losses = _require_path(report, "soak.process_losses", int)
    findings: list[dict[str, Any]] = []
    if not serial.startswith("emulator-") or not guard or context["target"]["identity"] != serial:
        status = "BLOCKED"
        findings.append(
            _finding(
                "TARGET_POLICY_VIOLATION",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "emulator_only_guard",
                {"serial": "emulator-*", "guard": True, "target_identity": serial},
                {"serial": serial, "guard": guard, "target_identity": context["target"]["identity"]},
                "Rerun interaction QA on one emulator with its guard enabled and bind the envelope to that serial.",
            )
        )
    elif (
        native_status.lower() != "pass"
        or any(value.lower() != "pass" for value in substatuses.values())
        or restart_fail != 0
        or restart_pass != restart_requested
        or actual_seconds < requested_seconds
        or process_losses != 0
    ):
        status = "FAIL"
        findings.append(
            _finding(
                "ANDROID_INTERACTION_FAILED",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "interaction",
                "all subflows pass, full restart count, complete soak, zero process loss",
                {"status": native_status, "substatuses": substatuses, "restart_fail": restart_fail, "process_losses": process_losses},
                "Repair the failing interaction, restart, or soak flow and rerun the complete emulator cycle.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {
            "restart_requested": restart_requested,
            "restart_pass": restart_pass,
            "restart_fail": restart_fail,
            "soak_requested_seconds": requested_seconds,
            "soak_actual_seconds": actual_seconds,
            "process_losses": process_losses,
        },
        findings,
        ["Android emulator interaction and soak evidence accepted." if status == "PASS" else "Android interaction evidence is incomplete or unsafe."],
    )


def adapt_web_matrix_interaction(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    native_status = _require_path(report, "status", str)
    case_count = _require_path(report, "caseCount", int)
    pass_count = _require_path(report, "passCount", int)
    fail_count = _require_path(report, "failCount", int)
    interaction_status = _require_path(report, "interaction.status", str)
    restart_requested = _require_path(report, "restartLoop.requestedIterations", int)
    restart_pass = _require_path(report, "restartLoop.passCount", int)
    restart_fail = _require_path(report, "restartLoop.failCount", int)
    findings: list[dict[str, Any]] = []
    if (
        native_status.lower() != "pass"
        or fail_count != 0
        or pass_count != case_count
        or interaction_status.lower() != "pass"
        or restart_fail != 0
        or restart_pass != restart_requested
    ):
        status = "FAIL"
        findings.append(
            _finding(
                "WEB_MATRIX_FAILED",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "matrix",
                "all cases, interaction flow, and restart loop pass",
                {"status": native_status, "case_count": case_count, "pass_count": pass_count, "fail_count": fail_count, "interaction": interaction_status, "restart_fail": restart_fail},
                "Repair the failed browser flow and rerun the complete Web matrix.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"case_count": case_count, "pass_count": pass_count, "fail_count": fail_count, "restart_pass": restart_pass},
        findings,
        ["Web interaction matrix accepted." if status == "PASS" else "Web matrix contains a failed or missing required flow."],
    )


def adapt_web_soak(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    complete = _require_path(report, "complete", bool)
    target_seconds = _require_path(report, "targetDurationSeconds", int)
    elapsed_ms = _require_path(report, "elapsedMs", int)
    input_bursts = _require_path(report, "inputBursts", int)
    errors = _require_path(report, "consoleErrors", list)
    warnings = _require_path(report, "consoleWarnings", list)
    findings: list[dict[str, Any]] = []
    if not complete or elapsed_ms < target_seconds * 1000 or input_bursts <= 0 or errors or warnings:
        status = "FAIL"
        findings.append(
            _finding(
                "WEB_SOAK_FAILED",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "soak",
                "complete duration with input and no console errors or warnings",
                {"complete": complete, "elapsed_ms": elapsed_ms, "target_ms": target_seconds * 1000, "input_bursts": input_bursts, "console_errors": len(errors), "console_warnings": len(warnings)},
                "Repair the runtime failure or warning and repeat the full Web soak.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"target_seconds": target_seconds, "elapsed_ms": elapsed_ms, "input_bursts": input_bursts, "console_error_count": len(errors), "console_warning_count": len(warnings)},
        findings,
        ["Web soak duration and diagnostics accepted." if status == "PASS" else "Web soak evidence is incomplete or contains diagnostics."],
    )


def adapt_git_topology(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    passed = _require_path(report, "pass", bool)
    failures = _require_path(report, "failures", list)
    parent_head = _require_path(report, "parent.head", str)
    gitlink = _require_path(report, "parent.gitlink", str)
    pages_head = _require_path(report, "pages.head", str)
    pages_clean = _require_path(report, "pages.clean", bool)
    findings: list[dict[str, Any]] = []
    if not passed or failures or not pages_clean or gitlink != pages_head or parent_head.lower() != context["source"]["commit"].lower():
        status = "FAIL"
        findings.append(
            _finding(
                "GIT_TOPOLOGY_MISMATCH",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "topology",
                "clean Pages tree, matching gitlink/head, and matching source commit",
                {"pass": passed, "failure_count": len(failures), "pages_clean": pages_clean, "gitlink": gitlink, "pages_head": pages_head, "parent_head": parent_head},
                "Restore the canonical parent/Pages topology and regenerate evidence from the accepted source commit.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"failure_count": len(failures), "pages_clean": pages_clean, "gitlink_matches_pages": gitlink == pages_head},
        findings,
        ["Git topology and source identity accepted." if status == "PASS" else "Git topology does not match the accepted source state."],
    )


def adapt_source_content_fingerprint(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    report_commit = _require_path(report, "source_commit", str)
    content_version = _require_path(report, "content_version", str)
    aggregate = _require_path(report, "aggregate_sha256", str)
    file_count = _require_path(report, "file_count", int)
    findings: list[dict[str, Any]] = []
    if not HEX_64.fullmatch(aggregate):
        raise AdapterError("MALFORMED_SOURCE", "aggregate_sha256", "64 hexadecimal characters", aggregate, "Regenerate the deterministic source manifest.")
    if report_commit.lower() != context["source"]["commit"].lower() or content_version != context["source"]["content_version"]:
        status = "BLOCKED"
        findings.append(
            _finding(
                "SOURCE_IDENTITY_MISMATCH",
                "BLOCKER",
                True,
                context["source_report"]["relative_path"],
                "source_identity",
                context["source"],
                {"commit": report_commit, "content_version": content_version},
                "Regenerate the source fingerprint from the exact accepted commit and content version.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"file_count": file_count, "aggregate_sha256": aggregate.upper()},
        findings,
        ["Source/content fingerprint accepted." if status == "PASS" else "Source/content fingerprint does not match the evidence anchor."],
    )


def adapt_web_runtime_probe_legacy(report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    runtime_ready = _require_path(report, "runtimeReady", bool)
    requested_marker = report.get("waitForLogPattern", "")
    marker_ready = report.get("waitForLogPatternReady", True if not requested_marker else False)
    if not isinstance(requested_marker, str) or type(marker_ready) is not bool:
        raise AdapterError("MALFORMED_SOURCE", "waitForLogPatternReady", "boolean", marker_ready, "Regenerate the Web runtime probe.")
    findings: list[dict[str, Any]] = []
    if not runtime_ready or (requested_marker and not marker_ready):
        status = "FAIL"
        findings.append(
            _finding(
                "WEB_RUNTIME_NOT_READY",
                "ERROR",
                True,
                context["source_report"]["relative_path"],
                "runtimeReady",
                True,
                runtime_ready,
                "Fix Web startup or marker readiness and rerun the probe; exit code zero alone is not accepted.",
            )
        )
    else:
        status = "PASS"
    return _result(
        status,
        {"runtime_ready": runtime_ready, "marker_requested": bool(requested_marker), "marker_ready": marker_ready},
        findings,
        ["Legacy Web runtime probe accepted by explicit semantic checks." if status == "PASS" else "Legacy Web runtime probe reported a false-ready state."],
    )


HANDLERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    name: value
    for name, value in globals().copy().items()
    if name.startswith("adapt_") and callable(value)
}


def detect_source_schema(report: dict[str, Any]) -> tuple[str, str]:
    if not isinstance(report, dict):
        raise AdapterError("MALFORMED_SOURCE", "$", "JSON object", type(report).__name__, "Provide one native JSON report object.")
    explicit = report.get("schema")
    if isinstance(explicit, str):
        match = re.search(r"\.v([0-9]+)$", explicit)
        return explicit, match.group(1) if match else "unknown"
    if report.get("statusSchemaVersion") == 2 and "qaReady" in report:
        return "mtr.android_toolchain_status.v2", "2"
    if report.get("manifest_kind") == "mtr_source_content_fingerprint" and report.get("schema_version") == 1:
        return "mtr.source_content_fingerprint.v1", "1"
    if report.get("schema_version") == 1 and all(key in report for key in ("pass", "parent", "pages")):
        return "mtr.git_topology.v1", "1"
    if type(report.get("runtimeReady")) is bool:
        return "mtr.web_runtime_probe.legacy", "legacy"
    raise AdapterError(
        "UNSUPPORTED_SCHEMA",
        "schema",
        "registered current quality schema",
        explicit if explicit is not None else "missing/unrecognized",
        "Add an audited adapter and fixtures before accepting this report.",
    )


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or Path(__file__).with_name("quality_adapter_registry.json")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError("INVALID_REGISTRY", "registry", "readable JSON", str(registry_path), "Restore and validate the canonical adapter registry.") from exc
    if registry.get("contract") != "mtr.quality_adapter_registry" or registry.get("schema_version") != 1:
        raise AdapterError("INVALID_REGISTRY", "registry.contract", "mtr.quality_adapter_registry v1", registry.get("contract"), "Use the canonical v1 registry.")
    return registry


def _validate_context(context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise AdapterError("INVALID_CONTEXT", "$", "JSON object", type(context).__name__, "Provide an explicit evidence context.")
    def required(dotted_path: str, expected_type: type | tuple[type, ...]) -> Any:
        return _require_path(
            context,
            dotted_path,
            expected_type,
            error_code="INVALID_CONTEXT",
            suggested_fix="Provide a complete trusted evidence context.",
        )

    evidence_id = required("evidence_id", str)
    if not SAFE_ID.fullmatch(evidence_id):
        raise AdapterError("INVALID_CONTEXT", "evidence_id", "safe lowercase identifier", evidence_id, "Use lowercase letters, digits, dot, colon, underscore, or hyphen.")
    report_path = _safe_relative_path(required("source_report.relative_path", str), "source_report.relative_path")
    report_sha = required("source_report.sha256", str)
    source_commit = required("source.commit", str)
    content_version = required("source.content_version", str)
    expected_commit = required("expected_source_commit", str)
    if not HEX_64.fullmatch(report_sha) or not HEX_40.fullmatch(source_commit) or not HEX_40.fullmatch(expected_commit):
        raise AdapterError("INVALID_CONTEXT", "source hashes", "40-char commit and 64-char SHA-256", {"report_sha": report_sha, "commit": source_commit, "expected": expected_commit}, "Provide canonical hexadecimal identities.")
    platform = required("target.platform", str)
    identity = required("target.identity", str)
    profile = required("target.profile", str)
    if platform not in {"source", "static", "web", "android-emulator", "android-device"} or not identity or not profile:
        raise AdapterError("INVALID_CONTEXT", "target", "supported non-empty target", context.get("target"), "Use a canonical target platform, identity, and profile.")
    tool_path = _safe_relative_path(required("tool.relative_path", str), "tool.relative_path")
    tool_sha = required("tool.sha256", str)
    command_id = required("tool.command_id", str)
    strict = required("tool.strict", bool)
    flags = required("tool.flags", list)
    if not HEX_64.fullmatch(tool_sha) or not SAFE_ID.fullmatch(command_id) or any(not isinstance(flag, str) or not flag for flag in flags) or len(flags) != len(set(flags)):
        raise AdapterError("INVALID_CONTEXT", "tool", "safe path/hash/id and unique non-empty flags", context.get("tool"), "Provide normalized tool identity and invocation metadata.")
    started_text = required("timing.started_at", str)
    finished_text = required("timing.finished_at", str)
    started = _parse_timestamp(started_text, "timing.started_at")
    finished = _parse_timestamp(finished_text, "timing.finished_at")
    if finished < started:
        raise AdapterError("INVALID_CONTEXT", "timing", "finished_at >= started_at", context.get("timing"), "Correct the monotonic evidence timing.")
    mandatory = required("mandatory", bool)
    applicable = required("applicable", bool)
    fresh = required("fresh", bool)
    physical_authorized = required("physical_device_authorized", bool)
    return {
        "evidence_id": evidence_id,
        "source_report": {"relative_path": report_path, "sha256": report_sha.upper()},
        "source": {"commit": source_commit.lower(), "content_version": content_version},
        "expected_source_commit": expected_commit.lower(),
        "target": {"platform": platform, "identity": identity, "profile": profile},
        "tool": {"relative_path": tool_path, "sha256": tool_sha.upper(), "command_id": command_id, "strict": strict, "flags": flags},
        "timing": {"started_at": started_text, "finished_at": finished_text, "duration_ms": int((finished - started).total_seconds() * 1000)},
        "mandatory": mandatory,
        "applicable": applicable,
        "fresh": fresh,
        "physical_device_authorized": physical_authorized,
    }


def adapt_report(report: dict[str, Any], raw_context: dict[str, Any], registry_path: Path | None = None) -> dict[str, Any]:
    context = _validate_context(raw_context)
    source_schema, source_version = detect_source_schema(report)
    registry = load_registry(registry_path)
    matches = [entry for entry in registry.get("adapters", []) if entry.get("source_schema") == source_schema]
    if not matches:
        raise AdapterError("UNSUPPORTED_SCHEMA", "schema", "registered current quality schema", source_schema, "Add an audited adapter and fixtures before accepting this report.")
    entry = matches[0]
    if entry.get("support") != "active":
        raise AdapterError("NON_ACTIVE_SOURCE", "schema", "active quality evidence", source_schema, "Use the current authoritative validator rather than historical or runtime data.")
    handler_name = entry.get("handler")
    handler = HANDLERS.get(handler_name)
    if handler is None:
        raise AdapterError("INVALID_REGISTRY", "handler", "implemented adapter handler", handler_name, "Restore registry/code parity.")

    global_findings: list[dict[str, Any]] = []
    effective_fresh = context["fresh"] and context["source"]["commit"] == context["expected_source_commit"]
    if not context["applicable"]:
        global_findings.append(_finding("EVIDENCE_NOT_APPLICABLE", "BLOCKER", True, context["source_report"]["relative_path"], "applicable", True, False, "Use an explicitly applicable gate or wait for M01.4 not-applicable profile semantics."))
    if not context["fresh"]:
        global_findings.append(_finding("STALE_EVIDENCE", "BLOCKER", True, context["source_report"]["relative_path"], "fresh", True, False, "Regenerate evidence from the active source checkpoint."))
    if context["source"]["commit"] != context["expected_source_commit"]:
        global_findings.append(_finding("SOURCE_COMMIT_MISMATCH", "BLOCKER", True, context["source_report"]["relative_path"], "source.commit", context["expected_source_commit"], context["source"]["commit"], "Regenerate evidence from the accepted source commit."))
    expected_platform = entry.get("target_platform")
    if expected_platform != "mixed" and context["target"]["platform"] != expected_platform:
        global_findings.append(_finding("TARGET_IDENTITY_MISMATCH", "BLOCKER", True, context["source_report"]["relative_path"], "target.platform", expected_platform, context["target"]["platform"], "Use the platform required by the registered adapter."))
    if context["target"]["platform"] == "android-device" and not context["physical_device_authorized"]:
        global_findings.append(_finding("PHYSICAL_DEVICE_NOT_AUTHORIZED", "BLOCKER", True, context["source_report"]["relative_path"], "physical_device_authorized", True, False, "Use an emulator or obtain an explicit physical-device command."))

    native = handler(report, context)
    findings = global_findings + native["findings"]
    if global_findings or native["status"] == "BLOCKED":
        status = "BLOCKED"
    elif native["status"] == "FAIL":
        status = "FAIL"
    else:
        status = "PASS"
    reasons = list(native["reasons"])
    if global_findings:
        reasons.append("Global freshness, source, applicability, or target identity checks blocked acceptance.")

    envelope = {
        "schema_version": 1,
        "contract": CONTRACT,
        "evidence_id": context["evidence_id"],
        "adapter": {"id": entry["id"], "version": entry["version"]},
        "source_report": {
            "schema_name": source_schema,
            "schema_version": source_version,
            "relative_path": context["source_report"]["relative_path"],
            "sha256": context["source_report"]["sha256"],
        },
        "source": context["source"],
        "target": context["target"],
        "tool": context["tool"],
        "timing": context["timing"],
        "status": status,
        "mandatory": context["mandatory"],
        "applicable": context["applicable"],
        "fresh": effective_fresh,
        "metrics": native["metrics"],
        "findings": findings,
        "decision_reasons": reasons,
    }
    validate_envelope(envelope)
    return envelope


def validate_envelope(envelope: dict[str, Any]) -> None:
    """Dependency-free runtime guard matching the canonical envelope contract."""

    required = {
        "schema_version", "contract", "evidence_id", "adapter", "source_report", "source", "target", "tool", "timing",
        "status", "mandatory", "applicable", "fresh", "metrics", "findings", "decision_reasons",
    }
    if not isinstance(envelope, dict) or set(envelope) != required:
        raise AdapterError("INVALID_ENVELOPE", "$", sorted(required), sorted(envelope) if isinstance(envelope, dict) else type(envelope).__name__, "Emit exactly the canonical top-level fields.")
    if envelope["schema_version"] != 1 or envelope["contract"] != CONTRACT or not SAFE_ID.fullmatch(envelope["evidence_id"]):
        raise AdapterError("INVALID_ENVELOPE", "identity", "canonical v1 contract and safe evidence id", {key: envelope.get(key) for key in ("schema_version", "contract", "evidence_id")}, "Use canonical envelope identity values.")
    if envelope["status"] not in {"PASS", "FAIL", "BLOCKED"}:
        raise AdapterError("INVALID_ENVELOPE", "status", "PASS|FAIL|BLOCKED", envelope["status"], "Use a canonical fail-closed status.")
    for field in ("mandatory", "applicable", "fresh"):
        if type(envelope[field]) is not bool:
            raise AdapterError("INVALID_ENVELOPE", field, "boolean", envelope[field], "Use a JSON boolean.")
    source = envelope["source"]
    if not isinstance(source, dict) or set(source) != {"commit", "content_version"} or not HEX_40.fullmatch(str(source.get("commit", ""))) or not isinstance(source.get("content_version"), str) or not source["content_version"]:
        raise AdapterError("INVALID_ENVELOPE", "source", "commit and content version", source, "Bind evidence to canonical source identity.")
    source_report = envelope["source_report"]
    if not isinstance(source_report, dict) or set(source_report) != {"schema_name", "schema_version", "relative_path", "sha256"} or not HEX_64.fullmatch(str(source_report.get("sha256", ""))):
        raise AdapterError("INVALID_ENVELOPE", "source_report", "canonical source report identity", source_report, "Provide schema, contained path, and SHA-256.")
    _safe_relative_path(source_report["relative_path"], "source_report.relative_path")
    tool = envelope["tool"]
    if not isinstance(tool, dict) or set(tool) != {"relative_path", "sha256", "command_id", "strict", "flags"} or not HEX_64.fullmatch(str(tool.get("sha256", ""))) or type(tool.get("strict")) is not bool or not isinstance(tool.get("flags"), list):
        raise AdapterError("INVALID_ENVELOPE", "tool", "canonical tool identity", tool, "Provide a normalized tool record.")
    _safe_relative_path(tool["relative_path"], "tool.relative_path")
    timing = envelope["timing"]
    if not isinstance(timing, dict) or set(timing) != {"started_at", "finished_at", "duration_ms"} or type(timing.get("duration_ms")) is not int or timing["duration_ms"] < 0:
        raise AdapterError("INVALID_ENVELOPE", "timing", "canonical timing", timing, "Provide valid start, finish, and duration.")
    started = _parse_timestamp(timing["started_at"], "timing.started_at")
    finished = _parse_timestamp(timing["finished_at"], "timing.finished_at")
    if finished < started or timing["duration_ms"] != int((finished - started).total_seconds() * 1000):
        raise AdapterError("INVALID_ENVELOPE", "timing.duration_ms", int((finished - started).total_seconds() * 1000), timing["duration_ms"], "Recompute duration from start and finish.")
    if not isinstance(envelope["metrics"], dict) or not isinstance(envelope["findings"], list) or not isinstance(envelope["decision_reasons"], list) or not envelope["decision_reasons"]:
        raise AdapterError("INVALID_ENVELOPE", "payload", "metrics object, findings list, and reasons", None, "Emit complete decision evidence.")
    for finding in envelope["findings"]:
        expected_keys = {"code", "severity", "blocking", "path", "field", "expected", "actual", "suggested_fix"}
        if not isinstance(finding, dict) or set(finding) != expected_keys or finding.get("severity") not in {"INFO", "WARNING", "ERROR", "BLOCKER"} or type(finding.get("blocking")) is not bool:
            raise AdapterError("INVALID_ENVELOPE", "findings", "canonical finding objects", finding, "Emit a complete typed finding.")
    blocking = [finding for finding in envelope["findings"] if finding["blocking"]]
    if envelope["status"] == "PASS" and (not envelope["applicable"] or not envelope["fresh"] or blocking):
        raise AdapterError("INVALID_ENVELOPE", "status", "PASS only for applicable fresh evidence without blockers", envelope["status"], "Use FAIL or BLOCKED.")
    if envelope["status"] in {"FAIL", "BLOCKED"} and not blocking:
        raise AdapterError("INVALID_ENVELOPE", "findings", "at least one blocking finding for FAIL/BLOCKED", envelope["findings"], "Explain every non-pass decision with a blocking finding.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        context = json.loads(args.context.read_text(encoding="utf-8"))
        envelope = adapt_report(report, context, args.registry)
    except AdapterError as exc:
        print(json.dumps({"status": "ERROR", "error": exc.as_dict()}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        error = AdapterError("MALFORMED_SOURCE", "$", "readable JSON", str(exc), "Repair or regenerate the input document.")
        print(json.dumps({"status": "ERROR", "error": error.as_dict()}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if envelope["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
