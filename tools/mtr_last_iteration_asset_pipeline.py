from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


RUNTIME_ROOT = Path("assets/resources/objectives/themed/last_iteration")
RESOURCE_PREFIX = "objectives/themed/last_iteration"

CATEGORY_TO_FOLDER = {
    "platforms": "platforms",
    "hazards": "hazards",
    "collectibles": "collectibles",
    "bonuses": "bonuses",
    "npc_decor": "npc_decor",
    "labels_signage": "labels_signage",
    "foreground_decor": "foreground_decor",
    "background_decor": "background_decor",
    "equipment": "equipment",
    "ui_achievements": "ui_achievements",
}

HAZARD_TYPES_BY_THEME = {
    "construction": [0, 6, 8, 9, 10, 17],
    "logistics": [3, 6, 11, 17],
    "office": [1, 15, 16, 10],
    "jungle": [12, 7, 6, 17],
    "farm": [4, 6, 8, 17],
    "inspection": [5, 10, 16, 17],
    "steampunk": [7, 9, 11, 16],
    "archive": [1, 13, 15, 16],
    "security": [3, 6, 14, 10],
    "industrial": [7, 8, 9, 11],
    "shared": [6, 10, 17],
}

SHEET_SLOTS: list[dict[str, Any]] = [
    {
        "slot": "construction_base",
        "sourceSetRu": "набор_строительных_платформ_и_инструментов",
        "theme": "construction",
        "levels": [1, 2, 10],
        "roles": ["platforms", "hazards", "signage", "foreground"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level01_construction",
    },
    {
        "slot": "logistics_base",
        "sourceSetRu": "логистический_инвентарь_для_платформера",
        "theme": "logistics",
        "levels": [4, 8, 11],
        "roles": ["platforms", "hazards", "midground", "interactive_prop"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level02_logistics",
    },
    {
        "slot": "office_base",
        "sourceSetRu": "множество_офисных_предметов_и_платформ",
        "theme": "office",
        "levels": [3, 9, 13, 15],
        "roles": ["platforms", "hazards", "foreground", "theme_marker"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level03_office",
    },
    {
        "slot": "steampunk_base",
        "sourceSetRu": "лист_иконок_для_игры_в_стимпанк_стиле",
        "theme": "steampunk",
        "levels": [7, 8, 11, 12],
        "roles": ["platforms", "hazards", "pickup_decor", "interactive_prop", "theme_marker"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level07_steampunk",
    },
    {
        "slot": "jungle_farm_base",
        "sourceSetRu": "коллекция_игровых_активов_джунглей",
        "theme": "jungle",
        "levels": [5, 12],
        "roles": ["platforms", "hazards", "collectibles", "background", "theme_marker"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level04_jungle",
    },
    {
        "slot": "inspection_base",
        "sourceSetRu": "инспекция_в_процессе_элементы_декора",
        "theme": "inspection",
        "levels": [3, 6],
        "roles": ["platforms", "hazards", "signage", "midground", "background", "theme_marker"],
        "usageTier": "supporting_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level06_inspection",
    },
    {
        "slot": "security_base",
        "sourceSetRu": "платформы_безопасности_и_атрибуты",
        "theme": "security",
        "levels": [4, 6, 14],
        "roles": ["platforms", "hazards", "signage", "interactive_prop"],
        "usageTier": "cross_cutting",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_safety",
    },
    {
        "slot": "roadworks_base",
        "sourceSetRu": "игровые_элементы_для_строительных_работ",
        "theme": "industrial",
        "levels": [1, 2, 8],
        "roles": ["platforms", "hazards", "signage", "foreground", "theme_marker"],
        "usageTier": "supporting_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_roadworks",
    },
    {
        "slot": "farm_base",
        "sourceSetRu": "фермерские_платформы_и_предметы",
        "theme": "farm",
        "levels": [5, 10],
        "roles": ["platforms", "hazards", "theme_marker"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "platformMainCount": 2,
        "atlasGroup": "atlas_level05_farm",
    },
    {
        "slot": "shared_runner_base",
        "sourceSetRu": "игровые_активы_и_элементы_платформера",
        "theme": "shared",
        "levels": [],
        "roles": ["platforms", "hazards", "collectibles", "foreground"],
        "usageTier": "fallback_only",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_fallback",
    },
    {
        "slot": "construction_extended",
        "sourceSetRu": "строительные_элементы_на_прозрачном_фоне",
        "theme": "construction",
        "levels": [1, 2, 10],
        "roles": ["platforms", "hazards", "foreground"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level01_construction",
    },
    {
        "slot": "logistics_extended",
        "sourceSetRu": "логистические_игровые_активы_2d",
        "theme": "logistics",
        "levels": [4, 11, 14],
        "roles": ["platforms", "hazards", "midground"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level02_logistics",
    },
    {
        "slot": "office_extended",
        "sourceSetRu": "офисные_игровые_элементы_в_стиле_мультфильма",
        "theme": "office",
        "levels": [3, 9, 13],
        "roles": ["platforms", "hazards", "foreground", "theme_marker"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level03_office",
    },
    {
        "slot": "steampunk_extended",
        "sourceSetRu": "индустриальные_элементы_в_стиле_стимпанк",
        "theme": "steampunk",
        "levels": [7, 12],
        "roles": ["platforms", "hazards", "interactive_prop", "theme_marker"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level07_steampunk",
    },
    {
        "slot": "jungle_extended",
        "sourceSetRu": "игровая_таблица_активов_джунглей_и_фермы",
        "theme": "jungle",
        "levels": [5, 12],
        "roles": ["platforms", "hazards", "background", "theme_marker"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level04_jungle",
    },
    {
        "slot": "inspection_extended",
        "sourceSetRu": "материалы_для_контроля_и_проверки",
        "theme": "inspection",
        "levels": [6, 9, 13, 15],
        "roles": ["hazards", "signage", "interactive_prop", "theme_marker"],
        "usageTier": "secondary_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_level06_inspection",
    },
    {
        "slot": "archive_extended",
        "sourceSetRu": "архивные_предметы_и_мебель",
        "theme": "archive",
        "levels": [8, 9, 13, 15],
        "roles": ["platforms", "hazards", "midground", "theme_marker"],
        "usageTier": "primary_theme",
        "platformRole": "PlatformMain",
        "atlasGroup": "atlas_level08_archive",
    },
    {
        "slot": "roadworks_extended",
        "sourceSetRu": "сheet_of_construction_and_transport_assets",
        "theme": "industrial",
        "levels": [1, 4, 11],
        "roles": ["platforms", "hazards", "midground", "theme_marker"],
        "usageTier": "bridge_theme",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_construction_transport",
    },
    {
        "slot": "security_extended",
        "sourceSetRu": "элементы_безопасности_и_охраны",
        "theme": "security",
        "levels": [6, 14, 15],
        "roles": ["hazards", "signage", "foreground"],
        "usageTier": "cross_cutting",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_safety",
    },
    {
        "slot": "shared_runner_extended",
        "sourceSetRu": "игровые_ассеты_для_платформера",
        "theme": "shared",
        "levels": [],
        "roles": ["platforms", "collectibles", "foreground"],
        "usageTier": "fallback_only",
        "platformRole": "PlatformAlt",
        "atlasGroup": "atlas_shared_fallback",
    },
    {"slot": "ui_main_menu", "theme": "ui", "levels": [], "surface": "main_menu", "roles": ["ui"], "segmentationMode": "layout"},
    {"slot": "ui_records", "theme": "ui", "levels": [], "surface": "records", "roles": ["ui"]},
    {"slot": "ui_achievements", "theme": "ui", "levels": [], "surface": "achievements", "roles": ["ui"]},
    {"slot": "ui_level_select", "theme": "ui", "levels": [], "surface": "level_select", "roles": ["ui"]},
    {"slot": "ui_skin_select", "theme": "ui", "levels": [], "surface": "skin_select", "roles": ["ui"]},
    {"slot": "ui_sound_settings", "theme": "ui", "levels": [], "surface": "sound_settings", "roles": ["ui"]},
    {"slot": "ui_developer", "theme": "ui", "levels": [], "surface": "developer", "roles": ["ui"]},
    {"slot": "ui_pause", "theme": "ui", "levels": [], "surface": "pause", "roles": ["ui"]},
    {"slot": "ui_death_primary", "theme": "ui", "levels": [], "surface": "death", "roles": ["ui"]},
    {"slot": "ui_death_secondary", "theme": "ui", "levels": [], "surface": "death", "roles": ["ui"]},
]


@dataclass(frozen=True)
class Component:
    label: int
    x: int
    y: int
    w: int
    h: int
    area: int

    @property
    def aspect(self) -> float:
        return self.w / max(1, self.h)


@dataclass(frozen=True)
class SheetLayoutCut:
    name: str
    role: str
    x: int
    y: int
    w: int
    h: int
    critical: bool = False


UI_LAYOUT_CUTS_BY_SLOT: dict[str, list[SheetLayoutCut]] = {
    "ui_main_menu": [
        SheetLayoutCut("main_title", "title", 5, 0, 1028, 326, True),
        SheetLayoutCut("monkey_icon", "icon", 1118, 0, 290, 294, True),
        SheetLayoutCut("object_title", "prop", 170, 344, 668, 98, True),
        SheetLayoutCut("button_forward", "button", 40, 460, 440, 136, True),
        SheetLayoutCut("button_records", "button", 510, 460, 438, 136, True),
        SheetLayoutCut("button_skins", "button", 40, 606, 440, 136, True),
        SheetLayoutCut("button_levels", "button", 510, 606, 438, 136, True),
        SheetLayoutCut("button_sound", "button", 40, 752, 440, 136, True),
        SheetLayoutCut("button_developer", "button", 510, 752, 438, 136, True),
        SheetLayoutCut("button_back", "button", 956, 948, 336, 126, True),
        SheetLayoutCut("banana_bolt_left", "icon", 948, 328, 138, 78),
        SheetLayoutCut("banana_bolt_mid_left", "icon", 1088, 328, 128, 78),
        SheetLayoutCut("banana_bolt_mid_right", "icon", 1218, 330, 118, 76),
        SheetLayoutCut("banana_bolt_right", "icon", 1340, 330, 98, 76),
        SheetLayoutCut("fasteners", "prop", 954, 450, 432, 76),
        SheetLayoutCut("warning_primate", "prop", 962, 568, 160, 172),
        SheetLayoutCut("plan_done", "prop", 1134, 558, 142, 174),
        SheetLayoutCut("report_sacred", "prop", 1300, 562, 138, 170),
        SheetLayoutCut("accountant_primate", "prop", 956, 760, 170, 146),
        SheetLayoutCut("banana_poster", "prop", 1136, 768, 134, 146),
        SheetLayoutCut("hammock_primate", "prop", 1270, 756, 170, 166),
        SheetLayoutCut("stripe_corner_large", "prop", 38, 900, 214, 166),
        SheetLayoutCut("stripe_corner_triangle", "prop", 288, 912, 146, 142),
        SheetLayoutCut("stripe_corner_small", "prop", 456, 914, 138, 138),
        SheetLayoutCut("stripe_plate", "prop", 636, 944, 190, 104),
    ],
}


REQUIRED_UI_SURFACE_ROLES: dict[str, dict[str, int]] = {
    "main_menu": {"title": 1, "button": 6, "icon": 1, "prop": 3},
    "records": {"title": 1, "card": 1, "button": 1},
    "achievements": {"title": 1, "card": 3},
    "level_select": {"title": 1, "card": 8},
    "skin_select": {"title": 1, "card": 3, "button": 2},
    "sound_settings": {"title": 1, "button": 2, "card": 1},
    "developer": {"title": 1, "card": 1},
    "pause": {"title": 1, "card": 1, "button": 3},
    "death": {"title": 1, "card": 2, "button": 2},
}

REQUIRED_THEME_CATEGORY_MINIMUMS: dict[str, dict[str, int]] = {
    "construction": {"platforms": 4, "hazards": 4},
    "logistics": {"platforms": 3, "hazards": 3},
    "office": {"platforms": 3, "hazards": 3},
    "jungle": {"platforms": 3, "hazards": 3},
    "farm": {"platforms": 3, "hazards": 3},
    "inspection": {"platforms": 3, "hazards": 3},
    "security": {"platforms": 2, "hazards": 3},
    "industrial": {"platforms": 3, "hazards": 3},
    "archive": {"platforms": 2, "hazards": 2},
}

SUPPLEMENTAL_PLATFORM_MAIN_THEMES: dict[str, int] = {
    "industrial": 2,
    "inspection": 2,
    "security": 2,
}

SUPPLEMENTAL_UI_BUTTONS: dict[str, list[tuple[str, str]]] = {
    "pause": [
        ("resume", "ПРОДОЛЖИТЬ"),
        ("sound", "ЗВУК"),
        ("menu", "В МЕНЮ"),
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9а-яё]+", "_", value, flags=re.IGNORECASE)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "asset"


def asset_namespace(slot_name: str) -> str:
    return slug(slot_name)


def ts_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def sorted_source_pngs(source_dir: Path) -> list[Path]:
    return sorted(source_dir.glob("*.png"), key=lambda p: (p.stat().st_mtime, p.name))


def has_real_alpha(img: Image.Image) -> bool:
    alpha = np.array(img.convert("RGBA").getchannel("A"))
    return int(alpha.min()) < 245 and int((alpha < 16).sum()) > 64


def border_background_mask(rgba: np.ndarray) -> np.ndarray:
    rgb = rgba[:, :, :3].astype(np.int16)
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    mean = rgb.mean(axis=2)
    chroma = maxc - minc

    # The supplied sheets usually have a baked gray checkerboard background.
    # A broad "light neutral" flood fill eats parchment, wood, and UI panels,
    # so learn the actual border colors and flood only those gray tiles.
    border_rgb = np.concatenate([
        rgb[0, :, :],
        rgb[-1, :, :],
        rgb[:, 0, :],
        rgb[:, -1, :],
    ], axis=0)
    border_max = border_rgb.max(axis=1)
    border_min = border_rgb.min(axis=1)
    border_mean = border_rgb.mean(axis=1)
    border_chroma = border_max - border_min
    border_bg = border_rgb[(border_mean >= 214) & (border_chroma <= 16)]
    if len(border_bg) == 0:
        border_bg = border_rgb[(border_mean >= 202) & (border_chroma <= 24)]

    if len(border_bg) > 0:
        quantized = ((border_bg // 12) * 12).astype(np.int32)
        packed = quantized[:, 0] * 65536 + quantized[:, 1] * 256 + quantized[:, 2]
        values, counts = np.unique(packed, return_counts=True)
        top = values[np.argsort(counts)[-8:]]
        centers = np.stack([
            top // 65536,
            (top // 256) % 256,
            top % 256,
        ], axis=1).astype(np.int16)
        close_to_border_tile = np.zeros(mean.shape, dtype=bool)
        for center in centers:
            dist = np.abs(rgb - center).max(axis=2)
            close_to_border_tile |= dist <= 24
    else:
        close_to_border_tile = np.zeros(mean.shape, dtype=bool)

    bg_candidate = close_to_border_tile
    count, labels = cv2.connectedComponents(bg_candidate.astype(np.uint8), 8)
    if count <= 1:
        return np.zeros(bg_candidate.shape, dtype=bool)
    border_labels = np.unique(np.concatenate([
        labels[0, :],
        labels[-1, :],
        labels[:, 0],
        labels[:, -1],
    ]))
    border_labels = border_labels[border_labels != 0]
    if len(border_labels) == 0:
        return np.zeros(bg_candidate.shape, dtype=bool)
    background = np.isin(labels, border_labels)
    return background


def foreground_alpha(img: Image.Image) -> tuple[np.ndarray, str]:
    rgba = np.array(img.convert("RGBA"))
    if has_real_alpha(img):
        alpha = rgba[:, :, 3]
        method = "source_alpha"
    else:
        bg = border_background_mask(rgba)
        fg = (~bg).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=1)
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)
        # Pull the edge inward by one pixel before softening. This removes baked
        # checkerboard/white fringe without deleting white highlights inside art.
        core = cv2.erode(fg, kernel, iterations=1)
        alpha = cv2.GaussianBlur((core * 255).astype(np.uint8), (3, 3), 0)
        alpha[fg == 0] = 0
        method = "edge_flood_checkerboard"
    return alpha, method


def clean_rgba(img: Image.Image, alpha: np.ndarray) -> Image.Image:
    rgba = np.array(img.convert("RGBA"))
    rgba[:, :, 3] = alpha
    rgba[alpha <= 2, :3] = 0
    return Image.fromarray(rgba, "RGBA")


def component_boxes(alpha: np.ndarray, min_area: int, max_sheet_fraction: float) -> tuple[np.ndarray, list[Component]]:
    mask = (alpha >= 18).astype(np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    h, w = mask.shape
    boxes: list[Component] = []
    for label in range(1, count):
        x, y, bw, bh, area = [int(v) for v in stats[label]]
        if area < min_area or bw < 24 or bh < 24:
            continue
        if bw * bh > w * h * max_sheet_fraction:
            continue
        boxes.append(Component(label, x, y, bw, bh, area))
    boxes.sort(key=lambda b: (b.y // 46, b.x))
    return labels, boxes


def crop_component(img: Image.Image, alpha: np.ndarray, labels: np.ndarray, component: Component, pad: int) -> Image.Image:
    rgba = np.array(img.convert("RGBA"))
    left = max(0, component.x - pad)
    top = max(0, component.y - pad)
    right = min(img.width, component.x + component.w + pad)
    bottom = min(img.height, component.y + component.h + pad)
    crop = rgba[top:bottom, left:right].copy()
    component_mask = (labels[top:bottom, left:right] == component.label).astype(np.uint8)
    component_mask = cv2.dilate(component_mask, np.ones((3, 3), np.uint8), iterations=1)
    crop_alpha = alpha[top:bottom, left:right].copy()
    crop_alpha[component_mask == 0] = 0
    crop[:, :, 3] = crop_alpha
    crop[crop_alpha <= 2, :3] = 0
    out = Image.fromarray(crop, "RGBA")
    bbox = out.getchannel("A").getbbox()
    if bbox:
        out = out.crop((
            max(0, bbox[0] - 2),
            max(0, bbox[1] - 2),
            min(out.width, bbox[2] + 2),
            min(out.height, bbox[3] + 2),
        ))
    return out


def scaled_layout_cut(cut: SheetLayoutCut, img: Image.Image) -> tuple[int, int, int, int]:
    sx = img.width / 1448
    sy = img.height / 1086
    left = max(0, int(round(cut.x * sx)))
    top = max(0, int(round(cut.y * sy)))
    right = min(img.width, int(round((cut.x + cut.w) * sx)))
    bottom = min(img.height, int(round((cut.y + cut.h) * sy)))
    return left, top, right, bottom


def layout_cut_crop(img: Image.Image, cut: SheetLayoutCut) -> Image.Image:
    left, top, right, bottom = scaled_layout_cut(cut, img)
    crop_img = img.crop((left, top, right, bottom)).convert("RGBA")
    rgba = np.array(crop_img)
    if has_real_alpha(crop_img):
        alpha = rgba[:, :, 3].copy()
    else:
        # Manual UI cuts are intentionally tight. The main menu contains large
        # parchment panels that are close to neutral gray, so use a stricter
        # checkerboard mask than the generic sheet segmentation path.
        rgb = rgba[:, :, :3].astype(np.int16)
        mean = rgb.mean(axis=2)
        chroma = rgb.max(axis=2) - rgb.min(axis=2)
        candidate = (mean >= 218) & (chroma <= 8)
        count, labels = cv2.connectedComponents(candidate.astype(np.uint8), 8)
        if count > 1:
            border_labels = np.unique(np.concatenate([
                labels[0, :],
                labels[-1, :],
                labels[:, 0],
                labels[:, -1],
            ]))
            border_labels = border_labels[border_labels != 0]
            bg = np.isin(labels, border_labels)
            if len(border_labels) == 0:
                bg = np.zeros(candidate.shape, dtype=bool)
        else:
            bg = np.zeros(candidate.shape, dtype=bool)
        fg = (~bg).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=1)
        alpha = cv2.GaussianBlur((fg * 255).astype(np.uint8), (3, 3), 0)
        alpha[fg == 0] = 0
    rgba[:, :, 3] = alpha
    rgba[alpha <= 2, :3] = 0
    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getchannel("A").getbbox()
    if bbox:
        out = out.crop((
            max(0, bbox[0] - 2),
            max(0, bbox[1] - 2),
            min(out.width, bbox[2] + 2),
            min(out.height, bbox[3] + 2),
        ))
    return out


def resize_for_runtime(img: Image.Image, category: str, ui_role: str | None = None) -> Image.Image:
    if ui_role:
        limits = {
            "title": (960, 280),
            "button": (640, 220),
            "card": (660, 430),
            "icon": (300, 300),
            "prop": (500, 500),
        }
        max_w, max_h = limits.get(ui_role, (500, 500))
    else:
        limits = {
            "platforms": (840, 280),
            "hazards": (520, 520),
            "collectibles": (240, 240),
            "bonuses": (280, 280),
            "npc_decor": (420, 520),
            "labels_signage": (560, 300),
            "foreground_decor": (520, 420),
            "background_decor": (760, 520),
            "equipment": (260, 260),
            "ui_achievements": (560, 300),
        }
        max_w, max_h = limits.get(category, (520, 520))
    if img.width <= max_w and img.height <= max_h:
        return img
    scale = min(max_w / img.width, max_h / img.height)
    return img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)


def ensure_transparent_margin(img: Image.Image, margin: int = 4) -> Image.Image:
    rgba = img.convert("RGBA")
    if margin <= 0 or rgba.getchannel("A").getbbox() is None:
        return rgba
    canvas = Image.new("RGBA", (rgba.width + margin * 2, rgba.height + margin * 2), (0, 0, 0, 0))
    canvas.alpha_composite(rgba, (margin, margin))
    return canvas


def load_title_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        Path("C:/Windows/Fonts/impact.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/tahomabd.ttf"),
    ]:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def fit_text_font(text: str, max_w: int, max_h: int, start_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    probe = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    for size in range(start_size, 18, -2):
        font = load_title_font(size)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=max(1, size // 28))
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
    return load_title_font(18)


def repaint_main_menu_title(crop: Image.Image) -> Image.Image:
    rgba = crop.convert("RGBA")
    draw = ImageDraw.Draw(rgba, "RGBA")
    w, h = rgba.size
    wipe = [
        int(w * 0.105),
        int(h * 0.285),
        int(w * 0.89),
        int(h * 0.76),
    ]
    draw.rounded_rectangle(wipe, radius=max(12, int(h * 0.04)), fill=(229, 205, 148, 246))
    for i in range(11):
        x0 = wipe[0] + 18 + i * max(28, (wipe[2] - wipe[0]) // 12)
        y0 = wipe[1] + (i * 17) % max(1, (wipe[3] - wipe[1]))
        draw.line((x0, y0, min(wipe[2] - 12, x0 + 54), max(wipe[1] + 4, y0 - 10)), fill=(112, 72, 43, 42), width=1)
    panel = [
        int(w * 0.205),
        int(h * 0.33),
        int(w * 0.81),
        int(h * 0.69),
    ]
    draw.rounded_rectangle(panel, radius=max(10, int(h * 0.035)), fill=(238, 216, 158, 238))
    draw.rounded_rectangle(panel, radius=max(10, int(h * 0.035)), outline=(116, 76, 44, 160), width=max(2, int(h * 0.012)))
    for i in range(7):
        x0 = panel[0] + 18 + i * max(22, (panel[2] - panel[0]) // 8)
        y0 = panel[1] + (i * 13) % max(1, (panel[3] - panel[1]))
        draw.line((x0, y0, min(panel[2] - 12, x0 + 42), max(panel[1] + 5, y0 - 8)), fill=(119, 74, 44, 58), width=1)
    text = "МАРТЫШКИН ТРУД"
    max_text_w = int((panel[2] - panel[0]) * 0.9)
    max_text_h = int((panel[3] - panel[1]) * 0.72)
    font = fit_text_font(text, max_text_w, max_text_h, int(h * 0.18))
    stroke = max(2, int(h * 0.012))
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = panel[0] + (panel[2] - panel[0] - tw) // 2 - bbox[0]
    ty = panel[1] + (panel[3] - panel[1] - th) // 2 - bbox[1] - int(h * 0.005)
    draw.text((tx + 3, ty + 4), text, font=font, fill=(68, 30, 18, 128), stroke_width=stroke, stroke_fill=(68, 30, 18, 56))
    draw.text((tx, ty), text, font=font, fill=(133, 31, 22, 255), stroke_width=stroke, stroke_fill=(250, 224, 166, 170))
    return rgba


def classify_ui(component: Component) -> str:
    aspect = component.aspect
    if aspect >= 3.7 and component.w >= 360:
        return "title"
    if aspect >= 2.2 and component.w >= 210 and component.h <= 170:
        return "button"
    if component.w >= 260 and component.h >= 110:
        return "card"
    if 0.55 <= aspect <= 1.65 and component.w <= 330 and component.h <= 330:
        return "icon"
    return "prop"


def classify_runtime(slot: dict[str, Any], component: Component, order: int) -> str:
    roles = set(slot.get("roles", []))
    aspect = component.aspect
    if "platforms" in roles and aspect >= 2.05 and component.w >= 155 and component.h <= 330:
        return "platforms"
    if "collectibles" in roles and component.w <= 260 and component.h <= 260 and aspect < 2.2:
        return "collectibles"
    if "signage" in roles and aspect >= 1.35 and component.h <= 260:
        return "hazards"
    if "hazards" in roles:
        return "hazards"
    if "interactive_prop" in roles:
        return "hazards"
    return "foreground_decor"


def role_for_runtime(slot: dict[str, Any], category: str, component: Component, component_order: int, category_order: int) -> str:
    roles = set(slot.get("roles", []))
    if category == "platforms":
        preferred = str(slot.get("platformRole") or "PlatformMain")
        main_count = int(slot.get("platformMainCount") or 4)
        if preferred == "PlatformMain" and category_order <= main_count:
            return "PlatformMain"
        return "PlatformAlt"
    if category == "hazards":
        if "signage" in roles and component.aspect >= 1.35 and component.h <= 260:
            return "Signage"
        if "interactive_prop" in roles:
            return "Obstacle" if category_order <= 3 else "InteractiveProp"
        return "Obstacle"
    if category == "collectibles":
        return "PickupDecor" if "pickup_decor" in roles else "Collectible"
    if category == "labels_signage":
        return "Signage"
    if category == "ui_achievements":
        return "UiSurface"
    if category == "background_decor":
        return "BackgroundProp"
    if category == "foreground_decor":
        return "ForegroundProp"
    if "midground" in roles:
        return "MidgroundProp"
    if "background" in roles:
        return "BackgroundProp"
    if "theme_marker" in roles:
        return "ThemeMarker"
    return "ForegroundProp"


def collision_type_for(category: str, role: str) -> str:
    if category == "platforms":
        return "solid_top"
    if category == "hazards":
        return "damage" if role in {"Obstacle", "InteractiveProp", "Signage"} else "none"
    if category == "collectibles":
        return "pickup"
    if category == "bonuses":
        return "trigger"
    return "none"


def render_layer_for(category: str, role: str) -> str:
    if category == "platforms":
        return "gameplay_platforms"
    if category == "hazards":
        return "gameplay_hazards"
    if category == "collectibles":
        return "gameplay_pickups"
    if category == "labels_signage":
        return "gameplay_signage"
    if role == "BackgroundProp" or category == "background_decor":
        return "background"
    if role == "MidgroundProp":
        return "midground"
    if role == "UiSurface" or category == "ui_achievements":
        return "hud"
    return "foreground"


def rarity_for(slot: dict[str, Any], category: str, category_order: int) -> str:
    tier = str(slot.get("usageTier") or "")
    if tier == "fallback_only":
        return "fallback"
    if category_order <= 3:
        return "common"
    if category in {"platforms", "hazards"} and category_order <= 7:
        return "uncommon"
    return "rare"


def cocos_image_meta(image_path: Path, width: int, height: int) -> dict[str, Any]:
    base_uuid = str(uuid.uuid4())
    half_w = width / 2
    half_h = height / 2
    display = image_path.stem
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
                "displayName": display,
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
                "displayName": display,
                "id": "f9941",
                "name": "spriteFrame",
                "userData": {
                    "trimThreshold": 1,
                    "rotated": False,
                    "offsetX": 0,
                    "offsetY": 0,
                    "trimX": 0,
                    "trimY": 0,
                    "width": width,
                    "height": height,
                    "rawWidth": width,
                    "rawHeight": height,
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
                        "rawPosition": [-half_w, -half_h, 0, half_w, -half_h, 0, -half_w, half_h, 0, half_w, half_h, 0],
                        "indexes": [0, 1, 2, 2, 1, 3],
                        "uv": [0, height, width, height, 0, 0, width, 0],
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
        "userData": {"type": "sprite-frame"},
    }


def write_png_with_meta(path: Path, img: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    path.with_suffix(path.suffix + ".meta").write_text(
        json.dumps(cocos_image_meta(path, img.width, img.height), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def trim_alpha_image(img: Image.Image, pad: int = 2) -> Image.Image:
    rgba = img.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if not bbox:
        return rgba
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(rgba.width, bbox[2] + pad)
    bottom = min(rgba.height, bbox[3] + pad)
    return rgba.crop((left, top, right, bottom))


def dominant_rgba_color(img: Image.Image) -> tuple[int, int, int]:
    rgba = np.array(img.convert("RGBA"))
    mask = rgba[:, :, 3] > 48
    if int(mask.sum()) == 0:
        return (176, 126, 64)
    sample = rgba[:, :, :3][mask]
    rgb = np.median(sample, axis=0)
    return tuple(int(max(0, min(255, v))) for v in rgb[:3])


def scale_to_height(img: Image.Image, max_height: int) -> Image.Image:
    if img.height <= max_height:
        return img
    scale = max_height / max(1, img.height)
    return img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)


def darken(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(int(max(0, min(255, c * factor))) for c in color)


def lighten(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(int(max(0, min(255, 255 - (255 - c) / max(0.01, factor)))) for c in color)


def compose_supplemental_platform(source: Image.Image, variant: int) -> Image.Image:
    base = scale_to_height(trim_alpha_image(source), 118)
    target_w = max(380, min(740, int(base.width * (2.35 if base.width < 280 else 1.42))))
    target_h = max(112, min(190, base.height + 44))
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    color = dominant_rgba_color(base)
    shade = darken(color, 0.56)
    draw = ImageDraw.Draw(canvas)
    rail_y = target_h - 38
    draw.rounded_rectangle([12, rail_y, target_w - 12, target_h - 14], radius=14, fill=(*shade, 92), outline=(*color, 132), width=2)
    for x in range(34 + (variant % 2) * 11, target_w - 28, 72):
        draw.ellipse([x - 5, rail_y + 7, x + 5, rail_y + 17], fill=(*darken(color, 0.82), 142))

    shadow_alpha = base.getchannel("A").filter(ImageFilter.GaussianBlur(5))
    shadow = Image.new("RGBA", base.size, (*darken(color, 0.28), 105))
    shadow.putalpha(shadow_alpha)

    paste_y = max(0, target_h - base.height - 22)
    if base.width >= target_w * 0.68:
        paste_x = (target_w - base.width) // 2
        canvas.alpha_composite(shadow, (paste_x + 4, paste_y + 8))
        canvas.alpha_composite(base, (paste_x, paste_y))
    else:
        step = max(48, int(base.width * 0.68))
        count = max(2, math.ceil((target_w - 36) / step))
        start = max(8, (target_w - (count - 1) * step - base.width) // 2)
        for idx in range(count):
            segment = base
            if idx % 2 == 1 and variant % 2 == 1:
                segment = base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            x = int(start + idx * step)
            canvas.alpha_composite(shadow, (x + 4, paste_y + 8))
            canvas.alpha_composite(segment, (x, paste_y))
    return trim_alpha_image(canvas, 0)


def ensure_supplemental_platforms(project_root: Path, entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    supplemental: list[dict[str, Any]] = []
    for theme, required_main_count in SUPPLEMENTAL_PLATFORM_MAIN_THEMES.items():
        theme_platforms = [
            entry for entry in entries
            if entry.get("theme") == theme and entry.get("category") == "platforms" and entry.get("runtimeEnabled", True)
        ]
        current_main = sum(1 for entry in theme_platforms if entry.get("assetType") == "PlatformMain" or entry.get("role") == "PlatformMain")
        needed = max(0, required_main_count - current_main)
        if needed <= 0:
            continue
        if not theme_platforms:
            warnings.append(f"Theme {theme} needs {needed} supplemental PlatformMain assets but has no source platform cutouts")
            continue
        bases_by_slot: list[dict[str, Any]] = []
        seen_slots: set[str] = set()
        for entry in theme_platforms:
            source_slot = str(entry.get("sourceSlot") or "")
            if source_slot in seen_slots:
                continue
            seen_slots.add(source_slot)
            bases_by_slot.append(entry)
        source_bases = bases_by_slot or theme_platforms
        for idx in range(needed):
            base_entry = source_bases[idx % len(source_bases)]
            base_path = Path(str(base_entry.get("runtimeFile") or ""))
            if not base_path.exists():
                warnings.append(f"Supplemental platform source is missing: {base_path}")
                continue
            img = ensure_transparent_margin(compose_supplemental_platform(Image.open(base_path).convert("RGBA"), idx + 1))
            levels = sorted({int(level) for level in base_entry.get("levels", [])})
            asset_id = f"mtr_last_{theme}_supplemental_platform_main_{idx + 1:02d}"
            folder = Path(theme) / CATEGORY_TO_FOLDER["platforms"]
            out_rel = RUNTIME_ROOT / folder / f"{asset_id}.png"
            out_abs = project_root / out_rel
            write_png_with_meta(out_abs, img)
            source_runtime_px = [int(v) for v in base_entry.get("runtimePx", [img.width, img.height])]
            supplemental.append({
                "sheetIndex": 900 + idx,
                "sourceSlot": str(base_entry.get("sourceSlot") or f"{theme}_supplemental"),
                "sourceFile": str(base_entry.get("sourceFile") or base_path),
                "sourceSha256": str(base_entry.get("sourceSha256") or sha256(base_path)),
                "sourceCutoutMethod": f"supplemental_style_matched_composite:{base_entry.get('runtimeResourceKey')}",
                "theme": theme,
                "levels": levels,
                "levelAffinity": [f"lvl{level:02d}" for level in levels],
                "surface": "",
                "category": "platforms",
                "role": "PlatformMain",
                "assetType": "PlatformMain",
                "uiRole": "",
                "sourceSetRu": str(base_entry.get("sourceSetRu") or f"{theme}_supplemental"),
                "usageTier": "supplemental_theme",
                "collisionType": "solid_top",
                "renderLayer": "gameplay_platforms",
                "rarity": "common",
                "atlasGroup": str(base_entry.get("atlasGroup") or f"atlas_{theme}"),
                "componentIndex": 900 + idx,
                "sourceCanvasPx": source_runtime_px,
                "sourceBoundsPx": [0, 0, source_runtime_px[0], source_runtime_px[1]],
                "sourceAreaPx": int(np.array(img.getchannel("A")).astype(bool).sum()),
                "runtimeFile": str(out_abs),
                "runtimeResourceKey": f"{RESOURCE_PREFIX}/{folder.as_posix()}/{asset_id}",
                "runtimePx": [img.width, img.height],
                "logicalType": None,
                "critical": True,
                "runtimeEnabled": True,
                "runtimeSha256": sha256(out_abs),
            })
    return supplemental, warnings


def compose_supplemental_ui_button(source: Image.Image, label: str, variant: int) -> Image.Image:
    base = trim_alpha_image(source.convert("RGBA"))
    color = dominant_rgba_color(base)
    paper = lighten(color, 1.26)
    edge = darken(color, 0.55)
    shadow = darken(color, 0.28)
    accent = (238, 186, 55) if variant % 2 else (216, 97, 65)
    target_w, target_h = 560, 156
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    body = [16, 18, target_w - 16, target_h - 18]
    draw.rounded_rectangle([body[0] + 8, body[1] + 9, body[2] + 8, body[3] + 9], radius=28, fill=(*shadow, 96))
    draw.rounded_rectangle(body, radius=28, fill=(*paper, 244), outline=(*edge, 230), width=5)
    draw.rounded_rectangle([body[0] + 8, body[1] + 8, body[2] - 8, body[3] - 8], radius=22, outline=(*lighten(color, 1.55), 150), width=2)

    stripe_w = 74
    stripe_box = [body[0] + 14, body[1] + 12, body[0] + stripe_w, body[3] - 12]
    draw.rounded_rectangle(stripe_box, radius=18, fill=(*darken(accent, 0.82), 205), outline=(*edge, 155), width=2)
    for i in range(-2, 7):
        x0 = stripe_box[0] + i * 22
        draw.line((x0, stripe_box[3], x0 + 58, stripe_box[1]), fill=(255, 236, 128, 132), width=9)

    bolt_r = 11
    for bx in (body[0] + 22, body[2] - 22):
        for by in (body[1] + 20, body[3] - 20):
            draw.ellipse([bx - bolt_r, by - bolt_r, bx + bolt_r, by + bolt_r], fill=(*darken(color, 0.46), 180), outline=(*lighten(color, 1.4), 120), width=2)

    text_font = fit_text_font(label, target_w - 150, target_h - 64, 48)
    stroke = 3
    bbox = draw.textbbox((0, 0), label, font=text_font, stroke_width=stroke)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = body[0] + stripe_w + (body[2] - body[0] - stripe_w - tw) // 2 - bbox[0]
    ty = body[1] + (body[3] - body[1] - th) // 2 - bbox[1] - 2
    draw.text((tx + 3, ty + 4), label, font=text_font, fill=(70, 42, 24, 118), stroke_width=stroke, stroke_fill=(70, 42, 24, 44))
    draw.text((tx, ty), label, font=text_font, fill=(*edge, 255), stroke_width=stroke, stroke_fill=(*lighten(color, 1.62), 188))
    return trim_alpha_image(canvas, 0)


def ensure_supplemental_ui_assets(project_root: Path, entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    supplemental: list[dict[str, Any]] = []
    for surface, buttons in SUPPLEMENTAL_UI_BUTTONS.items():
        existing = [
            entry for entry in entries
            if entry.get("surface") == surface and entry.get("uiRole") == "button" and entry.get("runtimeEnabled", True)
        ]
        needed = max(0, len(buttons) - len(existing))
        if needed <= 0:
            continue
        bases = [
            entry for entry in entries
            if entry.get("surface") == surface and entry.get("uiRole") in {"card", "title", "icon"} and entry.get("runtimeEnabled", True)
        ]
        if not bases:
            warnings.append(f"UI surface {surface} needs {needed} supplemental buttons but has no style source")
            continue
        for idx, (semantic, label) in enumerate(buttons[len(existing):], start=len(existing) + 1):
            base_entry = bases[(idx - 1) % len(bases)]
            base_path = Path(str(base_entry.get("runtimeFile") or ""))
            if not base_path.exists():
                warnings.append(f"Supplemental UI source is missing: {base_path}")
                continue
            img = ensure_transparent_margin(compose_supplemental_ui_button(Image.open(base_path).convert("RGBA"), label, idx))
            asset_id = f"mtr_last_{surface}_supplemental_button_{semantic}_{idx:02d}"
            folder = Path("ui") / surface / "button"
            out_rel = RUNTIME_ROOT / folder / f"{asset_id}.png"
            out_abs = project_root / out_rel
            write_png_with_meta(out_abs, img)
            source_runtime_px = [int(v) for v in base_entry.get("runtimePx", [img.width, img.height])]
            supplemental.append({
                "sheetIndex": 940 + idx,
                "sourceSlot": str(base_entry.get("sourceSlot") or f"ui_{surface}"),
                "sourceFile": str(base_entry.get("sourceFile") or base_path),
                "sourceSha256": str(base_entry.get("sourceSha256") or sha256(base_path)),
                "sourceCutoutMethod": f"supplemental_style_matched_ui_button:{base_entry.get('runtimeResourceKey')}",
                "theme": "ui",
                "levels": [],
                "levelAffinity": [],
                "surface": surface,
                "category": "ui_achievements",
                "role": "UiButton",
                "assetType": "UiButton",
                "uiRole": "button",
                "sourceSetRu": str(base_entry.get("sourceSetRu") or f"ui_{surface}"),
                "usageTier": "supplemental_ui",
                "collisionType": "none",
                "renderLayer": "hud",
                "rarity": "common",
                "atlasGroup": str(base_entry.get("atlasGroup") or f"atlas_ui_{surface}"),
                "componentIndex": 940 + idx,
                "sourceCanvasPx": source_runtime_px,
                "sourceBoundsPx": [0, 0, source_runtime_px[0], source_runtime_px[1]],
                "sourceAreaPx": int(np.array(img.getchannel("A")).astype(bool).sum()),
                "runtimeFile": str(out_abs),
                "runtimeResourceKey": f"{RESOURCE_PREFIX}/{folder.as_posix()}/{asset_id}",
                "runtimePx": [img.width, img.height],
                "logicalType": None,
                "critical": True,
                "runtimeEnabled": True,
                "runtimeSha256": sha256(out_abs),
            })
    return supplemental, warnings


def checkerboard(size: tuple[int, int], tile: int = 12) -> Image.Image:
    out = Image.new("RGBA", size, (25, 25, 25, 255))
    draw = ImageDraw.Draw(out)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            fill = (58, 58, 58, 255) if ((x // tile + y // tile) % 2) else (30, 30, 30, 255)
            draw.rectangle([x, y, min(size[0], x + tile), min(size[1], y + tile)], fill=fill)
    return out


def contact_sheet(entries: list[dict[str, Any]], output: Path, limit: int = 240) -> None:
    if not entries:
        return
    entries = entries[:limit]
    tile_w, tile_h = 220, 184
    cols = 5
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGBA", (cols * tile_w, rows * tile_h), (18, 18, 18, 255))
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(sheet)
    for idx, entry in enumerate(entries):
        image_path = Path(entry["runtimeFile"])
        if not image_path.exists():
            continue
        img = Image.open(image_path).convert("RGBA")
        bg = checkerboard((tile_w, tile_h - 42))
        img.thumbnail((tile_w - 18, tile_h - 58), Image.Resampling.LANCZOS)
        bg.alpha_composite(img, ((tile_w - img.width) // 2, (tile_h - 42 - img.height) // 2))
        x = (idx % cols) * tile_w
        y = (idx // cols) * tile_h
        sheet.alpha_composite(bg, (x, y))
        label = f"{entry.get('surface') or entry['theme']} {entry['category']}"
        draw.text((x + 6, y + tile_h - 37), label[:34], fill=(245, 230, 170, 255), font=font)
        draw.text((x + 6, y + tile_h - 21), image_path.stem[:35], fill=(208, 224, 235, 255), font=font)
        draw.text((x + 6, y + tile_h - 10), f"sheet {entry['sheetIndex']:02d} #{entry['componentIndex']:02d}", fill=(164, 184, 190, 255), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def process_layout_sheet(
    project_root: Path,
    source: Path,
    slot: dict[str, Any],
    sheet_index: int,
    cuts: list[SheetLayoutCut],
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    img = Image.open(source).convert("RGBA")
    source_hash = sha256(source)
    entries: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
    surface = str(slot["surface"])
    slot_name = str(slot["slot"])
    for order, cut in enumerate(cuts, start=1):
        crop = layout_cut_crop(img, cut)
        if crop.width < 16 or crop.height < 16 or crop.getchannel("A").getbbox() is None:
            warnings.append(f"{source.name}: layout cut {slot_name}.{cut.name} is empty")
            continue
        ui_role = cut.role
        category = "ui_achievements"
        role_counts[ui_role] = role_counts.get(ui_role, 0) + 1
        role = f"Ui{ui_role.title()}"
        asset_id = f"mtr_last_{slug(surface)}_{asset_namespace(slot_name)}_{slug(cut.name)}_{role_counts[ui_role]:02d}"
        crop = resize_for_runtime(crop, category, ui_role)
        if slot_name == "ui_main_menu" and cut.name == "main_title":
            crop = repaint_main_menu_title(crop)
        crop = ensure_transparent_margin(crop)
        folder = Path("ui") / surface / ui_role
        out_rel = RUNTIME_ROOT / folder / f"{asset_id}.png"
        out_abs = project_root / out_rel
        write_png_with_meta(out_abs, crop)
        left, top, right, bottom = scaled_layout_cut(cut, img)
        runtime_key = f"{RESOURCE_PREFIX}/{folder.as_posix()}/{asset_id}"
        entries.append({
            "sheetIndex": sheet_index,
            "sourceSlot": slot_name,
            "sourceFile": str(source),
            "sourceSha256": source_hash,
            "sourceCutoutMethod": f"layout_profile_checkerboard_flood:{slot_name}",
            "theme": "ui",
            "levels": [],
            "levelAffinity": [],
            "surface": surface,
            "category": category,
            "role": role,
            "assetType": role,
            "uiRole": ui_role,
            "sourceSetRu": str(slot.get("sourceSetRu") or slot_name),
            "usageTier": str(slot.get("usageTier") or "ui_surface"),
            "collisionType": "none",
            "renderLayer": "hud",
            "rarity": rarity_for(slot, category, role_counts[ui_role]),
            "atlasGroup": str(slot.get("atlasGroup") or f"atlas_ui_{surface}"),
            "componentIndex": order,
            "sourceCanvasPx": [img.width, img.height],
            "sourceBoundsPx": [left, top, right - left, bottom - top],
            "sourceAreaPx": int(np.array(crop.getchannel("A")).astype(bool).sum()),
            "runtimeFile": str(out_abs),
            "runtimeResourceKey": runtime_key,
            "runtimePx": [crop.width, crop.height],
            "logicalType": None,
            "critical": cut.critical,
            "runtimeEnabled": True,
            "runtimeSha256": sha256(out_abs),
        })
    return entries, warnings


def process_sheet(project_root: Path, source: Path, slot: dict[str, Any], sheet_index: int, args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[str]]:
    if slot.get("segmentationMode") == "layout":
        slot_name = str(slot.get("slot"))
        cuts = UI_LAYOUT_CUTS_BY_SLOT.get(slot_name)
        if not cuts:
            return [], [f"{source.name}: segmentationMode=layout but no layout profile for {slot_name}"]
        return process_layout_sheet(project_root, source, slot, sheet_index, cuts)

    warnings: list[str] = []
    img = Image.open(source).convert("RGBA")
    alpha, cutout_method = foreground_alpha(img)
    cleaned = clean_rgba(img, alpha)
    labels, boxes = component_boxes(alpha, args.min_area, args.max_sheet_fraction)
    if len(boxes) < 2:
        warnings.append(f"{source.name}: suspiciously few components extracted ({len(boxes)})")

    entries: list[dict[str, Any]] = []
    is_ui = "ui" in slot.get("roles", [])
    hazard_pool = HAZARD_TYPES_BY_THEME.get(slot["theme"], HAZARD_TYPES_BY_THEME["shared"])
    hazard_counter = 0
    role_counts: dict[str, int] = {}
    for order, component in enumerate(boxes, start=1):
        crop = crop_component(cleaned, alpha, labels, component, args.pad)
        if is_ui:
            ui_role = classify_ui(component)
            category = "ui_achievements"
            runtime_theme = "ui"
            folder = Path("ui") / str(slot["surface"]) / ui_role
            role = f"Ui{ui_role.title()}"
            role_counts[ui_role] = role_counts.get(ui_role, 0) + 1
            asset_id = f"mtr_last_{slug(slot['surface'])}_{asset_namespace(str(slot['slot']))}_{ui_role}_{role_counts[ui_role]:02d}"
            logical_type = None
            levels: list[int] = []
            level_affinity: list[str] = []
            surface = str(slot["surface"])
            critical = surface in {"main_menu", "pause", "death"} and role_counts[ui_role] <= 2
            crop = ensure_transparent_margin(resize_for_runtime(crop, category, ui_role))
        else:
            category = classify_runtime(slot, component, order)
            runtime_theme = str(slot["theme"])
            folder = Path(runtime_theme) / CATEGORY_TO_FOLDER[category]
            role_counts[category] = role_counts.get(category, 0) + 1
            category_order = role_counts[category]
            role = role_for_runtime(slot, category, component, order, category_order)
            asset_id = f"mtr_last_{asset_namespace(str(slot['slot']))}_{CATEGORY_TO_FOLDER[category]}_{role_counts[category]:03d}"
            levels = [int(v) for v in slot.get("levels", [])]
            level_affinity = [f"lvl{level:02d}" for level in levels]
            surface = ""
            critical = category in {"platforms", "hazards"} and role_counts[category] <= 3 and runtime_theme != "shared"
            logical_type = None
            if category == "hazards":
                logical_type = hazard_pool[hazard_counter % len(hazard_pool)]
                hazard_counter += 1
            crop = ensure_transparent_margin(resize_for_runtime(crop, category))

        out_rel = RUNTIME_ROOT / folder / f"{asset_id}.png"
        out_abs = project_root / out_rel
        write_png_with_meta(out_abs, crop)
        runtime_key = f"{RESOURCE_PREFIX}/{folder.as_posix()}/{asset_id}"
        entry = {
            "sheetIndex": sheet_index,
            "sourceSlot": slot["slot"],
            "sourceFile": str(source),
            "sourceSha256": sha256(source),
            "sourceCutoutMethod": cutout_method,
            "theme": runtime_theme,
            "levels": levels,
            "levelAffinity": level_affinity,
            "surface": surface,
            "category": category,
            "role": role,
            "assetType": role,
            "uiRole": ui_role if is_ui else "",
            "sourceSetRu": str(slot.get("sourceSetRu") or slot["slot"]),
            "usageTier": str(slot.get("usageTier") or "primary_theme"),
            "collisionType": collision_type_for(category, role),
            "renderLayer": render_layer_for(category, role),
            "rarity": rarity_for(slot, category, role_counts[ui_role if is_ui else category]),
            "atlasGroup": str(slot.get("atlasGroup") or f"atlas_{runtime_theme}"),
            "componentIndex": order,
            "sourceCanvasPx": [img.width, img.height],
            "sourceBoundsPx": [component.x, component.y, component.w, component.h],
            "sourceAreaPx": component.area,
            "runtimeFile": str(out_abs),
            "runtimeResourceKey": runtime_key,
            "runtimePx": [crop.width, crop.height],
            "logicalType": logical_type,
            "critical": critical,
            "runtimeEnabled": True,
            "runtimeSha256": sha256(out_abs),
        }
        entries.append(entry)
    return entries, warnings


def string_array(values: list[str]) -> str:
    return "[" + ", ".join(ts_quote(v) for v in dict.fromkeys(values)) + "]"


def write_generated_ts(entries: list[dict[str, Any]], output_path: Path) -> None:
    runtime_entries = [e for e in entries if e.get("runtimeEnabled", True)]
    gameplay_entries = [e for e in runtime_entries if not e.get("surface")]
    ui_entries = [e for e in runtime_entries if e.get("surface")]
    all_keys = [e["runtimeResourceKey"] for e in runtime_entries]
    platforms_by_level: dict[int, list[str]] = {}
    hazards_by_level_type: dict[str, list[str]] = {}
    ui_by_surface_role: dict[str, list[str]] = {}
    for e in gameplay_entries:
        key = e["runtimeResourceKey"]
        for level in e.get("levels", []):
            level = int(level)
            if e["category"] == "platforms":
                platforms_by_level.setdefault(level, []).append(key)
            elif e["category"] == "hazards":
                logical = e.get("logicalType")
                exact_key = f"{level}:{logical if logical is not None else '*'}"
                hazards_by_level_type.setdefault(exact_key, []).append(key)
                hazards_by_level_type.setdefault(f"{level}:*", []).append(key)
    for e in ui_entries:
        surface = str(e["surface"])
        role = str(e["uiRole"] or "*")
        key = e["runtimeResourceKey"]
        ui_by_surface_role.setdefault(f"{surface}:{role}", []).append(key)
        ui_by_surface_role.setdefault(f"{surface}:*", []).append(key)

    asset_lines: list[str] = []
    for e in gameplay_entries:
        levels = ", ".join(str(int(v)) for v in e.get("levels", []))
        level_affinity = ", ".join(ts_quote(str(v)) for v in e.get("levelAffinity", []))
        logical = "" if e.get("logicalType") is None else f", logicalType: {int(e['logicalType'])}"
        critical_flag = ", critical: true" if e.get("critical") else ""
        asset_lines.append(
            "    { "
            f"key: {ts_quote(e['runtimeResourceKey'])}, "
            f"category: {ts_quote(e['category'])} as ThemeRuntimeCategory, "
            f"theme: {ts_quote(e['theme'])}, "
            f"levels: [{levels}], "
            f"levelAffinity: [{level_affinity}], "
            f"sourceSlot: {ts_quote(e['sourceSlot'])}, "
            f"sourceSetRu: {ts_quote(e.get('sourceSetRu') or '')}, "
            f"role: {ts_quote(e['role'])}, "
            f"assetType: {ts_quote(e.get('assetType') or e['role'])}, "
            f"collisionType: {ts_quote(e.get('collisionType') or '')}, "
            f"renderLayer: {ts_quote(e.get('renderLayer') or '')}, "
            f"rarity: {ts_quote(e.get('rarity') or '')}, "
            f"atlasGroup: {ts_quote(e.get('atlasGroup') or '')}, "
            f"usageTier: {ts_quote(e.get('usageTier') or '')}"
            f"{logical}{critical_flag} "
            "},"
        )

    ui_lines: list[str] = []
    for e in ui_entries:
        critical_flag = ", critical: true" if e.get("critical") else ""
        ui_lines.append(
            "    { "
            f"key: {ts_quote(e['runtimeResourceKey'])}, "
            f"surface: {ts_quote(e['surface'])}, "
            f"role: {ts_quote(e['uiRole'])} as ThemedUiAssetRole, "
            f"sourceSlot: {ts_quote(e['sourceSlot'])}, "
            f"sourceSetRu: {ts_quote(e.get('sourceSetRu') or '')}, "
            f"assetType: {ts_quote(e.get('assetType') or e['role'])}, "
            f"collisionType: {ts_quote(e.get('collisionType') or 'none')}, "
            f"renderLayer: {ts_quote(e.get('renderLayer') or 'hud')}, "
            f"rarity: {ts_quote(e.get('rarity') or 'common')}, "
            f"atlasGroup: {ts_quote(e.get('atlasGroup') or '')}, "
            f"usageTier: {ts_quote(e.get('usageTier') or 'ui_surface')}, "
            f"width: {int(e['runtimePx'][0])}, height: {int(e['runtimePx'][1])}, index: {int(e['componentIndex'])}"
            f"{critical_flag} "
            "},"
        )

    platform_lines = [f"    {level}: {string_array(keys)}," for level, keys in sorted(platforms_by_level.items())]
    hazard_lines = [f"    {ts_quote(key)}: {string_array(keys)}," for key, keys in sorted(hazards_by_level_type.items())]
    ui_map_lines = [f"    {ts_quote(key)}: {string_array(keys)}," for key, keys in sorted(ui_by_surface_role.items())]
    text = f"""export type ThemeRuntimeCategory =
    | 'platforms'
    | 'hazards'
    | 'collectibles'
    | 'bonuses'
    | 'npc_decor'
    | 'labels_signage'
    | 'foreground_decor'
    | 'background_decor'
    | 'equipment'
    | 'ui_achievements';

export type ThemedUiAssetRole = 'title' | 'button' | 'card' | 'icon' | 'prop';

export interface ThemeAssetEntry {{
    key: string;
    category: ThemeRuntimeCategory;
    theme: string;
    levels: readonly number[];
    levelAffinity: readonly string[];
    sourceSlot: string;
    sourceSetRu: string;
    role: string;
    assetType: string;
    collisionType: string;
    renderLayer: string;
    rarity: string;
    atlasGroup: string;
    usageTier: string;
    logicalType?: number;
    runtimeEnabled?: boolean;
    critical?: boolean;
}}

export interface ThemedUiAssetEntry {{
    key: string;
    surface: string;
    role: ThemedUiAssetRole;
    sourceSlot: string;
    sourceSetRu: string;
    assetType: string;
    collisionType: string;
    renderLayer: string;
    rarity: string;
    atlasGroup: string;
    usageTier: string;
    width: number;
    height: number;
    index: number;
    critical?: boolean;
}}

// Generated by tools/mtr_last_iteration_asset_pipeline.py from the latest 30-sheet texture drop.
export const THEMED_ASSET_CATALOG_VERSION = 'generated-{datetime.now().strftime("%Y%m%d-%H%M%S")}';
export const THEMED_ASSET_ENTRIES: readonly ThemeAssetEntry[] = [
{chr(10).join(asset_lines)}
];

export const THEMED_UI_ASSET_ENTRIES: readonly ThemedUiAssetEntry[] = [
{chr(10).join(ui_lines)}
];

export const THEMED_PLATFORM_KEYS_BY_LEVEL: Record<number, readonly string[]> = {{
{chr(10).join(platform_lines)}
}};

export const THEMED_HAZARD_KEYS_BY_LEVEL_AND_TYPE: Record<string, readonly string[]> = {{
{chr(10).join(hazard_lines)}
}};

export const THEMED_UI_KEYS_BY_SURFACE_AND_ROLE: Record<string, readonly string[]> = {{
{chr(10).join(ui_map_lines)}
}};

function unique(keys: readonly string[]): string[] {{
    const seen: Record<string, boolean> = {{}};
    const result: string[] = [];
    for (const key of keys) {{
        if (!key || seen[key]) continue;
        seen[key] = true;
        result.push(key);
    }}
    return result;
}}

export const THEMED_ALL_RUNTIME_KEYS: readonly string[] = unique([
    ...THEMED_ASSET_ENTRIES.filter((entry) => entry.runtimeEnabled !== false).map((entry) => entry.key),
    ...THEMED_UI_ASSET_ENTRIES.map((entry) => entry.key),
]);

export function themedAssetKeysForLevel(levelIndex: number, category?: ThemeRuntimeCategory): string[] {{
    const levelNumber = levelIndex + 1;
    return unique(THEMED_ASSET_ENTRIES
        .filter((entry) => entry.runtimeEnabled !== false)
        .filter((entry) => !category || entry.category === category)
        .filter((entry) => entry.levels.includes(levelNumber))
        .map((entry) => entry.key));
}}

export function themedPlatformKeysForLevel(levelIndex: number): string[] {{
    const mapped = THEMED_PLATFORM_KEYS_BY_LEVEL[levelIndex + 1];
    if (mapped && mapped.length) return unique(mapped);
    return themedAssetKeysForLevel(levelIndex, 'platforms');
}}

export function themedObstacleKeysForType(levelIndex: number, obstacleType: number): string[] {{
    const levelNumber = levelIndex + 1;
    const exact = THEMED_HAZARD_KEYS_BY_LEVEL_AND_TYPE[`${{levelNumber}}:${{obstacleType}}`];
    if (exact && exact.length) return unique(exact);
    const wildcard = THEMED_HAZARD_KEYS_BY_LEVEL_AND_TYPE[`${{levelNumber}}:*`];
    if (wildcard && wildcard.length) return unique(wildcard);
    return unique(THEMED_ASSET_ENTRIES
        .filter((entry) => entry.runtimeEnabled !== false && entry.category === 'hazards')
        .filter((entry) => entry.levels.includes(levelNumber))
        .filter((entry) => entry.logicalType === undefined || entry.logicalType === obstacleType)
        .map((entry) => entry.key));
}}

export function themedUiAssetKeysForSurface(surface: string, role?: ThemedUiAssetRole): string[] {{
    const exact = role ? THEMED_UI_KEYS_BY_SURFACE_AND_ROLE[`${{surface}}:${{role}}`] : undefined;
    if (exact && exact.length) return unique(exact);
    const wildcard = THEMED_UI_KEYS_BY_SURFACE_AND_ROLE[`${{surface}}:*`];
    if (wildcard && wildcard.length) return unique(wildcard);
    return unique(THEMED_UI_ASSET_ENTRIES
        .filter((entry) => entry.surface === surface)
        .filter((entry) => !role || entry.role === role)
        .sort((a, b) => a.index - b.index)
        .map((entry) => entry.key));
}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def increment_nested_count(target: dict[str, dict[str, int]], outer: str, inner: str) -> None:
    if outer not in target:
        target[outer] = {}
    target[outer][inner] = target[outer].get(inner, 0) + 1


def summarize_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_theme_category: dict[str, dict[str, int]] = {}
    by_theme_asset_type: dict[str, dict[str, int]] = {}
    by_surface_role: dict[str, dict[str, int]] = {}
    by_level_source_slot: dict[str, dict[str, int]] = {}
    by_level_category: dict[str, dict[str, int]] = {}
    by_level_asset_type: dict[str, dict[str, int]] = {}
    runtime_enabled = 0
    critical = 0
    for entry in entries:
        if entry.get("runtimeEnabled"):
            runtime_enabled += 1
        if entry.get("critical"):
            critical += 1
        theme = str(entry.get("theme") or "unknown")
        category = str(entry.get("category") or "unknown")
        asset_type = str(entry.get("assetType") or entry.get("role") or "unknown")
        increment_nested_count(by_theme_category, theme, category)
        increment_nested_count(by_theme_asset_type, theme, asset_type)
        for level in entry.get("levels", []):
            level_key = f"lvl{int(level):02d}"
            increment_nested_count(by_level_source_slot, level_key, str(entry.get("sourceSlot") or "unknown"))
            increment_nested_count(by_level_category, level_key, category)
            increment_nested_count(by_level_asset_type, level_key, asset_type)
        surface = entry.get("surface")
        ui_role = entry.get("uiRole")
        if surface and ui_role:
            increment_nested_count(by_surface_role, str(surface), str(ui_role))
    return {
        "runtimeEnabled": runtime_enabled,
        "critical": critical,
        "byThemeCategory": by_theme_category,
        "byThemeAssetType": by_theme_asset_type,
        "bySurfaceRole": by_surface_role,
        "byLevelSourceSlot": by_level_source_slot,
        "byLevelCategory": by_level_category,
        "byLevelAssetType": by_level_asset_type,
    }


def validate_entries(entries: list[dict[str, Any]], source_count: int) -> tuple[dict[str, Any], list[str]]:
    summary = summarize_entries(entries)
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    checks.append({
        "scope": "source_sheets",
        "name": "mapped_sheet_count",
        "required": len(SHEET_SLOTS),
        "actual": source_count,
        "passed": source_count == len(SHEET_SLOTS),
    })

    runtime_keys = [str(entry.get("runtimeResourceKey") or "") for entry in entries if entry.get("runtimeEnabled", True)]
    duplicate_runtime_key_count = len(runtime_keys) - len(set(runtime_keys))
    checks.append({
        "scope": "runtime_catalog",
        "name": "unique_runtime_keys",
        "required": len(runtime_keys),
        "actual": len(set(runtime_keys)),
        "passed": duplicate_runtime_key_count == 0,
    })
    if duplicate_runtime_key_count:
        warnings.append(f"Runtime catalog has {duplicate_runtime_key_count} duplicate resource keys")

    hash_mismatches = 0
    missing_runtime_files = 0
    for entry in entries:
        runtime_file = Path(str(entry.get("runtimeFile") or ""))
        expected_sha = str(entry.get("runtimeSha256") or "")
        if not runtime_file.exists():
            missing_runtime_files += 1
            continue
        if expected_sha and sha256(runtime_file) != expected_sha:
            hash_mismatches += 1
    checks.append({
        "scope": "runtime_catalog",
        "name": "runtime_files_exist",
        "required": len(entries),
        "actual": len(entries) - missing_runtime_files,
        "passed": missing_runtime_files == 0,
    })
    checks.append({
        "scope": "runtime_catalog",
        "name": "runtime_sha256_matches",
        "required": 0,
        "actual": hash_mismatches,
        "passed": hash_mismatches == 0,
    })
    if missing_runtime_files:
        warnings.append(f"Runtime catalog is missing {missing_runtime_files} files")
    if hash_mismatches:
        warnings.append(f"Runtime catalog has {hash_mismatches} SHA256 mismatches")

    surface_counts: dict[str, dict[str, int]] = summary["bySurfaceRole"]
    for surface, roles in REQUIRED_UI_SURFACE_ROLES.items():
        for role, required in roles.items():
            actual = surface_counts.get(surface, {}).get(role, 0)
            passed = actual >= required
            checks.append({
                "scope": f"ui_surface:{surface}",
                "name": role,
                "required": required,
                "actual": actual,
                "passed": passed,
            })
            if not passed:
                warnings.append(f"UI surface {surface} has {actual} {role} assets, expected at least {required}")

    theme_counts: dict[str, dict[str, int]] = summary["byThemeCategory"]
    for theme, categories in REQUIRED_THEME_CATEGORY_MINIMUMS.items():
        for category, required in categories.items():
            actual = theme_counts.get(theme, {}).get(category, 0)
            passed = actual >= required
            checks.append({
                "scope": f"theme:{theme}",
                "name": category,
                "required": required,
                "actual": actual,
                "passed": passed,
            })
            if not passed:
                warnings.append(f"Theme {theme} has {actual} {category} assets, expected at least {required}")

    level_source_slots: dict[str, dict[str, int]] = summary["byLevelSourceSlot"]
    level_categories: dict[str, dict[str, int]] = summary["byLevelCategory"]
    level_asset_types: dict[str, dict[str, int]] = summary["byLevelAssetType"]
    for level in range(1, 16):
        level_key = f"lvl{level:02d}"
        slot_count = len(level_source_slots.get(level_key, {}))
        slot_passed = 2 <= slot_count <= 4
        checks.append({
            "scope": f"level_pool:{level_key}",
            "name": "source_slot_count",
            "required": "2..4",
            "actual": slot_count,
            "passed": slot_passed,
        })
        if not slot_passed:
            warnings.append(f"Level {level_key} uses {slot_count} source slots; expected a focused 2-4 set mini-pool")
        for category, required in {"platforms": 1, "hazards": 1}.items():
            actual = level_categories.get(level_key, {}).get(category, 0)
            passed = actual >= required
            checks.append({
                "scope": f"level_pool:{level_key}",
                "name": category,
                "required": required,
                "actual": actual,
                "passed": passed,
            })
            if not passed:
                warnings.append(f"Level {level_key} has {actual} {category} assets after thematic mapping")
        for asset_type, required in {"PlatformMain": 1, "PlatformAlt": 1}.items():
            actual = level_asset_types.get(level_key, {}).get(asset_type, 0)
            passed = actual >= required
            checks.append({
                "scope": f"level_pool:{level_key}",
                "name": asset_type,
                "required": required,
                "actual": actual,
                "passed": passed,
            })
            if not passed:
                warnings.append(f"Level {level_key} has {actual} {asset_type} assets after thematic mapping")

    fallback_level_refs = sum(
        len(entry.get("levels", []))
        for entry in entries
        if str(entry.get("usageTier") or "") == "fallback_only"
    )
    checks.append({
        "scope": "fallback_policy",
        "name": "fallback_sets_not_level_bound",
        "required": 0,
        "actual": fallback_level_refs,
        "passed": fallback_level_refs == 0,
    })
    if fallback_level_refs:
        warnings.append(f"Fallback-only sheets have {fallback_level_refs} level bindings")

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "summary": summary,
    }, warnings


def process_all(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    source_dir = Path(args.source_dir).resolve()
    sources = sorted_source_pngs(source_dir)
    warnings: list[str] = []
    if len(sources) < len(SHEET_SLOTS):
        warnings.append(f"expected {len(SHEET_SLOTS)} PNG sheets, found {len(sources)}")
    if len(sources) > len(SHEET_SLOTS):
        warnings.append(f"found {len(sources)} PNG sheets; only first {len(SHEET_SLOTS)} are mapped")
    output_root = project_root / RUNTIME_ROOT
    if args.clean and output_root.exists():
        shutil.rmtree(output_root)

    entries: list[dict[str, Any]] = []
    for sheet_index, (source, slot) in enumerate(zip(sources, SHEET_SLOTS), start=1):
        sheet_entries, sheet_warnings = process_sheet(project_root, source, slot, sheet_index, args)
        entries.extend(sheet_entries)
        warnings.extend(sheet_warnings)

    supplemental_entries, supplemental_warnings = ensure_supplemental_platforms(project_root, entries)
    entries.extend(supplemental_entries)
    warnings.extend(supplemental_warnings)

    supplemental_ui_entries, supplemental_ui_warnings = ensure_supplemental_ui_assets(project_root, entries)
    entries.extend(supplemental_ui_entries)
    warnings.extend(supplemental_ui_warnings)

    validation, validation_warnings = validate_entries(entries, len(sources))
    warnings.extend(validation_warnings)

    report = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "sourceDir": str(source_dir),
        "sourcePngCount": len(sources),
        "mappedSheetCount": min(len(sources), len(SHEET_SLOTS)),
        "entryCount": len(entries),
        "warnings": warnings,
        "validation": validation,
        "summary": validation["summary"],
        "slots": SHEET_SLOTS,
        "entries": entries,
    }
    manifest = project_root / "assets/resources/config/last_iteration_asset_manifest.generated.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = project_root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_generated_ts(entries, project_root / "assets/scripts/generated/ThemeAssetCatalog.generated.ts")
    contact_sheet(entries, project_root / args.preview, args.preview_limit)
    return {
        "sourcePngCount": len(sources),
        "entryCount": len(entries),
        "warnings": len(warnings),
        "manifest": str(manifest),
        "report": str(report_path),
        "preview": str(project_root / args.preview),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cut the latest Martyskin 30-sheet texture drop into themed Cocos runtime sprites.")
    parser.add_argument("--project-root", default=".", help="Cocos Creator project root.")
    parser.add_argument("--source-dir", required=True, help="Directory with the latest 30 PNG source sheets.")
    parser.add_argument("--min-area", type=int, default=850, help="Minimum connected foreground component area.")
    parser.add_argument("--max-sheet-fraction", type=float, default=0.72, help="Reject giant sheet-sized components.")
    parser.add_argument("--pad", type=int, default=10)
    parser.add_argument("--clean", action="store_true", help="Clean previous generated last_iteration assets before writing.")
    parser.add_argument("--report", default="qa/last_iteration_asset_pipeline_report.json")
    parser.add_argument("--preview", default="qa/asset-previews/last_iteration_asset_preview.png")
    parser.add_argument("--preview-limit", type=int, default=260)
    args = parser.parse_args()
    result = process_all(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
