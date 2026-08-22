from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = PROJECT_ROOT / "tools" / "codex" / "validate_m04_a_asset_contract.py"
FIXTURE_PATH = PROJECT_ROOT / "docs" / "global_modernization" / "v3" / "library" / "fixtures" / "assets" / "atlas_manifest_negative_cases.json"
SPEC = importlib.util.spec_from_file_location("validate_m04_a_asset_contract", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def get_path(value: Any, path: list[Any]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def parent_and_key(value: Any, path: list[Any]) -> tuple[Any, Any]:
    return get_path(value, path[:-1]), path[-1]


def apply_case(manifest: dict[str, Any], case: dict[str, Any]) -> None:
    operation = case["operation"]
    path = case["path"]
    if operation == "replace":
        parent, key = parent_and_key(manifest, path)
        parent[key] = case["value"]
    elif operation == "delete":
        parent, key = parent_and_key(manifest, path)
        del parent[key]
    elif operation == "delete_index":
        get_path(manifest, path).pop(case["index"])
    elif operation == "append_copy":
        target = get_path(manifest, path)
        target.append(copy.deepcopy(target[case["source_index"]]))
    elif operation == "append_selector_copy":
        target = get_path(manifest, path)
        source = manifest["atlas_groups"][case["source_group"]]["source_selectors"][case["source_selector"]]
        target.append(copy.deepcopy(source))
    elif operation == "copy_value":
        parent, key = parent_and_key(manifest, path)
        parent[key] = copy.deepcopy(get_path(manifest, case["source_path"]))
    else:
        raise AssertionError(f"unknown fixture operation: {operation}")


class M04AAssetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = VALIDATOR.load_json(PROJECT_ROOT / VALIDATOR.MANIFEST_RELATIVE)
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]

    def test_repository_contract_passes(self) -> None:
        report = VALIDATOR.validate_manifest(PROJECT_ROOT, check_git=False)
        self.assertEqual(report["status"], "PASS", report["findings"])
        self.assertEqual(report["counts"]["source_files"], 1638)
        self.assertEqual(report["counts"]["image_files"], 1558)
        self.assertEqual(report["counts"]["auto_atlas_files"], 3)
        self.assertEqual(report["counts"]["measured_static_atlases"], 3)
        measured = [
            group["atlas_id"]
            for group in self.manifest["atlas_groups"]
            if group["packing"]["implementation_status"] == "measured_static_atlas"
        ]
        self.assertEqual(measured, ["runner_collectibles", "objective_npc", "achievement_ui"])

    def test_measured_atlas_uuid_drift_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        group = next(group for group in manifest["atlas_groups"] if group["atlas_id"] == "objective_npc")
        group["packing"]["descriptor_uuid"] = "00000000-0000-4000-8000-000000000099"
        report = VALIDATOR.validate_manifest(PROJECT_ROOT, manifest, check_git=False)
        self.assertIn("AUTO_ATLAS_META_MISMATCH", {finding["code"] for finding in report["findings"]})

    def test_measured_atlas_malformed_evidence_records_structured_finding(self) -> None:
        group = next(group for group in self.manifest["atlas_groups"] if group["atlas_id"] == "objective_npc")
        real_load_json = VALIDATOR.load_json
        evidence_cases = (
            (group["packing"]["measurement_contract"], "ATLAS_MEASUREMENT_CONTRACT_INVALID_JSON"),
            (group["packing"]["acceptance_evidence"], "ATLAS_ACCEPTANCE_EVIDENCE_INVALID_JSON"),
        )
        for relative_path, expected_code in evidence_cases:
            target = (PROJECT_ROOT / relative_path).resolve()

            def load_json_with_failure(path: Path, *, _target: Path = target) -> Any:
                if path.resolve() == _target:
                    raise json.JSONDecodeError("fixture", "{", 1)
                return real_load_json(path)

            with self.subTest(path=relative_path), mock.patch.object(
                VALIDATOR, "load_json", side_effect=load_json_with_failure
            ):
                report = VALIDATOR.validate_manifest(PROJECT_ROOT, copy.deepcopy(self.manifest), check_git=False)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn(expected_code, {finding["code"] for finding in report["findings"]})

    def test_acceptance_count_must_match_measurement_contract(self) -> None:
        group = next(group for group in self.manifest["atlas_groups"] if group["atlas_id"] == "objective_npc")
        acceptance_path = (PROJECT_ROOT / group["packing"]["acceptance_evidence"]).resolve()
        real_load_json = VALIDATOR.load_json

        def load_json_with_drift(path: Path) -> Any:
            value = real_load_json(path)
            if path.resolve() == acceptance_path:
                value = copy.deepcopy(value)
                value["acceptance"]["checks_total"] -= 1
                value["acceptance"]["checks_passed"] -= 1
            return value

        with mock.patch.object(VALIDATOR, "load_json", side_effect=load_json_with_drift):
            report = VALIDATOR.validate_manifest(PROJECT_ROOT, copy.deepcopy(self.manifest), check_git=False)
        self.assertIn("ATLAS_ACCEPTANCE_EVIDENCE_MISMATCH", {finding["code"] for finding in report["findings"]})

    def test_negative_fixtures_fail_with_expected_code(self) -> None:
        for case in self.fixtures:
            with self.subTest(case=case["id"]):
                manifest = copy.deepcopy(self.manifest)
                apply_case(manifest, case)
                report = VALIDATOR.validate_manifest(PROJECT_ROOT, manifest, check_git=False)
                codes = {finding["code"] for finding in report["findings"]}
                self.assertEqual(report["status"], "FAIL")
                self.assertIn(case["expected_code"], codes)

    def test_inventory_digest_normalizes_text_and_preserves_binary_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04a_digest_", dir=PROJECT_ROOT / "temp") as raw_directory:
            root = Path(raw_directory)
            text_path = root / "a.json"
            binary_path = root / "b.png"
            text_path.write_bytes(b"one\r\ntwo\rthree\n")
            binary_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\r")

            digest, extensions, sizes = VALIDATOR.inventory_digest(
                [binary_path, text_path],
                lambda path: path.relative_to(root).as_posix(),
                {".json"},
            )

            self.assertEqual(VALIDATOR.canonical_bytes(text_path, {".json"}), b"one\ntwo\nthree\n")
            self.assertEqual(VALIDATOR.canonical_bytes(binary_path, {".json"}), binary_path.read_bytes())
            self.assertEqual(digest["count"], 2)
            self.assertEqual(digest["bytes"], len(b"one\ntwo\nthree\n") + len(binary_path.read_bytes()))
            self.assertEqual(extensions[".json"], {"count": 1, "bytes": len(b"one\ntwo\nthree\n")})
            self.assertEqual(sizes["a.json"], len(b"one\ntwo\nthree\n"))

    def test_meta_graph_pairs_governance_json_and_detects_real_orphan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04a_meta_", dir=PROJECT_ROOT / "temp") as raw_directory:
            project_root = Path(raw_directory)
            resources_root = project_root / "assets" / "resources"
            config_root = resources_root / "config"
            config_root.mkdir(parents=True)
            (config_root / "atlas_manifest.json").write_text("{}\n", encoding="utf-8")
            meta_documents = {
                project_root / "assets" / "resources.meta": "00000000-0000-4000-8000-000000000001",
                resources_root / "config.meta": "00000000-0000-4000-8000-000000000002",
                config_root / "atlas_manifest.json.meta": "00000000-0000-4000-8000-000000000003",
            }
            for path, uuid in meta_documents.items():
                path.write_text(json.dumps({"uuid": uuid}) + "\n", encoding="utf-8")

            findings: list[dict[str, Any]] = []
            report = VALIDATOR.validate_meta_graph(project_root, resources_root, findings)
            self.assertEqual(report["missing_pairs"], 0)
            self.assertEqual(report["orphan_meta"], 0)
            self.assertEqual(findings, [])

            (config_root / "orphan.json.meta").write_text(
                json.dumps({"uuid": "00000000-0000-4000-8000-000000000004"}) + "\n",
                encoding="utf-8",
            )
            findings = []
            report = VALIDATOR.validate_meta_graph(project_root, resources_root, findings)
            self.assertEqual(report["orphan_meta"], 1)
            self.assertIn("COCOS_META_ORPHAN", {finding["code"] for finding in findings})

    def test_report_and_provenance_path_resolution_is_project_contained(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04a_path_", dir=PROJECT_ROOT / "temp") as raw_directory:
            project_root = Path(raw_directory)
            contained = VALIDATOR.resolve_project_path(project_root, "evidence/report.json")
            self.assertEqual(contained, (project_root / "evidence" / "report.json").resolve())
            self.assertIsNone(VALIDATOR.resolve_project_path(project_root, "../escape.json"))

    def test_path_resolution_rejects_symlink_escape_when_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04a_symlink_", dir=PROJECT_ROOT / "temp") as raw_directory:
            container = Path(raw_directory)
            project_root = container / "project"
            outside = container / "outside"
            project_root.mkdir()
            outside.mkdir()
            link = project_root / "linked-outside"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                if os.name != "nt":
                    self.skipTest(f"directory symlinks are unavailable: {exc}")
                junction = subprocess.run(
                    ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if junction.returncode != 0:
                    self.skipTest(f"directory links are unavailable: {junction.stdout.strip()}")

            try:
                self.assertIsNone(VALIDATOR.resolve_project_path(project_root, "linked-outside/report.json"))
            finally:
                if link.exists():
                    link.rmdir()

    def test_invalid_schema_records_fail_closed_finding(self) -> None:
        findings: list[dict[str, Any]] = []
        VALIDATOR.validate_schema({}, {"type": "not-a-json-schema-type"}, findings)
        self.assertEqual({finding["code"] for finding in findings}, {"SCHEMA_DEFINITION_INVALID"})

    def test_source_baseline_may_be_ancestor_but_not_divergent(self) -> None:
        checkpoint = copy.deepcopy(self.manifest["source_checkpoint"])
        identity = VALIDATOR.load_json(PROJECT_ROOT / VALIDATOR.CONTENT_IDENTITY_RELATIVE)
        published = checkpoint["published_subtree_commit"]
        parent = checkpoint["parent_checkpoint"]
        tree = checkpoint["project_tree"]
        descendant = "f" * 40

        def fake_git_value(_root: Path, *arguments: str) -> str | None:
            values = {
                ("rev-parse", f"{published}^{{tree}}"): tree,
                ("rev-parse", "--verify", "--quiet", "origin/mtr-source-v3"): descendant,
                ("rev-parse", "--show-toplevel"): str(PROJECT_ROOT),
                ("cat-file", "-t", parent): "commit",
                ("rev-parse", f"{parent}^{{tree}}"): tree,
            }
            return values.get(arguments)

        ancestor_result = VALIDATOR.subprocess.CompletedProcess([], 0, "", "")
        divergent_result = VALIDATOR.subprocess.CompletedProcess([], 1, "", "")
        with mock.patch.object(VALIDATOR, "git_value", side_effect=fake_git_value), mock.patch.object(
            VALIDATOR, "run_git", return_value=ancestor_result
        ):
            findings: list[dict[str, Any]] = []
            report = VALIDATOR.validate_source_checkpoint(PROJECT_ROOT, checkpoint, identity, findings, True)
            self.assertEqual(report["remote_commit"], descendant)
            self.assertEqual(findings, [])

        with mock.patch.object(VALIDATOR, "git_value", side_effect=fake_git_value), mock.patch.object(
            VALIDATOR, "run_git", return_value=divergent_result
        ):
            findings = []
            VALIDATOR.validate_source_checkpoint(PROJECT_ROOT, checkpoint, identity, findings, True)
            self.assertIn("PUBLISHED_BASELINE_NOT_ON_SOURCE_REF", {finding["code"] for finding in findings})


if __name__ == "__main__":
    unittest.main()
