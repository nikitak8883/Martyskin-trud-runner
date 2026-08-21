#!/usr/bin/env python3
"""Validate the M04-A asset inventory, ownership and atlas policy contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_RELATIVE = Path("assets/resources/config/atlas_manifest.json")
MANIFEST_META_RELATIVE = Path("assets/resources/config/atlas_manifest.json.meta")
SCHEMA_RELATIVE = Path("docs/global_modernization/v3/M04/schemas/atlas_manifest.schema.json")
CONTENT_IDENTITY_RELATIVE = Path("assets/resources/config/content_identity.json")
RESOURCES_RELATIVE = Path("assets/resources")
RESOURCES_META_RELATIVE = Path("assets/resources.meta")
EXPECTED_REPOSITORY = "https://github.com/nikitak8883/Martyskin-trud-runner.git"
EXPECTED_SOURCE_BRANCH = "mtr-source-v3"
EXPECTED_GOVERNANCE_SOURCE_EXCLUSIONS = {
    "config/atlas_manifest.json",
    "config/content_identity.json",
}
EXPECTED_GOVERNANCE_META_EXCLUSIONS = {
    "assets/resources/config/atlas_manifest.json.meta",
    "assets/resources/config/content_identity.json.meta",
}
IMAGE_EXTENSIONS = {".png", ".jpg"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_finding(
    findings: list[dict[str, Any]],
    code: str,
    path: str,
    expected: Any,
    actual: Any,
) -> None:
    findings.append({"code": code, "path": path, "expected": expected, "actual": actual})


def canonical_bytes(path: Path, text_extensions: set[str]) -> bytes:
    payload = path.read_bytes()
    if path.suffix.lower() not in text_extensions:
        return payload
    text = payload.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def inventory_digest(
    files: Iterable[Path],
    relative_path: Any,
    text_extensions: set[str],
) -> tuple[dict[str, Any], dict[str, dict[str, int]], dict[str, int]]:
    records: list[bytes] = []
    extension_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "bytes": 0})
    sizes: dict[str, int] = {}
    for path in sorted(files, key=relative_path):
        relative = relative_path(path)
        payload = canonical_bytes(path, text_extensions)
        digest = hashlib.sha256(payload).hexdigest().upper()
        records.append(f"{relative}\0{len(payload)}\0{digest}\n".encode("utf-8"))
        bucket = extension_counts[path.suffix.lower()]
        bucket["count"] += 1
        bucket["bytes"] += len(payload)
        sizes[relative] = len(payload)
    return (
        {
            "count": len(records),
            "bytes": sum(sizes.values()),
            "sha256": hashlib.sha256(b"".join(records)).hexdigest().upper(),
        },
        dict(sorted(extension_counts.items())),
        sizes,
    )


def path_matches(relative: str, selector_path: str, mode: str) -> bool:
    if mode == "exact_file":
        return relative == selector_path
    return relative == selector_path or relative.startswith(f"{selector_path}/")


def resolve_project_path(project_root: Path, relative: str) -> Path | None:
    resolved_root = project_root.resolve()
    resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def validate_schema(manifest: Any, schema: Any, findings: list[dict[str, Any]]) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        add_finding(findings, "SCHEMA_DEFINITION_INVALID", "$schema", "valid Draft 2020-12 schema", str(exc))
        return
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(manifest), key=lambda item: [str(part) for part in item.absolute_path]):
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        add_finding(findings, "SCHEMA_VIOLATION", path, error.validator, error.message)


def validate_meta_graph(project_root: Path, resources_root: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    sources = sorted(path for path in resources_root.rglob("*") if path.is_file() and path.suffix != ".meta")
    directories = [resources_root, *sorted(path for path in resources_root.rglob("*") if path.is_dir())]
    missing_pairs: list[str] = []
    for target in [*sources, *directories]:
        meta = Path(f"{target}.meta")
        if not meta.is_file():
            missing_pairs.append(target.relative_to(project_root).as_posix())
    for path in missing_pairs:
        add_finding(findings, "COCOS_META_MISSING", path, "paired .meta", None)

    meta_files = [project_root / RESOURCES_META_RELATIVE, *sorted(resources_root.rglob("*.meta"))]
    uuid_owners: dict[str, list[str]] = defaultdict(list)
    invalid_json = 0
    invalid_uuid = 0
    for meta in meta_files:
        relative = meta.relative_to(project_root).as_posix()
        try:
            value = load_json(meta)
        except (OSError, json.JSONDecodeError) as exc:
            invalid_json += 1
            add_finding(findings, "COCOS_META_INVALID_JSON", relative, "valid JSON", str(exc))
            continue
        uuid = value.get("uuid") if isinstance(value, dict) else None
        if not isinstance(uuid, str) or not UUID_RE.fullmatch(uuid):
            invalid_uuid += 1
            add_finding(findings, "COCOS_META_INVALID_UUID", relative, "lowercase UUID", uuid)
        else:
            uuid_owners[uuid].append(relative)

    duplicate_uuids = {uuid: owners for uuid, owners in uuid_owners.items() if len(owners) > 1}
    for uuid, owners in sorted(duplicate_uuids.items()):
        add_finding(findings, "COCOS_META_DUPLICATE_UUID", uuid, "one owner", owners)

    orphan_meta: list[str] = []
    for meta in resources_root.rglob("*.meta"):
        target = Path(str(meta)[:-5])
        if not target.exists():
            orphan_meta.append(meta.relative_to(project_root).as_posix())
    for path in orphan_meta:
        add_finding(findings, "COCOS_META_ORPHAN", path, "existing source or directory", None)

    return {
        "source_files": len(sources),
        "directories": len(directories),
        "meta_files": len(meta_files),
        "missing_pairs": len(missing_pairs),
        "invalid_json": invalid_json,
        "invalid_uuid": invalid_uuid,
        "duplicate_uuids": len(duplicate_uuids),
        "orphan_meta": len(orphan_meta),
    }


def run_git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_value(project_root: Path, *arguments: str) -> str | None:
    result = run_git(project_root, *arguments)
    return result.stdout.strip() if result.returncode == 0 else None


def validate_source_checkpoint(
    project_root: Path,
    checkpoint: Any,
    content_identity: Any,
    findings: list[dict[str, Any]],
    check_git: bool,
) -> dict[str, Any]:
    if not isinstance(checkpoint, dict):
        return {"checked": False}
    published = str(checkpoint.get("published_subtree_commit", ""))
    parent = str(checkpoint.get("parent_checkpoint", ""))
    expected_tree = str(checkpoint.get("project_tree", ""))
    if checkpoint.get("repository") != EXPECTED_REPOSITORY:
        add_finding(findings, "SOURCE_REPOSITORY_MISMATCH", "source_checkpoint.repository", EXPECTED_REPOSITORY, checkpoint.get("repository"))
    if checkpoint.get("branch") != EXPECTED_SOURCE_BRANCH:
        add_finding(findings, "SOURCE_BRANCH_MISMATCH", "source_checkpoint.branch", EXPECTED_SOURCE_BRANCH, checkpoint.get("branch"))

    identity_source = content_identity.get("source", {}) if isinstance(content_identity, dict) else {}
    expected_version = f"mtr-v3-source-{published[:12]}" if SHA1_RE.fullmatch(published) else None
    if identity_source.get("baseline_commit") != published:
        add_finding(findings, "CONTENT_IDENTITY_BASELINE_MISMATCH", "content_identity.source.baseline_commit", published, identity_source.get("baseline_commit"))
    if content_identity.get("logical_content_version") != expected_version:
        add_finding(findings, "CONTENT_IDENTITY_VERSION_MISMATCH", "content_identity.logical_content_version", expected_version, content_identity.get("logical_content_version"))

    result: dict[str, Any] = {"checked": check_git, "published_commit": published, "parent_checkpoint": parent}
    if not check_git:
        return result

    published_tree = git_value(project_root, "rev-parse", f"{published}^{{tree}}")
    result["published_tree"] = published_tree
    if published_tree != expected_tree:
        add_finding(findings, "PUBLISHED_TREE_MISMATCH", "source_checkpoint.project_tree", expected_tree, published_tree)

    remote_ref = f"origin/{EXPECTED_SOURCE_BRANCH}"
    remote_commit = git_value(project_root, "rev-parse", "--verify", "--quiet", remote_ref)
    result["remote_ref"] = remote_ref
    result["remote_commit"] = remote_commit
    if remote_commit is not None and remote_commit != published:
        ancestor = run_git(project_root, "merge-base", "--is-ancestor", published, remote_commit).returncode == 0
        if not ancestor:
            add_finding(findings, "PUBLISHED_BASELINE_NOT_ON_SOURCE_REF", remote_ref, f"{published} or descendant", remote_commit)

    repository_root_text = git_value(project_root, "rev-parse", "--show-toplevel")
    parent_available = git_value(project_root, "cat-file", "-t", parent) == "commit"
    result["parent_available"] = parent_available
    if repository_root_text and parent_available:
        repository_root = Path(repository_root_text).resolve()
        try:
            prefix = project_root.resolve().relative_to(repository_root).as_posix()
        except ValueError:
            prefix = "."
        parent_tree = git_value(project_root, "rev-parse", f"{parent}^{{tree}}" if prefix == "." else f"{parent}:{prefix}")
        result["parent_project_tree"] = parent_tree
        if parent_tree != expected_tree:
            add_finding(findings, "PARENT_PROJECT_TREE_MISMATCH", "source_checkpoint.parent_checkpoint", expected_tree, parent_tree)
    return result


def validate_manifest(
    project_root: Path,
    manifest: Any | None = None,
    *,
    check_git: bool = True,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    resources_root = project_root / RESOURCES_RELATIVE
    findings: list[dict[str, Any]] = []
    manifest = load_json(project_root / MANIFEST_RELATIVE) if manifest is None else manifest
    schema = load_json(project_root / SCHEMA_RELATIVE)
    content_identity = load_json(project_root / CONTENT_IDENTITY_RELATIVE)
    validate_schema(manifest, schema, findings)
    if not isinstance(manifest, dict):
        return {"schema_version": 1, "contract": "mtr.m04_a_asset_contract_validation", "status": "FAIL", "findings": findings}

    inventory = manifest.get("inventory", {})
    canonicalization = inventory.get("canonicalization", {}) if isinstance(inventory, dict) else {}
    text_extensions = set(canonicalization.get("text_extensions", []))
    source_exclusions = set(inventory.get("excluded_governance_source_files", [])) if isinstance(inventory, dict) else set()
    meta_exclusions = set(inventory.get("excluded_governance_meta_files", [])) if isinstance(inventory, dict) else set()
    if source_exclusions != EXPECTED_GOVERNANCE_SOURCE_EXCLUSIONS:
        add_finding(findings, "SOURCE_EXCLUSION_POLICY_MISMATCH", "inventory.excluded_governance_source_files", sorted(EXPECTED_GOVERNANCE_SOURCE_EXCLUSIONS), sorted(source_exclusions))
    if meta_exclusions != EXPECTED_GOVERNANCE_META_EXCLUSIONS:
        add_finding(findings, "META_EXCLUSION_POLICY_MISMATCH", "inventory.excluded_governance_meta_files", sorted(EXPECTED_GOVERNANCE_META_EXCLUSIONS), sorted(meta_exclusions))

    source_files = [
        path for path in resources_root.rglob("*")
        if path.is_file()
        and path.suffix != ".meta"
        and path.relative_to(resources_root).as_posix() not in source_exclusions
    ]
    source_digest, extensions, source_sizes = inventory_digest(
        source_files,
        lambda path: path.relative_to(resources_root).as_posix(),
        text_extensions,
    )
    expected_source = inventory.get("source_payload") if isinstance(inventory, dict) else None
    if source_digest != expected_source:
        add_finding(findings, "SOURCE_FINGERPRINT_MISMATCH", "inventory.source_payload", expected_source, source_digest)
    expected_extensions = inventory.get("extension_counts") if isinstance(inventory, dict) else None
    if extensions != expected_extensions:
        add_finding(findings, "SOURCE_EXTENSION_COUNTS_MISMATCH", "inventory.extension_counts", expected_extensions, extensions)

    meta_files = [
        path for path in resources_root.rglob("*.meta")
        if path.relative_to(project_root).as_posix() not in meta_exclusions
    ]
    if RESOURCES_META_RELATIVE.as_posix() not in meta_exclusions:
        meta_files.append(project_root / RESOURCES_META_RELATIVE)
    meta_digest, _, _ = inventory_digest(
        meta_files,
        lambda path: path.relative_to(project_root).as_posix(),
        text_extensions,
    )
    expected_meta = inventory.get("cocos_metadata") if isinstance(inventory, dict) else None
    if meta_digest != expected_meta:
        add_finding(findings, "META_FINGERPRINT_MISMATCH", "inventory.cocos_metadata", expected_meta, meta_digest)

    scope_ids: set[str] = set()
    scope_owners: dict[str, str] = {}
    ownership_matches: dict[str, list[str]] = defaultdict(list)
    ownership_observed: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "bytes": 0})
    for index, scope in enumerate(manifest.get("ownership_scopes", [])):
        if not isinstance(scope, dict):
            continue
        scope_id = str(scope.get("scope_id", ""))
        if scope_id in scope_ids:
            add_finding(findings, "DUPLICATE_SCOPE_ID", f"ownership_scopes[{index}].scope_id", "unique", scope_id)
        scope_ids.add(scope_id)
        scope_owners[scope_id] = str(scope.get("owner", ""))
        for provenance in scope.get("provenance", []):
            resolved = resolve_project_path(project_root, str(provenance))
            if resolved is None or not resolved.is_file():
                add_finding(findings, "PROVENANCE_MISSING", f"ownership_scopes[{index}].provenance", "existing project file", provenance)
        for relative, size in source_sizes.items():
            if path_matches(relative, str(scope.get("path", "")), str(scope.get("match", ""))):
                ownership_matches[relative].append(scope_id)
                ownership_observed[scope_id]["count"] += 1
                ownership_observed[scope_id]["bytes"] += size
        expected_observed = {"count": scope.get("asset_count"), "bytes": scope.get("total_bytes")}
        if ownership_observed[scope_id] != expected_observed:
            add_finding(findings, "OWNERSHIP_OBSERVED_MISMATCH", f"ownership_scopes[{index}]", expected_observed, ownership_observed[scope_id])

    unowned = sorted(relative for relative in source_sizes if not ownership_matches.get(relative))
    overlaps = {relative: owners for relative, owners in ownership_matches.items() if len(owners) != 1}
    if unowned:
        add_finding(findings, "OWNERSHIP_UNCOVERED", "ownership_scopes", "every source exactly once", unowned[:50])
    if overlaps:
        add_finding(findings, "OWNERSHIP_OVERLAP", "ownership_scopes", "one owner per source", dict(list(sorted(overlaps.items()))[:50]))

    image_files = {
        path.relative_to(resources_root).as_posix(): path
        for path in resources_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    }
    atlas_ids: set[str] = set()
    atlas_matches: dict[str, list[str]] = defaultdict(list)
    auto_atlas_files = sorted(
        path.relative_to(project_root).as_posix()
        for path in (project_root / "assets").rglob("*")
        if path.is_file() and path.suffix.lower() in {".pac", ".plist", ".atlas", ".spriteatlas"}
    )
    for index, group in enumerate(manifest.get("atlas_groups", [])):
        if not isinstance(group, dict):
            continue
        atlas_id = str(group.get("atlas_id", ""))
        if atlas_id in atlas_ids:
            add_finding(findings, "DUPLICATE_ATLAS_ID", f"atlas_groups[{index}].atlas_id", "unique", atlas_id)
        atlas_ids.add(atlas_id)
        for provenance in group.get("provenance", []):
            resolved = resolve_project_path(project_root, str(provenance))
            if resolved is None or not resolved.is_file():
                add_finding(findings, "PROVENANCE_MISSING", f"atlas_groups[{index}].provenance", "existing project file", provenance)
        observed = {"count": 0, "bytes": 0}
        matched_in_group: set[str] = set()
        for selector in group.get("source_selectors", []):
            selector_path = str(selector.get("path", ""))
            mode = str(selector.get("match", ""))
            extensions_allowed = set(selector.get("extensions", []))
            for relative, path in image_files.items():
                if path.suffix.lower() in extensions_allowed and path_matches(relative, selector_path, mode):
                    matched_in_group.add(relative)
        for relative in matched_in_group:
            atlas_matches[relative].append(atlas_id)
            observed["count"] += 1
            observed["bytes"] += len(canonical_bytes(image_files[relative], text_extensions))
        owner_mismatches = {
            relative: scope_owners.get(ownership_matches[relative][0], "")
            for relative in sorted(matched_in_group)
            if len(ownership_matches.get(relative, [])) == 1
            and scope_owners.get(ownership_matches[relative][0], "") != str(group.get("owner", ""))
        }
        if owner_mismatches:
            add_finding(
                findings,
                "ATLAS_OWNER_MISMATCH",
                f"atlas_groups[{index}].owner",
                group.get("owner"),
                dict(list(owner_mismatches.items())[:50]),
            )
        if observed != group.get("observed"):
            add_finding(findings, "ATLAS_OBSERVED_MISMATCH", f"atlas_groups[{index}].observed", group.get("observed"), observed)
        packing = group.get("packing", {})
        if packing.get("implementation_status") == "policy_only_not_packed" and group.get("runtime_effect") is not False:
            add_finding(findings, "POLICY_ONLY_RUNTIME_EFFECT", f"atlas_groups[{index}].runtime_effect", False, group.get("runtime_effect"))

    atlas_uncovered = sorted(relative for relative in image_files if not atlas_matches.get(relative))
    atlas_overlaps = {relative: groups for relative, groups in atlas_matches.items() if len(groups) != 1}
    if atlas_uncovered:
        add_finding(findings, "ATLAS_SELECTOR_UNCOVERED", "atlas_groups", "every PNG/JPG exactly once", atlas_uncovered[:50])
    if atlas_overlaps:
        add_finding(findings, "ATLAS_SELECTOR_OVERLAP", "atlas_groups", "one group per PNG/JPG", dict(list(sorted(atlas_overlaps.items()))[:50]))

    bundle = manifest.get("bundle", {})
    resources_meta = load_json(project_root / RESOURCES_META_RELATIVE)
    bundle_user_data = resources_meta.get("userData", {}) if isinstance(resources_meta, dict) else {}
    actual_bundle = {
        "bundle_id": bundle_user_data.get("bundleName"),
        "is_bundle": bundle_user_data.get("isBundle"),
        "priority": bundle_user_data.get("priority"),
    }
    expected_bundle = {
        "bundle_id": bundle.get("bundle_id"),
        "is_bundle": bundle.get("is_bundle"),
        "priority": bundle.get("priority"),
    }
    if actual_bundle != expected_bundle:
        add_finding(findings, "BUNDLE_META_MISMATCH", "bundle", expected_bundle, actual_bundle)

    manifest_meta = load_json(project_root / MANIFEST_META_RELATIVE)
    expected_manifest_meta = {
        "ver": "2.0.1",
        "importer": "json",
        "imported": True,
        "files": [".json"],
        "subMetas": {},
        "userData": {},
    }
    actual_manifest_meta = {key: manifest_meta.get(key) for key in expected_manifest_meta} if isinstance(manifest_meta, dict) else manifest_meta
    if actual_manifest_meta != expected_manifest_meta or not UUID_RE.fullmatch(str(manifest_meta.get("uuid", ""))):
        add_finding(findings, "ATLAS_MANIFEST_META_INVALID", MANIFEST_META_RELATIVE.as_posix(), expected_manifest_meta, manifest_meta)

    checkpoint = validate_source_checkpoint(
        project_root,
        manifest.get("source_checkpoint"),
        content_identity,
        findings,
        check_git,
    )
    if manifest.get("content_identity", {}).get("logical_content_version") != content_identity.get("logical_content_version"):
        add_finding(findings, "CONTENT_IDENTITY_MANIFEST_MISMATCH", "content_identity.logical_content_version", content_identity.get("logical_content_version"), manifest.get("content_identity", {}).get("logical_content_version"))

    meta_graph = validate_meta_graph(project_root, resources_root, findings)
    return {
        "schema_version": 1,
        "contract": "mtr.m04_a_asset_contract_validation",
        "status": "PASS" if not findings else "FAIL",
        "counts": {
            "source_files": len(source_sizes),
            "ownership_scopes": len(manifest.get("ownership_scopes", [])),
            "image_files": len(image_files),
            "atlas_groups": len(manifest.get("atlas_groups", [])),
            "auto_atlas_files": len(auto_atlas_files),
            "findings": len(findings),
        },
        "fingerprints": {"source_payload": source_digest, "cocos_metadata": meta_digest},
        "coverage": {
            "unowned_sources": len(unowned),
            "ownership_overlaps": len(overlaps),
            "uncovered_images": len(atlas_uncovered),
            "atlas_overlaps": len(atlas_overlaps),
        },
        "bundle": actual_bundle,
        "meta_graph": meta_graph,
        "source_checkpoint": checkpoint,
        "auto_atlas_files": auto_atlas_files,
        "findings": findings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--report", default="")
    parser.add_argument("--skip-git", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    project_root = Path(args.project_root).resolve()
    report = validate_manifest(project_root, check_git=not args.skip_git)
    if args.report:
        output = resolve_project_path(project_root, args.report)
        if output is None:
            raise SystemExit("report path escapes project root")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
