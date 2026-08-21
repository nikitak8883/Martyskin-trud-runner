from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = PROJECT_ROOT / "tools" / "codex" / "render_m04_b_contact_sheets.py"
INDEX_PATH = PROJECT_ROOT / "docs" / "global_modernization" / "v3" / "M04" / "contact_sheet_index.json"
SCHEMA_PATH = PROJECT_ROOT / "docs" / "global_modernization" / "v3" / "M04" / "schemas" / "contact_sheet_index.schema.json"
SPEC = importlib.util.spec_from_file_location("render_m04_b_contact_sheets", GENERATOR_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


EXPECTED_CATEGORY_COUNTS = {
    "hud": 11,
    "menu": 240,
    "runner": 84,
    "bonuses": 900,
    "obstacles": 290,
    "backgrounds": 31,
    "vfx": 2,
}


class M04BContactSheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_and_required_category_order(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.validate(self.index, self.schema, cls=jsonschema.Draft202012Validator)
        self.assertEqual(
            [category["id"] for category in self.index["categories"]],
            GENERATOR.CATEGORY_ORDER,
        )

    def test_index_covers_every_runtime_image_exactly_once(self) -> None:
        assets = [asset for category in self.index["categories"] for asset in category["assets"]]
        paths = [asset["path"] for asset in assets]
        runtime_paths = sorted(
            path.relative_to(PROJECT_ROOT / "assets" / "resources").as_posix()
            for path in (PROJECT_ROOT / "assets" / "resources").rglob("*")
            if path.is_file() and path.suffix.lower() in GENERATOR.IMAGE_EXTENSIONS
        )
        self.assertEqual(len(paths), 1558)
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(sorted(paths), runtime_paths)
        self.assertEqual(self.index["summary"]["assetCount"], len(paths))

    def test_category_and_sheet_counts_are_self_consistent(self) -> None:
        actual = {category["id"]: category["assetCount"] for category in self.index["categories"]}
        self.assertEqual(actual, EXPECTED_CATEGORY_COUNTS)
        sheet_count = 0
        for category in self.index["categories"]:
            self.assertEqual(category["assetCount"], len(category["assets"]))
            self.assertEqual(category["sheetCount"], len(category["sheets"]))
            self.assertEqual(category["assetCount"], sum(sheet["assetCount"] for sheet in category["sheets"]))
            sheet_ids = {sheet["id"] for sheet in category["sheets"]}
            self.assertEqual({asset["sheetId"] for asset in category["assets"]}, sheet_ids)
            for sheet_id in sheet_ids:
                cells = [asset["cellIndex"] for asset in category["assets"] if asset["sheetId"] == sheet_id]
                self.assertEqual(sorted(cells), list(range(len(cells))))
            sheet_count += category["sheetCount"]
        self.assertEqual(sheet_count, self.index["summary"]["sheetCount"])
        self.assertEqual(sheet_count, 29)

    def test_manifest_links_and_source_hashes_resolve(self) -> None:
        atlas_path = PROJECT_ROOT / self.index["source"]["atlasManifest"]
        self.assertEqual(GENERATOR.sha256_file(atlas_path), self.index["source"]["atlasManifestSha256"])
        for category in self.index["categories"]:
            for provenance in category["provenance"]:
                self.assertTrue((PROJECT_ROOT / provenance).is_file(), provenance)
            for asset in category["assets"]:
                source = PROJECT_ROOT / "assets" / "resources" / asset["path"]
                self.assertTrue(source.is_file(), source)
                self.assertEqual(GENERATOR.sha256_file(source), asset["sha256"])

    def test_classifier_examples_cover_all_required_families(self) -> None:
        examples = {
            "objectives/ui/ui_label_plate_01.png": "hud",
            "ui/shared/buttons/button_primary_idle.png": "menu",
            "characters/player_skins/brigadir/base/idle.png": "runner",
            "characters/player_skins/brigadir/bonus/helmet/idle.png": "bonuses",
            "objectives/themed/last_iteration/jungle/hazards/example.png": "obstacles",
            "backgrounds/level01.jpg": "backgrounds",
            "objectives/collectibles/collectible_banana_glow_new.png": "vfx",
            "backgrounds/level16.jpeg": "backgrounds",
        }
        for path, expected in examples.items():
            with self.subTest(path=path):
                self.assertEqual(GENERATOR.classify(path), expected)

    def test_page_render_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_sheet_", dir=PROJECT_ROOT / "temp") as raw:
            resources = Path(raw)
            source = resources / "icons" / "fixture.png"
            source.parent.mkdir(parents=True)
            Image.new("RGBA", (40, 30), (30, 200, 90, 180)).save(source)
            asset = {
                "path": "icons/fixture.png",
                "width": 40,
                "height": 30,
                "atlasId": "fixture_atlas",
            }
            first = GENERATOR.render_page("hud", 1, [asset], resources)
            second = GENERATOR.render_page("hud", 1, [asset], resources)
            self.assertEqual(first, second)
            self.assertEqual(GENERATOR.sha256_bytes(first), GENERATOR.sha256_bytes(second))

    def test_stale_cleanup_removes_only_generator_owned_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m04b_cleanup_", dir=PROJECT_ROOT / "temp") as raw:
            output = Path(raw)
            expected = output / "m04b_hud-01.png"
            stale = output / "m04b_hud-99.png"
            stale_tmp = output / ".m04b_menu-01.png.tmp"
            unrelated = output / "manual-notes.txt"
            for path in (expected, stale, stale_tmp, unrelated):
                path.write_bytes(b"fixture")
            removed = GENERATOR.remove_stale_artifacts(output, {expected.name})
            self.assertEqual(removed, [stale_tmp.name, stale.name])
            self.assertTrue(expected.is_file())
            self.assertTrue(unrelated.is_file())
            self.assertFalse(stale.exists())
            self.assertFalse(stale_tmp.exists())


if __name__ == "__main__":
    unittest.main()
