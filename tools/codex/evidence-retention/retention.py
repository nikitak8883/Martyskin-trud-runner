#!/usr/bin/env python3
"""Create a fail-closed, index-first evidence-retention dry run.

This module intentionally has no evidence delete/apply operation.  It reads the accepted
M00 evidence index, validates the indexed corpus against the filesystem, assigns
one retention class to every indexed file, and atomically writes a review-only
report outside the evidence tree.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
WINDOWS_INVALID_CHARS = frozenset('<>"|?*')
WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
ALLOWED_OUTPUT_PREFIX = "docs/global_modernization/v3/M01/"
EXPECTED_OUTPUT_NAME = "evidence_retention_dry_run.json"
EXPECTED_OUTPUT_PATH = ALLOWED_OUTPUT_PREFIX + EXPECTED_OUTPUT_NAME


class RetentionError(RuntimeError):
    """Raised when a dry run cannot be proven safe and complete."""


@dataclass(frozen=True)
class JsonSnapshot:
    path: Path
    sha256: str
    value: Mapping[str, Any]


@dataclass(frozen=True)
class IndexedEvidence:
    path: str
    bytes: int
    modified_at: str
    modified_time: datetime
    sha256: str


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _read_json_snapshot(path: Path, label: str) -> JsonSnapshot:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RetentionError(f"cannot read {label}: {path}: {exc}") from exc
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetentionError(f"invalid UTF-8 JSON in {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RetentionError(f"{label} must be a JSON object: {path}")
    return JsonSnapshot(path=path, sha256=_sha256_bytes(payload), value=value)


def _canonical_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RetentionError(f"{label} must be a non-empty relative POSIX path")
    if "\x00" in value or "\\" in value or ":" in value:
        raise RetentionError(f"{label} contains a forbidden Windows path token: {value!r}")
    if value.startswith("/") or value.endswith("/") or "//" in value:
        raise RetentionError(f"{label} is not a canonical relative POSIX path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RetentionError(f"{label} contains an unsafe path segment: {value!r}")
    for part in parts:
        if any(ord(character) < 32 or character in WINDOWS_INVALID_CHARS for character in part):
            raise RetentionError(f"{label} contains a Windows-invalid character: {value!r}")
        if part.endswith((" ", ".")):
            raise RetentionError(f"{label} contains a trailing dot or space: {value!r}")
        reserved_stem = part.split(".", 1)[0].upper()
        if reserved_stem in WINDOWS_RESERVED_NAMES:
            raise RetentionError(f"{label} contains a reserved Windows name: {value!r}")
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != value:
        raise RetentionError(f"{label} is not canonical: {value!r}")
    return normalized


def _is_within(path: Path, root: Path) -> bool:
    try:
        common = os.path.commonpath(
            [os.path.normcase(str(path)), os.path.normcase(str(root))]
        )
    except ValueError:
        return False
    return common == os.path.normcase(str(root))


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError as exc:
        raise RetentionError(f"cannot inspect path component {path}: {exc}") from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _ensure_no_symlink_component(path: Path, stop: Path, label: str) -> None:
    current = path
    while True:
        if _is_reparse_point(current):
            raise RetentionError(
                f"{label} contains a symbolic-link or reparse-point component: {current}"
            )
        if current == stop:
            return
        if stop not in current.parents:
            raise RetentionError(f"{label} escaped its containment root: {path}")
        current = current.parent


def _resolve_existing_under(root: Path, relative: str, label: str) -> Path:
    relative = _canonical_relative(relative, label)
    candidate = root.joinpath(*relative.split("/"))
    try:
        _ensure_no_symlink_component(candidate, root, label)
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise RetentionError(f"{label} is missing or inaccessible: {relative}: {exc}") from exc
    if not _is_within(resolved, root):
        raise RetentionError(f"{label} resolves outside its containment root: {relative}")
    return resolved


def _resolve_output_under(
    project_root: Path,
    evidence_root: Path,
    relative: str,
    protected_inputs: Iterable[Path],
) -> Path:
    relative = _canonical_relative(relative, "output path")
    candidate = project_root.joinpath(*relative.split("/"))
    parent = candidate.parent
    try:
        _ensure_no_symlink_component(parent, project_root, "output parent")
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise RetentionError(f"output parent is missing or inaccessible: {parent}: {exc}") from exc
    resolved = resolved_parent / candidate.name
    if candidate.exists() and candidate.is_symlink():
        raise RetentionError(f"output path must not be a symbolic link: {relative}")
    if not _is_within(resolved, project_root):
        raise RetentionError(f"output path resolves outside project root: {relative}")
    if _is_within(resolved, evidence_root):
        raise RetentionError("output path must be outside the evidence root")
    protected = {os.path.normcase(str(path)) for path in protected_inputs}
    if os.path.normcase(str(resolved)) in protected:
        raise RetentionError("output path collides with a protected input")
    return resolved


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise RetentionError(f"{label} must be a non-empty ISO-8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    # Windows PowerShell can emit seven fractional digits. datetime accepts six,
    # so trim only excess fractional precision while preserving the timezone.
    normalized = re.sub(r"(\.\d{6})\d+(?=[+-]\d\d:\d\d$)", r"\1", normalized)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise RetentionError(f"{label} is not valid ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise RetentionError(f"{label} must include a timezone: {value!r}")
    return parsed.astimezone(timezone.utc)


def _canonical_generated_at(value: str | None) -> str:
    if value is None:
        current = datetime.now(timezone.utc)
    else:
        current = _parse_timestamp(value, "generated-at")
    return current.isoformat(timespec="seconds").replace("+00:00", "Z")


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RetentionError(f"{label} must be an array of non-empty strings")
    return list(value)


def _validate_policy(value: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schemaVersion") != 1:
        raise RetentionError("policy schemaVersion must equal 1")
    if value.get("contract") != "mtr.evidence_retention_policy":
        raise RetentionError("policy contract must equal mtr.evidence_retention_policy")
    policy_id = value.get("policyId")
    if not isinstance(policy_id, str) or not policy_id:
        raise RetentionError("policyId must be a non-empty string")
    evidence_root = _canonical_relative(value.get("evidenceRoot"), "policy evidenceRoot")
    index_path = _canonical_relative(value.get("indexPath"), "policy indexPath")
    output_path = _canonical_relative(value.get("outputPath"), "policy outputPath")
    if output_path != EXPECTED_OUTPUT_PATH:
        raise RetentionError(
            f"policy outputPath must equal the canonical M01.5 report {EXPECTED_OUTPUT_PATH}"
        )
    recent_count = value.get("recentGroupCount")
    if not isinstance(recent_count, int) or isinstance(recent_count, bool) or recent_count < 0:
        raise RetentionError("recentGroupCount must be a non-negative integer")
    recent_pattern = value.get("recentGroupPattern")
    if not isinstance(recent_pattern, str) or not recent_pattern:
        raise RetentionError("recentGroupPattern must be a non-empty regex")
    try:
        re.compile(recent_pattern)
    except re.error as exc:
        raise RetentionError(f"recentGroupPattern is invalid: {exc}") from exc

    accepted_links = value.get("acceptedRunLinks")
    if not isinstance(accepted_links, list):
        raise RetentionError("acceptedRunLinks must be an array")
    normalized_links: list[dict[str, str]] = []
    seen_link_ids: set[str] = set()
    for position, raw in enumerate(accepted_links):
        if not isinstance(raw, dict):
            raise RetentionError(f"acceptedRunLinks[{position}] must be an object")
        link_id = raw.get("id")
        kind = raw.get("kind")
        if not isinstance(link_id, str) or not link_id or link_id in seen_link_ids:
            raise RetentionError(f"acceptedRunLinks[{position}].id is missing or duplicated")
        if not isinstance(kind, str) or not kind:
            raise RetentionError(f"acceptedRunLinks[{position}].kind must be non-empty")
        seen_link_ids.add(link_id)
        normalized_links.append(
            {
                "id": link_id,
                "kind": kind,
                "path": _canonical_relative(
                    raw.get("path"), f"acceptedRunLinks[{position}].path"
                ),
            }
        )

    content_identity = value.get("contentIdentity")
    if not isinstance(content_identity, dict):
        raise RetentionError("contentIdentity must be an object")
    content_status = content_identity.get("status")
    content_version = content_identity.get("version")
    if not isinstance(content_status, str) or not content_status:
        raise RetentionError("contentIdentity.status must be non-empty")
    if content_version is not None and not isinstance(content_version, str):
        raise RetentionError("contentIdentity.version must be a string or null")

    return {
        "schemaVersion": 1,
        "contract": "mtr.evidence_retention_policy",
        "policyId": policy_id,
        "evidenceRoot": evidence_root,
        "indexPath": index_path,
        "outputPath": output_path,
        "recentGroupCount": recent_count,
        "recentGroupPattern": recent_pattern,
        "protectedPathGlobs": _require_string_list(
            value.get("protectedPathGlobs"), "protectedPathGlobs"
        ),
        "protectedNameGlobs": _require_string_list(
            value.get("protectedNameGlobs"), "protectedNameGlobs"
        ),
        "retainedNameGlobs": _require_string_list(
            value.get("retainedNameGlobs"), "retainedNameGlobs"
        ),
        "rotatableRawSuffixes": _require_string_list(
            value.get("rotatableRawSuffixes"), "rotatableRawSuffixes"
        ),
        "acceptedRunLinks": normalized_links,
        "contentIdentity": {
            "status": content_status,
            "version": content_version,
        },
    }


def _validate_index(value: Mapping[str, Any]) -> tuple[list[IndexedEvidence], int]:
    if value.get("schemaVersion") != 1:
        raise RetentionError("evidence index schemaVersion must equal 1")
    raw_files = value.get("files")
    if not isinstance(raw_files, list):
        raise RetentionError("evidence index files must be an array")
    parsed: list[IndexedEvidence] = []
    seen_paths: set[str] = set()
    for position, raw in enumerate(raw_files):
        if not isinstance(raw, dict):
            raise RetentionError(f"files[{position}] must be an object")
        relative = _canonical_relative(raw.get("path"), f"files[{position}].path")
        identity = relative.casefold()
        if identity in seen_paths:
            raise RetentionError(f"duplicate case-insensitive evidence path: {relative}")
        seen_paths.add(identity)
        size = raw.get("bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise RetentionError(f"files[{position}].bytes must be a non-negative integer")
        digest = raw.get("sha256")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise RetentionError(f"files[{position}].sha256 must be a 64-character hex digest")
        modified_at = raw.get("modifiedAt")
        parsed.append(
            IndexedEvidence(
                path=relative,
                bytes=size,
                modified_at=modified_at,
                modified_time=_parse_timestamp(modified_at, f"files[{position}].modifiedAt"),
                sha256=digest.upper(),
            )
        )
    declared_count = value.get("fileCount")
    if declared_count != len(parsed):
        raise RetentionError(
            f"evidence index fileCount mismatch: declared={declared_count!r} actual={len(parsed)}"
        )
    total_bytes = sum(entry.bytes for entry in parsed)
    if value.get("totalBytes") != total_bytes:
        raise RetentionError(
            "evidence index totalBytes does not equal the sum of indexed file sizes"
        )
    return sorted(parsed, key=lambda entry: entry.path.casefold()), total_bytes


def _match(value: str, patterns: Sequence[str]) -> str | None:
    for pattern in patterns:
        if fnmatch.fnmatchcase(value.casefold(), pattern.casefold()):
            return pattern
    return None


def _group_for(entry: IndexedEvidence, recent_pattern: re.Pattern[str]) -> str | None:
    if "/" not in entry.path:
        return None
    first = entry.path.split("/", 1)[0]
    return first if recent_pattern.fullmatch(first) else None


def _select_recent_groups(
    entries: Sequence[IndexedEvidence], pattern: str, count: int
) -> list[str]:
    compiled = re.compile(pattern)
    newest: dict[str, datetime] = {}
    for entry in entries:
        group = _group_for(entry, compiled)
        if group is not None and entry.modified_time > newest.get(group, datetime.min.replace(tzinfo=timezone.utc)):
            newest[group] = entry.modified_time
    ordered = sorted(
        newest,
        key=lambda group: (group[:8], newest[group].timestamp(), group.casefold()),
        reverse=True,
    )
    return ordered[:count]


def _classify(
    entry: IndexedEvidence,
    policy: Mapping[str, Any],
    recent_groups: set[str],
) -> tuple[str, str, str | None]:
    basename = PurePosixPath(entry.path).name
    path_match = _match(entry.path, policy["protectedPathGlobs"])
    if path_match is not None:
        return "protected", f"protected_path_glob:{path_match}", None
    name_match = _match(basename, policy["protectedNameGlobs"])
    if name_match is not None:
        return "protected", f"protected_name_glob:{name_match}", None

    group = _group_for(entry, re.compile(policy["recentGroupPattern"]))
    if group in recent_groups:
        return "retained_recent", f"latest_{policy['recentGroupCount']}_dated_groups", group
    retained_match = _match(basename, policy["retainedNameGlobs"])
    if retained_match is not None:
        return "retained_recent", f"current_failure_corpus:{retained_match}", group

    suffix = PurePosixPath(entry.path).suffix.casefold()
    raw_suffixes = {item.casefold() for item in policy["rotatableRawSuffixes"]}
    reason = (
        f"superseded_raw_evidence:{suffix or '<no_suffix>'}"
        if suffix in raw_suffixes
        else "superseded_non_anchor_evidence"
    )
    return "rotatable", reason, group


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RetentionError(f"cannot hash accepted-run link {path}: {exc}") from exc
    return digest.hexdigest().upper()


def _verify_corpus(
    evidence_root: Path, entries: Sequence[IndexedEvidence]
) -> dict[str, Any]:
    indexed_paths: set[str] = set()
    for entry in entries:
        resolved = _resolve_existing_under(evidence_root, entry.path, "indexed evidence")
        if not resolved.is_file():
            raise RetentionError(f"indexed evidence is not a regular file: {entry.path}")
        try:
            file_stat = resolved.stat()
        except OSError as exc:
            raise RetentionError(f"cannot stat indexed evidence {entry.path}: {exc}") from exc
        actual_size = file_stat.st_size
        if actual_size != entry.bytes:
            raise RetentionError(
                f"indexed evidence size drift: {entry.path}: index={entry.bytes} disk={actual_size}"
            )
        actual_modified = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)
        if abs((actual_modified - entry.modified_time).total_seconds()) > 0.001:
            raise RetentionError(
                "indexed evidence modification-time drift: "
                f"{entry.path}: index={entry.modified_at} disk={actual_modified.isoformat()}"
            )
        indexed_paths.add(entry.path.casefold())

    discovered: set[str] = set()
    try:
        candidates = sorted(evidence_root.rglob("*"), key=lambda path: str(path).casefold())
    except OSError as exc:
        raise RetentionError(f"cannot enumerate evidence root: {exc}") from exc
    for candidate in candidates:
        if _is_reparse_point(candidate):
            raise RetentionError(
                f"evidence corpus contains a symbolic link or reparse point: {candidate}"
            )
        if not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise RetentionError(f"cannot resolve evidence file {candidate}: {exc}") from exc
        if not _is_within(resolved, evidence_root):
            raise RetentionError(f"evidence file resolves outside evidence root: {candidate}")
        relative = candidate.relative_to(evidence_root).as_posix()
        canonical = _canonical_relative(relative, "discovered evidence path")
        discovered.add(canonical.casefold())

    unindexed = sorted(discovered - indexed_paths)
    missing_from_disk = sorted(indexed_paths - discovered)
    if unindexed:
        preview = ", ".join(unindexed[:5])
        raise RetentionError(
            f"evidence root contains {len(unindexed)} unindexed file(s); first: {preview}"
        )
    if missing_from_disk:
        preview = ", ".join(missing_from_disk[:5])
        raise RetentionError(
            f"evidence index contains {len(missing_from_disk)} missing file(s); first: {preview}"
        )
    return {
        "status": "PASS",
        "indexedFilesResolved": len(entries),
        "discoveredFiles": len(discovered),
        "missingFiles": 0,
        "sizeDriftFiles": 0,
        "modificationTimeDriftFiles": 0,
        "unindexedFiles": 0,
        "contentRehashPerformed": False,
        "contentRehashReason": "index-first dry-run trusts M00 SHA-256 values after path and size reconciliation",
    }


def _verify_accepted_links(
    project_root: Path, links: Sequence[Mapping[str, str]]
) -> tuple[list[dict[str, Any]], list[Path]]:
    reports: list[dict[str, Any]] = []
    paths: list[Path] = []
    for link in links:
        resolved = _resolve_existing_under(project_root, link["path"], "accepted-run link")
        if not resolved.is_file():
            raise RetentionError(f"accepted-run link is not a regular file: {link['path']}")
        reports.append(
            {
                "id": link["id"],
                "kind": link["kind"],
                "path": link["path"],
                "bytes": resolved.stat().st_size,
                "sha256": _hash_file(resolved),
                "status": "VERIFIED",
            }
        )
        paths.append(resolved)
    return reports, paths


def _current_git_commit(project_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RetentionError(f"cannot read current Git commit: {exc}") from exc
    commit = completed.stdout.strip()
    if completed.returncode != 0 or GIT_COMMIT_RE.fullmatch(commit) is None:
        raise RetentionError(
            f"cannot read a valid current Git commit: {completed.stderr.strip()}"
        )
    return commit.lower()


def build_dry_run(
    *,
    project_root: Path,
    policy_relative: str,
    output_relative: str,
    generated_at: str | None = None,
    source_commit: str | None = None,
) -> tuple[dict[str, Any], Path]:
    try:
        project_root = project_root.resolve(strict=True)
    except OSError as exc:
        raise RetentionError(f"project root is missing or inaccessible: {exc}") from exc
    if not project_root.is_dir():
        raise RetentionError("project root must be a directory")

    policy_path = _resolve_existing_under(project_root, policy_relative, "policy path")
    policy_snapshot = _read_json_snapshot(policy_path, "retention policy")
    policy = _validate_policy(policy_snapshot.value)
    if output_relative != policy["outputPath"]:
        raise RetentionError(
            "CLI output path must exactly match the reviewed policy outputPath"
        )
    evidence_root = _resolve_existing_under(
        project_root, policy["evidenceRoot"], "evidence root"
    )
    if not evidence_root.is_dir():
        raise RetentionError("configured evidence root must be a directory")
    index_path = _resolve_existing_under(project_root, policy["indexPath"], "index path")
    index_snapshot = _read_json_snapshot(index_path, "evidence index")
    entries, total_bytes = _validate_index(index_snapshot.value)

    declared_root = index_snapshot.value.get("root")
    if not isinstance(declared_root, str) or not declared_root:
        raise RetentionError("evidence index root must be a non-empty absolute path")
    try:
        declared_root_resolved = Path(declared_root).resolve(strict=True)
    except OSError as exc:
        raise RetentionError(f"evidence index root is missing or inaccessible: {exc}") from exc
    if os.path.normcase(str(declared_root_resolved)) != os.path.normcase(str(evidence_root)):
        raise RetentionError("evidence index root does not match the configured evidence root")

    corpus_integrity = _verify_corpus(evidence_root, entries)
    accepted_links, accepted_paths = _verify_accepted_links(
        project_root, policy["acceptedRunLinks"]
    )
    output_path = _resolve_output_under(
        project_root,
        evidence_root,
        output_relative,
        [policy_path, index_path, *accepted_paths],
    )

    commit = source_commit or _current_git_commit(project_root)
    if GIT_COMMIT_RE.fullmatch(commit) is None:
        raise RetentionError("source commit must be a full 40-character Git commit")
    commit = commit.lower()
    recent_groups = _select_recent_groups(
        entries, policy["recentGroupPattern"], policy["recentGroupCount"]
    )
    recent_set = set(recent_groups)

    counts = {"protected": 0, "retained_recent": 0, "rotatable": 0}
    byte_counts = {"protected": 0, "retained_recent": 0, "rotatable": 0}
    report_entries: list[dict[str, Any]] = []
    group_summaries: dict[str, dict[str, Any]] = {}
    for entry in entries:
        classification, reason, group = _classify(entry, policy, recent_set)
        counts[classification] += 1
        byte_counts[classification] += entry.bytes
        proposed_action = (
            "PRESERVE"
            if classification in {"protected", "retained_recent"}
            else "REVIEW_ONLY_FOR_FUTURE_APPROVED_ROTATION"
        )
        report_entries.append(
            {
                "path": entry.path,
                "bytes": entry.bytes,
                "modifiedAt": entry.modified_at,
                "sha256": entry.sha256,
                "group": group,
                "classification": classification,
                "reason": reason,
                "proposedAction": proposed_action,
            }
        )
        group_key = group or "<ungrouped>"
        summary = group_summaries.setdefault(
            group_key,
            {
                "group": group_key,
                "counts": {"protected": 0, "retained_recent": 0, "rotatable": 0},
                "bytes": {"protected": 0, "retained_recent": 0, "rotatable": 0},
            },
        )
        summary["counts"][classification] += 1
        summary["bytes"][classification] += entry.bytes

    if sum(counts.values()) != len(entries) or sum(byte_counts.values()) != total_bytes:
        raise RetentionError("retention classification did not cover the complete evidence index")

    result = {
        "schemaVersion": 1,
        "contract": "mtr.evidence_retention_dry_run",
        "workPackage": "M01.5",
        "policyId": policy["policyId"],
        "generatedAt": _canonical_generated_at(generated_at),
        "status": "PASS_DRY_RUN_ONLY",
        "mode": "INDEX_FIRST_DELETE_INCAPABLE",
        "deletionPerformed": False,
        "evidenceDeleteCapabilityPresent": False,
        "temporaryOutputCleanupPresent": True,
        "temporaryOutputCleanupScope": ".evidence_retention_dry_run.json.tmp.<pid> only",
        "sourceIdentity": {
            "currentCommit": commit,
            "indexSourceCommit": index_snapshot.value.get("sourceHead"),
            "contentIdentity": policy["contentIdentity"],
        },
        "inputs": {
            "policyPath": policy_relative,
            "policySha256": policy_snapshot.sha256,
            "indexPath": policy["indexPath"],
            "indexSha256": index_snapshot.sha256,
            "evidenceRoot": policy["evidenceRoot"],
            "outputPath": policy["outputPath"],
            "indexDeclaredRootMatched": True,
        },
        "pathGuards": {
            "status": "PASS",
            "projectContainment": True,
            "evidenceContainment": True,
            "outputOutsideEvidence": True,
            "symlinkOrReparseEscapeDetected": False,
            "canonicalRelativePaths": True,
        },
        "corpusIntegrity": corpus_integrity,
        "acceptedRunLinks": accepted_links,
        "retention": {
            "indexedFiles": len(entries),
            "indexedBytes": total_bytes,
            "recentGroupCount": policy["recentGroupCount"],
            "recentGroups": recent_groups,
            "counts": counts,
            "bytes": byte_counts,
            "rotatableReviewCandidateFiles": counts["rotatable"],
            "rotatableReviewCandidateBytes": byte_counts["rotatable"],
            "classificationComplete": True,
        },
        "groupSummaries": [group_summaries[key] for key in sorted(group_summaries)],
        "entries": report_entries,
        "futureApplyBlockers": [
            "M01.5 has no evidence delete/apply code path",
            "explicit bounded cleanup approval is absent",
            "candidate backup and rollback manifest is absent",
            "post-cleanup rebuild and QA are outside this work package",
        ],
    }
    return result, output_path


def _revalidate_before_write(
    project_root: Path,
    result: Mapping[str, Any],
    output_path: Path,
) -> None:
    """Recheck every protected input and the corpus immediately before replace."""

    project_root = project_root.resolve(strict=True)
    inputs = result.get("inputs")
    if not isinstance(inputs, dict):
        raise RetentionError("dry-run result inputs are missing before final write")

    policy_relative = inputs.get("policyPath")
    index_relative = inputs.get("indexPath")
    evidence_relative = inputs.get("evidenceRoot")
    output_relative = inputs.get("outputPath")
    for value, label in (
        (policy_relative, "revalidation policy path"),
        (index_relative, "revalidation index path"),
        (evidence_relative, "revalidation evidence root"),
        (output_relative, "revalidation output path"),
    ):
        _canonical_relative(value, label)

    policy_path = _resolve_existing_under(project_root, policy_relative, "revalidation policy")
    index_path = _resolve_existing_under(project_root, index_relative, "revalidation index")
    policy_snapshot = _read_json_snapshot(policy_path, "revalidation policy")
    index_snapshot = _read_json_snapshot(index_path, "revalidation index")
    if policy_snapshot.sha256 != inputs.get("policySha256"):
        raise RetentionError("retention policy changed before atomic report write")
    if index_snapshot.sha256 != inputs.get("indexSha256"):
        raise RetentionError("evidence index changed before atomic report write")
    current_commit = _current_git_commit(project_root)
    source_identity = result.get("sourceIdentity")
    if not isinstance(source_identity, dict) or current_commit != source_identity.get("currentCommit"):
        raise RetentionError("Git HEAD changed before atomic report write")

    accepted = result.get("acceptedRunLinks")
    if not isinstance(accepted, list):
        raise RetentionError("accepted-run links are missing before final write")
    accepted_paths: list[Path] = []
    for position, link in enumerate(accepted):
        if not isinstance(link, dict):
            raise RetentionError(f"acceptedRunLinks[{position}] is malformed before final write")
        relative = _canonical_relative(
            link.get("path"), f"acceptedRunLinks[{position}].path revalidation"
        )
        resolved = _resolve_existing_under(
            project_root, relative, "accepted-run link revalidation"
        )
        if resolved.stat().st_size != link.get("bytes") or _hash_file(resolved) != link.get("sha256"):
            raise RetentionError(f"accepted-run link changed before atomic report write: {relative}")
        accepted_paths.append(resolved)

    evidence_root = _resolve_existing_under(
        project_root, evidence_relative, "evidence root revalidation"
    )
    revalidated_output = _resolve_output_under(
        project_root,
        evidence_root,
        output_relative,
        [policy_path, index_path, *accepted_paths],
    )
    if os.path.normcase(str(revalidated_output)) != os.path.normcase(str(output_path)):
        raise RetentionError("output path identity changed before atomic report write")

    raw_entries = result.get("entries")
    if not isinstance(raw_entries, list):
        raise RetentionError("dry-run entries are missing before final write")
    entries: list[IndexedEvidence] = []
    for position, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            raise RetentionError(f"dry-run entries[{position}] is malformed")
        relative = _canonical_relative(raw.get("path"), f"dry-run entries[{position}].path")
        size = raw.get("bytes")
        modified_at = raw.get("modifiedAt")
        digest = raw.get("sha256")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise RetentionError(f"dry-run entries[{position}].bytes is malformed")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise RetentionError(f"dry-run entries[{position}].sha256 is malformed")
        entries.append(
            IndexedEvidence(
                path=relative,
                bytes=size,
                modified_at=modified_at,
                modified_time=_parse_timestamp(
                    modified_at, f"dry-run entries[{position}].modifiedAt"
                ),
                sha256=digest.upper(),
            )
        )
    _verify_corpus(evidence_root, entries)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise RetentionError(f"cannot atomically write dry-run report {path}: {exc}") from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--generated-at")
    parser.add_argument("--source-commit")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result, output_path = build_dry_run(
            project_root=args.project_root,
            policy_relative=args.policy,
            output_relative=args.output,
            generated_at=args.generated_at,
            source_commit=args.source_commit,
        )
        _revalidate_before_write(args.project_root, result, output_path)
        _atomic_write_json(output_path, result)
    except RetentionError as exc:
        print(f"M01.5 BLOCKED: {exc}", file=sys.stderr)
        return 2
    retention = result["retention"]
    print(
        "M01.5 PASS_DRY_RUN_ONLY "
        f"files={retention['indexedFiles']} "
        f"protected={retention['counts']['protected']} "
        f"retained_recent={retention['counts']['retained_recent']} "
        f"rotatable={retention['counts']['rotatable']} "
        f"output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
