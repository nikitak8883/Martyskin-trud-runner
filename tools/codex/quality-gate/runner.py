#!/usr/bin/env python3
"""Typed, shell-free and fail-closed MTR quality-gate runner."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from types import ModuleType
from typing import Any

from schema_engine import SchemaEngine, SchemaValidationError, sha256_file


SCHEMA_DIRECTORY_RELATIVE = Path("docs/global_modernization/v3/library/schemas")
ADAPTER_RELATIVE = Path("docs/global_modernization/v3/library/adapters/quality_evidence_adapter.py")
REGISTRY_RELATIVE = Path("docs/global_modernization/v3/library/adapters/quality_adapter_registry.json")
REQUIREMENTS_LOCK = Path(__file__).resolve().with_name("requirements.lock")
CONFIG_SCHEMA = "quality_gate_config.schema.json"
REPORT_SCHEMA = "quality_gate_report.schema.json"
ENVELOPE_SCHEMA = "quality_evidence_envelope.schema.json"
REGISTRY_SCHEMA = "quality_adapter_registry.schema.json"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")
HEX_40 = re.compile(r"^[0-9a-fA-F]{40}$")


class GateError(ValueError):
    """Typed fail-closed runner error."""

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
            "expected": _json_safe(self.expected),
            "actual": _json_safe(self.actual),
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True)
class EvidenceSpec:
    native_report_path: str
    tool_path: str
    target: dict[str, str]
    strict: bool
    flags: tuple[str, ...]
    applicable: bool


@dataclass(frozen=True)
class StepSpec:
    id: str
    mandatory: bool
    enabled: bool
    executable: str
    arguments: tuple[str, ...]
    working_directory: str
    timeout_seconds: int
    expected_exit_codes: tuple[int, ...]
    artifact_paths: tuple[str, ...]
    evidence: EvidenceSpec | None


@dataclass(frozen=True)
class GateConfig:
    schema_version: int
    contract: str
    gate_id: str
    artifact_directory: str
    steps: tuple[StepSpec, ...]


@dataclass(frozen=True)
class FileIdentity:
    sha256: str
    bytes: int
    modified_ns: int


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _is_unc(value: str) -> bool:
    return value.startswith("\\\\") or value.startswith("//")


def _is_windows_root_or_device_path(value: str) -> bool:
    normalized = value.replace("/", "\\").casefold()
    return normalized.startswith("\\??\\") or normalized.startswith("\\device\\") or (
        normalized.startswith("\\") and not normalized.startswith("\\\\")
    )


def _validate_path_text(value: Any, field: str, *, relative_only: bool) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise GateError("INVALID_PATH", field, "non-empty path up to 4096 characters", value, "Use a bounded path string.")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise GateError("INVALID_PATH", field, "path without control characters", value, "Remove NUL/newline characters.")
    if _is_unc(value):
        raise GateError("UNC_PATH_REJECTED", field, "local path", value, "Use a local project or executable path, not a network share.")
    if _is_windows_root_or_device_path(value):
        raise GateError(
            "WINDOWS_DEVICE_PATH_REJECTED",
            field,
            "drive-qualified or project-relative path",
            value,
            "Do not use drive-root-relative or Windows device namespace paths.",
        )
    windows = PureWindowsPath(value)
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if windows.drive and not windows.is_absolute():
        raise GateError("DRIVE_RELATIVE_PATH_REJECTED", field, "absolute drive path or project-relative path", value, "Do not use ambiguous Windows drive-relative syntax such as C:folder.")
    if any(part == ".." for part in parts):
        raise GateError("PATH_TRAVERSAL", field, "path without '..' components", value, "Keep every configured path inside the project root.")
    if relative_only and (Path(value).is_absolute() or windows.is_absolute() or bool(windows.drive)):
        raise GateError("ABSOLUTE_PATH_REJECTED", field, "project-relative path", value, "Use a path relative to project root.")
    colon_parts = parts[1:] if windows.drive else parts
    if any(":" in part for part in colon_parts):
        raise GateError("ADS_PATH_REJECTED", field, "path without alternate-data-stream syntax", value, "Remove ':' from path components.")
    return value


def _ensure_contained(project_root: Path, candidate: Path, field: str) -> Path:
    root = project_root.resolve(strict=True)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GateError("PATH_OUTSIDE_PROJECT", field, str(root), str(resolved), "Keep cwd, reports and artifacts inside project root.") from exc
    return resolved


def resolve_project_path(
    project_root: Path,
    raw_path: str,
    field: str,
    *,
    must_exist: bool = False,
    expect_directory: bool = False,
) -> Path:
    _validate_path_text(raw_path, field, relative_only=True)
    candidate = _ensure_contained(project_root, project_root / Path(raw_path), field)
    if must_exist and not candidate.exists():
        raise GateError("PATH_NOT_FOUND", field, "existing contained path", raw_path, "Create or restore the required project path.")
    if must_exist and expect_directory and not candidate.is_dir():
        raise GateError("NOT_A_DIRECTORY", field, "existing directory", raw_path, "Use a project directory.")
    if must_exist and not expect_directory and not candidate.is_file():
        raise GateError("NOT_A_FILE", field, "existing file", raw_path, "Use a project file.")
    return candidate


def resolve_cli_path(project_root: Path, raw_path: str, field: str, *, must_exist: bool = False) -> Path:
    _validate_path_text(raw_path, field, relative_only=False)
    supplied = Path(raw_path)
    candidate = supplied if supplied.is_absolute() else project_root / supplied
    candidate = _ensure_contained(project_root, candidate, field)
    if must_exist and not candidate.is_file():
        raise GateError("PATH_NOT_FOUND", field, "existing contained file", raw_path, "Use a file inside project root.")
    return candidate


def project_relative(project_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(project_root.resolve(strict=True)).as_posix()


def _resolve_executable(project_root: Path, value: str) -> Path:
    _validate_path_text(value, "step.executable", relative_only=False)
    windows = PureWindowsPath(value)
    supplied = Path(value)
    has_separator = "/" in value or "\\" in value
    if supplied.is_absolute() or windows.is_absolute() or bool(windows.drive):
        executable = supplied.resolve(strict=False)
    elif has_separator:
        executable = resolve_project_path(project_root, value, "step.executable", must_exist=True)
    else:
        if not re.fullmatch(r"[A-Za-z0-9._+\-]+", value):
            raise GateError("INVALID_EXECUTABLE_NAME", "step.executable", "safe basename or explicit path", value, "Remove shell syntax from the executable field.")
        located = shutil.which(value)
        if not located:
            raise GateError("EXECUTABLE_NOT_FOUND", "step.executable", "executable available on PATH", value, "Install the tool or configure a valid executable.")
        executable = Path(located).resolve(strict=True)
    if _is_unc(str(executable)):
        raise GateError("UNC_PATH_REJECTED", "step.executable", "local executable", str(executable), "Use a local executable.")
    if not executable.is_file():
        raise GateError("EXECUTABLE_NOT_FOUND", "step.executable", "existing executable file", value, "Install or restore the executable.")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise GateError("EXECUTABLE_NOT_EXECUTABLE", "step.executable", "executable file", value, "Grant execute permission or select a valid executable.")
    if os.name == "nt" and executable.suffix.lower() in {".bat", ".cmd"}:
        raise GateError("IMPLICIT_SHELL_REJECTED", "step.executable", "native executable", value, "Invoke powershell.exe with a contained script argument instead of a batch file.")
    return executable


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    payload = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(path, payload)


def _load_json_object(path: Path, field: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError("MALFORMED_JSON", field, "readable JSON object", str(exc), "Repair or regenerate the JSON file.") from exc
    if not isinstance(document, dict):
        raise GateError("MALFORMED_JSON", field, "top-level JSON object", type(document).__name__, "Emit a JSON object.")
    return document


def _parse_config(document: dict[str, Any]) -> GateConfig:
    steps: list[StepSpec] = []
    step_ids: set[str] = set()
    for raw_step in document["steps"]:
        step_id = raw_step["id"]
        if step_id in step_ids:
            raise GateError("DUPLICATE_STEP_ID", "steps.id", "unique step IDs", step_id, "Rename the duplicate step.")
        step_ids.add(step_id)
        raw_evidence = raw_step.get("evidence")
        evidence = None
        if raw_evidence is not None:
            evidence = EvidenceSpec(
                native_report_path=raw_evidence["native_report_path"],
                tool_path=raw_evidence["tool_path"],
                target=dict(raw_evidence["target"]),
                strict=raw_evidence["strict"],
                flags=tuple(raw_evidence["flags"]),
                applicable=raw_evidence["applicable"],
            )
        steps.append(
            StepSpec(
                id=step_id,
                mandatory=raw_step["mandatory"],
                enabled=raw_step["enabled"],
                executable=raw_step["executable"],
                arguments=tuple(raw_step["arguments"]),
                working_directory=raw_step["working_directory"],
                timeout_seconds=raw_step["timeout_seconds"],
                expected_exit_codes=tuple(raw_step["expected_exit_codes"]),
                artifact_paths=tuple(raw_step.get("artifact_paths", [])),
                evidence=evidence,
            )
        )
    return GateConfig(
        schema_version=document["schema_version"],
        contract=document["contract"],
        gate_id=document["gate_id"],
        artifact_directory=document["artifact_directory"],
        steps=tuple(steps),
    )


def _identity(path: Path) -> FileIdentity | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return FileIdentity(sha256=sha256_file(path), bytes=stat.st_size, modified_ns=stat.st_mtime_ns)


def _artifact(project_root: Path, path: Path, kind: str) -> dict[str, Any]:
    identity = _identity(path)
    if identity is None:
        raise GateError("ARTIFACT_NOT_FOUND", "artifact", "existing file", str(path), "Regenerate the declared artifact.")
    return {
        "kind": kind,
        "relative_path": project_relative(project_root, path),
        "sha256": identity.sha256,
        "bytes": identity.bytes,
    }


def _finding(
    code: str,
    severity: str,
    blocking: bool,
    step_id: str | None,
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
        "step_id": step_id,
        "path": path,
        "field": field,
        "expected": _json_safe(expected),
        "actual": _json_safe(actual),
        "suggested_fix": suggested_fix,
    }


def _gate_error_finding(error: GateError, step_id: str | None, path: str = "") -> dict[str, Any]:
    return _finding(
        error.code,
        "BLOCKER",
        True,
        step_id,
        path,
        error.field,
        error.expected,
        error.actual,
        error.suggested_fix,
    )


def _temporary_capture(final_path: Path) -> Path:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{final_path.name}.", suffix=".tmp", dir=final_path.parent)
    os.close(descriptor)
    return Path(name)


def _finalize_capture(temporary: Path, final_path: Path) -> None:
    with temporary.open("ab") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, final_path)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        taskkill = system_root / "System32" / "taskkill.exe"
        if taskkill.is_file():
            try:
                subprocess.run(
                    [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (OSError, subprocess.SubprocessError):
                pass
        if process.poll() is None:
            try:
                process.kill()
            except (OSError, ProcessLookupError):
                pass
    else:
        try:
            process_group = os.getpgid(process.pid)
            os.killpg(process_group, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                process.terminate()
            except (OSError, ProcessLookupError):
                pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                try:
                    process.kill()
                except (OSError, ProcessLookupError):
                    pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except (OSError, ProcessLookupError):
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


def _validate_output_topology(
    project_root: Path,
    config_path: Path,
    output_path: Path,
    artifact_directory: Path,
    config: GateConfig,
) -> dict[Path, tuple[str, FileIdentity]]:
    protected_inputs = {
        config_path.resolve(strict=True): "gate config",
        (project_root / ADAPTER_RELATIVE).resolve(strict=True): "M01.2 adapter",
        (project_root / REGISTRY_RELATIVE).resolve(strict=True): "adapter registry",
        REQUIREMENTS_LOCK.resolve(strict=True): "validator lock",
    }
    for schema_path in (project_root / SCHEMA_DIRECTORY_RELATIVE).glob("*.schema.json"):
        protected_inputs[schema_path.resolve(strict=True)] = f"canonical schema {schema_path.name}"
    for step in config.steps:
        if step.enabled and step.evidence is not None:
            tool_path = resolve_project_path(project_root, step.evidence.tool_path, f"steps.{step.id}.evidence.tool_path", must_exist=True)
            protected_inputs[tool_path.resolve(strict=True)] = f"tool input for {step.id}"

    owned_outputs: dict[Path, str] = {}

    def register(path: Path, owner: str) -> None:
        resolved = _ensure_contained(project_root, path, owner)
        protected_owner = protected_inputs.get(resolved)
        if protected_owner is not None:
            raise GateError("OUTPUT_INPUT_COLLISION", owner, "path distinct from protected input", protected_owner, "Choose a dedicated generated-output path.")
        previous = owned_outputs.get(resolved)
        if previous is not None:
            raise GateError("OUTPUT_PATH_COLLISION", owner, "unique generated-output path", previous, "Give every capture, native report and declared artifact its own path.")
        owned_outputs[resolved] = owner

    register(output_path, "gate report")
    for step in config.steps:
        register(artifact_directory / f"{step.id}.stdout.txt", f"stdout capture for {step.id}")
        register(artifact_directory / f"{step.id}.stderr.txt", f"stderr capture for {step.id}")
        if not step.enabled:
            continue
        if step.evidence is not None:
            register(
                resolve_project_path(project_root, step.evidence.native_report_path, f"steps.{step.id}.evidence.native_report_path"),
                f"native report for {step.id}",
            )
        for artifact_path in step.artifact_paths:
            register(
                resolve_project_path(project_root, artifact_path, f"steps.{step.id}.artifact_paths"),
                f"declared artifact for {step.id}",
            )
    snapshots: dict[Path, tuple[str, FileIdentity]] = {}
    for path, label in protected_inputs.items():
        identity = _identity(path)
        if identity is None:
            raise GateError("PROTECTED_INPUT_MISSING", label, "existing immutable input", str(path), "Restore the runner input before execution.")
        snapshots[path] = (label, identity)
    return snapshots


def _load_adapter(project_root: Path) -> ModuleType:
    adapter_path = resolve_project_path(project_root, ADAPTER_RELATIVE.as_posix(), "adapter", must_exist=True)
    specification = importlib.util.spec_from_file_location("mtr_quality_evidence_adapter", adapter_path)
    if specification is None or specification.loader is None:
        raise GateError("ADAPTER_LOAD_FAILED", "adapter", "loadable Python module", str(adapter_path), "Restore the M01.2 adapter module.")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _argument_matches_tool(arguments: tuple[str, ...], executable: Path, tool: Path, cwd: Path, root: Path) -> bool:
    if executable.resolve(strict=False) == tool.resolve(strict=False):
        return True
    for argument in arguments:
        if not argument or argument.startswith("-") or "\x00" in argument:
            continue
        supplied = Path(argument)
        candidates = [supplied] if supplied.is_absolute() else [cwd / supplied, root / supplied]
        for candidate in candidates:
            try:
                if candidate.resolve(strict=False) == tool.resolve(strict=False):
                    return True
            except OSError:
                continue
    return False


def _declared_flags_present(arguments: tuple[str, ...], flags: tuple[str, ...]) -> list[str]:
    actual = {value.lower() if os.name == "nt" else value for value in arguments}
    return [flag for flag in flags if (flag.lower() if os.name == "nt" else flag) not in actual]


def _adapt_evidence(
    *,
    project_root: Path,
    adapter: ModuleType,
    schema_engine: SchemaEngine,
    step: StepSpec,
    executable: Path,
    cwd: Path,
    report_path: Path,
    pre_identity: FileIdentity | None,
    started_at: str,
    finished_at: str,
    source_commit: str,
    expected_source_commit: str,
    content_version: str,
    allow_physical_device: bool,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    evidence = step.evidence
    if evidence is None:
        return None, []
    findings: list[dict[str, Any]] = []
    after_identity = _identity(report_path)
    if after_identity is None:
        findings.append(
            _finding("NATIVE_REPORT_MISSING", "BLOCKER", True, step.id, evidence.native_report_path, "evidence.native_report_path", "fresh JSON report", "missing", "Regenerate the native report in this step.")
        )
        return None, findings
    fresh = pre_identity is None or pre_identity != after_identity
    tool_path = resolve_project_path(project_root, evidence.tool_path, f"steps.{step.id}.evidence.tool_path", must_exist=True)
    if not _argument_matches_tool(step.arguments, executable, tool_path, cwd, project_root):
        findings.append(
            _finding("TOOL_IDENTITY_NOT_IN_COMMAND", "BLOCKER", True, step.id, evidence.tool_path, "evidence.tool_path", "the hashed tool must be the executable or one argument", list(step.arguments), "Bind evidence to the tool that was actually executed.")
        )
        return None, findings
    missing_flags = _declared_flags_present(step.arguments, evidence.flags)
    if missing_flags:
        findings.append(
            _finding("DECLARED_FLAG_NOT_EXECUTED", "BLOCKER", True, step.id, evidence.tool_path, "evidence.flags", list(evidence.flags), {"arguments": list(step.arguments), "missing": missing_flags}, "Place every declared strict flag in the actual argument array.")
        )
        return None, findings
    try:
        native_report = _load_json_object(report_path, f"steps.{step.id}.native_report")
        context = {
            "evidence_id": f"{step.id}.evidence",
            "source_report": {
                "relative_path": project_relative(project_root, report_path),
                "sha256": after_identity.sha256,
            },
            "source": {
                "commit": source_commit,
                "content_version": content_version,
            },
            "expected_source_commit": expected_source_commit,
            "target": evidence.target,
            "tool": {
                "relative_path": project_relative(project_root, tool_path),
                "sha256": sha256_file(tool_path),
                "command_id": step.id,
                "strict": evidence.strict,
                "flags": list(evidence.flags),
            },
            "timing": {
                "started_at": started_at,
                "finished_at": finished_at,
            },
            "mandatory": step.mandatory,
            "applicable": evidence.applicable,
            "fresh": fresh,
            "physical_device_authorized": allow_physical_device,
        }
        registry_path = resolve_project_path(project_root, REGISTRY_RELATIVE.as_posix(), "adapter_registry", must_exist=True)
        envelope = adapter.adapt_report(native_report, context, registry_path)
        adapter.validate_envelope(envelope)
        schema_engine.validate(ENVELOPE_SCHEMA, envelope)
    except GateError as exc:
        findings.append(_gate_error_finding(exc, step.id, evidence.native_report_path))
        return None, findings
    except SchemaValidationError as exc:
        findings.append(
            _finding("EVIDENCE_SCHEMA_INVALID", "BLOCKER", True, step.id, evidence.native_report_path, "evidence_envelope", "canonical Draft 2020-12 envelope", exc.as_dict(), "Fix the adapter or canonical schema mismatch.")
        )
        return None, findings
    except adapter.AdapterError as exc:
        detail = exc.as_dict()
        findings.append(
            _finding(detail["code"], "BLOCKER", True, step.id, evidence.native_report_path, detail["field"], detail["expected"], detail["actual"], detail["suggested_fix"])
        )
        return None, findings
    for item in envelope["findings"]:
        findings.append(
            _finding(
                item["code"],
                item["severity"],
                item["blocking"],
                step.id,
                item["path"],
                item["field"],
                item["expected"],
                item["actual"],
                item["suggested_fix"],
            )
        )
    return envelope, findings


def _run_step(
    *,
    project_root: Path,
    artifact_directory: Path,
    step: StepSpec,
    adapter: ModuleType,
    schema_engine: SchemaEngine,
    source_commit: str,
    expected_source_commit: str,
    content_version: str,
    allow_physical_device: bool,
) -> dict[str, Any]:
    stdout_path = resolve_project_path(project_root, project_relative(project_root, artifact_directory / f"{step.id}.stdout.txt"), f"steps.{step.id}.stdout")
    stderr_path = resolve_project_path(project_root, project_relative(project_root, artifact_directory / f"{step.id}.stderr.txt"), f"steps.{step.id}.stderr")
    cwd = resolve_project_path(project_root, step.working_directory, f"steps.{step.id}.working_directory", must_exist=True, expect_directory=True)
    evidence_report_path = None
    evidence_pre = None
    if step.evidence is not None:
        evidence_report_path = resolve_project_path(project_root, step.evidence.native_report_path, f"steps.{step.id}.evidence.native_report_path")
        evidence_pre = _identity(evidence_report_path)
    declared_paths = [resolve_project_path(project_root, path, f"steps.{step.id}.artifact_paths") for path in step.artifact_paths]
    declared_pre = {path: _identity(path) for path in declared_paths}

    started_wall = _utc_now()
    started_monotonic = time.monotonic_ns()
    executable: Path | None = None
    exit_code: int | None = None
    timed_out = False
    status = "PASS"
    findings: list[dict[str, Any]] = []
    reasons: list[str] = []
    stdout_temporary = _temporary_capture(stdout_path)
    stderr_temporary = _temporary_capture(stderr_path)
    try:
        if not step.enabled:
            status = "SKIPPED"
            blocking = step.mandatory
            findings.append(
                _finding("MANDATORY_STEP_SKIPPED" if blocking else "OPTIONAL_STEP_SKIPPED", "BLOCKER" if blocking else "INFO", blocking, step.id, "", "enabled", True if blocking else "optional", False, "Enable the mandatory step or keep it explicitly optional.")
            )
            reasons.append("Step was disabled by typed configuration.")
        else:
            try:
                executable = _resolve_executable(project_root, step.executable)
            except GateError as exc:
                status = "BLOCKED"
                findings.append(_gate_error_finding(exc, step.id))
                reasons.append("Executable resolution failed closed.")
            if executable is not None:
                environment = os.environ.copy()
                environment.setdefault("PYTHONUTF8", "1")
                creationflags = 0
                popen_options: dict[str, Any] = {}
                if os.name == "nt":
                    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
                else:
                    popen_options["start_new_session"] = True
                try:
                    with stdout_temporary.open("wb") as stdout_handle, stderr_temporary.open("wb") as stderr_handle:
                        process = subprocess.Popen(
                            [str(executable), *step.arguments],
                            cwd=cwd,
                            env=environment,
                            stdin=subprocess.DEVNULL,
                            stdout=stdout_handle,
                            stderr=stderr_handle,
                            shell=False,
                            close_fds=True,
                            creationflags=creationflags,
                            **popen_options,
                        )
                        try:
                            exit_code = process.wait(timeout=step.timeout_seconds)
                        except subprocess.TimeoutExpired:
                            timed_out = True
                            _terminate_process_tree(process)
                            exit_code = process.returncode
                except OSError as exc:
                    status = "BLOCKED"
                    findings.append(
                        _finding("PROCESS_START_FAILED", "BLOCKER", True, step.id, "", "command", "startable shell-free process", str(exc), "Repair the executable, arguments, cwd or OS permissions.")
                    )
                    reasons.append("Process could not be started.")
                if timed_out:
                    status = "BLOCKED"
                    findings.append(
                        _finding("PROCESS_TREE_TIMEOUT", "BLOCKER", True, step.id, "", "timeout_seconds", f"completion within {step.timeout_seconds}s", "timed out and process tree terminated", "Fix the hang or raise the explicit bounded timeout.")
                    )
                    reasons.append("Process exceeded its timeout and its process tree was terminated.")
                elif status != "BLOCKED" and exit_code not in step.expected_exit_codes:
                    status = "FAIL"
                    findings.append(
                        _finding("UNEXPECTED_EXIT_CODE", "ERROR", True, step.id, "", "exit_code", list(step.expected_exit_codes), exit_code, "Fix the command failure before accepting the gate.")
                    )
                    reasons.append("Process returned an unexpected exit code.")
                elif status == "PASS":
                    reasons.append("Process completed with an expected exit code.")
    finally:
        _finalize_capture(stdout_temporary, stdout_path)
        _finalize_capture(stderr_temporary, stderr_path)

    finished_wall = _utc_now()
    duration_ms = max(0, (time.monotonic_ns() - started_monotonic) // 1_000_000)
    artifacts = [_artifact(project_root, stdout_path, "stdout"), _artifact(project_root, stderr_path, "stderr")]

    if step.enabled and executable is not None and not timed_out:
        for path in declared_paths:
            after = _identity(path)
            before = declared_pre[path]
            if after is None:
                status = "BLOCKED"
                findings.append(
                    _finding("DECLARED_ARTIFACT_MISSING", "BLOCKER", True, step.id, project_relative(project_root, path), "artifact_paths", "fresh artifact", "missing", "Regenerate the declared artifact.")
                )
            elif before is not None and before == after:
                status = "BLOCKED"
                findings.append(
                    _finding("DECLARED_ARTIFACT_STALE", "BLOCKER", True, step.id, project_relative(project_root, path), "artifact_paths", "artifact changed by this step", "unchanged pre-existing file", "Make the command regenerate its declared output.")
                )
            else:
                artifacts.append(_artifact(project_root, path, "declared"))

    envelope = None
    if step.enabled and executable is not None and evidence_report_path is not None and not timed_out:
        envelope, evidence_findings = _adapt_evidence(
            project_root=project_root,
            adapter=adapter,
            schema_engine=schema_engine,
            step=step,
            executable=executable,
            cwd=cwd,
            report_path=evidence_report_path,
            pre_identity=evidence_pre,
            started_at=_iso(started_wall),
            finished_at=_iso(finished_wall),
            source_commit=source_commit,
            expected_source_commit=expected_source_commit,
            content_version=content_version,
            allow_physical_device=allow_physical_device,
        )
        findings.extend(evidence_findings)
        if _identity(evidence_report_path) is not None:
            artifacts.append(_artifact(project_root, evidence_report_path, "native_report"))
        if envelope is None:
            status = "BLOCKED"
            reasons.append("Canonical evidence adaptation failed closed.")
        elif envelope["status"] == "BLOCKED":
            status = "BLOCKED"
            reasons.extend(envelope["decision_reasons"])
        elif envelope["status"] == "FAIL" and status != "BLOCKED":
            status = "FAIL"
            reasons.extend(envelope["decision_reasons"])
        else:
            reasons.extend(envelope["decision_reasons"])

    if not reasons:
        reasons.append("Step completed without a runnable command.")
    return {
        "id": step.id,
        "mandatory": step.mandatory,
        "enabled": step.enabled,
        "status": status,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "command": {
            "executable": step.executable,
            "resolved_executable": str(executable) if executable is not None else None,
            "arguments": list(step.arguments),
            "working_directory": step.working_directory.replace("\\", "/"),
            "timeout_seconds": step.timeout_seconds,
            "expected_exit_codes": list(step.expected_exit_codes),
        },
        "timing": {
            "started_at": _iso(started_wall),
            "finished_at": _iso(finished_wall),
            "duration_ms": duration_ms,
        },
        "artifacts": artifacts,
        "evidence_envelope": envelope,
        "findings": findings,
        "decision_reasons": list(dict.fromkeys(reasons)),
    }


def _overall_status(
    steps: list[dict[str, Any]],
    source_matches: bool,
    dirty_source_allowed: bool,
    source_stable: bool,
    protected_inputs_stable: bool,
) -> str:
    if not source_matches or not dirty_source_allowed or not source_stable or not protected_inputs_stable:
        return "BLOCKED"
    mandatory = [step for step in steps if step["mandatory"]]
    if any(step["status"] in {"BLOCKED", "SKIPPED"} for step in mandatory):
        return "BLOCKED"
    if any(step["status"] == "FAIL" for step in mandatory):
        return "FAIL"
    return "PASS"


def semantic_projection(report: dict[str, Any]) -> dict[str, Any]:
    """Stable comparison surface that intentionally excludes clocks and run IDs."""

    return {
        "gate_id": report["gate_id"],
        "status": report["status"],
        "source_matches": report["source"]["matches_expected"],
        "source_stable": report["source"]["stable_during_run"],
        "source_dirty": report["source"]["dirty"],
        "dirty_authorized": report["source"]["dirty_authorized"],
        "steps": [
            {
                "id": step["id"],
                "mandatory": step["mandatory"],
                "enabled": step["enabled"],
                "status": step["status"],
                "exit_code": step["exit_code"],
                "timed_out": step["timed_out"],
                "finding_codes": [finding["code"] for finding in step["findings"]],
                "evidence_status": step["evidence_envelope"]["status"] if step["evidence_envelope"] else None,
            }
            for step in report["steps"]
        ],
    }


def run_gate(
    *,
    project_root: Path,
    config_path: Path,
    output_path: Path,
    source_commit: str,
    expected_source_commit: str,
    content_version: str,
    source_dirty: bool,
    allow_physical_device: bool = False,
    allow_dirty_source: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = project_root.resolve(strict=True)
    if not HEX_40.fullmatch(source_commit) or not HEX_40.fullmatch(expected_source_commit):
        raise GateError("INVALID_SOURCE_COMMIT", "source_commit", "40 hexadecimal characters", {"source": source_commit, "expected": expected_source_commit}, "Use exact Git commit identities.")
    if not content_version or len(content_version) > 256:
        raise GateError("INVALID_CONTENT_VERSION", "content_version", "non-empty value up to 256 characters", content_version, "Use the canonical content version.")
    config_path = _ensure_contained(root, config_path, "config_path")
    output_path = _ensure_contained(root, output_path, "output_path")
    if not config_path.is_file():
        raise GateError("CONFIG_NOT_FOUND", "config_path", "existing contained JSON file", str(config_path), "Provide a valid typed gate configuration.")
    if output_path == config_path:
        raise GateError("OUTPUT_COLLISION", "output_path", "path distinct from config", str(output_path), "Choose a dedicated report path.")
    if output_path.suffix.lower() != ".json":
        raise GateError("INVALID_REPORT_EXTENSION", "output_path", ".json file", str(output_path), "Use a .json path for the atomic machine-readable report.")

    schema_engine = SchemaEngine(root / SCHEMA_DIRECTORY_RELATIVE, REQUIREMENTS_LOCK)
    engine_identity = schema_engine.assert_isolated_runtime()
    config_document = _load_json_object(config_path, "config_path")
    try:
        schema_engine.validate(CONFIG_SCHEMA, config_document)
    except SchemaValidationError as exc:
        raise GateError("CONFIG_SCHEMA_INVALID", "config", "canonical typed configuration", exc.as_dict(), "Fix every reported schema issue before execution.") from exc
    config = _parse_config(config_document)
    if not SAFE_ID.fullmatch(config.gate_id):
        raise GateError("INVALID_GATE_ID", "gate_id", "safe lowercase identifier", config.gate_id, "Use a canonical gate identifier.")

    registry_path = resolve_project_path(root, REGISTRY_RELATIVE.as_posix(), "adapter_registry", must_exist=True)
    registry = _load_json_object(registry_path, "adapter_registry")
    try:
        schema_engine.validate(REGISTRY_SCHEMA, registry)
    except SchemaValidationError as exc:
        raise GateError("REGISTRY_SCHEMA_INVALID", "adapter_registry", "canonical registry", exc.as_dict(), "Restore registry/schema parity.") from exc
    adapter = _load_adapter(root)

    artifact_directory = resolve_project_path(root, config.artifact_directory, "artifact_directory")
    if artifact_directory == root:
        raise GateError("ARTIFACT_ROOT_REJECTED", "artifact_directory", "dedicated project subdirectory", config.artifact_directory, "Keep generated captures out of the project root.")
    artifact_directory.mkdir(parents=True, exist_ok=True)
    artifact_directory = _ensure_contained(root, artifact_directory, "artifact_directory")
    if not artifact_directory.is_dir():
        raise GateError("NOT_A_DIRECTORY", "artifact_directory", "contained directory", str(artifact_directory), "Use a writable project directory.")
    if output_path == artifact_directory or artifact_directory in output_path.parents and output_path.name.endswith((".stdout.txt", ".stderr.txt")):
        raise GateError("OUTPUT_COLLISION", "output_path", "dedicated JSON report path", str(output_path), "Keep the summary separate from step captures.")
    protected_input_snapshots = _validate_output_topology(root, config_path, output_path, artifact_directory, config)
    config_hash = protected_input_snapshots[config_path.resolve(strict=True)][1].sha256

    started = time.monotonic_ns()
    source_commit = source_commit.lower()
    expected_source_commit = expected_source_commit.lower()
    step_results = [
        _run_step(
            project_root=root,
            artifact_directory=artifact_directory,
            step=step,
            adapter=adapter,
            schema_engine=schema_engine,
            source_commit=source_commit,
            expected_source_commit=expected_source_commit,
            content_version=content_version,
            allow_physical_device=allow_physical_device,
        )
        for step in config.steps
    ]
    source_matches = source_commit == expected_source_commit
    source_probe_error: GateError | None = None
    final_source_commit: str | None = None
    final_source_dirty: bool | None = None
    try:
        final_source_commit = _git_output(root, ["rev-parse", "HEAD"]).lower()
        final_source_dirty = bool(_git_output(root, ["status", "--porcelain", "--untracked-files=normal", "--", "."]))
        source_stable = final_source_commit == source_commit and final_source_dirty == bool(source_dirty)
    except GateError as exc:
        source_probe_error = exc
        source_stable = False

    changed_inputs: list[dict[str, Any]] = []
    for path, (label, before) in protected_input_snapshots.items():
        after = _identity(path)
        if after != before:
            changed_inputs.append(
                {
                    "label": label,
                    "path": project_relative(root, path),
                    "before": before.sha256,
                    "after": after.sha256 if after is not None else None,
                }
            )
    protected_inputs_stable = not changed_inputs
    dirty_source_allowed = not source_dirty or allow_dirty_source
    overall = _overall_status(step_results, source_matches, dirty_source_allowed, source_stable, protected_inputs_stable)
    top_findings: list[dict[str, Any]] = []
    if not source_matches:
        top_findings.append(
            _finding("SOURCE_COMMIT_MISMATCH", "BLOCKER", True, None, "", "source.commit", expected_source_commit, source_commit, "Run against the accepted source commit or update the explicit expected identity.")
        )
    if source_dirty and not allow_dirty_source:
        top_findings.append(
            _finding("DIRTY_SOURCE_NOT_AUTHORIZED", "BLOCKER", True, None, "", "source.dirty", False, True, "Commit or revert project changes, or use the explicit development-only allow-dirty switch.")
        )
    if not source_stable:
        if source_probe_error is not None:
            top_findings.append(
                _finding("SOURCE_REVALIDATION_FAILED", "BLOCKER", True, None, "", "source.stable_during_run", True, source_probe_error.as_dict(), "Restore Git availability and rerun the complete gate.")
            )
        else:
            top_findings.append(
                _finding(
                    "SOURCE_CHANGED_DURING_RUN",
                    "BLOCKER",
                    True,
                    None,
                    "",
                    "source.stable_during_run",
                    {"commit": source_commit, "dirty": bool(source_dirty)},
                    {"commit": final_source_commit, "dirty": final_source_dirty},
                    "Discard this report and rerun against an unchanged source tree.",
                )
            )
    for changed in changed_inputs:
        top_findings.append(
            _finding(
                "PROTECTED_INPUT_CHANGED_DURING_RUN",
                "BLOCKER",
                True,
                None,
                changed["path"],
                "protected_inputs",
                {"label": changed["label"], "sha256": changed["before"]},
                {"sha256": changed["after"]},
                "Restore the canonical input and rerun the complete gate.",
            )
        )
    for step_result in step_results:
        for item in step_result["findings"]:
            promoted = dict(item)
            promoted["blocking"] = bool(item["blocking"] and step_result["mandatory"])
            top_findings.append(promoted)
    artifacts = [artifact for step_result in step_results for artifact in step_result["artifacts"]]
    if overall == "PASS":
        decision_reasons = ["All mandatory steps completed without FAIL, BLOCKED or SKIPPED status."]
    elif overall == "FAIL":
        decision_reasons = ["At least one mandatory step reported a product or validation failure."]
    else:
        decision_reasons = ["The gate was blocked by missing, skipped, stale, timed-out, source-drifted or otherwise untrusted evidence."]
    if run_id is None:
        stamp = _utc_now().strftime("%Y%m%d%H%M%S")
        run_id = f"qg.{stamp}.{config_hash[:12].lower()}"
    if not SAFE_ID.fullmatch(run_id):
        raise GateError("INVALID_RUN_ID", "run_id", "safe lowercase identifier", run_id, "Use lowercase letters, digits, dot, colon, underscore or hyphen.")
    report = {
        "schema_version": 1,
        "contract": "mtr.quality_gate_report",
        "run_id": run_id,
        "gate_id": config.gate_id,
        "generated_at": _iso(_utc_now()),
        "status": overall,
        "source": {
            "commit": source_commit,
            "expected_commit": expected_source_commit,
            "matches_expected": source_matches,
            "content_version": content_version,
            "dirty": bool(source_dirty),
            "dirty_authorized": bool(allow_dirty_source),
            "stable_during_run": source_stable,
        },
        "config": {
            "relative_path": project_relative(root, config_path),
            "sha256": config_hash,
        },
        "schema_engine": engine_identity,
        "duration_ms": max(0, (time.monotonic_ns() - started) // 1_000_000),
        "steps": step_results,
        "artifacts": artifacts,
        "findings": top_findings,
        "decision_reasons": decision_reasons,
    }
    try:
        schema_engine.validate(REPORT_SCHEMA, report)
    except SchemaValidationError as exc:
        raise GateError("REPORT_SCHEMA_INVALID", "report", "canonical quality-gate report", exc.as_dict(), "Fix the runner/schema invariant before replacing the prior report.") from exc
    atomic_write_json(output_path, report)
    return report


def _git_output(project_root: Path, arguments: list[str]) -> str:
    git = shutil.which("git")
    if not git:
        raise GateError("GIT_NOT_FOUND", "source_commit", "git executable", "missing", "Install Git or provide source identity through a supported environment.")
    completed = subprocess.run(
        [git, "-C", str(project_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        shell=False,
    )
    if completed.returncode != 0:
        raise GateError("GIT_IDENTITY_FAILED", "source_commit", "successful git identity query", completed.stderr.strip(), "Run inside the canonical Git worktree.")
    return completed.stdout.strip()


def _resolve_source_identity(project_root: Path, source_commit: str, expected_commit: str | None) -> tuple[str, str, bool]:
    head = _git_output(project_root, ["rev-parse", "HEAD"])
    if source_commit != "auto" and source_commit.lower() != head.lower():
        raise GateError(
            "SOURCE_DECLARATION_MISMATCH",
            "source_commit",
            head.lower(),
            source_commit.lower(),
            "Use --source-commit auto or provide the exact current Git HEAD.",
        )
    actual = head
    expected = actual if expected_commit is None else expected_commit
    dirty_output = _git_output(project_root, ["status", "--porcelain", "--untracked-files=normal", "--", "."])
    return actual, expected, bool(dirty_output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", default="auto")
    parser.add_argument("--expected-source-commit")
    parser.add_argument("--content-version", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--allow-physical-device", action="store_true")
    parser.add_argument("--allow-dirty-source", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve(strict=True)
        config_path = resolve_cli_path(root, args.config, "config_path", must_exist=True)
        output_path = resolve_cli_path(root, args.output, "output_path")
        source_commit, expected_commit, dirty = _resolve_source_identity(root, args.source_commit, args.expected_source_commit)
        report = run_gate(
            project_root=root,
            config_path=config_path,
            output_path=output_path,
            source_commit=source_commit,
            expected_source_commit=expected_commit,
            content_version=args.content_version,
            source_dirty=dirty,
            allow_physical_device=args.allow_physical_device,
            allow_dirty_source=args.allow_dirty_source,
            run_id=args.run_id,
        )
    except (GateError, RuntimeError, OSError) as exc:
        detail = exc.as_dict() if isinstance(exc, GateError) else {
            "code": "RUNNER_INTERNAL_BLOCK",
            "field": "runner",
            "expected": "successful bounded execution",
            "actual": str(exc),
            "suggested_fix": "Inspect the runner environment and retry after correcting the explicit error.",
        }
        print(json.dumps({"status": "BLOCKED", "error": detail}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 3
    print(json.dumps({"status": report["status"], "report": str(output_path)}, ensure_ascii=False, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
