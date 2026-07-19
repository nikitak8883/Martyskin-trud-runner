#!/usr/bin/env python3
"""Pinned Draft 2020-12 schema engine for the MTR quality gate."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012


@dataclass(frozen=True)
class SchemaIssue:
    instance_path: str
    schema_path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "instance_path": self.instance_path,
            "schema_path": self.schema_path,
            "message": self.message,
        }


class SchemaValidationError(ValueError):
    """A deterministic collection of Draft 2020-12 validation errors."""

    def __init__(self, schema_name: str, issues: list[SchemaIssue]) -> None:
        super().__init__(f"{schema_name}: {len(issues)} schema validation error(s)")
        self.schema_name = schema_name
        self.issues = issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_requirements_lock(path: Path) -> dict[str, str]:
    packages: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line or line.count("==") != 1:
            raise RuntimeError(f"Unsupported requirements.lock entry: {line!r}")
        name, version = line.split("==", 1)
        normalized = name.strip().lower().replace("_", "-")
        if not normalized or not version.strip() or normalized in packages:
            raise RuntimeError(f"Invalid or duplicate requirements.lock entry: {line!r}")
        packages[normalized] = version.strip()
    if "jsonschema" not in packages:
        raise RuntimeError("requirements.lock must pin jsonschema")
    return packages


class SchemaEngine:
    """Offline-only schema registry; remote references are never retrieved."""

    def __init__(self, schema_directory: Path, requirements_lock: Path) -> None:
        self.schema_directory = schema_directory.resolve(strict=True)
        self.requirements_lock = requirements_lock.resolve(strict=True)
        self.schemas: dict[str, dict[str, Any]] = {}
        resources: list[tuple[str, Any]] = []
        for path in sorted(self.schema_directory.glob("*.schema.json")):
            document = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(document, dict):
                raise RuntimeError(f"Schema is not an object: {path}")
            Draft202012Validator.check_schema(document)
            schema_id = document.get("$id")
            if not isinstance(schema_id, str) or not schema_id:
                raise RuntimeError(f"Schema has no canonical $id: {path}")
            if path.name in self.schemas:
                raise RuntimeError(f"Duplicate schema filename: {path.name}")
            self.schemas[path.name] = document
            resources.append((schema_id, DRAFT202012.create_resource(document)))
        self.registry = Registry().with_resources(resources)
        self.lock_sha256 = sha256_file(self.requirements_lock)

    def assert_isolated_runtime(self) -> dict[str, Any]:
        expected_lock = os.environ.get("MTR_QUALITY_GATE_LOCK_SHA256", "").upper()
        isolated_flag = os.environ.get("MTR_QUALITY_GATE_ISOLATED") == "1"
        in_venv = Path(sys.prefix).resolve() != Path(sys.base_prefix).resolve()
        if not isolated_flag or not in_venv or expected_lock != self.lock_sha256:
            raise RuntimeError(
                "UNTRUSTED_VALIDATOR_ENV: invoke bootstrap.py or run.ps1; "
                "the runner requires its exact isolated venv and lock identity"
            )
        expected_packages = parse_requirements_lock(self.requirements_lock)
        actual_packages: dict[str, str] = {}
        mismatches: list[str] = []
        for name, expected_version in sorted(expected_packages.items()):
            try:
                actual_version = metadata.version(name)
            except metadata.PackageNotFoundError:
                mismatches.append(f"{name}: missing (expected {expected_version})")
                continue
            actual_packages[name] = actual_version
            if actual_version != expected_version:
                mismatches.append(f"{name}: {actual_version} (expected {expected_version})")
        if mismatches:
            raise RuntimeError("VALIDATOR_LOCK_MISMATCH: " + "; ".join(mismatches))
        return {
            "name": "jsonschema",
            "version": actual_packages["jsonschema"],
            "draft": "2020-12",
            "isolated": True,
            "lock_sha256": self.lock_sha256,
            "python_version": ".".join(str(value) for value in sys.version_info[:3]),
        }

    def validate(self, schema_name: str, instance: Any) -> None:
        schema = self.schemas.get(schema_name)
        if schema is None:
            raise RuntimeError(f"Unknown canonical schema: {schema_name}")
        validator = Draft202012Validator(schema, registry=self.registry)
        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                tuple(str(part) for part in error.absolute_schema_path),
                error.message,
            ),
        )
        if not errors:
            return
        issues = [
            SchemaIssue(
                instance_path=_json_pointer(error.absolute_path),
                schema_path=_json_pointer(error.absolute_schema_path),
                message=error.message,
            )
            for error in errors
        ]
        raise SchemaValidationError(schema_name, issues)


def _json_pointer(parts: Any) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else "/"
