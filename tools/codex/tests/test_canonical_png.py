"""Byte-preserving codec guard and negative PNG container controls."""
from __future__ import annotations

import hashlib
import io
import struct
import unittest
from unittest import mock
import zlib
from pathlib import Path

from PIL import Image
from tools.asset_generation import canonical_png as PNG


PROJECT = Path(__file__).resolve().parents[3]
GOLDEN = PROJECT / "tools/asset_generation/source_assets/logistics/lifebuoy-runtime.png"
GOLDEN_SHA = "0A430E298AF44E9615DB233AE1847FBDAFAAB73792AD30AE190D435D09504933"


def container(ihdr: bytes, rows: bytes, *, extra_stream: bytes = b"") -> bytes:
    return (PNG.SIGNATURE + PNG._chunk(b"IHDR", ihdr)
            + PNG._chunk(b"IDAT", zlib.compress(rows, 9) + extra_stream) + PNG._chunk(b"IEND", b""))


IHDR = struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)
ROWS = b"\x00\x20\x80\xff\x30\x90\xaa"


class CanonicalPngTests(unittest.TestCase):
    def test_toolchain_has_no_fallback(self) -> None:
        PNG.require_toolchain()
        self.assertEqual(PNG.PACKAGE_VERSION, "1.0.0")
        self.assertEqual(PNG.CODEC_VERSION, "2.2.5")
        for target, value in (("PIL.__version__", "12.2.0"),
                              ("compressor.ZLIBNG_VERSION", "2.3.3"),
                              ("compressor.ZLIBNG_RUNTIME_VERSION", "2.3.3")):
            parent, attribute = target.split(".")
            with self.subTest(target=target), mock.patch.object(getattr(PNG, parent), attribute, value):
                with self.assertRaisesRegex(RuntimeError, "requires"):
                    PNG.canonicalize_png(container(IHDR, ROWS))
        with mock.patch.object(PNG.metadata, "version", return_value="1.0.1"):
            with self.assertRaisesRegex(RuntimeError, "requires"):
                PNG.canonicalize_png(container(IHDR, ROWS))

    def test_original_reviewed_png_is_preserved_byte_for_byte(self) -> None:
        golden = GOLDEN.read_bytes()
        self.assertEqual(hashlib.sha256(golden).hexdigest().upper(), GOLDEN_SHA)
        self.assertEqual(PNG.canonicalize_png(golden), golden)

    def test_system_zlib_input_reproduces_the_original_bytes(self) -> None:
        golden = GOLDEN.read_bytes()
        ihdr = golden[16:29]
        offset = 8
        compressed = bytearray()
        while offset < len(golden):
            size = struct.unpack_from(">I", golden, offset)[0]
            if golden[offset + 4:offset + 8] == b"IDAT":
                compressed.extend(golden[offset + 8:offset + 8 + size])
            offset += size + 12
        rows = zlib.decompress(compressed)
        plain_zlib = container(ihdr, rows)
        # This fixture genuinely uses the system codec, not a copied golden.
        self.assertNotEqual(plain_zlib, golden)
        self.assertEqual(PNG.canonicalize_png(plain_zlib), golden)

    def test_rgb_rgba_pixels_and_repeat_bytes_are_preserved(self) -> None:
        for mode, color in (("RGB", (20, 90, 220)), ("RGBA", (20, 90, 220, 100))):
            with self.subTest(mode=mode):
                image = Image.new(mode, (9, 7), color)
                payload = PNG.encode_png(image)
                self.assertEqual(payload, PNG.encode_png(image))
                self.assertEqual(payload, PNG.canonicalize_png(payload))
                with Image.open(io.BytesIO(payload)) as decoded:
                    self.assertEqual(decoded.mode, mode)
                    self.assertEqual(decoded.size, image.size)
                    self.assertEqual(decoded.tobytes(), image.tobytes())

    def test_unsupported_image_mode_is_not_silently_converted(self) -> None:
        with self.assertRaisesRegex(ValueError, "only RGB or RGBA"):
            PNG.encode_png(Image.new("L", (2, 2)))

    def test_image_pixel_limit_precedes_serialization(self) -> None:
        with mock.patch.object(PNG, "MAX_PIXELS", 3):
            with self.assertRaisesRegex(ValueError, "pixel limit"):
                PNG.encode_png(Image.new("RGB", (2, 2)))

    def test_signature_size_crc_and_truncation_are_rejected(self) -> None:
        good = container(IHDR, ROWS)
        malformed = [b"wrong", PNG.SIGNATURE, good[:-1], good[:11], good[:25],
                     good[:29] + b"\0\0\0\0" + good[33:]]
        for payload in malformed:
            with self.subTest(size=len(payload)):
                with self.assertRaises(ValueError):
                    PNG.canonicalize_png(payload)
        with mock.patch.object(PNG, "MAX_PNG_BYTES", len(good) - 1):
            with self.assertRaisesRegex(ValueError, "size"):
                PNG.canonicalize_png(good)

    def test_chunk_order_ancillary_metadata_and_trailing_bytes_fail_closed(self) -> None:
        good = container(IHDR, ROWS)
        for payload in [
            good + b"tail",
            good[:8] + PNG._chunk(b"tEXt", b"name\0value") + good[8:],
            good[:33] + PNG._chunk(b"IHDR", IHDR) + good[33:],
            PNG.SIGNATURE + PNG._chunk(b"IDAT", zlib.compress(ROWS)) + good[8:33] + PNG._chunk(b"IEND", b""),
            PNG.SIGNATURE + PNG._chunk(b"IHDR", IHDR) + PNG._chunk(b"IEND", b""),
        ]:
            with self.subTest(payload=payload[:40].hex()):
                with self.assertRaises(ValueError):
                    PNG.canonicalize_png(payload)

    def test_dimensions_depth_palette_and_interlace_fail_closed(self) -> None:
        for values in [(0, 1, 8, 2, 0, 0, 0), (2, 0, 8, 2, 0, 0, 0),
                       (2, 1, 16, 2, 0, 0, 0), (2, 1, 8, 3, 0, 0, 0),
                       (2, 1, 8, 2, 1, 0, 0), (2, 1, 8, 2, 0, 1, 0),
                       (2, 1, 8, 2, 0, 0, 1), (PNG.MAX_PIXELS, 2, 8, 2, 0, 0, 0)]:
            with self.subTest(ihdr=values):
                with self.assertRaisesRegex(ValueError, "dimensions"):
                    PNG.canonicalize_png(container(struct.pack(">IIBBBBB", *values), ROWS))

    def test_decompression_row_count_filters_and_termination_fail_closed(self) -> None:
        for rows, tail in [(ROWS[:-1], b""), (ROWS + b"\0", b""),
                           (b"\x05" + ROWS[1:], b""), (ROWS, zlib.compress(b"second"))]:
            with self.subTest(rows=rows.hex(), tail=tail.hex()):
                with self.assertRaisesRegex(ValueError, "row count"):
                    PNG.canonicalize_png(container(IHDR, rows, extra_stream=tail))
        for compressed in (b"invalid", zlib.compress(ROWS)[:-1]):
            with self.subTest(compressed=compressed.hex()):
                bad = (PNG.SIGNATURE + PNG._chunk(b"IHDR", IHDR)
                       + PNG._chunk(b"IDAT", compressed) + PNG._chunk(b"IEND", b""))
                with self.assertRaises(ValueError):
                    PNG.canonicalize_png(bad)


if __name__ == "__main__":
    unittest.main()
