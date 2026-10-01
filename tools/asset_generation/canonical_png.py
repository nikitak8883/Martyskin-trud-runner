"""Tool-only PNG serialization with the original reviewed byte identity.

Pillow owns pixels and PNG filters; a locked compressor owns IDAT bytes.
No system codec fallback, metadata stripping, or runtime asset mutation.
"""
from __future__ import annotations

import io
from importlib import metadata
import struct
import zlib

import PIL
from zlib_ng import zlib_ng as compressor


PILLOW_VERSION = "12.3.0"
PACKAGE_VERSION = "1.0.0"
CODEC_VERSION = "2.2.5"
SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PIXELS = 16 * 1024 * 1024
MAX_PNG_BYTES = 128 * 1024 * 1024
IDAT_CHUNK_BYTES = 65536


def require_toolchain() -> None:
    if PIL.__version__ != PILLOW_VERSION:
        raise RuntimeError(f"Canonical PNG requires Pillow {PILLOW_VERSION}")
    if (metadata.version("zlib-ng") != PACKAGE_VERSION
            or compressor.ZLIBNG_VERSION != CODEC_VERSION
            or compressor.ZLIBNG_RUNTIME_VERSION != CODEC_VERSION):
        raise RuntimeError(f"Canonical PNG requires zlib-ng {PACKAGE_VERSION} / codec {CODEC_VERSION}")


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def canonicalize_png(data: bytes) -> bytes:
    """Recompress verified, non-interlaced 8-bit RGB(A) PNG filter rows.

    Reject unsupported chunks instead of silently dropping metadata. Limits
    bound decompression; CRC, stream termination, row count/filter and IHDR are
    checked before constructing output. Compression parameters reproduce all
    29 original M04-B sheets and the reviewed lifebuoy without refreshing pins.
    """
    require_toolchain()
    if not isinstance(data, bytes) or len(data) > MAX_PNG_BYTES or not data.startswith(SIGNATURE):
        raise ValueError("Invalid canonical PNG signature or size")
    offset = len(SIGNATURE)
    ihdr = None
    idat = bytearray()
    ended = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", data, offset)[0]
        end = offset + size + 12
        if end > len(data):
            raise ValueError("Truncated PNG payload")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("PNG chunk CRC mismatch")
        if kind == b"IHDR" and ihdr is None and offset == len(SIGNATURE) and size == 13:
            ihdr = payload
        elif kind == b"IDAT" and ihdr is not None and not ended:
            idat.extend(payload)
        elif kind == b"IEND" and ihdr is not None and idat and size == 0 and end == len(data):
            ended = True
        else:
            raise ValueError("Unsupported PNG chunk or order")
        offset = end
    if ihdr is None or not idat or not ended:
        raise ValueError("Incomplete PNG structure")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr)
    if (width == 0 or height == 0 or width * height > MAX_PIXELS or depth != 8
            or color not in (2, 6) or compression != 0 or filtering != 0 or interlace != 0):
        raise ValueError("Unsupported PNG dimensions, mode, or encoding")
    stride = width * (3 if color == 2 else 4) + 1
    expected = stride * height
    decoder = zlib.decompressobj()
    try:
        rows = decoder.decompress(idat, expected + 1)
    except zlib.error as exc:
        raise ValueError("Invalid PNG compressed rows") from exc
    if (len(rows) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
            or any(rows[y * stride] > 4 for y in range(height))):
        raise ValueError("Invalid PNG row count, filters, or stream termination")
    encoder = compressor.compressobj(9, compressor.DEFLATED, 15, 9, compressor.Z_FILTERED)
    compressed = encoder.compress(rows) + encoder.flush()
    return (SIGNATURE + _chunk(b"IHDR", ihdr)
            + b"".join(_chunk(b"IDAT", compressed[start:start + IDAT_CHUNK_BYTES])
                       for start in range(0, len(compressed), IDAT_CHUNK_BYTES))
            + _chunk(b"IEND", b""))


def encode_png(image, *, optimize: bool = False) -> bytes:
    require_toolchain()
    if image.mode not in ("RGB", "RGBA"):
        raise ValueError("Canonical PNG accepts only RGB or RGBA images")
    if image.width * image.height > MAX_PIXELS:
        raise ValueError("Canonical PNG image exceeds pixel limit")
    intermediate = io.BytesIO()
    image.save(intermediate, format="PNG", compress_level=9, optimize=optimize)
    return canonicalize_png(intermediate.getvalue())
