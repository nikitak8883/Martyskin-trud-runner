#!/usr/bin/env python3
"""M01.3 process, containment, schema, adapter and atomic-write self-tests."""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


QUALITY_GATE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIRECTORY = PROJECT_ROOT / "docs/global_modernization/v3/library/schemas"
FIXTURE_RELATIVE = "tools/codex/quality-gate/tests/fixture_command.py"
sys.path.insert(0, str(QUALITY_GATE_ROOT))

import runner  # noqa: E402
from schema_engine import SchemaEngine, SchemaValidationError  # noqa: E402


SOURCE_COMMIT = runner._git_output(PROJECT_ROOT, ["rev-parse", "HEAD"]).lower()
SOURCE_DIRTY = bool(runner._git_output(PROJECT_ROOT, ["status", "--porcelain", "--untracked-files=normal", "--", "."]))


class QualityGateRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = PROJECT_ROOT / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(prefix="m01_3_quality_gate_", dir=temp_root)
        self.directory = Path(self._temporary.name)
        self.relative_directory = self.directory.relative_to(PROJECT_ROOT).as_posix()
        self.config_path = self.directory / "gate.json"
        self.output_path = self.directory / "report.json"
        self.run_counter = 0

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def base_step(self, mode: str = "pass") -> dict[str, Any]:
        return {
            "id": f"fixture_{mode.replace('-', '_')}",
            "mandatory": True,
            "enabled": True,
            "executable": sys.executable,
            "arguments": [FIXTURE_RELATIVE, "--mode", mode],
            "working_directory": ".",
            "timeout_seconds": 10,
            "expected_exit_codes": [0],
        }

    def config(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "contract": "mtr.quality_gate_config",
            "gate_id": "mtr.m01_3.selftest",
            "artifact_directory": f"{self.relative_directory}/artifacts",
            "steps": steps,
        }

    def write_config(self, document: dict[str, Any]) -> None:
        self.config_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def run_config(self, document: dict[str, Any], output_path: Path | None = None) -> dict[str, Any]:
        self.write_config(document)
        self.run_counter += 1
        return runner.run_gate(
            project_root=PROJECT_ROOT,
            config_path=self.config_path,
            output_path=output_path or self.output_path,
            source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            content_version="m01.3-selftest",
            source_dirty=SOURCE_DIRTY,
            allow_dirty_source=True,
            run_id=f"qg.selftest.{self.run_counter}",
        )

    def test_pass_records_separate_streams_and_valid_report(self) -> None:
        step = self.base_step()
        step["arguments"].append("--stderr")
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "PASS")
        result = report["steps"][0]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exit_code"], 0)
        stdout = PROJECT_ROOT / result["artifacts"][0]["relative_path"]
        stderr = PROJECT_ROOT / result["artifacts"][1]["relative_path"]
        self.assertIn("fixture-pass", stdout.read_text(encoding="utf-8"))
        self.assertIn("fixture-stderr", stderr.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(self.output_path.read_text(encoding="utf-8"))["status"], "PASS")

    def test_nonzero_mandatory_step_fails(self) -> None:
        report = self.run_config(self.config([self.base_step("fail")]))
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["steps"][0]["exit_code"], 7)
        self.assertIn("UNEXPECTED_EXIT_CODE", [item["code"] for item in report["findings"]])

    def test_missing_tool_blocks(self) -> None:
        step = self.base_step()
        step["id"] = "missing_tool"
        step["executable"] = "mtr-tool-that-does-not-exist-019edad0"
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIsNone(report["steps"][0]["exit_code"])
        self.assertIn("EXECUTABLE_NOT_FOUND", [item["code"] for item in report["findings"]])

    def test_timeout_terminates_child_process_tree(self) -> None:
        marker = self.directory / "child.marker"
        step = self.base_step("spawn-child")
        step["arguments"].extend(
            [
                "--marker",
                marker.relative_to(PROJECT_ROOT).as_posix(),
                "--delay",
                "3",
                "--parent-sleep",
                "20",
            ]
        )
        step["timeout_seconds"] = 1
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["steps"][0]["timed_out"])
        time.sleep(3.5)
        self.assertFalse(marker.exists(), "child process survived process-tree termination")

    def test_skipped_mandatory_step_blocks_without_starting(self) -> None:
        step = self.base_step()
        step["enabled"] = False
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["steps"][0]["status"], "SKIPPED")
        self.assertIn("MANDATORY_STEP_SKIPPED", [item["code"] for item in report["findings"]])

    def test_optional_skipped_step_is_visible_but_nonblocking(self) -> None:
        step = self.base_step()
        step["mandatory"] = False
        step["enabled"] = False
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["findings"][0]["blocking"])

    def test_malformed_config_is_rejected_before_process_start(self) -> None:
        document = self.config([self.base_step()])
        document["steps"][0]["arguments"] = "--not-an-array"
        self.write_config(document)
        with self.assertRaises(runner.GateError) as caught:
            runner.run_gate(
                project_root=PROJECT_ROOT,
                config_path=self.config_path,
                output_path=self.output_path,
                source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                content_version="m01.3-selftest",
                source_dirty=SOURCE_DIRTY,
            )
        self.assertEqual(caught.exception.code, "CONFIG_SCHEMA_INVALID")
        self.assertFalse(self.output_path.exists())

    def test_path_guards_reject_traversal_ads_and_unc(self) -> None:
        cases = [
            ("../escape", "PATH_TRAVERSAL"),
            ("temp/report.json:evil", "ADS_PATH_REJECTED"),
            (r"\\server\share\report.json", "UNC_PATH_REJECTED"),
            (r"C:relative\report.json", "DRIVE_RELATIVE_PATH_REJECTED"),
            (r"\??\C:\temp\report.json", "WINDOWS_DEVICE_PATH_REJECTED"),
            (r"\Device\HarddiskVolume1\report.json", "WINDOWS_DEVICE_PATH_REJECTED"),
        ]
        for value, code in cases:
            with self.subTest(value=value), self.assertRaises(runner.GateError) as caught:
                runner.resolve_project_path(PROJECT_ROOT, value, "test.path")
            self.assertEqual(caught.exception.code, code)

    def test_symlink_escape_is_rejected_after_resolution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m01_3_outside_") as raw_outside:
            link = self.directory / "outside-link"
            try:
                link.symlink_to(Path(raw_outside), target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlink creation is unavailable: {exc}")
            with self.assertRaises(runner.GateError) as caught:
                runner.resolve_project_path(
                    PROJECT_ROOT,
                    f"{self.relative_directory}/outside-link/report.json",
                    "test.symlink",
                )
            self.assertEqual(caught.exception.code, "PATH_OUTSIDE_PROJECT")

    @unittest.skipIf(os.name == "nt", "POSIX execute-bit guard")
    def test_posix_non_executable_file_is_rejected(self) -> None:
        candidate = self.directory / "not-executable"
        candidate.write_text("fixture\n", encoding="utf-8")
        candidate.chmod(0o644)
        with self.assertRaises(runner.GateError) as caught:
            runner._resolve_executable(PROJECT_ROOT, candidate.relative_to(PROJECT_ROOT).as_posix())
        self.assertEqual(caught.exception.code, "EXECUTABLE_NOT_EXECUTABLE")

    def test_config_schema_rejects_unsafe_paths_and_accepts_dot_relative(self) -> None:
        engine = SchemaEngine(SCHEMA_DIRECTORY, QUALITY_GATE_ROOT / "requirements.lock")
        engine.assert_isolated_runtime()
        valid = self.config([self.base_step()])
        valid["artifact_directory"] = "./temp/schema-path-ok"
        engine.validate(runner.CONFIG_SCHEMA, valid)
        for unsafe in ("../escape", "/absolute/path", r"C:\absolute\path", r"\\server\share", "temp/file:stream"):
            mutation = copy.deepcopy(valid)
            mutation["artifact_directory"] = unsafe
            with self.subTest(path=unsafe), self.assertRaises(SchemaValidationError):
                engine.validate(runner.CONFIG_SCHEMA, mutation)

    def test_source_identity_mismatch_blocks_exit_zero(self) -> None:
        self.write_config(self.config([self.base_step()]))
        report = runner.run_gate(
            project_root=PROJECT_ROOT,
            config_path=self.config_path,
            output_path=self.output_path,
            source_commit=SOURCE_COMMIT,
            expected_source_commit="b" * 40,
            content_version="m01.3-selftest",
            source_dirty=SOURCE_DIRTY,
            allow_dirty_source=True,
            run_id="qg.selftest.source-mismatch",
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_COMMIT_MISMATCH", [item["code"] for item in report["findings"]])

    def test_dirty_source_blocks_without_explicit_development_authorization(self) -> None:
        self.write_config(self.config([self.base_step()]))
        with mock.patch.object(runner, "_git_output", side_effect=[SOURCE_COMMIT, " M simulated-source"]):
            report = runner.run_gate(
                project_root=PROJECT_ROOT,
                config_path=self.config_path,
                output_path=self.output_path,
                source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                content_version="m01.3-selftest",
                source_dirty=True,
                run_id="qg.selftest.dirty-source",
            )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["source"]["dirty_authorized"])
        self.assertIn("DIRTY_SOURCE_NOT_AUTHORIZED", [item["code"] for item in report["findings"]])

    def test_output_path_collision_is_rejected_before_process_start(self) -> None:
        native = self.directory / "collision.json"
        step = self.base_step("write-runtime")
        step["id"] = "output_collision"
        step["arguments"].extend(["--output", native.relative_to(PROJECT_ROOT).as_posix()])
        step["evidence"] = {
            "native_report_path": native.relative_to(PROJECT_ROOT).as_posix(),
            "tool_path": FIXTURE_RELATIVE,
            "target": {"platform": "web", "identity": "selftest-web", "profile": "m01.3-selftest"},
            "strict": True,
            "flags": [],
            "applicable": True,
        }
        self.write_config(self.config([step]))
        with self.assertRaises(runner.GateError) as caught:
            runner.run_gate(
                project_root=PROJECT_ROOT,
                config_path=self.config_path,
                output_path=native,
                source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                content_version="m01.3-selftest",
                source_dirty=SOURCE_DIRTY,
                allow_dirty_source=True,
            )
        self.assertEqual(caught.exception.code, "OUTPUT_PATH_COLLISION")
        self.assertFalse(native.exists())

    def test_source_change_during_run_blocks_report(self) -> None:
        with mock.patch.object(runner, "_git_output", side_effect=["c" * 40, ""]):
            report = self.run_config(self.config([self.base_step()]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["source"]["stable_during_run"])
        self.assertIn("SOURCE_CHANGED_DURING_RUN", [item["code"] for item in report["findings"]])

    def test_explicit_source_commit_cannot_override_git_head(self) -> None:
        with mock.patch.object(runner, "_git_output", return_value=SOURCE_COMMIT):
            with self.assertRaises(runner.GateError) as caught:
                runner._resolve_source_identity(PROJECT_ROOT, "d" * 40, None)
        self.assertEqual(caught.exception.code, "SOURCE_DECLARATION_MISMATCH")

    def test_protected_config_change_during_run_blocks_report(self) -> None:
        step = self.base_step("write-text")
        step["arguments"].extend(["--output", self.config_path.relative_to(PROJECT_ROOT).as_posix()])
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("PROTECTED_INPUT_CHANGED_DURING_RUN", [item["code"] for item in report["findings"]])

    def test_fresh_native_report_is_adapted_and_schema_validated(self) -> None:
        native = self.directory / "runtime.json"
        step = self.base_step("write-runtime")
        step["id"] = "evidence_pass"
        step["arguments"].extend(["--output", native.relative_to(PROJECT_ROOT).as_posix()])
        step["evidence"] = {
            "native_report_path": native.relative_to(PROJECT_ROOT).as_posix(),
            "tool_path": FIXTURE_RELATIVE,
            "target": {"platform": "web", "identity": "selftest-web", "profile": "m01.3-selftest"},
            "strict": True,
            "flags": [],
            "applicable": True,
        }
        report = self.run_config(self.config([step]))
        envelope = report["steps"][0]["evidence_envelope"]
        self.assertEqual(report["status"], "PASS")
        self.assertIsNotNone(envelope)
        self.assertEqual(envelope["status"], "PASS")
        self.assertEqual(envelope["source_report"]["schema_name"], "mtr.web_runtime_probe.legacy")

    def test_unchanged_native_report_is_stale_and_blocks(self) -> None:
        native = self.directory / "runtime.json"
        native.write_text('{"runtimeReady": true}\n', encoding="utf-8")
        step = self.base_step("pass")
        step["id"] = "stale_evidence"
        step["evidence"] = {
            "native_report_path": native.relative_to(PROJECT_ROOT).as_posix(),
            "tool_path": FIXTURE_RELATIVE,
            "target": {"platform": "web", "identity": "selftest-web", "profile": "m01.3-selftest"},
            "strict": True,
            "flags": [],
            "applicable": True,
        }
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        envelope = report["steps"][0]["evidence_envelope"]
        self.assertIsNotNone(envelope)
        self.assertEqual(envelope["status"], "BLOCKED")
        self.assertIn("STALE_EVIDENCE", [item["code"] for item in report["findings"]])

    def test_declared_artifact_must_be_regenerated(self) -> None:
        artifact = self.directory / "preexisting.txt"
        artifact.write_text("old\n", encoding="utf-8")
        step = self.base_step()
        step["artifact_paths"] = [artifact.relative_to(PROJECT_ROOT).as_posix()]
        report = self.run_config(self.config([step]))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("DECLARED_ARTIFACT_STALE", [item["code"] for item in report["findings"]])

    def test_same_config_has_same_semantic_projection(self) -> None:
        document = self.config([self.base_step()])
        first = self.run_config(document, self.directory / "first.json")
        second = self.run_config(document, self.directory / "second.json")
        self.assertEqual(runner.semantic_projection(first), runner.semantic_projection(second))

    def test_report_write_is_atomic_and_leaves_no_temp_tail(self) -> None:
        self.output_path.write_text('{"old": true}\n', encoding="utf-8")
        report = self.run_config(self.config([self.base_step()]))
        self.assertEqual(json.loads(self.output_path.read_text(encoding="utf-8"))["run_id"], report["run_id"])
        self.assertEqual(list(self.output_path.parent.glob(f".{self.output_path.name}.*.tmp")), [])

    def test_report_schema_rejects_false_green_mutation(self) -> None:
        report = self.run_config(self.config([self.base_step()]))
        engine = SchemaEngine(SCHEMA_DIRECTORY, QUALITY_GATE_ROOT / "requirements.lock")
        engine.assert_isolated_runtime()
        mutations = []
        invalid_status = copy.deepcopy(report)
        invalid_status["status"] = "GREEN"
        mutations.append(invalid_status)
        source_mismatch_pass = copy.deepcopy(report)
        source_mismatch_pass["source"]["matches_expected"] = False
        mutations.append(source_mismatch_pass)
        dirty_unauthorized_pass = copy.deepcopy(report)
        dirty_unauthorized_pass["source"]["dirty"] = True
        dirty_unauthorized_pass["source"]["dirty_authorized"] = False
        mutations.append(dirty_unauthorized_pass)
        unstable_source_pass = copy.deepcopy(report)
        unstable_source_pass["source"]["stable_during_run"] = False
        mutations.append(unstable_source_pass)
        mandatory_skip_pass = copy.deepcopy(report)
        mandatory_skip_pass["steps"][0]["status"] = "SKIPPED"
        mandatory_skip_pass["steps"][0]["enabled"] = False
        mandatory_skip_pass["steps"][0]["exit_code"] = None
        mutations.append(mandatory_skip_pass)
        invalid_step_status = copy.deepcopy(report)
        invalid_step_status["steps"][0]["status"] = "GREEN"
        mutations.append(invalid_step_status)
        for mutation in mutations:
            with self.subTest(status=mutation["status"], source=mutation["source"]["matches_expected"]), self.assertRaises(SchemaValidationError):
                engine.validate(runner.REPORT_SCHEMA, mutation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
