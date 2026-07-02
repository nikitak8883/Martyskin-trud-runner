from __future__ import annotations

import argparse
import json
import math
import struct
import uuid
import zlib
from pathlib import Path

SIZE = 128
SCALE = 3
ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "resources" / "objectives" / "themed" / "last_iteration" / "ui" / "level_select" / "icon"
QA_DIR = ROOT / "docs" / "qa"
NAMESPACE = uuid.UUID("018f8d17-aeca-7a25-b002-5a1e3f6a7b0c")

Color = tuple[int, int, int, int]

THEMES: tuple[tuple[str, Color, Color, Color], ...] = (
    ("crane", (244, 184, 74, 255), (82, 55, 28, 255), (255, 232, 139, 255)),
    ("banana_crates", (246, 204, 68, 255), (90, 63, 31, 255), (127, 91, 42, 255)),
    ("forms", (231, 211, 146, 255), (77, 67, 54, 255), (119, 91, 51, 255)),
    ("jungle", (147, 212, 100, 255), (42, 89, 48, 255), (203, 236, 126, 255)),
    ("farm", (239, 194, 92, 255), (111, 74, 38, 255), (93, 136, 67, 255)),
    ("inspector", (88, 206, 178, 255), (56, 44, 70, 255), (236, 188, 88, 255)),
    ("factory", (229, 142, 72, 255), (80, 58, 44, 255), (191, 111, 65, 255)),
    ("archive", (209, 171, 101, 255), (84, 66, 45, 255), (241, 221, 159, 255)),
    ("reactor", (182, 236, 80, 255), (42, 85, 56, 255), (248, 214, 75, 255)),
    ("corridor", (229, 151, 98, 255), (77, 58, 43, 255), (221, 202, 146, 255)),
    ("night_shift", (113, 173, 235, 255), (29, 37, 67, 255), (240, 220, 143, 255)),
    ("training", (214, 184, 105, 255), (72, 58, 42, 255), (230, 213, 157, 255)),
    ("tower", (224, 181, 91, 255), (92, 77, 59, 255), (235, 211, 135, 255)),
    ("ministry", (224, 161, 82, 255), (92, 64, 44, 255), (214, 196, 145, 255)),
    ("heart", (245, 191, 68, 255), (92, 55, 38, 255), (231, 92, 72, 255)),
)


def rgba(color: tuple[int, int, int] | Color, alpha: int | None = None) -> Color:
    if len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b = color
        a = 255
    return (r, g, b, a if alpha is None else alpha)


def blend_pixel(buf: bytearray, width: int, height: int, x: int, y: int, color: Color) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    sr, sg, sb, sa = color
    if sa <= 0:
        return
    i = (y * width + x) * 4
    dr, dg, db, da = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
    if sa == 255 and da == 0:
        buf[i : i + 4] = bytes((sr, sg, sb, sa))
        return
    s = sa / 255.0
    d = da / 255.0
    out_a = s + d * (1.0 - s)
    if out_a <= 0:
        return
    buf[i] = round((sr * s + dr * d * (1.0 - s)) / out_a)
    buf[i + 1] = round((sg * s + dg * d * (1.0 - s)) / out_a)
    buf[i + 2] = round((sb * s + db * d * (1.0 - s)) / out_a)
    buf[i + 3] = round(out_a * 255)


class Canvas:
    def __init__(self, size: int = SIZE, scale: int = SCALE) -> None:
        self.size = size
        self.scale = scale
        self.width = size * scale
        self.height = size * scale
        self.buf = bytearray(self.width * self.height * 4)

    def px(self, value: float) -> int:
        return round(value * self.scale)

    def circle(self, cx: float, cy: float, radius: float, color: Color) -> None:
        cxp, cyp, rp = self.px(cx), self.px(cy), self.px(radius)
        rr = rp * rp
        for y in range(cyp - rp, cyp + rp + 1):
            for x in range(cxp - rp, cxp + rp + 1):
                if (x - cxp) * (x - cxp) + (y - cyp) * (y - cyp) <= rr:
                    blend_pixel(self.buf, self.width, self.height, x, y, color)

    def ring(self, cx: float, cy: float, radius: float, width: float, color: Color) -> None:
        cxp, cyp, rp, wp = self.px(cx), self.px(cy), self.px(radius), max(1, self.px(width))
        outer = rp * rp
        inner = max(0, rp - wp) * max(0, rp - wp)
        for y in range(cyp - rp, cyp + rp + 1):
            for x in range(cxp - rp, cxp + rp + 1):
                d = (x - cxp) * (x - cxp) + (y - cyp) * (y - cyp)
                if inner <= d <= outer:
                    blend_pixel(self.buf, self.width, self.height, x, y, color)

    def rect(self, x: float, y: float, w: float, h: float, color: Color, radius: float = 0) -> None:
        x0, y0, x1, y1 = self.px(x), self.px(y), self.px(x + w), self.px(y + h)
        r = self.px(radius)
        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                if r > 0:
                    cx = min(max(px, x0 + r), x1 - r)
                    cy = min(max(py, y0 + r), y1 - r)
                    if (px - cx) * (px - cx) + (py - cy) * (py - cy) > r * r:
                        continue
                blend_pixel(self.buf, self.width, self.height, px, py, color)

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float, color: Color) -> None:
        ax, ay, bx, by = self.px(x1), self.px(y1), self.px(x2), self.px(y2)
        half = max(1.0, self.px(width) / 2.0)
        min_x, max_x = math.floor(min(ax, bx) - half - 1), math.ceil(max(ax, bx) + half + 1)
        min_y, max_y = math.floor(min(ay, by) - half - 1), math.ceil(max(ay, by) + half + 1)
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy or 1
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
                cx = ax + t * dx
                cy = ay + t * dy
                if (px - cx) * (px - cx) + (py - cy) * (py - cy) <= half * half:
                    blend_pixel(self.buf, self.width, self.height, px, py, color)
        self.circle(x1, y1, width / 2.0, color)
        self.circle(x2, y2, width / 2.0, color)

    def polyline(self, points: tuple[tuple[float, float], ...], width: float, color: Color) -> None:
        for a, b in zip(points, points[1:]):
            self.line(a[0], a[1], b[0], b[1], width, color)

    def polygon(self, points: tuple[tuple[float, float], ...], color: Color) -> None:
        pts = [(self.px(x), self.px(y)) for x, y in points]
        min_x, max_x = min(x for x, _ in pts), max(x for x, _ in pts)
        min_y, max_y = min(y for _, y in pts), max(y for _, y in pts)
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    xi, yi = pts[i]
                    xj, yj = pts[j]
                    if (yi > py) != (yj > py):
                        x_cross = (xj - xi) * (py - yi) / ((yj - yi) or 1) + xi
                        if px < x_cross:
                            inside = not inside
                    j = i
                if inside:
                    blend_pixel(self.buf, self.width, self.height, px, py, color)

    def star(self, cx: float, cy: float, outer: float, inner: float, color: Color, points: int = 5) -> None:
        pts: list[tuple[float, float]] = []
        for i in range(points * 2):
            radius = outer if i % 2 == 0 else inner
            angle = -math.pi / 2 + i * math.pi / points
            pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        self.polygon(tuple(pts), color)

    def downsample(self) -> bytearray:
        out = bytearray(self.size * self.size * 4)
        s = self.scale
        for y in range(self.size):
            for x in range(self.size):
                sum_a = 0
                sum_r = 0
                sum_g = 0
                sum_b = 0
                for sy in range(s):
                    for sx in range(s):
                        i = ((y * s + sy) * self.width + (x * s + sx)) * 4
                        a = self.buf[i + 3]
                        sum_a += a
                        sum_r += self.buf[i] * a
                        sum_g += self.buf[i + 1] * a
                        sum_b += self.buf[i + 2] * a
                oi = (y * self.size + x) * 4
                if sum_a:
                    out[oi] = round(sum_r / sum_a)
                    out[oi + 1] = round(sum_g / sum_a)
                    out[oi + 2] = round(sum_b / sum_a)
                    out[oi + 3] = round(sum_a / (s * s))
        return out


def draw_backplate(canvas: Canvas, accent: Color, base: Color, detail: Color) -> None:
    canvas.circle(64, 68, 55, (28, 18, 10, 96))
    canvas.circle(64, 63, 54, (42, 25, 12, 238))
    canvas.circle(64, 60, 49, base)
    canvas.ring(64, 60, 53, 4, accent)
    canvas.circle(64, 60, 38, rgba(detail, 34))
    canvas.line(28, 35, 38, 28, 5, rgba(accent, 180))
    canvas.line(100, 91, 111, 84, 5, rgba(accent, 135))
    for x, y in ((37, 34), (91, 34), (38, 88), (90, 88)):
        canvas.circle(x, y, 3.0, rgba((255, 239, 174), 160))


def draw_banana(canvas: Canvas, x: float, y: float, scale: float, accent: Color) -> None:
    pts = ((x - 19 * scale, y + 2 * scale), (x - 7 * scale, y - 9 * scale), (x + 10 * scale, y - 8 * scale), (x + 21 * scale, y + 6 * scale))
    canvas.polyline(pts, 13 * scale, (48, 31, 13, 150))
    canvas.polyline(pts, 8 * scale, accent)
    canvas.polyline(((x - 16 * scale, y + 0 * scale), (x - 5 * scale, y - 4 * scale), (x + 10 * scale, y - 3 * scale)), 2.0 * scale, (255, 244, 166, 155))
    canvas.circle(x + 22 * scale, y + 6 * scale, 2.5 * scale, (69, 99, 45, 230))


def draw_document(canvas: Canvas, x: float, y: float, w: float, h: float, paper: Color, ink: Color, accent: Color) -> None:
    canvas.rect(x, y, w, h, (42, 28, 14, 120), 3)
    canvas.rect(x, y - 2, w, h, paper, 3)
    canvas.polygon(((x + w - 13, y - 2), (x + w, y + 11), (x + w - 13, y + 11)), accent)
    for i, length in enumerate((w - 23, w - 16, w - 29)):
        canvas.line(x + 8, y + 16 + i * 9, x + 8 + length, y + 16 + i * 9, 2.1, ink)


def draw_theme(canvas: Canvas, index: int, name: str, accent: Color, base: Color, detail: Color) -> None:
    dark = (39, 24, 12, 215)
    ink = (49, 31, 16, 225)
    draw_backplate(canvas, accent, base, detail)
    if name == "crane":
        canvas.line(45, 88, 45, 38, 5, dark)
        canvas.line(32, 41, 92, 41, 5, dark)
        canvas.line(36, 42, 80, 69, 3.5, rgba(detail, 245))
        canvas.line(83, 42, 83, 71, 3.5, rgba(detail, 245))
        canvas.line(83, 71, 74, 82, 5, accent)
        canvas.rect(32, 85, 28, 9, rgba(detail, 245), 2)
        draw_banana(canvas, 72, 31, 0.62, rgba(accent, 250))
    elif name == "banana_crates":
        draw_banana(canvas, 64, 41, 0.9, rgba(accent, 255))
        for x in (36, 66):
            canvas.rect(x, 62, 28, 27, rgba(detail, 248), 3)
            canvas.rect(x + 3, 65, 22, 21, rgba((73, 46, 20), 65), 2)
            canvas.line(x + 5, 75, x + 23, 75, 2.3, ink)
            canvas.line(x + 14, 65, x + 14, 88, 2.0, ink)
    elif name == "forms":
        draw_document(canvas, 45, 35, 38, 58, rgba(detail, 250), ink, accent)
        canvas.star(86, 82, 10, 5, accent)
    elif name == "jungle":
        canvas.polygon(((63, 28), (99, 58), (68, 97), (30, 66)), rgba(accent, 245))
        canvas.line(38, 72, 91, 45, 4, rgba(base, 235))
        canvas.line(57, 60, 38, 48, 3, rgba(detail, 230))
        canvas.line(67, 66, 88, 80, 3, rgba(detail, 225))
        draw_banana(canvas, 50, 91, 0.48, rgba(detail, 235))
    elif name == "farm":
        canvas.rect(40, 58, 48, 33, rgba(detail, 248), 3)
        canvas.polygon(((34, 58), (64, 32), (94, 58)), accent)
        canvas.rect(57, 73, 14, 18, dark, 2)
        canvas.line(33, 94, 95, 94, 4, rgba((88, 146, 65), 245))
        canvas.line(42, 89, 31, 96, 3, rgba((88, 146, 65), 235))
        canvas.line(86, 89, 97, 96, 3, rgba((88, 146, 65), 235))
    elif name == "inspector":
        canvas.circle(64, 55, 25, dark)
        canvas.circle(64, 55, 20, rgba(accent, 248))
        canvas.circle(64, 55, 11, rgba(detail, 245))
        for angle in (-60, -30, 0, 30, 60):
            rad = math.radians(angle)
            canvas.line(64, 79, 64 + math.sin(rad) * 26, 79 + math.cos(rad) * 20, 3.2, rgba(detail, 235))
        canvas.circle(64, 55, 6, rgba(base, 255))
    elif name == "factory":
        canvas.rect(33, 61, 61, 27, rgba(detail, 245), 4)
        canvas.rect(38, 34, 13, 28, dark, 2)
        canvas.rect(74, 42, 13, 20, dark, 2)
        canvas.circle(81, 32, 7, rgba(detail, 90))
        canvas.circle(49, 26, 6, rgba(detail, 80))
        canvas.ring(62, 74, 14, 4, accent)
        for a in range(0, 360, 60):
            rad = math.radians(a)
            canvas.line(62, 74, 62 + math.cos(rad) * 15, 74 + math.sin(rad) * 15, 3, accent)
    elif name == "archive":
        for i, y in enumerate((43, 61, 79)):
            canvas.rect(35, y, 58, 15, rgba(detail if i != 1 else accent, 245), 3)
            canvas.line(45, y + 8, 83, y + 8, 2, ink)
            canvas.rect(58, y + 5, 12, 4, rgba(base, 220), 1)
        draw_document(canvas, 73, 32, 19, 23, rgba(detail, 225), ink, accent)
    elif name == "reactor":
        canvas.circle(64, 64, 9, accent)
        canvas.ring(64, 64, 29, 3, rgba(detail, 245))
        canvas.line(34, 64, 94, 64, 3, rgba(detail, 245))
        canvas.line(43, 38, 85, 90, 3, rgba(detail, 245))
        canvas.line(85, 38, 43, 90, 3, rgba(detail, 245))
        for x, y in ((94, 64), (43, 38), (85, 90)):
            canvas.circle(x, y, 5, accent)
        draw_banana(canvas, 64, 31, 0.55, rgba(accent, 255))
    elif name == "corridor":
        canvas.polygon(((31, 36), (58, 48), (58, 96), (31, 87)), rgba(detail, 245))
        canvas.polygon(((97, 36), (70, 48), (70, 96), (97, 87)), rgba(detail, 245))
        canvas.line(58, 48, 70, 48, 4, accent)
        canvas.line(64, 48, 64, 99, 4, accent)
        canvas.circle(51, 68, 4, ink)
        canvas.circle(77, 68, 4, ink)
    elif name == "night_shift":
        canvas.circle(58, 56, 24, rgba(detail, 245))
        canvas.circle(69, 48, 24, rgba(base, 255))
        for x, y, r in ((89, 79, 10), (38, 40, 5), (98, 39, 5)):
            canvas.star(x, y, r, r * 0.45, accent)
    elif name == "training":
        canvas.polygon(((37, 35), (63, 44), (63, 95), (37, 87)), rgba(detail, 245))
        canvas.polygon(((91, 35), (65, 44), (65, 95), (91, 87)), rgba(accent, 245))
        canvas.line(64, 42, 64, 96, 3, ink)
        canvas.line(72, 68, 80, 77, 4, ink)
        canvas.line(80, 77, 94, 51, 4, ink)
    elif name == "tower":
        canvas.rect(44, 35, 40, 58, rgba(detail, 245), 4)
        canvas.rect(36, 84, 56, 11, accent, 3)
        for y in (48, 62, 76):
            canvas.line(52, y, 76, y, 2.5, ink)
        canvas.line(70, 34, 70, 21, 3, accent)
        canvas.polygon(((70, 21), (94, 28), (70, 35)), accent)
    elif name == "ministry":
        canvas.polygon(((31, 49), (64, 29), (97, 49)), accent)
        canvas.rect(34, 88, 60, 8, accent, 2)
        for x in (43, 59, 75):
            canvas.rect(x, 51, 9, 38, rgba(detail, 248), 2)
        canvas.circle(88, 35, 7, rgba(detail, 105))
        canvas.circle(99, 28, 6, rgba(detail, 82))
    elif name == "heart":
        canvas.circle(54, 50, 15, rgba(detail, 245))
        canvas.circle(74, 50, 15, rgba(detail, 245))
        canvas.polygon(((39, 55), (89, 55), (64, 91)), rgba(detail, 245))
        canvas.ring(64, 66, 27, 4, accent)
        canvas.line(37, 66, 91, 66, 3, accent)
        canvas.circle(64, 66, 7, accent)
    else:
        canvas.star(64, 62, 28, 12, accent)


def write_png_rgba(path: Path, width: int, height: int, pixels: bytes | bytearray) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * stride : (y + 1) * stride])
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_meta(path: Path, display_name: str, asset_uuid: str) -> None:
    meta = {
        "ver": "1.0.27",
        "importer": "image",
        "imported": True,
        "uuid": asset_uuid,
        "files": [".json", ".png"],
        "subMetas": {
            "6c48a": {
                "importer": "texture",
                "uuid": f"{asset_uuid}@6c48a",
                "displayName": display_name,
                "id": "6c48a",
                "name": "texture",
                "userData": {
                    "wrapModeS": "clamp-to-edge",
                    "wrapModeT": "clamp-to-edge",
                    "imageUuidOrDatabaseUri": asset_uuid,
                    "isUuid": True,
                    "visible": False,
                    "minfilter": "linear",
                    "magfilter": "linear",
                    "mipfilter": "none",
                    "anisotropy": 0,
                },
                "ver": "1.0.22",
                "imported": True,
                "files": [".json"],
                "subMetas": {},
            },
            "f9941": {
                "importer": "sprite-frame",
                "uuid": f"{asset_uuid}@f9941",
                "displayName": display_name,
                "id": "f9941",
                "name": "spriteFrame",
                "userData": {
                    "trimThreshold": 1,
                    "rotated": False,
                    "offsetX": 0,
                    "offsetY": 0,
                    "trimX": 0,
                    "trimY": 0,
                    "width": SIZE,
                    "height": SIZE,
                    "rawWidth": SIZE,
                    "rawHeight": SIZE,
                    "borderTop": 0,
                    "borderBottom": 0,
                    "borderLeft": 0,
                    "borderRight": 0,
                    "packable": True,
                    "pixelsToUnit": 100,
                    "pivotX": 0.5,
                    "pivotY": 0.5,
                    "meshType": 0,
                    "vertices": {
                        "rawPosition": [-64, -64, 0, 64, -64, 0, -64, 64, 0, 64, 64, 0],
                        "indexes": [0, 1, 2, 2, 1, 3],
                        "uv": [0, SIZE, SIZE, SIZE, 0, 0, SIZE, 0],
                        "nuv": [0, 0, 1, 0, 0, 1, 1, 1],
                        "minPos": [-64, -64, 0],
                        "maxPos": [64, 64, 0],
                    },
                    "isUuid": True,
                    "imageUuidOrDatabaseUri": f"{asset_uuid}@6c48a",
                    "atlasUuid": "",
                    "trimType": "auto",
                },
                "ver": "1.0.12",
                "imported": True,
                "files": [".json"],
                "subMetas": {},
            },
        },
        "userData": {
            "type": "sprite-frame",
            "fixAlphaTransparencyArtifacts": False,
            "hasAlpha": True,
            "redirect": f"{asset_uuid}@6c48a",
        },
    }
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_icon(index: int, theme: tuple[str, Color, Color, Color]) -> bytearray:
    name, accent, base, detail = theme
    canvas = Canvas()
    draw_theme(canvas, index, name, accent, base, detail)
    return canvas.downsample()


def paste_rgba(dst: bytearray, dst_w: int, dst_h: int, src: bytearray, src_w: int, src_h: int, x0: int, y0: int) -> None:
    for y in range(src_h):
        for x in range(src_w):
            si = (y * src_w + x) * 4
            blend_pixel(dst, dst_w, dst_h, x0 + x, y0 + y, (src[si], src[si + 1], src[si + 2], src[si + 3]))


def make_contact_sheet(icons: list[bytearray]) -> None:
    cols = 5
    cell = 144
    rows = math.ceil(len(icons) / cols)
    width = cols * cell
    height = rows * cell
    sheet = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 4
            sheet[i : i + 4] = bytes((31, 24, 16, 255))
    for index, icon in enumerate(icons):
        col = index % cols
        row = index // cols
        x = col * cell + 8
        y = row * cell + 8
        paste_rgba(sheet, width, height, icon, SIZE, SIZE, x, y)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    write_png_rgba(QA_DIR / "level_select_theme_icons_contact_sheet.png", width, height, sheet)


def generate() -> dict[str, object]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    icons: list[bytearray] = []
    files: list[str] = []
    for idx, theme in enumerate(THEMES, 1):
        display_name = f"mtr_level_select_theme_icon_{idx:02d}"
        asset_uuid = str(uuid.uuid5(NAMESPACE, display_name))
        pixels = make_icon(idx, theme)
        png_path = ASSET_DIR / f"{display_name}.png"
        meta_path = ASSET_DIR / f"{display_name}.png.meta"
        write_png_rgba(png_path, SIZE, SIZE, pixels)
        write_meta(meta_path, display_name, asset_uuid)
        icons.append(pixels)
        files.append(str(png_path))
    make_contact_sheet(icons)
    result = verify_assets()
    result["generated"] = files
    return result


def png_info(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG with IHDR")
    width, height = struct.unpack(">II", data[16:24])
    bit_depth = data[24]
    color_type = data[25]
    return width, height, bit_depth, color_type


def verify_assets() -> dict[str, object]:
    pngs = sorted(ASSET_DIR.glob("mtr_level_select_theme_icon_*.png"))
    metas = sorted(ASSET_DIR.glob("mtr_level_select_theme_icon_*.png.meta"))
    if len(pngs) != len(THEMES):
        raise AssertionError(f"expected {len(THEMES)} level-select theme PNGs, found {len(pngs)}")
    if len(metas) != len(THEMES):
        raise AssertionError(f"expected {len(THEMES)} level-select theme meta files, found {len(metas)}")
    dimensions: list[tuple[str, int, int, int, int]] = []
    for png in pngs:
        width, height, bit_depth, color_type = png_info(png)
        if (width, height, bit_depth, color_type) != (SIZE, SIZE, 8, 6):
            raise AssertionError(f"{png.name} must be {SIZE}x{SIZE} RGBA8, got {(width, height, bit_depth, color_type)}")
        dimensions.append((png.name, width, height, bit_depth, color_type))
    for meta in metas:
        data = json.loads(meta.read_text(encoding="utf-8"))
        if data.get("importer") != "image" or not data.get("userData", {}).get("hasAlpha"):
            raise AssertionError(f"{meta.name} must be Cocos image meta with alpha")
        sprite = data.get("subMetas", {}).get("f9941", {}).get("userData", {})
        if sprite.get("rawWidth") != SIZE or sprite.get("rawHeight") != SIZE:
            raise AssertionError(f"{meta.name} sprite-frame raw size mismatch")
    return {
        "asset_dir": str(ASSET_DIR),
        "png_count": len(pngs),
        "meta_count": len(metas),
        "dimensions": dimensions,
        "contact_sheet": str(QA_DIR / "level_select_theme_icons_contact_sheet.png"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cocos-compatible PNG theme icons for the level-select menu.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = verify_assets() if args.verify_only else generate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
