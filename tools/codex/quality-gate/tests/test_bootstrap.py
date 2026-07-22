#!/usr/bin/env python3
"""M01.3 isolated bootstrap unit tests."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


QUALITY_GATE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(QUALITY_GATE_ROOT))

import bootstrap  # noqa: E402


class QualityGateBootstrapTests(unittest.TestCase):
    def test_base_python_falls_back_when_interpreter_does_not_expose_base(self) -> None:
        with mock.patch.object(bootstrap.sys, "_base_executable", None, create=True):
            self.assertEqual(bootstrap._base_python(), Path(sys.executable).resolve())

    def test_lock_contains_only_exact_versions(self) -> None:
        packages = bootstrap._locked_packages()
        self.assertEqual(
            packages,
            {
                "attrs": "26.1.0",
                "jsonschema": "4.26.0",
                "jsonschema-specifications": "2025.9.1",
                "pillow": "12.3.0",
                "referencing": "0.37.0",
                "rpds-py": "2026.6.3",
            },
        )

    def test_atomic_json_replaces_document_without_temp_tail(self) -> None:
        temp_root = PROJECT_ROOT / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="m01_3_bootstrap_atomic_", dir=temp_root) as raw_directory:
            directory = Path(raw_directory)
            output = directory / "marker.json"
            output.write_text('{"old": true}\n', encoding="utf-8")
            bootstrap._atomic_json(output, {"status": "PASS", "value": 2})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"status": "PASS", "value": 2})
            self.assertEqual(list(directory.glob(".marker.json.*.tmp")), [])

    @unittest.skipUnless(os.name == "nt", "Windows UNC guard")
    def test_cache_override_rejects_unc_path(self) -> None:
        with mock.patch.dict(os.environ, {"MTR_QUALITY_GATE_CACHE": r"\\server\share\quality-gate"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "local path"):
                bootstrap._cache_root()

    def test_waiter_times_out_without_deleting_foreign_lock(self) -> None:
        temp_root = PROJECT_ROOT / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="m01_3_bootstrap_lock_", dir=temp_root) as raw_directory:
            cache = Path(raw_directory)
            lock_sha = bootstrap._sha256(bootstrap.LOCK_PATH)
            environment = cache / f"venv-py{sys.version_info.major}{sys.version_info.minor}-{lock_sha[:12].lower()}"
            lock_directory = cache / f".{environment.name}.bootstrap.lock"
            lock_directory.mkdir()
            with (
                mock.patch.object(bootstrap, "_cache_root", return_value=cache),
                mock.patch.object(bootstrap, "_probe", return_value=False),
                mock.patch.object(
                    bootstrap.time,
                    "monotonic",
                    side_effect=[0.0, bootstrap.BOOTSTRAP_LOCK_WAIT_SECONDS + 1.0],
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "Timed out waiting for bootstrap lock"):
                    bootstrap.ensure_environment()
            self.assertTrue(lock_directory.is_dir(), "a waiter must not delete another process's lock")

    def test_active_invalid_environment_is_never_rebuilt_in_place(self) -> None:
        temp_root = PROJECT_ROOT / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="m01_3_bootstrap_self_guard_", dir=temp_root) as raw_directory:
            cache = Path(raw_directory)
            with (
                mock.patch.object(bootstrap, "_cache_root", return_value=cache),
                mock.patch.object(bootstrap, "_probe", return_value=False),
                mock.patch.object(bootstrap, "_current_interpreter_inside", return_value=True),
                mock.patch.object(bootstrap, "_install") as install,
            ):
                with self.assertRaisesRegex(RuntimeError, "ACTIVE_VALIDATOR_ENVIRONMENT_INVALID"):
                    bootstrap.ensure_environment()
            install.assert_not_called()

    def test_profile_entrypoint_routes_to_allowlisted_profile_runner(self) -> None:
        fake_environment = PROJECT_ROOT / "temp/fake-profile-bootstrap"
        completed = mock.Mock(returncode=0)
        with (
            mock.patch.object(bootstrap, "ensure_environment", return_value=(fake_environment, "A" * 64)),
            mock.patch.object(bootstrap.subprocess, "run", return_value=completed) as run,
        ):
            result = bootstrap.main(["--entrypoint", "profile", "--", "--scope", "scope.json"])
        self.assertEqual(result, 0)
        command = run.call_args.args[0]
        runtime_environment = run.call_args.kwargs["env"]
        self.assertEqual(Path(command[1]), bootstrap.PROFILE_RUNNER_PATH)
        self.assertEqual(command[2:], ["--scope", "scope.json"])
        self.assertEqual(runtime_environment["PATH"].split(os.pathsep)[0], str(Path(command[0]).parent))
        self.assertEqual(runtime_environment["VIRTUAL_ENV"], str(fake_environment))
        self.assertEqual(runtime_environment["MTR_QUALITY_GATE_ISOLATED"], "1")
        self.assertNotIn("PYTHONHOME", runtime_environment)


if __name__ == "__main__":
    unittest.main(verbosity=2)
