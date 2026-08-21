from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = PROJECT_ROOT / "tools" / "validate-assets.py"
FIXTURE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "global_modernization"
    / "v3"
    / "library"
    / "fixtures"
    / "assets"
    / "pre_import_negative_cases.json"
)
SPEC = importlib.util.spec_from_file_location("validate_assets_m04_b", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


ROOT_UUID = "11111111-1111-4111-8111-111111111111"
TEXTURE_UUID = f"{ROOT_UUID}@6c48a"
SPRITE_UUID = f"{ROOT_UUID}@f9941"


def image_meta(stem: str = "good_asset") -> dict[str, Any]:
    return {
        "ver": "1.0.27",
        "importer": "image",
        "imported": True,
        "uuid": ROOT_UUID,
        "files": [".json", ".png"],
        "subMetas": {
            "6c48a": {
                "importer": "texture",
                "uuid": TEXTURE_UUID,
                "displayName": stem,
                "id": "6c48a",
                "name": "texture",
                "userData": {
                    "imageUuidOrDatabaseUri": ROOT_UUID,
                    "isUuid": True,
                },
            },
            "f9941": {
                "importer": "sprite-frame",
                "uuid": SPRITE_UUID,
                "displayName": stem,
                "id": "f9941",
                "name": "spriteFrame",
                "userData": {
                    "trimThreshold": 1,
                    "rotated": False,
                    "offsetX": 0,
                    "offsetY": 0,
                    "trimX": 0,
                    "trimY": 0,
                    "width": 64,
                    "height": 64,
                    "rawWidth": 64,
                    "rawHeight": 64,
                    "packable": True,
                    "pivotX": 0.5,
                    "pivotY": 0.5,
                    "imageUuidOrDatabaseUri": TEXTURE_UUID,
                    "atlasUuid": "",
                    "trimType": "none",
                },
            },
        },
        "userData": {
            "type": "sprite-frame",
            "fixAlphaTransparencyArtifacts": False,
            "hasAlpha": True,
            "redirect": TEXTURE_UUID,
        },
    }


def atlas_manifest() -> dict[str, Any]:
    provenance = ["docs/provenance.json"]
    return {
        "ownership_scopes": [
            {
                "scope_id": "fixture_scope",
                "path": "icons",
                "match": "prefix",
                "bundle_id": "resources",
                "provenance": list(provenance),
            }
        ],
        "atlas_groups": [
            {
                "atlas_id": "fixture_atlas",
                "source_selectors": [
                    {"path": "icons", "match": "prefix", "extensions": [".png"]}
                ],
                "bundle_id": "resources",
                "packing": {"mode": "static_atlas_candidate"},
                "provenance": list(provenance),
            }
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_fixture(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    resources = root / "assets" / "resources"
    image_path = resources / "icons" / "good_asset.png"
    image_path.parent.mkdir(parents=True)
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(12, 52):
        for y in range(10, 54):
            image.putpixel((x, y), (40, 180, 90, 255))
    image.save(image_path)
    write_json(Path(str(image_path) + ".meta"), image_meta())
    write_json(
        root / "assets" / "resources.meta",
        {
            "uuid": "22222222-2222-4222-8222-222222222222",
            "userData": {"isBundle": True, "bundleName": "resources", "priority": 8},
        },
    )
    write_json(root / "docs" / "provenance.json", {"source": "fixture"})
    return resources, image_path, atlas_manifest()


def run_fixture(root: Path, atlas: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    resources = root / "assets" / "resources"
    pngs, _ = VALIDATOR.scan_pngs(resources, 2048)
    return VALIDATOR.validate_image_governance(
        root,
        resources,
        atlas,
        pngs,
        root / "assets" / "quarantine",
    )


class M04BPreImportValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.negative_cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]

    def test_repository_pre_import_contract_passes(self) -> None:
        args = argparse.Namespace(
            project_root=str(PROJECT_ROOT),
            resources_root="assets/resources",
            atlas_manifest="assets/resources/config/atlas_manifest.json",
            player_skins_manifest="docs/skins_integration/manifests/player_skins_manifest.json",
            ui_skin_manifest="assets/resources/config/ui_skin_manifest.json",
            objective_runtime_usage="assets/resources/config/current_objective_runtime_usage.json",
            last_iteration_asset_manifest="assets/resources/config/last_iteration_asset_manifest.generated.json",
            quarantine_root="assets/quarantine",
            max_edge=2048,
            report="",
            fail_on_white_matte=True,
            skip_reference_checks=False,
            reference_missing_sample_limit=50,
        )
        report = VALIDATOR.build_report(args)
        self.assertEqual(report["schema"], "mtr.asset_validation.v1")
        self.assertEqual(report["summary"]["blockerCount"], 0, report["blockers"][:10])
        self.assertEqual(report["preImport"]["summary"]["imageCount"], 1558)
        self.assertEqual(report["preImport"]["summary"]["blockerCount"], 0)
        self.assertEqual(report["preImport"]["trimTypes"], {"auto": 585, "none": 973})
        self.assertEqual(report["preImport"]["pivots"], {"0.5,0.5": 1558})

    def test_minimal_valid_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_valid_", dir=PROJECT_ROOT / "temp") as raw:
            root = Path(raw)
            _, _, atlas = make_fixture(root)
            report, blockers = run_fixture(root, atlas)
            self.assertEqual(report["status"], "PASS", blockers)
            self.assertEqual(blockers, [])

    def test_negative_fixtures_fail_with_expected_type(self) -> None:
        for case in self.negative_cases:
            with self.subTest(case=case["id"]), tempfile.TemporaryDirectory(
                prefix=f"m04b_{case['id']}_", dir=PROJECT_ROOT / "temp"
            ) as raw:
                root = Path(raw)
                resources, image_path, atlas = make_fixture(root)
                meta_path = Path(str(image_path) + ".meta")
                operation = case["operation"]
                if operation == "rename_image":
                    renamed = image_path.with_name(case["value"])
                    image_path.rename(renamed)
                    meta_path.rename(Path(str(renamed) + ".meta"))
                elif operation == "set_sprite_field":
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    meta["subMetas"]["f9941"]["userData"][case["field"]] = case["value"]
                    write_json(meta_path, meta)
                elif operation == "set_root_field":
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    meta["userData"][case["field"]] = case["value"]
                    write_json(meta_path, meta)
                elif operation == "clear_group_provenance":
                    atlas["atlas_groups"][0]["provenance"] = []
                elif operation == "move_to_runtime_quarantine":
                    target = resources / "quarantine" / image_path.name
                    target.parent.mkdir(parents=True)
                    image_path.rename(target)
                    meta_path.rename(Path(str(target) + ".meta"))
                elif operation == "set_bundle_name":
                    bundle_path = root / "assets" / "resources.meta"
                    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
                    bundle["userData"]["bundleName"] = case["value"]
                    write_json(bundle_path, bundle)
                elif operation == "add_dangling_scene_uuid":
                    write_json(root / "assets" / "fixture.scene", {"asset": {"__uuid__": case["value"]}})
                else:
                    self.fail(f"unsupported fixture operation: {operation}")

                _, blockers = run_fixture(root, copy.deepcopy(atlas))
                finding_types = {item["type"] for item in blockers}
                self.assertIn(case["expected_type"], finding_types, blockers)

    def test_fully_transparent_frame_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_null_", dir=PROJECT_ROOT / "temp") as raw:
            root = Path(raw)
            _, image_path, atlas = make_fixture(root)
            Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(image_path)
            _, blockers = run_fixture(root, atlas)
            self.assertIn("image_null_frame", {item["type"] for item in blockers})

    def test_malformed_manifest_collections_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_manifest_", dir=PROJECT_ROOT / "temp") as raw:
            root = Path(raw)
            _, _, atlas = make_fixture(root)
            atlas["atlas_groups"] = "not-a-list"
            atlas["ownership_scopes"] = []
            _, blockers = run_fixture(root, atlas)
            finding_types = {item["type"] for item in blockers}
            self.assertIn("atlas_groups_invalid", finding_types)
            self.assertIn("ownership_scopes_invalid", finding_types)

    def test_resource_reference_cannot_escape_resources_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_reference_", dir=PROJECT_ROOT / "temp") as raw:
            root = Path(raw)
            resources = root / "assets" / "resources"
            resources.mkdir(parents=True)
            outside = root / "outside.png"
            Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(outside)
            exists, normalized, resolved = VALIDATOR.resource_key_exists(resources, "../../outside")
            self.assertFalse(exists)
            self.assertEqual(normalized, "../../outside")
            self.assertIsNone(resolved)

    def test_containment_rejects_outside_and_symlink_when_available(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_containment_", dir=PROJECT_ROOT / "temp") as raw:
            root = Path(raw)
            outside = root / "outside"
            project = root / "project"
            outside.mkdir()
            project.mkdir()
            self.assertIsNone(VALIDATOR.contained_path(project, outside / "report.json"))
            outside_asset = outside / "escaped.png"
            Image.new("RGBA", (2, 2), (255, 255, 255, 255)).save(outside_asset)
            link = project / "escaped.png"
            try:
                link.symlink_to(outside_asset)
            except OSError:
                # Windows without Developer Mode still exercises the same
                # resolved-path guard through the direct outside candidate.
                return
            self.assertIsNone(VALIDATOR.contained_path(project, link))


if __name__ == "__main__":
    unittest.main()
