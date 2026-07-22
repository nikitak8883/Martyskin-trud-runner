from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "validate-content-identity.py"
SPEC = importlib.util.spec_from_file_location("mtr_validate_content_identity", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ContentIdentityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.identity = MODULE.load_json(PROJECT_ROOT / MODULE.IDENTITY_RELATIVE)
        cls.manifest = MODULE.load_json(PROJECT_ROOT / MODULE.M00_MANIFEST_RELATIVE)

    def test_repository_identity_document_is_valid(self) -> None:
        self.assertEqual(MODULE.validate_identity_document(self.identity, self.manifest), [])

    def test_freeze_aggregate_drift_is_rejected(self) -> None:
        identity = copy.deepcopy(self.identity)
        identity["freeze_provenance"]["aggregate_sha256"] = "0" * 64
        errors = MODULE.validate_identity_document(identity, self.manifest)
        self.assertTrue(any("aggregate_sha256" in error and "mismatch" in error for error in errors))

    def test_invalid_source_commit_is_rejected(self) -> None:
        identity = copy.deepcopy(self.identity)
        identity["source"]["baseline_commit"] = "not-a-commit"
        errors = MODULE.validate_identity_document(identity, self.manifest)
        self.assertTrue(any("baseline_commit" in error for error in errors))
        self.assertTrue(any("logical_content_version" in error for error in errors))

    def test_shared_and_platform_report_fields_are_fixed(self) -> None:
        identity = copy.deepcopy(self.identity)
        identity["platform_contract"]["artifact_manifest_scope"] = "shared"
        errors = MODULE.validate_identity_document(identity, self.manifest)
        self.assertTrue(any("artifact_manifest_scope" in error for error in errors))

    def test_report_writer_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "temp") as directory:
            root = Path(directory)
            outside = root.parent / f"{root.name}.outside.json"
            with self.assertRaisesRegex(ValueError, "escapes project root"):
                MODULE.write_report_atomic(root, outside, "{}\n")
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
