#!/usr/bin/env python3
"""Validate the shared Web/Android content identity and build-report preflight."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


IDENTITY_RELATIVE = Path("assets/resources/config/content_identity.json")
META_RELATIVE = Path("assets/resources/config/content_identity.json.meta")
M00_MANIFEST_RELATIVE = Path("docs/global_modernization/v3/M00/source_content_manifest.json")
BUILD_WRAPPER_RELATIVE = Path("tools/Run-MtrCocosBuild.ps1")
BUILD_CONFIGS = (Path("build-web-mobile.json"), Path("build-android-emulator.json"), Path("build-android.json"))
EXPECTED_REPOSITORY = "https://github.com/nikitak8883/Martyskin-trud-runner.git"
EXPECTED_BRANCH = "mtr-source-v3"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
VERSION_RE = re.compile(r"^mtr-v3-source-[0-9a-f]{12}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected object")
        return
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{label}: missing keys {missing}")
    if unknown:
        errors.append(f"{label}: unknown keys {unknown}")


def validate_identity_document(identity: Any, manifest: Any) -> list[str]:
    errors: list[str] = []
    _exact_keys(
        identity,
        {"schema_version", "contract", "logical_content_version", "source", "freeze_provenance", "platform_contract", "bump_policy"},
        "identity",
        errors,
    )
    if not isinstance(identity, dict):
        return errors

    if identity.get("schema_version") != 1:
        errors.append("identity.schema_version: expected 1")
    if identity.get("contract") != "mtr.content_identity":
        errors.append("identity.contract: expected mtr.content_identity")
    if not VERSION_RE.fullmatch(str(identity.get("logical_content_version", ""))):
        errors.append("identity.logical_content_version: invalid format")

    source = identity.get("source")
    _exact_keys(source, {"repository", "branch", "baseline_commit", "baseline_kind"}, "identity.source", errors)
    if isinstance(source, dict):
        if source.get("repository") != EXPECTED_REPOSITORY:
            errors.append("identity.source.repository: unexpected repository")
        if source.get("branch") != EXPECTED_BRANCH:
            errors.append("identity.source.branch: unexpected branch")
        if not SHA1_RE.fullmatch(str(source.get("baseline_commit", ""))):
            errors.append("identity.source.baseline_commit: expected lowercase 40-hex commit")
        if source.get("baseline_kind") != "published_source_before_identity_metadata":
            errors.append("identity.source.baseline_kind: unexpected value")
        expected_version = f"mtr-v3-source-{str(source.get('baseline_commit', ''))[:12]}"
        if identity.get("logical_content_version") != expected_version:
            errors.append("identity.logical_content_version: does not match baseline commit")

    provenance = identity.get("freeze_provenance")
    _exact_keys(
        provenance,
        {"manifest", "source_commit", "source_tree", "content_version", "aggregate_sha256", "file_count", "total_bytes"},
        "identity.freeze_provenance",
        errors,
    )
    if isinstance(provenance, dict):
        if provenance.get("manifest") != M00_MANIFEST_RELATIVE.as_posix():
            errors.append("identity.freeze_provenance.manifest: unexpected path")
        manifest_pairs = {
            "source_commit": "source_commit",
            "source_tree": "source_tree",
            "content_version": "content_version",
            "aggregate_sha256": "aggregate_sha256",
            "file_count": "file_count",
            "total_bytes": "total_bytes",
        }
        for identity_key, manifest_key in manifest_pairs.items():
            if provenance.get(identity_key) != manifest.get(manifest_key):
                errors.append(f"identity.freeze_provenance.{identity_key}: M00 manifest mismatch")
        if not SHA1_RE.fullmatch(str(provenance.get("source_commit", ""))):
            errors.append("identity.freeze_provenance.source_commit: invalid commit")
        if not SHA1_RE.fullmatch(str(provenance.get("source_tree", ""))):
            errors.append("identity.freeze_provenance.source_tree: invalid tree")
        if not SHA256_RE.fullmatch(str(provenance.get("aggregate_sha256", ""))):
            errors.append("identity.freeze_provenance.aggregate_sha256: invalid SHA-256")

    platform = identity.get("platform_contract")
    _exact_keys(
        platform,
        {"targets", "shared_report_field", "artifact_manifest_field", "artifact_manifest_scope"},
        "identity.platform_contract",
        errors,
    )
    if isinstance(platform, dict):
        if platform.get("targets") != ["web-mobile", "android"]:
            errors.append("identity.platform_contract.targets: expected web-mobile and android")
        if platform.get("shared_report_field") != "contentIdentity":
            errors.append("identity.platform_contract.shared_report_field: unexpected field")
        if platform.get("artifact_manifest_field") != "platformArtifactManifest":
            errors.append("identity.platform_contract.artifact_manifest_field: unexpected field")
        if platform.get("artifact_manifest_scope") != "per-platform":
            errors.append("identity.platform_contract.artifact_manifest_scope: expected per-platform")

    bump = identity.get("bump_policy")
    _exact_keys(bump, {"baseline_precedes_identity_metadata", "required_when", "not_required_when"}, "identity.bump_policy", errors)
    if isinstance(bump, dict):
        if bump.get("baseline_precedes_identity_metadata") is not True:
            errors.append("identity.bump_policy.baseline_precedes_identity_metadata: expected true")
        if bump.get("required_when") != ["runtime_code", "runtime_asset", "content_config", "scene", "shared_build_behavior"]:
            errors.append("identity.bump_policy.required_when: unexpected policy")
        if bump.get("not_required_when") != ["audit_documentation", "rotating_qa_evidence", "ci_only_tooling"]:
            errors.append("identity.bump_policy.not_required_when: unexpected policy")
    return errors


def validate_meta(meta: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(meta, dict):
        return ["content identity meta: expected object"]
    if meta.get("ver") != "2.0.1" or meta.get("importer") != "json" or meta.get("imported") is not True:
        errors.append("content identity meta: invalid Cocos JSON importer contract")
    if meta.get("files") != [".json"] or meta.get("subMetas") != {} or meta.get("userData") != {}:
        errors.append("content identity meta: invalid JSON asset shape")
    if not UUID_RE.fullmatch(str(meta.get("uuid", ""))):
        errors.append("content identity meta: invalid UUID")
    return errors


def _run_git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def validate_git_baseline(project_root: Path, commit: str) -> list[str]:
    if not SHA1_RE.fullmatch(commit):
        return ["git baseline: invalid commit format"]
    object_check = _run_git(project_root, "cat-file", "-e", f"{commit}^{{commit}}")
    if object_check.returncode != 0:
        return ["git baseline: commit object is unavailable"]
    refs = ("HEAD", "codex/mtr-source-v3", "origin/mtr-source-v3")
    reachable = False
    for ref in refs:
        if _run_git(project_root, "rev-parse", "--verify", "--quiet", ref).returncode != 0:
            continue
        if _run_git(project_root, "merge-base", "--is-ancestor", commit, ref).returncode == 0:
            reachable = True
            break
    return [] if reachable else ["git baseline: commit is not reachable from the current or canonical source refs"]


def run_build_preflight(
    project_root: Path,
    config_path: Path,
    identity_sha256: str,
    meta_sha256: str,
) -> tuple[dict[str, Any] | None, str | None]:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        return None, "PowerShell executable not found for build identity preflight"
    command = [
        shell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(project_root / BUILD_WRAPPER_RELATIVE),
        "-ProjectRoot",
        str(project_root),
        "-ConfigPath",
        str(config_path),
        "-ValidateContentIdentityOnly",
    ]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=60)
    if result.returncode != 0:
        return None, f"{config_path}: build preflight failed: {result.stderr.strip() or result.stdout.strip()}"
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, f"{config_path}: build preflight returned invalid JSON: {exc}"
    content = report.get("contentIdentity", {})
    if content.get("identityFileSha256") != identity_sha256:
        return None, f"{config_path}: build preflight identity SHA-256 mismatch"
    if content.get("identityMetaFileSha256") != meta_sha256:
        return None, f"{config_path}: build preflight identity meta SHA-256 mismatch"
    return report, None


def validate_repository(project_root: Path, *, check_git: bool = True, run_preflight: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    identity_path = project_root / IDENTITY_RELATIVE
    manifest_path = project_root / M00_MANIFEST_RELATIVE
    meta_path = project_root / META_RELATIVE
    try:
        identity = load_json(identity_path)
        manifest = load_json(manifest_path)
        meta = load_json(meta_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "findings": [f"input parse failed: {exc}"], "preflights": []}

    errors.extend(validate_identity_document(identity, manifest))
    errors.extend(validate_meta(meta))
    identity_sha256 = hashlib.sha256(identity_path.read_bytes()).hexdigest().upper()
    meta_sha256 = hashlib.sha256(meta_path.read_bytes()).hexdigest().upper()
    source_commit = str(identity.get("source", {}).get("baseline_commit", ""))
    if check_git:
        errors.extend(validate_git_baseline(project_root, source_commit))

    platforms: list[str] = []
    for config_path in BUILD_CONFIGS:
        try:
            config = load_json(project_root / config_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{config_path}: config parse failed: {exc}")
            continue
        platform = config.get("platform")
        if platform not in ("web-mobile", "android"):
            errors.append(f"{config_path}: unsupported platform {platform!r}")
        platforms.append(str(platform))
    if platforms != ["web-mobile", "android", "android"]:
        errors.append("build configs: expected one Web and two Android targets")

    preflights: list[dict[str, Any]] = []
    if run_preflight and not errors:
        for config_path in BUILD_CONFIGS:
            report, error = run_build_preflight(project_root, config_path, identity_sha256, meta_sha256)
            if error:
                errors.append(error)
                continue
            assert report is not None
            preflights.append(report)
        if len(preflights) == 3:
            shared = [copy.deepcopy(item.get("contentIdentity")) for item in preflights]
            if not all(item == shared[0] for item in shared[1:]):
                errors.append("build preflights: Web and Android contentIdentity values differ")
            artifact_platforms = [item.get("platformArtifactManifest", {}).get("platform") for item in preflights]
            if artifact_platforms != ["web-mobile", "android", "android"]:
                errors.append("build preflights: platform artifact manifests are not target-specific")
            if any(item.get("platformArtifactManifest", {}).get("scope") != "per-platform" for item in preflights):
                errors.append("build preflights: artifact manifest scope must remain per-platform")

    return {
        "schema_version": 1,
        "contract": "mtr.content_identity_validation",
        "status": "PASS" if not errors else "FAIL",
        "identity_path": IDENTITY_RELATIVE.as_posix(),
        "identity_sha256": identity_sha256,
        "identity_meta_sha256": meta_sha256,
        "logical_content_version": identity.get("logical_content_version"),
        "source_commit": source_commit,
        "build_config_count": len(BUILD_CONFIGS),
        "preflight_count": len(preflights),
        "preflights": preflights,
        "findings": errors,
    }


def write_report_atomic(project_root: Path, report_path: Path, text: str) -> None:
    resolved_root = project_root.resolve()
    resolved_report = report_path.resolve()
    try:
        resolved_report.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("report path escapes project root") from exc
    resolved_report.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=resolved_report.parent,
            prefix=f".{resolved_report.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
            temporary_name = stream.name
        os.replace(temporary_name, resolved_report)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--skip-git", action="store_true")
    parser.add_argument("--skip-build-preflight", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = validate_repository(root, check_git=not args.skip_git, run_preflight=not args.skip_build_preflight)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = root / report_path
        try:
            write_report_atomic(root, report_path, text)
        except (OSError, ValueError) as exc:
            sys.stderr.write(f"report write failed: {exc}\n")
            return 2
    sys.stdout.write(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
