from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "retention.py"
SPEC = importlib.util.spec_from_file_location("mtr_evidence_retention", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
retention = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = retention
SPEC.loader.exec_module(retention)


class EvidenceRetentionTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        self.evidence = self.project / "docs" / "qa" / "evidence"
        self.output_dir = (
            self.project / "docs" / "global_modernization" / "v3" / "M01"
        )
        self.policy_dir = self.project / "tools"
        self.index_dir = self.project / "indexes"
        self.accepted_dir = self.project / "accepted"
        for directory in (
            self.evidence,
            self.output_dir,
            self.policy_dir,
            self.index_dir,
            self.accepted_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        self.files = {
            "20260101_old/raw.log": (b"old raw\n", "2026-01-01T01:00:00+00:00"),
            "20260101_old/release_summary.json": (
                b'{"status":"accepted"}\n',
                "2026-01-01T02:00:00+00:00",
            ),
            "20260101_old/rollback_backup.zip": (
                b"backup",
                "2026-01-01T02:30:00+00:00",
            ),
            "20260101_old/replay.cjs": (
                b"module.exports = {};\n",
                "2026-01-01T02:45:00+00:00",
            ),
            "20260102_mid/screen.png": (b"mid png", "2026-01-02T01:00:00+00:00"),
            "20260103_new/screen.png": (b"new png", "2026-01-03T01:00:00+00:00"),
            "legacy.bin": (b"legacy", "2025-12-31T01:00:00+00:00"),
        }
        for relative, (payload, modified_at) in self.files.items():
            target = self.evidence.joinpath(*relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            timestamp = datetime.fromisoformat(modified_at).timestamp()
            os.utime(target, (timestamp, timestamp))

        (self.accepted_dir / "checkpoint.json").write_text(
            '{"status":"PASS"}\n', encoding="utf-8"
        )
        self.policy = self._default_policy()
        self._write_policy()
        self._write_index()
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(
            ["git", "config", "user.email", "m01-5-tests@example.invalid"],
            cwd=self.project,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "M01.5 Tests"],
            cwd=self.project,
            check=True,
        )
        subprocess.run(
            ["git", "config", "core.autocrlf", "false"],
            cwd=self.project,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.project, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "fixture"], cwd=self.project, check=True
        )
        self.source_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest().upper()

    def _default_policy(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "contract": "mtr.evidence_retention_policy",
            "policyId": "test.m01.5",
            "evidenceRoot": "docs/qa/evidence",
            "indexPath": "indexes/evidence.json",
            "outputPath": "docs/global_modernization/v3/M01/evidence_retention_dry_run.json",
            "recentGroupCount": 2,
            "recentGroupPattern": "^[0-9]{8}_.+$",
            "protectedPathGlobs": ["*/final_gate_static/*.json"],
            "protectedNameGlobs": [
                "*.md",
                "*manifest*.json",
                "*summary*.json",
                "*report*.json",
                "*backup*",
                "*.cjs",
            ],
            "retainedNameGlobs": ["*failure_corpus*"],
            "rotatableRawSuffixes": [".log", ".png", ".bin", ".json"],
            "acceptedRunLinks": [
                {
                    "id": "checkpoint",
                    "kind": "accepted_test",
                    "path": "accepted/checkpoint.json",
                }
            ],
            "contentIdentity": {
                "status": "UNAVAILABLE_UNTIL_TEST_BASELINE",
                "version": None,
            },
        }

    def _write_policy(self) -> None:
        (self.policy_dir / "retention.json").write_text(
            json.dumps(self.policy, indent=2) + "\n", encoding="utf-8"
        )

    def _index_value(self, *, root: Path | None = None) -> dict[str, object]:
        entries = []
        for relative, (payload, modified_at) in sorted(self.files.items()):
            entries.append(
                {
                    "path": relative,
                    "bytes": len(payload),
                    "modifiedAt": modified_at,
                    "sha256": self._digest(payload),
                }
            )
        return {
            "schemaVersion": 1,
            "generatedAt": "2026-01-04T00:00:00+00:00",
            "root": str(root or self.evidence),
            "sourceHead": "1" * 40,
            "fileCount": len(entries),
            "totalBytes": sum(entry["bytes"] for entry in entries),
            "files": entries,
        }

    def _write_index(self, value: dict[str, object] | None = None) -> None:
        (self.index_dir / "evidence.json").write_text(
            json.dumps(value or self._index_value(), indent=2) + "\n",
            encoding="utf-8",
        )

    def _build(
        self,
        output: str = "docs/global_modernization/v3/M01/evidence_retention_dry_run.json",
    ):
        return retention.build_dry_run(
            project_root=self.project,
            policy_relative="tools/retention.json",
            output_relative=output,
            generated_at="2026-01-05T00:00:00Z",
            source_commit=self.source_commit,
        )

    def test_complete_classification_is_deterministic_and_delete_incapable(self) -> None:
        first, first_output = self._build()
        second, second_output = self._build()
        self.assertEqual(first, second)
        self.assertEqual(first_output, second_output)
        self.assertEqual(first["status"], "PASS_DRY_RUN_ONLY")
        self.assertFalse(first["deletionPerformed"])
        self.assertFalse(first["evidenceDeleteCapabilityPresent"])
        self.assertTrue(first["temporaryOutputCleanupPresent"])
        self.assertEqual(first["retention"]["counts"], {
            "protected": 3,
            "retained_recent": 2,
            "rotatable": 2,
        })
        self.assertEqual(
            first["retention"]["recentGroups"],
            ["20260103_new", "20260102_mid"],
        )
        self.assertEqual(len(first["entries"]), len(self.files))
        retention._revalidate_before_write(self.project, first, first_output)
        retention._atomic_write_json(first_output, first)
        self.assertTrue(first_output.is_file())
        for relative in self.files:
            self.assertTrue(self.evidence.joinpath(*relative.split("/")).is_file())

    def test_index_path_traversal_fails_closed(self) -> None:
        value = self._index_value()
        value["files"][0]["path"] = "../escape.log"
        self._write_index(value)
        with self.assertRaisesRegex(retention.RetentionError, "unsafe path segment"):
            self._build()

    def test_windows_ads_or_absolute_index_path_fails_closed(self) -> None:
        for unsafe in (
            "safe.txt:stream",
            "C:/outside.txt",
            "/outside.txt",
            "CON/report.txt",
            "bad?.txt",
        ):
            with self.subTest(unsafe=unsafe):
                value = self._index_value()
                value["files"][0]["path"] = unsafe
                self._write_index(value)
                with self.assertRaises(retention.RetentionError):
                    self._build()

    def test_duplicate_case_insensitive_index_path_fails_closed(self) -> None:
        value = self._index_value()
        duplicate = dict(value["files"][0])
        duplicate["path"] = duplicate["path"].upper()
        value["files"].append(duplicate)
        value["fileCount"] += 1
        value["totalBytes"] += duplicate["bytes"]
        self._write_index(value)
        with self.assertRaisesRegex(retention.RetentionError, "duplicate case-insensitive"):
            self._build()

    def test_declared_root_mismatch_fails_closed(self) -> None:
        other = self.project / "other-evidence"
        other.mkdir()
        self._write_index(self._index_value(root=other))
        with self.assertRaisesRegex(retention.RetentionError, "root does not match"):
            self._build()

    def test_missing_or_size_drift_fails_closed(self) -> None:
        target = self.evidence / "legacy.bin"
        target.unlink()
        with self.assertRaises(retention.RetentionError):
            self._build()
        target.write_bytes(b"legacy changed")
        with self.assertRaisesRegex(retention.RetentionError, "size drift"):
            self._build()

    def test_unindexed_file_fails_closed(self) -> None:
        (self.evidence / "unindexed.log").write_text("not indexed\n", encoding="utf-8")
        with self.assertRaisesRegex(retention.RetentionError, "unindexed file"):
            self._build()

    def test_output_is_fixed_by_reviewed_policy(self) -> None:
        with self.assertRaisesRegex(retention.RetentionError, "exactly match"):
            self._build("accepted/checkpoint.json")
        self.policy["outputPath"] = "docs/qa/evidence/evidence_retention_dry_run.json"
        self._write_policy()
        with self.assertRaisesRegex(retention.RetentionError, "canonical M01.5 report"):
            self._build("docs/qa/evidence/evidence_retention_dry_run.json")

    def test_invalid_accepted_run_link_fails_closed(self) -> None:
        self.policy["acceptedRunLinks"][0]["path"] = "../outside.json"
        self._write_policy()
        with self.assertRaises(retention.RetentionError):
            self._build()

    def test_symlink_escape_fails_closed_when_supported(self) -> None:
        outside = self.project / "outside.log"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.evidence / "escape.log"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(retention.RetentionError, "symbolic link"):
            self._build()

    def test_index_totals_must_match_entries(self) -> None:
        value = self._index_value()
        value["totalBytes"] += 1
        self._write_index(value)
        with self.assertRaisesRegex(retention.RetentionError, "totalBytes"):
            self._build()

    def test_same_size_evidence_drift_is_detected_by_mtime(self) -> None:
        target = self.evidence / "legacy.bin"
        target.write_bytes(b"LEGACY")
        self.assertEqual(target.stat().st_size, len(b"legacy"))
        with self.assertRaisesRegex(retention.RetentionError, "modification-time drift"):
            self._build()

    def test_protected_input_change_before_write_fails_closed(self) -> None:
        result, output = self._build()
        accepted = self.accepted_dir / "checkpoint.json"
        accepted.write_text('{"status":"FAIL"}\n', encoding="utf-8")
        with self.assertRaisesRegex(retention.RetentionError, "changed before atomic"):
            retention._revalidate_before_write(self.project, result, output)


if __name__ == "__main__":
    unittest.main()
