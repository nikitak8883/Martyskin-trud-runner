from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


PROJECT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("reviewed_sources", PROJECT / "tools/asset_generation/reviewed_runtime_sources.py")
assert SPEC and SPEC.loader
SOURCES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCES)


class ReviewedSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = json.loads((PROJECT / SOURCES.CONFIG).read_text(encoding="utf-8"))
        self.targets = []
        self.entries = []
        for record in self.config["entries"]:
            for key in ("source", "meta_source"):
                target = self.root / record[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PROJECT / record[key], target)
            generated = record["provenance"]["generated_source"]
            shutil.copyfile(PROJECT / generated, self.root / generated)
            target = self.root / f"assets/resources/{record['runtime_resource_key']}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"old-runtime")
            target.with_suffix(".png.meta").write_bytes(b"old-meta")
            self.targets.append(target)
            self.entries.append({"runtimeResourceKey": record["runtime_resource_key"],
                                 "sourceFile": "original-sheet.png", "sourceBounds": [1, 2, 3, 4]})
        self.target = self.targets[0]
        self.write_config()

    def write_config(self) -> None:
        path = self.root / SOURCES.CONFIG
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.config), encoding="utf-8")

    def test_repository_reviewed_asset_passes(self) -> None:
        manifest = json.loads((PROJECT / SOURCES.MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(SOURCES.apply_sources(PROJECT, manifest["entries"])["status"], "PASS")

    def test_preflight_checks_pins_without_requiring_runtime_or_writing(self) -> None:
        self.target.unlink()
        self.assertEqual(SOURCES.preflight_sources(self.root)["status"], "PASS")
        self.assertFalse(self.target.exists())

    def test_pipeline_checks_pins_before_legacy_mutation(self) -> None:
        source = (PROJECT / "tools/mtr_last_iteration_asset_pipeline.py").read_text(encoding="utf-8")
        start = source.index("def process_all(")
        self.assertLess(source.index("preflight_sources(project_root)", start), source.index("shutil.rmtree(output_root)", start))

    def test_apply_is_idempotent_and_preserves_identity_and_lineage(self) -> None:
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        initial = (self.target.read_bytes(), self.target.with_suffix(".png.meta").read_bytes(), copy.deepcopy(self.entries))
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.assertEqual(initial, (self.target.read_bytes(), self.target.with_suffix(".png.meta").read_bytes(), self.entries))
        self.assertEqual(json.loads(initial[1])["uuid"], self.config["entries"][0]["uuid"])
        self.assertEqual(self.entries[0]["sourceFile"], "original-sheet.png")
        self.assertEqual(self.entries[0]["sourceBounds"], [1, 2, 3, 4])
        self.assertEqual(SOURCES.apply_sources(self.root, self.entries)["status"], "PASS")

    def test_bad_hash_does_not_mutate(self) -> None:
        self.config["entries"][0]["source_sha256"] = "0" * 64
        self.write_config()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.assertEqual(self.target.read_bytes(), b"old-runtime")
        self.assertNotIn("reviewedSourceOverride", self.entries[0])

    def test_invalid_later_record_prevents_partial_apply(self) -> None:
        second = copy.deepcopy(self.config["entries"][0])
        second["runtime_resource_key"] += "_missing"
        self.config["entries"].append(second)
        self.write_config()
        with self.assertRaisesRegex(ValueError, "exactly one manifest"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.assertTrue(all(target.read_bytes() == b"old-runtime" for target in self.targets))
        self.assertTrue(all(target.with_suffix(".png.meta").read_bytes() == b"old-meta" for target in self.targets))
        self.assertTrue(all("reviewedSourceOverride" not in entry for entry in self.entries))

    def test_source_traversal_rejected(self) -> None:
        self.config["entries"][0]["source"] = "../../escape.png"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "escapes"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)

    def test_runtime_traversal_rejected(self) -> None:
        self.config["entries"][0]["runtime_resource_key"] = "objectives/themed/last_iteration/../../escape"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "escapes"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)

    def test_opaque_center_rejected_even_with_updated_source_hash(self) -> None:
        record = self.config["entries"][0]
        source = self.root / record["source"]
        with Image.open(source) as image:
            image.putpixel((120, 112), (255, 255, 255, 255))
            image.save(source)
        record["source_sha256"] = SOURCES.digest(source)
        self.write_config()
        with self.assertRaisesRegex(ValueError, "Opaque pixels"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)

    def test_runtime_hash_and_manifest_drift_rejected(self) -> None:
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.target.write_bytes(b"matte-regression")
        with self.assertRaisesRegex(ValueError, "Runtime source"):
            SOURCES.apply_sources(self.root, self.entries)
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.entries[0]["reviewedSourceOverride"] = {}
        with self.assertRaisesRegex(ValueError, "Manifest provenance"):
            SOURCES.apply_sources(self.root, self.entries)

    def test_uuid_drift_rejected(self) -> None:
        self.config["entries"][0]["uuid"] = "00000000-0000-4000-8000-000000000001"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "metadata contract"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)

    def test_normalization_is_repeatable(self) -> None:
        spec = importlib.util.spec_from_file_location("normalize_source", PROJECT / "tools/asset_generation/normalize_reviewed_sprite.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = self.root / "normalized.png"
        for record in self.config["entries"]:
            with self.subTest(key=record["runtime_resource_key"]):
                frame = record["provenance"].get("source_box")
                module.normalize(self.root / record["provenance"]["generated_source"], output,
                                 tuple(record["dimensions"]), tuple(record["alpha_bbox"]),
                                 source_box=tuple(frame) if frame is not None else None)
                self.assertEqual(SOURCES.digest(output), record["source_sha256"])

    def test_each_asset_opaque_gap_rejected_before_any_write(self) -> None:
        for record in self.config["entries"]:
            with self.subTest(key=record["runtime_resource_key"]):
                source = self.root / record["source"]
                original = source.read_bytes()
                old_hash = record["source_sha256"]
                x0, y0, _, _ = record["transparent_boxes"][0]
                with Image.open(source) as image:
                    image.putpixel((x0, y0), (255, 255, 255, 255))
                    image.save(source)
                record["source_sha256"] = SOURCES.digest(source)
                self.write_config()
                with self.assertRaisesRegex(ValueError, "Opaque pixels"):
                    SOURCES.apply_sources(self.root, self.entries, apply=True)
                self.assertTrue(all(target.read_bytes() == b"old-runtime" for target in self.targets))
                self.assertTrue(all("reviewedSourceOverride" not in entry for entry in self.entries))
                source.write_bytes(original)
                record["source_sha256"] = old_hash
        self.write_config()

    def test_low_alpha_outliers_cannot_fake_visible_silhouette(self) -> None:
        record = next(record for record in self.config["entries"] if "source_box" in record["provenance"])
        source = self.root / record["source"]
        image = Image.new("RGBA", tuple(record["dimensions"]), (0, 0, 0, 0))
        x0, y0, x1, y1 = record["alpha_bbox"]
        image.putpixel((x0, y0), (80, 50, 20, 1))
        image.putpixel((x1-1, y1-1), (80, 50, 20, 1))
        image.putpixel(((x0+x1)//2, (y0+y1)//2), (80, 50, 20, 255))
        image.save(source)
        record["source_sha256"] = SOURCES.digest(source)
        self.write_config()
        with self.assertRaisesRegex(ValueError, "Visible silhouette"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.assertTrue(all(target.read_bytes() == b"old-runtime" for target in self.targets))

    def test_reviewed_frame_never_clips_visible_pixels_or_writes_on_error(self) -> None:
        spec = importlib.util.spec_from_file_location("normalize_source", PROJECT / "tools/asset_generation/normalize_reviewed_sprite.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        record = next(record for record in self.config["entries"] if "source_box" in record["provenance"])
        source = self.root / record["provenance"]["generated_source"]
        output = self.root / "no-partial-normalization.png"
        output.write_bytes(b"previous-output")
        frames = [(0, 0, 10, 10), (-1, 0, 20, 20)]
        for frame in frames:
            with self.subTest(frame=frame), self.assertRaisesRegex(ValueError, "visible artwork|source bounds"):
                module.normalize(source, output, tuple(record["dimensions"]), tuple(record["alpha_bbox"]), source_box=frame)
            self.assertEqual(output.read_bytes(), b"previous-output")

    def test_all_runtime_metadata_and_manifest_lineage_preserved(self) -> None:
        original = copy.deepcopy(self.entries)
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        for record, entry, previous, target in zip(self.config["entries"], self.entries, original, self.targets):
            self.assertEqual(target.with_suffix(".png.meta").read_bytes(), (PROJECT / record["meta_source"]).read_bytes())
            self.assertEqual(entry["sourceFile"], previous["sourceFile"])
            self.assertEqual(entry["sourceBounds"], previous["sourceBounds"])
        self.assertEqual(SOURCES.apply_sources(self.root, self.entries)["reviewed_source_count"], len(self.config["entries"]))

    def test_every_reviewed_gap_blocks_repinning_opaque_backing(self) -> None:
        for record in self.config["entries"]:
            source = self.root / record["source"]
            original = source.read_bytes()
            original_hash = record["source_sha256"]
            for box in record["transparent_boxes"]:
                with self.subTest(key=record["runtime_resource_key"], box=box):
                    with Image.open(source) as image:
                        image.putpixel((box[0], box[1]), (255, 255, 255, 255))
                        image.save(source)
                    record["source_sha256"] = SOURCES.digest(source)
                    self.write_config()
                    with self.assertRaisesRegex(ValueError, "Opaque pixels"):
                        SOURCES.apply_sources(self.root, self.entries, apply=True)
                    self.assertTrue(all(target.read_bytes() == b"old-runtime" for target in self.targets))
                    self.assertTrue(all(target.with_suffix(".png.meta").read_bytes() == b"old-meta" for target in self.targets))
                    source.write_bytes(original)
            record["source_sha256"] = original_hash
        self.write_config()

    def test_raw_generation_pin_rejects_before_any_runtime_write(self) -> None:
        record = self.config["entries"][-1]
        generated = self.root / record["provenance"]["generated_source"]
        generated.write_bytes(generated.read_bytes() + b"drift")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            SOURCES.apply_sources(self.root, self.entries, apply=True)
        self.assertTrue(all(target.read_bytes() == b"old-runtime" for target in self.targets))
        self.assertTrue(all(target.with_suffix(".png.meta").read_bytes() == b"old-meta" for target in self.targets))
        self.assertTrue(all("reviewedSourceOverride" not in entry for entry in self.entries))

    def test_pinned_metadata_git_roundtrip_ignores_host_autocrlf(self) -> None:
        SOURCES.apply_sources(self.root, self.entries, apply=True)
        shutil.copyfile(PROJECT / ".gitattributes", self.root / ".gitattributes")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        def git(*args: str) -> bytes:
            return subprocess.run(["git", *args], cwd=self.root, check=True,
                                  capture_output=True, creationflags=flags).stdout

        git("init", "--quiet")
        relatives = [relative for record in self.config["entries"]
                     for relative in (record["meta_source"], f"assets/resources/{record['runtime_resource_key']}.png.meta")]
        pins = {relative: record["meta_sha256"] for record in self.config["entries"]
                for relative in (record["meta_source"], f"assets/resources/{record['runtime_resource_key']}.png.meta")}
        for policy in ("false", "true"):
            for relative in relatives:
                blob = git("-c", f"core.autocrlf={policy}", "hash-object", "-w",
                           f"--path={relative}", relative).decode().strip()
                payload = git("-c", f"core.autocrlf={policy}", "cat-file", "--filters",
                              f"--path={relative}", blob)
                self.assertEqual(hashlib.sha256(payload).hexdigest().upper(), pins[relative])


if __name__ == "__main__":
    unittest.main()
