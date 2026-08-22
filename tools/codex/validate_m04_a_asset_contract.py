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
ATLAS_FAMILY_UNIT_RE = re.compile(r"^M04-C-FAMILY-[A-Z0-9-]+$")
ATLAS_CONTRACT_TO_ACCEPTANCE_SCHEMA = {
    "mtr.m04_c_atlas_pilot_contract.v1": "mtr.m04_c_atlas_pilot_acceptance.v1",
    "mtr.m04_c_atlas_family_contract.v1": "mtr.m04_c_atlas_family_acceptance.v1",
}


def descriptor_identity(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, dict):
        return []
    descriptors = value.get("descriptors")
    if isinstance(descriptors, list):
        return [
            {
                "descriptor": str(item.get("descriptor", "")),
                "descriptor_uuid": str(item.get("descriptor_uuid", "")),
            }
            for item in descriptors
            if isinstance(item, dict)
        ]
    if value.get("descriptor") is None and value.get("descriptor_uuid") is None:
        return []
    return [{
        "descriptor": str(value.get("descriptor", "")),
        "descriptor_uuid": str(value.get("descriptor_uuid", "")),
    }]


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
    measured_descriptors: dict[str, list[str]] = defaultdict(list)
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
        implementation_status = packing.get("implementation_status")
        descriptor_fields = {
            key: packing.get(key)
            for key in ("descriptor", "descriptor_uuid", "descriptors", "measurement_contract", "acceptance_evidence")
            if packing.get(key) is not None
        }
        if implementation_status == "policy_only_not_packed" and group.get("runtime_effect") is not False:
            add_finding(findings, "POLICY_ONLY_RUNTIME_EFFECT", f"atlas_groups[{index}].runtime_effect", False, group.get("runtime_effect"))
        if implementation_status != "measured_static_atlas" and descriptor_fields:
            add_finding(findings, "UNMEASURED_ATLAS_DESCRIPTOR", f"atlas_groups[{index}].packing", "no descriptor fields", descriptor_fields)
        if implementation_status == "measured_static_atlas":
            raw_descriptors = packing.get("descriptors")
            descriptor_specs = raw_descriptors if isinstance(raw_descriptors, list) else [{
                "descriptor": packing.get("descriptor"),
                "descriptor_uuid": packing.get("descriptor_uuid"),
            }]
            manifest_descriptor_identity = descriptor_identity(packing)
            for descriptor_index, descriptor_spec in enumerate(descriptor_specs):
                descriptor_label = (
                    f"atlas_groups[{index}].packing.descriptors[{descriptor_index}]"
                    if isinstance(raw_descriptors, list)
                    else f"atlas_groups[{index}].packing"
                )
                if not isinstance(descriptor_spec, dict):
                    add_finding(findings, "AUTO_ATLAS_DESCRIPTOR_INVALID", descriptor_label, "descriptor object", descriptor_spec)
                    continue
                descriptor = str(descriptor_spec.get("descriptor", ""))
                descriptor_uuid = str(descriptor_spec.get("descriptor_uuid", ""))
                measured_descriptors[descriptor].append(atlas_id)
                descriptor_path = resolve_project_path(project_root, descriptor)
                descriptor_meta_path = resolve_project_path(project_root, f"{descriptor}.meta")
                source_directory = descriptor_spec.get("source_directory")
                if source_directory is not None:
                    source_root = resolve_project_path(project_root, str(source_directory))
                    expected_source_count = descriptor_spec.get("source_count")
                    actual_source_count = (
                        len(list(source_root.glob("*.png")))
                        if source_root is not None and source_root.is_dir()
                        else None
                    )
                    descriptor_parent = descriptor_path.parent if descriptor_path is not None else None
                    if source_root is None or not source_root.is_dir() or descriptor_parent != source_root:
                        add_finding(
                            findings,
                            "AUTO_ATLAS_SOURCE_DIRECTORY_MISMATCH",
                            descriptor_label,
                            "existing directory equal to descriptor parent",
                            source_directory,
                        )
                    if actual_source_count != expected_source_count:
                        add_finding(
                            findings,
                            "AUTO_ATLAS_SOURCE_COUNT_MISMATCH",
                            f"{descriptor_label}.source_count",
                            expected_source_count,
                            actual_source_count,
                        )
                if descriptor_path is None or not descriptor_path.is_file():
                    add_finding(findings, "AUTO_ATLAS_DESCRIPTOR_MISSING", f"{descriptor_label}.descriptor", "existing project file", descriptor)
                else:
                    try:
                        descriptor_value = load_json(descriptor_path)
                    except (OSError, json.JSONDecodeError) as exc:
                        add_finding(findings, "AUTO_ATLAS_DESCRIPTOR_INVALID", descriptor, {"__type__": "cc.SpriteAtlas"}, str(exc))
                    else:
                        if descriptor_value != {"__type__": "cc.SpriteAtlas"}:
                            add_finding(findings, "AUTO_ATLAS_DESCRIPTOR_INVALID", descriptor, {"__type__": "cc.SpriteAtlas"}, descriptor_value)
                if descriptor_meta_path is None or not descriptor_meta_path.is_file():
                    add_finding(findings, "AUTO_ATLAS_META_MISSING", f"{descriptor}.meta", "existing project file", None)
                else:
                    try:
                        descriptor_meta = load_json(descriptor_meta_path)
                    except (OSError, json.JSONDecodeError) as exc:
                        add_finding(findings, "AUTO_ATLAS_META_INVALID", f"{descriptor}.meta", "valid JSON", str(exc))
                    else:
                        actual_meta_header = {
                            "ver": descriptor_meta.get("ver"),
                            "importer": descriptor_meta.get("importer"),
                            "imported": descriptor_meta.get("imported"),
                            "uuid": descriptor_meta.get("uuid"),
                            "files": descriptor_meta.get("files"),
                            "subMetas": descriptor_meta.get("subMetas"),
                        }
                        expected_meta_header = {
                            "ver": "1.0.8",
                            "importer": "auto-atlas",
                            "imported": True,
                            "uuid": descriptor_uuid,
                            "files": [".json"],
                            "subMetas": {},
                        }
                        if actual_meta_header != expected_meta_header:
                            add_finding(findings, "AUTO_ATLAS_META_MISMATCH", f"{descriptor}.meta", expected_meta_header, actual_meta_header)
                        user_data = descriptor_meta.get("userData", {})
                        expected_user_data = {
                            "maxWidth": packing.get("max_texture_size"),
                            "maxHeight": packing.get("max_texture_size"),
                            "padding": packing.get("padding_px"),
                            "allowRotation": False,
                            "forceSquared": False,
                            "powerOfTwo": False,
                            "algorithm": "MaxRects",
                            "format": "png",
                            "quality": 80,
                            "contourBleed": True,
                            "paddingBleed": True,
                            "filterUnused": False,
                            "removeTextureInBundle": True,
                            "removeImageInBundle": True,
                            "removeSpriteAtlasInBundle": True,
                            "compressSettings": {},
                            "textureSetting": {
                                "wrapModeS": "clamp-to-edge",
                                "wrapModeT": "clamp-to-edge",
                                "minfilter": "linear",
                                "magfilter": "linear",
                                "mipfilter": "none",
                                "anisotropy": 0,
                            },
                        }
                        if user_data != expected_user_data:
                            add_finding(findings, "AUTO_ATLAS_SETTINGS_MISMATCH", f"{descriptor}.meta.userData", expected_user_data, user_data)

            measurement_path = resolve_project_path(project_root, str(packing.get("measurement_contract", "")))
            acceptance_path = resolve_project_path(project_root, str(packing.get("acceptance_evidence", "")))
            measurement_checks: dict[str, Any] | None = None
            expected_acceptance_schema: str | None = None
            expected_acceptance_unit: str | None = None
            expected_parent_unit: str | None = None
            if measurement_path is None or not measurement_path.is_file():
                add_finding(findings, "ATLAS_MEASUREMENT_CONTRACT_MISSING", f"atlas_groups[{index}].packing.measurement_contract", "existing project file", packing.get("measurement_contract"))
            else:
                try:
                    measurement = load_json(measurement_path)
                except (OSError, json.JSONDecodeError) as exc:
                    add_finding(findings, "ATLAS_MEASUREMENT_CONTRACT_INVALID_JSON", str(packing.get("measurement_contract")), "valid JSON object", str(exc))
                else:
                    if not isinstance(measurement, dict):
                        add_finding(findings, "ATLAS_MEASUREMENT_CONTRACT_INVALID", str(packing.get("measurement_contract")), "JSON object", type(measurement).__name__)
                    else:
                        measurement_candidate = measurement.get("candidate") if isinstance(measurement.get("candidate"), dict) else {}
                        measurement_result = measurement.get("candidate_result") if isinstance(measurement.get("candidate_result"), dict) else {}
                        measurement_checks_value = measurement_result.get("acceptance_checks")
                        if isinstance(measurement_checks_value, dict):
                            measurement_checks = measurement_checks_value
                        measurement_schema = str(measurement.get("$schema", ""))
                        measurement_unit = str(measurement.get("unit_id", ""))
                        is_pilot_contract = (
                            measurement_schema == "mtr.m04_c_atlas_pilot_contract.v1"
                            and measurement_unit == "M04-C-PILOT"
                            and measurement.get("parent_unit") is None
                        )
                        is_family_contract = (
                            measurement_schema == "mtr.m04_c_atlas_family_contract.v1"
                            and ATLAS_FAMILY_UNIT_RE.fullmatch(measurement_unit) is not None
                            and measurement.get("parent_unit") == "M04-C-FAMILIES"
                        )
                        measurement_identity_valid = is_pilot_contract or is_family_contract
                        if measurement_identity_valid:
                            expected_acceptance_schema = ATLAS_CONTRACT_TO_ACCEPTANCE_SCHEMA[measurement_schema]
                            expected_acceptance_unit = measurement_unit
                            expected_parent_unit = "M04-C-FAMILIES" if is_family_contract else None
                        measurement_actual = {
                            "schema": measurement_schema,
                            "unit_id": measurement_unit,
                            "parent_unit": measurement.get("parent_unit"),
                            "status": measurement.get("status"),
                            "atlas_id": measurement_candidate.get("atlas_id"),
                            "descriptors": descriptor_identity(measurement_candidate),
                            "result": measurement_result.get("status"),
                            "acceptance_checks": measurement_checks,
                        }
                        measurement_expected = {
                            "schema": measurement_schema if measurement_identity_valid else sorted(ATLAS_CONTRACT_TO_ACCEPTANCE_SCHEMA),
                            "unit_id": measurement_unit if measurement_identity_valid else "M04-C-PILOT or M04-C-FAMILY-<ID>",
                            "parent_unit": expected_parent_unit,
                            "status": "candidate_accepted",
                            "atlas_id": atlas_id,
                            "descriptors": manifest_descriptor_identity,
                            "result": "accepted",
                            "acceptance_checks": measurement_checks,
                        }
                        checks_valid = (
                            isinstance(measurement_checks, dict)
                            and isinstance(measurement_checks.get("total"), int)
                            and measurement_checks["total"] > 0
                            and measurement_checks.get("passed") == measurement_checks["total"]
                        )
                        if not measurement_identity_valid or not checks_valid or measurement_actual != measurement_expected:
                            add_finding(findings, "ATLAS_MEASUREMENT_CONTRACT_MISMATCH", str(packing.get("measurement_contract")), measurement_expected, measurement_actual)
            if acceptance_path is None or not acceptance_path.is_file():
                add_finding(findings, "ATLAS_ACCEPTANCE_EVIDENCE_MISSING", f"atlas_groups[{index}].packing.acceptance_evidence", "existing project file", packing.get("acceptance_evidence"))
            else:
                try:
                    acceptance = load_json(acceptance_path)
                except (OSError, json.JSONDecodeError) as exc:
                    add_finding(findings, "ATLAS_ACCEPTANCE_EVIDENCE_INVALID_JSON", str(packing.get("acceptance_evidence")), "valid JSON object", str(exc))
                else:
                    if not isinstance(acceptance, dict):
                        add_finding(findings, "ATLAS_ACCEPTANCE_EVIDENCE_INVALID", str(packing.get("acceptance_evidence")), "JSON object", type(acceptance).__name__)
                    else:
                        acceptance_candidate = acceptance.get("candidate") if isinstance(acceptance.get("candidate"), dict) else {}
                        acceptance_result = acceptance.get("acceptance") if isinstance(acceptance.get("acceptance"), dict) else {}
                        acceptance_actual = {
                            "schema": acceptance.get("$schema"),
                            "unit_id": acceptance.get("unit_id"),
                            "parent_unit": acceptance.get("parent_unit"),
                            "status": acceptance.get("status"),
                            "atlas_id": acceptance_candidate.get("atlas_id"),
                            "descriptors": descriptor_identity(acceptance_candidate),
                            "checks_passed": acceptance_result.get("checks_passed"),
                            "checks_total": acceptance_result.get("checks_total"),
                        }
                        expected_total = measurement_checks.get("total") if isinstance(measurement_checks, dict) else None
                        acceptance_expected = {
                            "schema": expected_acceptance_schema,
                            "unit_id": expected_acceptance_unit,
                            "parent_unit": expected_parent_unit,
                            "status": "PASS",
                            "atlas_id": atlas_id,
                            "descriptors": manifest_descriptor_identity,
                            "checks_passed": expected_total,
                            "checks_total": expected_total,
                        }
                        if expected_total is None or expected_acceptance_schema is None or acceptance_actual != acceptance_expected:
                            add_finding(findings, "ATLAS_ACCEPTANCE_EVIDENCE_MISMATCH", str(packing.get("acceptance_evidence")), acceptance_expected, acceptance_actual)

    duplicate_descriptors = {descriptor: groups for descriptor, groups in measured_descriptors.items() if len(groups) != 1}
    for descriptor, groups in sorted(duplicate_descriptors.items()):
        add_finding(findings, "AUTO_ATLAS_DESCRIPTOR_DUPLICATE", descriptor, "one measured atlas group", groups)
    measured_descriptor_set = {descriptor for descriptor in measured_descriptors if descriptor}
    unregistered_auto_atlases = sorted(set(auto_atlas_files) - measured_descriptor_set)
    missing_auto_atlases = sorted(measured_descriptor_set - set(auto_atlas_files))
    if unregistered_auto_atlases:
        add_finding(findings, "AUTO_ATLAS_UNREGISTERED", "atlas_groups", "all descriptors registered", unregistered_auto_atlases)
    if missing_auto_atlases:
        add_finding(findings, "AUTO_ATLAS_REGISTERED_MISSING", "atlas_groups", "all registered descriptors exist", missing_auto_atlases)

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
            "measured_static_atlases": sum(len(groups) for groups in measured_descriptors.values()),
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
