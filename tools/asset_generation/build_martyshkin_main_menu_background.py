from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

try:
    import cv2
except ModuleNotFoundError:  # pragma: no cover - depends on local toolchain.
    cv2 = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "nessesary" / "10.1"
GENERATED_SOURCE_DIR = PROJECT_ROOT / "nessesary" / "generated"
GENERATED_MAIN_MENU_FAR_SOURCE = GENERATED_SOURCE_DIR / "main_menu_bg_far_generated_20260619.png"
OUT_DIR = PROJECT_ROOT / "assets" / "resources" / "ui" / "main_menu_background"
QA_DIR = PROJECT_ROOT / "qa" / "main-menu-background-10-1"
ACTIVE_SINGLE_LAYER_ASSETS = {"main_menu_bg_far.png"}
PRESERVE_DECORATIVE_FAR_EDGE_SIGNS = False
SKIPPED_LEGACY_ASSETS = [
    "main_menu_bg_mid.png",
    "main_menu_bg_near_left.png",
    "main_menu_bg_near_right.png",
    "main_menu_bg_top_hanging.png",
    "main_menu_bg_bottom_foreground.png",
    "main_menu_grade_overlay.png",
    "main_menu_decor_props_sheet.png",
]


@dataclass(frozen=True)
class AssetSpec:
    source_index: int
    file_name: str
    mode: str
    size: tuple[int, int]
    alpha_policy: str
    packable: bool
    role: str


SPECS: list[AssetSpec] = [
    AssetSpec(1, "main_menu_bg_far.png", "RGB", (2048, 1152), "opaque", False, "far scenic background"),
]

ACTIVE_SPECS: list[AssetSpec] = [spec for spec in SPECS if spec.file_name in ACTIVE_SINGLE_LAYER_ASSETS]

MAIN_MENU_FAR_DETEXT_RECTS: tuple[tuple[int, int, int, int], ...] = (
    # Optional fallback only.  The current UI audit allows non-interactive
    # decorative signs on the backdrop, while forbidding ghost labels and
    # interactive baked text under the menu.  The default path preserves the
    # scenic illustration; patching these areas locally creates visible spots.
    (196, 404, 454, 604),
    (1748, 640, 2048, 848),
)
MAIN_MENU_FAR_DETEXT_CLONE_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, 230),
    (-420, 130),
)


def natural_source_index(path: Path) -> int:
    match = re.search(r"\((\d+)\)", path.name)
    if match:
        return int(match.group(1))
    return 999


def source_files() -> dict[int, Path]:
    files = sorted(SOURCE_DIR.glob("*.png"), key=lambda p: (natural_source_index(p), p.name))
    mapping: dict[int, Path] = {}
    for i, path in enumerate(files, 1):
        mapping[natural_source_index(path) if natural_source_index(path) != 999 else i] = path
    return mapping


def source_for_spec(spec: AssetSpec, source_map: dict[int, Path]) -> Path:
    if spec.file_name == "main_menu_bg_far.png" and GENERATED_MAIN_MENU_FAR_SOURCE.exists():
        return GENERATED_MAIN_MENU_FAR_SOURCE
    source = source_map.get(spec.source_index)
    if not source:
        raise SystemExit(f"Missing source index {spec.source_index}")
    return source


def validate_active_sources(source_map: dict[int, Path]) -> None:
    """Require only sources that can actually be used by the active runtime policy."""

    missing: list[str] = []
    for spec in ACTIVE_SPECS:
        if spec.file_name == "main_menu_bg_far.png" and GENERATED_MAIN_MENU_FAR_SOURCE.exists():
            continue
        if spec.source_index not in source_map:
            missing.append(f"{spec.file_name}: source index {spec.source_index}")
    if missing:
        raise SystemExit(
            "Missing active main-menu backdrop source(s): "
            + ", ".join(missing)
            + f". Legacy onion-layer sources are intentionally not required by the single-PNG policy."
        )


def resize_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = math.ceil(src_w * scale)
    new_h = math.ceil(src_h * scale)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def resize_contain(img: Image.Image, size: tuple[int, int], fill=(0, 0, 0, 0)) -> Image.Image:
    target_w, target_h = size
    rgba = img.convert("RGBA")
    scale = min(target_w / rgba.width, target_h / rgba.height)
    new_w = max(1, round(rgba.width * scale))
    new_h = max(1, round(rgba.height * scale))
    resized = rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, fill)
    canvas.alpha_composite(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def connected_components(mask: np.ndarray) -> tuple[int, np.ndarray]:
    if cv2 is None:
        raise RuntimeError(
            "OpenCV is required only for legacy transparent-layer extraction. "
            "The active single-layer main-menu backdrop generation does not need it."
        )
    count, labels = cv2.connectedComponents(mask.astype(np.uint8), 8)
    return int(count), labels.astype(np.int32, copy=False)


def largest_connected_background(candidate: np.ndarray, center_seed: bool) -> np.ndarray:
    count, labels = connected_components(candidate)
    if count <= 1:
        return candidate
    h, w = candidate.shape
    border_labels = set(np.unique(np.concatenate([labels[0, :], labels[h - 1, :], labels[:, 0], labels[:, w - 1]])))
    if center_seed:
        cx1, cx2 = int(w * 0.23), int(w * 0.77)
        cy1, cy2 = int(h * 0.20), int(h * 0.82)
        center_labels = set(np.unique(labels[cy1:cy2, cx1:cx2]))
    else:
        center_labels = set()
    areas = np.bincount(labels.reshape(-1), minlength=count)
    area_cutoff = int(h * w * 0.08)
    keep_labels = {label for label in border_labels | center_labels if label > 0}
    keep_labels.update(label for label, area in enumerate(areas) if label > 0 and area >= area_cutoff)
    return np.isin(labels, list(keep_labels))


def alpha_from_background_mask(mask: np.ndarray, width: int, height: int) -> Image.Image:
    mask_img = Image.fromarray((mask.astype(np.uint8) * 255), "L")
    dilated = mask_img.filter(ImageFilter.MaxFilter(3))
    softened = dilated.filter(ImageFilter.GaussianBlur(0.65))
    alpha = Image.new("L", (width, height), 255)
    alpha = Image.composite(Image.new("L", (width, height), 0), alpha, softened)
    return alpha


def remove_checkerboard(img: Image.Image, size: tuple[int, int], atmosphere: bool = False) -> Image.Image:
    rgba = resize_cover(img.convert("RGBA"), size)
    arr = np.asarray(rgba).astype(np.int16)
    rgb = arr[:, :, :3]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    brightness = rgb.mean(axis=2)
    neutral = (maxc - minc) < (20 if atmosphere else 18)
    bright = brightness > (128 if atmosphere else 150)
    candidate = neutral & bright
    bg = largest_connected_background(candidate, center_seed=True)
    alpha = alpha_from_background_mask(bg, rgba.width, rgba.height)
    out = rgba.copy()
    out.putalpha(alpha)
    return out


def remove_black_background(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    rgba = resize_contain(img.convert("RGBA"), size)
    arr = np.asarray(rgba).astype(np.int16)
    rgb = arr[:, :, :3]
    brightness = rgb.mean(axis=2)
    candidate = brightness < 38
    bg = largest_connected_background(candidate, center_seed=False)
    alpha = alpha_from_background_mask(bg, rgba.width, rgba.height)
    out = rgba.copy()
    out.putalpha(alpha)
    return out


def generated_grade_overlay(size: tuple[int, int]) -> Image.Image:
    w, h = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    alpha = np.zeros((h, w), dtype=np.float32)

    def add_glow(cx: float, cy: float, rx: float, ry: float, strength: float) -> None:
        nonlocal alpha
        dist = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        alpha += np.exp(-dist * 2.2) * strength

    add_glow(w * 0.06, h * 0.94, w * 0.42, h * 0.26, 56)
    add_glow(w * 0.93, h * 0.08, w * 0.38, h * 0.25, 34)
    add_glow(w * 0.52, h * 0.48, w * 0.82, h * 0.72, 13)

    # Soft diagonal sunbeams, intentionally weak in the center menu-safe zone.
    for offset, strength in ((-280, 18), (120, 12), (520, 10)):
        beam = np.abs((x - y * 1.45) - offset)
        alpha += np.clip(1 - beam / 92, 0, 1) * strength * np.clip((h - y) / h, 0, 1)

    center_quiet = np.exp(-(((x - w * 0.5) / (w * 0.31)) ** 2 + ((y - h * 0.48) / (h * 0.33)) ** 2) * 1.9)
    alpha *= 1 - center_quiet * 0.46

    rng = np.random.default_rng(20260612)
    particle = np.zeros((h, w), dtype=np.float32)
    for _ in range(135):
        px = int(rng.integers(0, w))
        py = int(rng.integers(int(h * 0.05), int(h * 0.96)))
        radius = int(rng.integers(2, 8))
        strength = float(rng.uniform(9, 24))
        x1, x2 = max(0, px - radius * 3), min(w, px + radius * 3 + 1)
        y1, y2 = max(0, py - radius * 3), min(h, py + radius * 3 + 1)
        yy, xx = np.mgrid[y1:y2, x1:x2]
        particle[y1:y2, x1:x2] += np.exp(-(((xx - px) ** 2 + (yy - py) ** 2) / max(1, radius * radius * 2.6))) * strength
    alpha += particle
    alpha = np.clip(alpha, 0, 82).astype(np.uint8)
    alpha[alpha < 3] = 0

    color = np.zeros((h, w, 4), dtype=np.uint8)
    color[:, :, 0] = 255
    color[:, :, 1] = 206
    color[:, :, 2] = 122
    color[:, :, 3] = alpha
    return Image.fromarray(color, "RGBA").filter(ImageFilter.GaussianBlur(0.25))


def soft_clear_alpha(img: Image.Image, rect: tuple[int, int, int, int], blur: float, keep: float = 0.0) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A")).astype(np.float32)
    clear = Image.new("L", rgba.size, 0)
    draw = ImageDraw.Draw(clear)
    draw.rectangle(rect, fill=255)
    clear = clear.filter(ImageFilter.GaussianBlur(blur))
    clear_arr = np.asarray(clear).astype(np.float32) / 255.0
    multiplier = 1.0 - clear_arr * (1.0 - keep)
    new_alpha = np.clip(alpha * multiplier, 0, 255).astype(np.uint8)
    out = rgba.copy()
    out.putalpha(Image.fromarray(new_alpha, "L"))
    return out


def quiet_opaque_menu_center(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    rgba = rgb.convert("RGBA")
    blurred = rgba.filter(ImageFilter.GaussianBlur(14))
    warm = Image.new("RGBA", rgba.size, (92, 70, 44, 255))
    quiet = Image.blend(blurred, warm, 0.42)
    mask = Image.new("L", rgba.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((430, 98, 1618, 1090), fill=232)
    mask = mask.filter(ImageFilter.GaussianBlur(118))
    out = Image.composite(quiet, rgba, mask)
    return out.convert("RGB")


def detext_fill_patch(base: Image.Image, rect: tuple[int, int, int, int], index: int) -> Image.Image:
    """Create a local non-text scenic fill for a removed baked sign."""

    x1, y1, x2, y2 = rect
    patch_w = x2 - x1
    patch_h = y2 - y1

    dx, dy = MAIN_MENU_FAR_DETEXT_CLONE_OFFSETS[index]
    sx1 = min(max(0, x1 + dx), max(0, base.width - patch_w))
    sy1 = min(max(0, y1 + dy), max(0, base.height - patch_h))
    patch = base.crop((sx1, sy1, sx1 + patch_w, sy1 + patch_h)).convert("RGB")

    pad = 112
    sample_box = (
        max(0, x1 - pad),
        max(0, y1 - pad),
        min(base.width, x2 + pad),
        min(base.height, y2 + pad),
    )
    sample = np.asarray(base.crop(sample_box).convert("RGB"), dtype=np.float32)
    outside = np.ones(sample.shape[:2], dtype=bool)
    sx1, sy1 = x1 - sample_box[0], y1 - sample_box[1]
    sx2, sy2 = sx1 + patch_w, sy1 + patch_h
    outside[max(0, sy1):min(outside.shape[0], sy2), max(0, sx1):min(outside.shape[1], sx2)] = False
    pixels = sample[outside]
    base_color = np.median(pixels, axis=0) if pixels.size else np.array([90.0, 80.0, 58.0], dtype=np.float32)

    arr = np.asarray(patch, dtype=np.float32)
    patch_color = np.median(arr.reshape(-1, 3), axis=0)
    arr += (base_color - patch_color)[None, None, :] * 0.58
    patch = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.65)).convert("RGBA")

    rng = np.random.default_rng(2026061901 + index)
    draw = ImageDraw.Draw(patch, "RGBA")
    for _ in range(7):
        px = int(rng.integers(-patch_w // 8, patch_w))
        py = int(rng.integers(-patch_h // 8, patch_h))
        length = int(rng.integers(max(18, patch_w // 9), max(20, patch_w // 4)))
        tone = int(rng.integers(-18, 20))
        color = (
            int(np.clip(base_color[0] + tone, 0, 255)),
            int(np.clip(base_color[1] + tone * 0.85, 0, 255)),
            int(np.clip(base_color[2] + tone * 0.55, 0, 255)),
            int(rng.integers(12, 26)),
        )
        draw.line((px, py, px + length, py + int(rng.integers(-16, 16))), fill=color, width=int(rng.integers(2, 5)))
    for _ in range(5):
        px = int(rng.integers(-20, patch_w))
        py = int(rng.integers(-8, patch_h))
        color = (45, 67, 42, int(rng.integers(10, 22)))
        draw.ellipse((px, py, px + int(rng.integers(32, 74)), py + int(rng.integers(10, 24))), fill=color)
    return patch


def remove_readable_far_signage(img: Image.Image) -> Image.Image:
    """Remove baked text/signage from the single active main-menu backdrop."""

    rgb = img.convert("RGB")
    if cv2 is not None:
        arr = np.asarray(rgb, dtype=np.uint8)
        mask = np.zeros((rgb.height, rgb.width), dtype=np.uint8)
        for rect in MAIN_MENU_FAR_DETEXT_RECTS:
            x1, y1, x2, y2 = rect
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

        kernel = np.ones((9, 9), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        fixed_bgr = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
        fixed_rgb = cv2.cvtColor(fixed_bgr, cv2.COLOR_BGR2RGB)
        fixed = Image.fromarray(fixed_rgb).convert("RGBA")
    else:
        fixed = rgb.convert("RGBA")
        for index, rect in enumerate(MAIN_MENU_FAR_DETEXT_RECTS):
            x1, y1, x2, y2 = rect
            patch = detext_fill_patch(fixed, rect, index)
            mask = Image.new("L", (x2 - x1, y2 - y1), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, x2 - x1, y2 - y1), radius=24, fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(26))
            fixed.paste(patch.convert("RGBA"), (x1, y1), mask)

    # Add only a tiny amount of non-readable organic noise over the removed
    # sign zones.  The backdrop must remain one scene, not visible UI plaques.
    overlay = Image.new("RGBA", fixed.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    for index, (x1, y1, x2, y2) in enumerate(MAIN_MENU_FAR_DETEXT_RECTS):
        pole = (108, 91, 58, 18)
        cord = (65, 55, 38, 14)
        leaf = (48, 73, 45, 16)
        span = max(1, x2 - x1)
        for t in (0.18, 0.76):
            x = round(x1 + span * t)
            draw.line((x, y1 + 8, x - 8, y2 - 8), fill=pole, width=2)
        draw.line((x1 + 16, y2 - 18, x2 - 16, y1 + 34), fill=cord, width=2)
        leaf_anchor = (x1 - 8 if index == 0 else x2 - 52, y1 + 8)
        for n in range(3):
            lx = leaf_anchor[0] + n * 15
            ly = leaf_anchor[1] + (n % 2) * 9
            draw.ellipse((lx, ly, lx + 38, ly + 15), fill=leaf)

    fixed = Image.alpha_composite(fixed, overlay)
    return fixed.convert("RGB")


def tone_single_layer_main_menu_far(img: Image.Image) -> Image.Image:
    """Grade the backdrop so it is visible in-menu but does not fight buttons."""

    rgb = img.convert("RGB")
    arr = np.asarray(rgb, dtype=np.float32)
    h, w = arr.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (x / max(1, w - 1)) - 0.5
    ny = (y / max(1, h - 1)) - 0.45
    edge = np.clip((nx / 0.66) ** 2 + (ny / 0.56) ** 2, 0.0, 1.0)
    vertical = y / max(1, h - 1)
    center_quiet = np.exp(-(((x - w * 0.54) / (w * 0.36)) ** 2 + ((y - h * 0.52) / (h * 0.44)) ** 2) * 1.55)

    multiplier = 0.92 - edge * 0.14 - vertical * 0.035
    warm_shadow = np.array([18.0, 15.0, 10.0], dtype=np.float32)
    arr = arr * multiplier[:, :, None] + warm_shadow * (1.0 - multiplier[:, :, None])

    # A very soft center matte prevents the bright sky from behaving like a
    # second UI panel behind the PNG buttons.
    matte = np.array([112.0, 88.0, 52.0], dtype=np.float32)
    arr = arr * (1.0 - center_quiet[:, :, None] * 0.10) + matte * (center_quiet[:, :, None] * 0.10)

    # Keep a little warm jungle sunlight.  This restores the "picture" that
    # disappeared when the old layers were removed, but stays one flat backdrop.
    glow = np.exp(-(((x - w * 0.50) / (w * 0.42)) ** 2 + ((y - h * 0.33) / (h * 0.32)) ** 2) * 2.2)
    arr += glow[:, :, None] * np.array([8.0, 6.0, 2.0], dtype=np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")


def prepare_generated_main_menu_far_background(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Normalize the production generated backdrop without local patching."""

    scenic = resize_cover(img.convert("RGB"), size)
    scenic = ImageEnhance.Color(scenic).enhance(1.06)
    scenic = ImageEnhance.Contrast(scenic).enhance(1.03)
    scenic = ImageEnhance.Brightness(scenic).enhance(0.99)
    return scenic.convert("RGB")


def sanitized_single_layer_far_background(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    scenic = resize_cover(img.convert("RGB"), size)
    if not PRESERVE_DECORATIVE_FAR_EDGE_SIGNS:
        scenic = remove_readable_far_signage(scenic)
    return tone_single_layer_main_menu_far(scenic)


def apply_menu_safe_zone_alpha(img: Image.Image, file_name: str) -> Image.Image:
    if file_name == "main_menu_bg_near_left.png":
        return soft_clear_alpha(img, (520, 0, img.width, img.height), 104, keep=0.0)
    if file_name == "main_menu_bg_near_right.png":
        return soft_clear_alpha(img, (0, 0, 1590, img.height), 104, keep=0.0)
    if file_name == "main_menu_bg_top_hanging.png":
        return soft_clear_alpha(img, (300, 0, 1748, 980), 116, keep=0.0)
    if file_name == "main_menu_bg_bottom_foreground.png":
        return soft_clear_alpha(img, (330, 320, 1720, img.height), 136, keep=0.0)
    return img


def create_directory_meta(path: Path) -> None:
    meta = path.with_suffix(path.suffix + ".meta") if path.suffix else Path(str(path) + ".meta")
    if meta.exists():
        return
    meta.write_text(json.dumps({
        "ver": "1.2.0",
        "importer": "directory",
        "imported": True,
        "uuid": str(uuid.uuid4()),
        "files": [],
        "subMetas": {},
        "userData": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def existing_image_uuid(path: Path) -> str | None:
    meta_path = path.with_suffix(path.suffix + ".meta")
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    value = meta.get("uuid")
    return value if isinstance(value, str) and value else None


def image_meta(path: Path, img: Image.Image, has_alpha: bool, packable: bool, base_uuid: str | None = None) -> dict:
    base_uuid = base_uuid or str(uuid.uuid4())
    name = path.stem
    w, h = img.size
    half_w = w / 2
    half_h = h / 2
    return {
        "ver": "1.0.27",
        "importer": "image",
        "imported": True,
        "uuid": base_uuid,
        "files": [".json", ".png"],
        "subMetas": {
            "6c48a": {
                "importer": "texture",
                "uuid": f"{base_uuid}@6c48a",
                "displayName": name,
                "id": "6c48a",
                "name": "texture",
                "userData": {
                    "wrapModeS": "clamp-to-edge",
                    "wrapModeT": "clamp-to-edge",
                    "imageUuidOrDatabaseUri": base_uuid,
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
                "uuid": f"{base_uuid}@f9941",
                "displayName": name,
                "id": "f9941",
                "name": "spriteFrame",
                "userData": {
                    "trimThreshold": 1,
                    "rotated": False,
                    "offsetX": 0,
                    "offsetY": 0,
                    "trimX": 0,
                    "trimY": 0,
                    "width": w,
                    "height": h,
                    "rawWidth": w,
                    "rawHeight": h,
                    "borderTop": 0,
                    "borderBottom": 0,
                    "borderLeft": 0,
                    "borderRight": 0,
                    "packable": packable,
                    "pixelsToUnit": 100,
                    "pivotX": 0.5,
                    "pivotY": 0.5,
                    "meshType": 0,
                    "vertices": {
                        "rawPosition": [-half_w, -half_h, 0, half_w, -half_h, 0, -half_w, half_h, 0, half_w, half_h, 0],
                        "indexes": [0, 1, 2, 2, 1, 3],
                        "uv": [0, h, w, h, 0, 0, w, 0],
                        "nuv": [0, 0, 1, 0, 0, 1, 1, 1],
                        "minPos": [-half_w, -half_h, 0],
                        "maxPos": [half_w, half_h, 0],
                    },
                    "isUuid": True,
                    "imageUuidOrDatabaseUri": f"{base_uuid}@6c48a",
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
            "hasAlpha": has_alpha,
            "redirect": f"{base_uuid}@6c48a",
        },
    }


def save_meta(path: Path, img: Image.Image, has_alpha: bool, packable: bool) -> None:
    base_uuid = existing_image_uuid(path)
    path.with_suffix(path.suffix + ".meta").write_text(
        json.dumps(image_meta(path, img, has_alpha, packable, base_uuid), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def alpha_stats(img: Image.Image) -> dict:
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    hist = alpha.histogram()
    total = rgba.width * rgba.height
    transparent = sum(hist[:8])
    opaque = sum(hist[248:])
    return {
        "size": [rgba.width, rgba.height],
        "mode": rgba.mode,
        "alphaMinMax": list(alpha.getextrema()),
        "transparentPct": round(transparent * 100 / total, 3),
        "opaquePct": round(opaque * 100 / total, 3),
        "bbox": list(alpha.getbbox() or (0, 0, 0, 0)),
    }


def checkerboard(size: tuple[int, int], tile: int = 24) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (32, 29, 24, 255))
    draw = ImageDraw.Draw(img)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            color = (78, 72, 62, 255) if ((x // tile) + (y // tile)) % 2 else (42, 38, 32, 255)
            draw.rectangle([x, y, x + tile - 1, y + tile - 1], fill=color)
    return img


def contact_sheet(paths: list[Path], out_path: Path) -> None:
    tile_w, tile_h = 420, 260
    cols = 2
    rows = math.ceil(len(paths) / cols)
    sheet = Image.new("RGBA", (tile_w * cols, rows * (tile_h + 42)), (24, 20, 16, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, path in enumerate(paths):
        x = (i % cols) * tile_w
        y = (i // cols) * (tile_h + 42)
        img = Image.open(path).convert("RGBA")
        bg = checkerboard((tile_w, tile_h))
        img.thumbnail((tile_w, tile_h), Image.Resampling.LANCZOS)
        bg.alpha_composite(img, ((tile_w - img.width) // 2, (tile_h - img.height) // 2))
        sheet.alpha_composite(bg, (x, y))
        draw.text((x + 8, y + tile_h + 8), path.name, fill=(246, 228, 180, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path, quality=92)


def main() -> None:
    source_map = source_files()
    validate_active_sources(source_map)

    uses_generated_far_source = GENERATED_MAIN_MENU_FAR_SOURCE.exists()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    create_directory_meta(PROJECT_ROOT / "assets" / "resources" / "ui")
    create_directory_meta(OUT_DIR)

    report: dict[str, object] = {
        "sourceDir": str(SOURCE_DIR),
        "outDir": str(OUT_DIR),
        "setId": "main_menu_background_set",
        "runtimePolicy": "single active PNG backdrop; legacy onion layers are not regenerated into assets/resources",
        "skippedLegacyAssets": SKIPPED_LEGACY_ASSETS,
        "productionSource": str(GENERATED_MAIN_MENU_FAR_SOURCE) if uses_generated_far_source else "fallback: nessesary/10.1 source index 1",
        "productionSourceKind": "generated cohesive scenic PNG" if uses_generated_far_source else "legacy audit source with text-removal fallback",
        "centerSafeZonePolicy": "single coherent scenic picture; no ghost labels, UI props, readable text, patch marks, or onion-layer remnants in the menu backdrop",
        "decorativeFarEdgeSignsPreserved": PRESERVE_DECORATIVE_FAR_EDGE_SIGNS,
        "inactiveDetextRects": [] if uses_generated_far_source or PRESERVE_DECORATIVE_FAR_EDGE_SIGNS else [list(rect) for rect in MAIN_MENU_FAR_DETEXT_RECTS],
        "assets": [],
    }
    output_paths: list[Path] = []
    for spec in ACTIVE_SPECS:
        source = source_for_spec(spec, source_map)
        img = Image.open(source)
        if spec.file_name != "main_menu_bg_far.png":
            raise ValueError(f"Inactive legacy main-menu layer reached active generator: {spec.file_name}")
        out_img = prepare_generated_main_menu_far_background(img, spec.size) if source == GENERATED_MAIN_MENU_FAR_SOURCE else sanitized_single_layer_far_background(img, spec.size)
        save_img = out_img
        has_alpha = False

        out_path = OUT_DIR / spec.file_name
        save_img.save(out_path)
        save_meta(out_path, save_img.convert("RGBA"), has_alpha, spec.packable)
        output_paths.append(out_path)
        item = {
            "file": str(out_path),
            "source": str(source),
            "role": spec.role,
            "alphaPolicy": spec.alpha_policy,
            "hasAlpha": has_alpha,
            **alpha_stats(save_img),
        }
        report["assets"].append(item)

    report_path = QA_DIR / "main_menu_background_10_1_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    contact_sheet(output_paths, QA_DIR / "main_menu_background_10_1_contact_sheet.jpg")
    print(json.dumps({"generated": len(output_paths), "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
