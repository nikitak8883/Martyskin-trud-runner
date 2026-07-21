#!/usr/bin/env python3
"""M01.4 profile composition, freshness and applicability self-tests."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock


QUALITY_GATE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIRECTORY = PROJECT_ROOT / "docs/global_modernization/v3/library/schemas"
CATALOG_PATH = PROJECT_ROOT / "docs/global_modernization/v3/M01/quality_gate.config.json"
FIXTURE_RELATIVE = "tools/codex/quality-gate/tests/fixture_command.py"
sys.path.insert(0, str(QUALITY_GATE_ROOT))

import profile_runner  # noqa: E402
import runner  # noqa: E402
from profile_engine import ProfileError, resolve_profile, validate_catalog  # noqa: E402
from schema_engine import SchemaEngine, SchemaValidationError, sha256_file  # noqa: E402


SOURCE_COMMIT = runner._git_output(PROJECT_ROOT, ["rev-parse", "HEAD"]).lower()
SOURCE_DIRTY = bool(runner._git_output(PROJECT_ROOT, ["status", "--porcelain", "--untracked-files=normal", "--", "."]))
CONTENT_VERSION = "m01.4-selftest"


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class QualityProfileRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = PROJECT_ROOT / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(prefix="m01_4_quality_profile_", dir=temp_root)
        self.directory = Path(self._temporary.name)
        self.relative_directory = self.directory.relative_to(PROJECT_ROOT).as_posix()
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.scope_started = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.child_counter = 0

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def profile(self, profile_id: str) -> dict[str, Any]:
        return next(profile for profile in self.catalog["profiles"] if profile["id"] == profile_id)

    def test_json_snapshot_rejects_change_during_read(self) -> None:
        path = self.directory / "moving-input.json"
        path.write_text('{"value": 1}\n', encoding="utf-8")
        actual = path.stat()
        before = SimpleNamespace(
            st_dev=actual.st_dev,
            st_ino=actual.st_ino,
            st_size=actual.st_size,
            st_mtime_ns=actual.st_mtime_ns,
        )
        after = SimpleNamespace(
            st_dev=actual.st_dev,
            st_ino=actual.st_ino,
            st_size=actual.st_size,
            st_mtime_ns=actual.st_mtime_ns + 1,
        )

        with mock.patch.object(profile_runner.os, "fstat", side_effect=[before, after]):
            with self.assertRaises(runner.GateError) as caught:
                profile_runner._load_json_snapshot({}, path, "moving input", "moving_input")

        self.assertEqual(caught.exception.code, "PROTECTED_INPUT_CHANGED_DURING_READ")

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper integration")
    def test_powershell_wrapper_forwards_explicit_switches_and_exit_code(self) -> None:
        bindings = {
            slot["id"]: self.create_child_report(slot["gate_id"])
            for slot in self.profile("D4")["slots"]
        }
        scope_path = self.write_scope("D4", bindings, name="wrapper-scope.json")
        output_path = self.directory / "wrapper-report.json"
        script_path = QUALITY_GATE_ROOT / "run-profile.ps1"

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-ScopePath",
                str(scope_path),
                "-OutputPath",
                str(output_path),
                "-ConfigPath",
                str(CATALOG_PATH),
                "-AllowPhysicalDevice",
                "-AllowDirtySource",
                "-PythonExecutable",
                str(Path(getattr(sys, "_base_executable", sys.executable)).resolve()),
            ],
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["source"]["dirty_authorized"])

    def create_child_report(self, gate_id: str, *, mode: str = "pass") -> Path:
        self.child_counter += 1
        child_dir = self.directory / f"child-{self.child_counter:02d}"
        child_dir.mkdir(parents=True, exist_ok=True)
        relative_child = child_dir.relative_to(PROJECT_ROOT).as_posix()
        config_path = child_dir / "gate.json"
        report_path = child_dir / "report.json"
        config = {
            "schema_version": 1,
            "contract": "mtr.quality_gate_config",
            "gate_id": gate_id,
            "artifact_directory": f"{relative_child}/artifacts",
            "steps": [
                {
                    "id": "fixture_gate",
                    "mandatory": True,
                    "enabled": True,
                    "executable": sys.executable,
                    "arguments": [FIXTURE_RELATIVE, "--mode", mode],
                    "working_directory": ".",
                    "timeout_seconds": 10,
                    "expected_exit_codes": [0],
                }
            ],
        }
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        runner.run_gate(
            project_root=PROJECT_ROOT,
            config_path=config_path,
            output_path=report_path,
            source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            content_version=CONTENT_VERSION,
            source_dirty=SOURCE_DIRTY,
            allow_dirty_source=SOURCE_DIRTY,
            run_id=f"qg.profile-child.{self.child_counter}",
        )
        return report_path

    def write_scope(
        self,
        profile_id: str,
        bindings: dict[str, Path],
        *,
        decisions: list[dict[str, Any]] | None = None,
        started_at: datetime | None = None,
        name: str = "scope.json",
    ) -> Path:
        scope_path = self.directory / name
        scope = {
            "schema_version": 1,
            "contract": "mtr.quality_profile_scope",
            "profile_id": profile_id,
            "run_id": f"profile.selftest.{profile_id.lower().replace('_', '-')}",
            "started_at": iso(started_at or self.scope_started),
            "source_commit": SOURCE_COMMIT,
            "content_version": CONTENT_VERSION,
            "profile_config_sha256": sha256_file(CATALOG_PATH),
            "condition_decisions": decisions or [],
            "evidence_bindings": [
                {
                    "slot_id": slot_id,
                    "report_path": path.relative_to(PROJECT_ROOT).as_posix(),
                }
                for slot_id, path in bindings.items()
            ],
        }
        scope_path.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return scope_path

    def run_scope(self, scope_path: Path, output_name: str = "profile-report.json") -> dict[str, Any]:
        return profile_runner.run_profile(
            project_root=PROJECT_ROOT,
            config_path=CATALOG_PATH,
            scope_path=scope_path,
            output_path=self.directory / output_name,
            allow_dirty_source=SOURCE_DIRTY,
        )

    def test_catalog_schema_and_canonical_topology(self) -> None:
        engine = SchemaEngine(SCHEMA_DIRECTORY, QUALITY_GATE_ROOT / "requirements.lock")
        engine.assert_isolated_runtime()
        engine.validate(profile_runner.PROFILE_CONFIG_SCHEMA, self.catalog)
        profiles = validate_catalog(self.catalog)
        self.assertEqual(set(profiles), {"D4", "P4", "M2_PLUS", "QA7", "RC2"})
        self.assertEqual({key: len(value["slots"]) for key, value in profiles.items()}, {
            "D4": 4,
            "P4": 4,
            "M2_PLUS": 12,
            "QA7": 7,
            "RC2": 20,
        })

    def test_d4_profile_passes_and_has_deterministic_semantic_projection(self) -> None:
        bindings = {
            slot["id"]: self.create_child_report(slot["gate_id"])
            for slot in self.profile("D4")["slots"]
        }
        scope_path = self.write_scope("D4", bindings)
        first = self.run_scope(scope_path, "profile-first.json")
        second = self.run_scope(scope_path, "profile-second.json")
        self.assertEqual(first["status"], "PASS")
        self.assertEqual([slot["status"] for slot in first["slots"]], ["PASS"] * 4)
        self.assertEqual(profile_runner.semantic_projection(first), profile_runner.semantic_projection(second))

    def test_missing_mandatory_binding_blocks_with_valid_report(self) -> None:
        scope_path = self.write_scope("D4", {})
        report = self.run_scope(scope_path)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual([slot["status"] for slot in report["slots"]], ["BLOCKED"] * 4)
        self.assertIn("MANDATORY_EVIDENCE_MISSING", [finding["code"] for finding in report["findings"]])

    def test_stale_child_report_blocks(self) -> None:
        slot = self.profile("D4")["slots"][0]
        child = self.create_child_report(slot["gate_id"])
        scope_path = self.write_scope("D4", {slot["id"]: child}, started_at=datetime.now(timezone.utc) + timedelta(seconds=1))
        report = self.run_scope(scope_path)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("STALE_PROFILE_EVIDENCE", [finding["code"] for finding in report["findings"]])

    def test_unknown_child_schema_blocks_instead_of_false_green(self) -> None:
        slot = self.profile("D4")["slots"][0]
        child = self.create_child_report(slot["gate_id"])
        document = json.loads(child.read_text(encoding="utf-8"))
        document["contract"] = "unknown.false_green"
        child.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        scope_path = self.write_scope("D4", {slot["id"]: child})
        report = self.run_scope(scope_path)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("CHILD_REPORT_SCHEMA_UNKNOWN_OR_INVALID", [finding["code"] for finding in report["findings"]])

    def test_changed_child_artifact_blocks(self) -> None:
        slot = self.profile("D4")["slots"][0]
        child = self.create_child_report(slot["gate_id"])
        document = json.loads(child.read_text(encoding="utf-8"))
        artifact = PROJECT_ROOT / document["artifacts"][0]["relative_path"]
        artifact.write_text("tampered after child gate\n", encoding="utf-8")
        scope_path = self.write_scope("D4", {slot["id"]: child})
        report = self.run_scope(scope_path)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("CHILD_ARTIFACT_CHANGED", [finding["code"] for finding in report["findings"]])

    def test_copied_child_report_is_rejected_as_reuse(self) -> None:
        first_slot, second_slot = self.profile("D4")["slots"][:2]
        first = self.create_child_report(first_slot["gate_id"])
        copied = self.directory / "copied-report.json"
        copied.write_bytes(first.read_bytes())
        scope_path = self.write_scope("D4", {first_slot["id"]: first, second_slot["id"]: copied})
        report = self.run_scope(scope_path)
        codes = [finding["code"] for finding in report["findings"]]
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("CHILD_RUN_ID_REUSED", codes)
        self.assertIn("CHILD_REPORT_REUSED", codes)

    def test_aggregate_output_cannot_overwrite_child_config(self) -> None:
        slot = self.profile("D4")["slots"][0]
        child = self.create_child_report(slot["gate_id"])
        document = json.loads(child.read_text(encoding="utf-8"))
        child_config = PROJECT_ROOT / document["config"]["relative_path"]
        before = sha256_file(child_config)
        scope_path = self.write_scope("D4", {slot["id"]: child})
        with self.assertRaises(ProfileError) as caught:
            profile_runner.run_profile(
                project_root=PROJECT_ROOT,
                config_path=CATALOG_PATH,
                scope_path=scope_path,
                output_path=child_config,
                allow_dirty_source=True,
            )
        self.assertEqual(caught.exception.code, "PROFILE_OUTPUT_INPUT_COLLISION")
        self.assertEqual(sha256_file(child_config), before)

    def test_m2_focused_recovery_is_explicit_not_applicable(self) -> None:
        profile = self.profile("M2_PLUS")
        mandatory = [slot for slot in profile["slots"] if slot["requirement"] == "mandatory"]
        scope = {
            "profile_id": "M2_PLUS",
            "profile_config_sha256": sha256_file(CATALOG_PATH),
            "condition_decisions": [
                {
                    "condition_id": "high_risk_recovery",
                    "applicable": False,
                    "reason_code": "not_triggered_by_scope",
                    "reason": "No GameRoot, save, signing, release or failure-recovery seam is in this test scope.",
                }
            ],
            "evidence_bindings": [
                {"slot_id": slot["id"], "report_path": f"temp/{slot['id']}.json"}
                for slot in mandatory
            ],
        }
        resolution = resolve_profile(
            self.catalog,
            scope,
            config_sha256=sha256_file(CATALOG_PATH),
            allow_physical_device=False,
        )
        not_applicable = [slot for slot in resolution.slots if slot.applicability["status"] == "not_applicable"]
        self.assertEqual(len(not_applicable), 4)
        self.assertTrue(all(not slot.effective_mandatory and slot.report_path is None for slot in not_applicable))

    def test_missing_conditional_decision_is_configuration_error(self) -> None:
        profile = self.profile("M2_PLUS")
        mandatory = [slot for slot in profile["slots"] if slot["requirement"] == "mandatory"]
        scope = {
            "profile_id": "M2_PLUS",
            "profile_config_sha256": sha256_file(CATALOG_PATH),
            "condition_decisions": [],
            "evidence_bindings": [
                {"slot_id": slot["id"], "report_path": f"temp/{slot['id']}.json"}
                for slot in mandatory
            ],
        }
        with self.assertRaises(ProfileError) as caught:
            resolve_profile(self.catalog, scope, config_sha256=sha256_file(CATALOG_PATH), allow_physical_device=False)
        self.assertEqual(caught.exception.code, "CONDITION_DECISION_SET_MISMATCH")

    def test_m2_cycle_order_rejects_overlapping_passes(self) -> None:
        profile = self.profile("M2_PLUS")
        mandatory = [slot for slot in profile["slots"] if slot["requirement"] == "mandatory"]
        scope = {
            "profile_id": "M2_PLUS",
            "profile_config_sha256": sha256_file(CATALOG_PATH),
            "condition_decisions": [
                {
                    "condition_id": "high_risk_recovery",
                    "applicable": False,
                    "reason_code": "not_triggered_by_scope",
                    "reason": "No focused recovery trigger is present.",
                }
            ],
            "evidence_bindings": [
                {"slot_id": slot["id"], "report_path": f"temp/cycle-{index}.json"}
                for index, slot in enumerate(mandatory)
            ],
        }
        resolution = resolve_profile(
            self.catalog,
            scope,
            config_sha256=sha256_file(CATALOG_PATH),
            allow_physical_device=False,
        )
        results = [
            {"id": slot.id, "cycle_id": slot.cycle_id}
            for slot in resolution.slots
        ]
        pass_a = next(slot for slot in resolution.slots if slot.cycle_id == "pass_a")
        pass_b = next(slot for slot in resolution.slots if slot.cycle_id == "pass_b")
        generated = {
            pass_a.id: datetime(2026, 7, 21, 12, 0, 2, tzinfo=timezone.utc),
            pass_b.id: datetime(2026, 7, 21, 12, 0, 1, tzinfo=timezone.utc),
        }
        findings = profile_runner._cycle_order_findings(resolution, results, generated)
        self.assertEqual([finding["code"] for finding in findings], ["PROFILE_CYCLE_ORDER_INVALID"])

    def test_scope_hash_mismatch_is_configuration_error(self) -> None:
        scope = {
            "profile_id": "D4",
            "profile_config_sha256": "A" * 64,
            "condition_decisions": [],
            "evidence_bindings": [],
        }
        with self.assertRaises(ProfileError) as caught:
            resolve_profile(self.catalog, scope, config_sha256=sha256_file(CATALOG_PATH), allow_physical_device=False)
        self.assertEqual(caught.exception.code, "PROFILE_CONFIG_HASH_MISMATCH")

    def test_physical_device_condition_requires_explicit_cli_authorization(self) -> None:
        profile = self.profile("RC2")
        bindings = [
            {"slot_id": slot["id"], "report_path": f"temp/{slot['id']}.json"}
            for slot in profile["slots"]
            if slot["requirement"] == "mandatory" or slot.get("condition_id") == "physical_device_authorized"
        ]
        scope = {
            "profile_id": "RC2",
            "profile_config_sha256": sha256_file(CATALOG_PATH),
            "condition_decisions": [
                {
                    "condition_id": "play_store_target",
                    "applicable": False,
                    "reason_code": "play_target_not_approved",
                    "reason": "No Play distribution target is approved.",
                },
                {"condition_id": "physical_device_authorized", "applicable": True},
            ],
            "evidence_bindings": bindings,
        }
        with self.assertRaises(ProfileError) as caught:
            resolve_profile(self.catalog, scope, config_sha256=sha256_file(CATALOG_PATH), allow_physical_device=False)
        self.assertEqual(caught.exception.code, "PHYSICAL_DEVICE_NOT_AUTHORIZED")

    def test_report_schema_rejects_false_green_mutation(self) -> None:
        scope_path = self.write_scope("D4", {})
        blocked = self.run_scope(scope_path)
        false_green = copy.deepcopy(blocked)
        false_green["status"] = "PASS"
        false_green["source"]["matches_scope"] = True
        false_green["source"]["stable_during_run"] = True
        engine = SchemaEngine(SCHEMA_DIRECTORY, QUALITY_GATE_ROOT / "requirements.lock")
        engine.assert_isolated_runtime()
        with self.assertRaises(SchemaValidationError):
            engine.validate(profile_runner.PROFILE_REPORT_SCHEMA, false_green)


if __name__ == "__main__":
    unittest.main(verbosity=2)
