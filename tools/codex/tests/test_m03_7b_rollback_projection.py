from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("m03_7b_rollback_proof", ROOT / "tools/codex/m03_7b_rollback_proof.py")
assert SPEC and SPEC.loader
PROOF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROOF)
MANIFEST = ROOT / "docs/global_modernization/v3/M03/M03_7B_CLEANUP_MANIFEST.json"
ROLLBACK = json.loads(MANIFEST.read_text(encoding="utf-8"))["rollback"]
PROJECTION = json.loads((ROOT / "docs/global_modernization/v3/M03/M03_7B_SOURCE_ROLLBACK_PROJECTION.json").read_text(encoding="utf-8"))
MANIFEST_SHA = hashlib.sha256(MANIFEST.read_bytes().replace(b"\r\n", b"\n")).hexdigest().upper()


def query(*, legacy: str | None = None, faults: dict[tuple[str, ...], str | Exception] | None = None):
    def execute(*args: str) -> str:
        if faults and args in faults:
            value = faults[args]
            if isinstance(value, Exception):
                raise value
            return value
        if args == ("cat-file", "-t", ROLLBACK["anchor_commit"]):
            if legacy is None:
                raise RuntimeError("original checkpoint not in source-only history")
            return legacy
        source = PROJECTION["source_anchor"]
        if args == ("cat-file", "-t", source):
            return "commit"
        if args == ("rev-parse", f"{source}^{{tree}}"):
            return PROJECTION["source_tree"]
        if args == ("merge-base", "--is-ancestor", source, "HEAD"):
            return ""
        for relative, blob in ROLLBACK["pre_change_blobs"].items():
            if args in (("rev-parse", f"{source}:{relative}"),
                        ("rev-parse", f"{ROLLBACK['anchor_commit']}:{ROLLBACK['project_prefix']}{relative}")):
                return blob
        raise RuntimeError(f"unexpected Git query: {args}")
    return execute


class RollbackProjectionTests(unittest.TestCase):
    def verify(self, *, projection=None, source_only=True, git=None, rollback=None, digest=None):
        return PROOF.verify_rollback_proof(
            rollback or ROLLBACK, projection=projection if projection is not None else PROJECTION,
            manifest_sha256_utf8_lf=digest or MANIFEST_SHA, source_only=source_only,
            git_query=git or query(),
        )

    def test_original_anchor_remains_primary(self):
        result = self.verify(source_only=False, git=query(legacy="commit"))
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["mode"], "original-monorepo")
        self.assertEqual(result["anchor"], ROLLBACK["anchor_commit"])
        self.assertEqual(result["verified_blobs"], 10)

    def test_exact_source_tree_and_all_original_blobs(self):
        result = self.verify()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["mode"], "verified-source-projection")
        self.assertEqual(result["anchor"], PROJECTION["source_anchor"])
        self.assertEqual(result["verified_blobs"], 10)

    def test_missing_monorepo_anchor_never_uses_source_fallback(self):
        self.assertIn("rollback_original_anchor_unavailable", self.verify(source_only=False)["errors"])

    def test_noncommit_original_anchor_never_uses_fallback(self):
        self.assertIn("rollback_anchor_not_commit", self.verify(git=query(legacy="blob"))["errors"])

    def test_missing_projection_fails_closed(self):
        result = PROOF.verify_rollback_proof(ROLLBACK, projection=None, manifest_sha256_utf8_lf=MANIFEST_SHA,
                                           source_only=True, git_query=query())
        self.assertIn("rollback_projection_missing", result["errors"])

    def test_divergent_source_checkpoint_rejected(self):
        fault = {("merge-base", "--is-ancestor", PROJECTION["source_anchor"], "HEAD"): RuntimeError("not an ancestor")}
        result = self.verify(git=query(faults=fault))
        self.assertTrue(result["errors"])
        self.assertEqual(result["verified_blobs"], 0)

    def test_observed_source_tree_drift_rejected(self):
        fault = {("rev-parse", f"{PROJECTION['source_anchor']}^{{tree}}"): "f" * 40}
        self.assertIn("rollback_projection_tree_mismatch", self.verify(git=query(faults=fault))["errors"])

    def test_one_wrong_or_missing_blob_cannot_pass(self):
        relative = "assets/scripts/GameRoot.ts"
        operation = ("rev-parse", f"{PROJECTION['source_anchor']}:{relative}")
        for value in ("f" * 40, RuntimeError("blob missing")):
            with self.subTest(value=str(value)):
                result = self.verify(git=query(faults={operation: value}))
                self.assertTrue(result["errors"])
                self.assertLess(result["verified_blobs"], 10)

    def test_traversal_blob_path_rejected_before_git(self):
        rollback = copy.deepcopy(ROLLBACK)
        rollback["pre_change_blobs"]["../escape"] = rollback["pre_change_blobs"].pop("assets/scripts/GameRoot.ts")
        self.assertIn("rollback_blob_set_invalid", self.verify(rollback=rollback)["errors"])


def negative_projection_case(field, value):
    def test(self):
        projection = copy.deepcopy(PROJECTION)
        projection[field] = value
        result = self.verify(projection=projection)
        self.assertTrue(result["errors"], field)
        self.assertEqual(result["verified_blobs"], 0)
    return test


for _field, _value in (
    ("schema_version", 2), ("contract", "unrelated"), ("legacy_anchor", "f" * 40),
    ("legacy_project_prefix", "wrong/"), ("cleanup_manifest_sha256_utf8_lf", "f" * 64),
    ("source_anchor", "invalid"), ("source_tree", "invalid"), ("legacy_project_tree", "f" * 40),
    ("pre_change_blobs", {}),
):
    setattr(RollbackProjectionTests, f"test_reject_projection_{_field}", negative_projection_case(_field, _value))

if __name__ == "__main__":
    unittest.main()
