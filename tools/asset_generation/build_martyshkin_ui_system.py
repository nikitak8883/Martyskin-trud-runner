from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "resources" / "ui" / "shared"
RNG = random.Random(20260618)


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def vertical_gradient(size: tuple[int, int], top: str, bottom: str, alpha: int = 255) -> Image.Image:
    w, h = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = image.load()
    c0 = rgba(top, alpha)
    c1 = rgba(bottom, alpha)
    for y in range(h):
        t = y / max(1, h - 1)
        row = tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(4))
        for x in range(w):
            pixels[x, y] = row
    return image


def rounded_mask(size: tuple[int, int], radius: int, inset: int = 0) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((inset, inset, size[0] - inset - 1, size[1] - inset - 1), radius, fill=255)
    return mask


def add_texture(image: Image.Image, amount: int = 140, scratches: int = 18) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    for _ in range(amount):
        x = RNG.randrange(8, max(9, w - 8))
        y = RNG.randrange(8, max(9, h - 8))
        r = RNG.choice((1, 1, 2, 3))
        color = (255, 242, 194, RNG.randrange(5, 18)) if RNG.random() > 0.42 else (24, 13, 7, RNG.randrange(6, 24))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    for _ in range(scratches):
        x = RNG.randrange(18, max(19, w - 60))
        y = RNG.randrange(12, max(13, h - 12))
        length = RNG.randrange(18, max(19, min(110, w // 3)))
        draw.line((x, y, min(w - 12, x + length), y + RNG.choice((-1, 0, 1))), fill=(36, 19, 9, 28), width=1)


def add_bolts(draw: ImageDraw.ImageDraw, size: tuple[int, int], radius: int = 9, inset: int = 24) -> None:
    w, h = size
    for x, y in ((inset, inset), (w - inset, inset), (inset, h - inset), (w - inset, h - inset)):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgba("#3B2B1D"), outline=rgba("#E6C67B"), width=2)
        draw.line((x - radius // 2, y, x + radius // 2, y), fill=rgba("#B79049"), width=2)


def save_button(name: str, top: str, bottom: str, border: str, glow: str, pressed: bool = False) -> None:
    size = (640, 116)
    radius = 28
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    shadow_draw.rounded_rectangle((10, 12, size[0] - 10, size[1] - 5), radius, fill=(8, 6, 4, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))

    face = vertical_gradient(size, top, bottom)
    face.putalpha(rounded_mask(size, radius, 8))
    if pressed:
        face = face.transform(size, Image.Transform.AFFINE, (1, 0, 0, 0, 0.94, 5), resample=Image.Resampling.BICUBIC)

    image = Image.alpha_composite(shadow, face)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((8, 6, size[0] - 9, size[1] - 10), radius, outline=rgba(border), width=7)
    draw.rounded_rectangle((17, 15, size[0] - 18, size[1] - 19), radius - 8, outline=rgba(glow, 118), width=3)
    draw.line((58, 28, size[0] - 58, 28), fill=rgba("#FFF2B0", 65), width=3)
    add_bolts(draw, size, radius=7, inset=31)
    add_texture(image, 115, 12)
    path = OUT / "buttons" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def save_panel(name: str, size: tuple[int, int], compact: bool = False) -> None:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    radius = 32 if not compact else 22
    draw.rounded_rectangle((8, 8, w - 9, h - 9), radius, fill=rgba("#17130F", 218), outline=rgba("#5A351C", 245), width=10)
    draw.rounded_rectangle((20, 20, w - 21, h - 21), radius - 8, fill=rgba("#332516", 207), outline=rgba("#D5A448", 210), width=4)
    draw.rounded_rectangle((30, 30, w - 31, h - 31), radius - 13, fill=rgba("#201A13", 185), outline=rgba("#F1D487", 58), width=2)
    for y in range(52, h - 40, 68):
        draw.line((40, y, w - 40, y), fill=rgba("#8F6230", 22), width=2)
    add_bolts(draw, size, radius=8 if not compact else 6, inset=28 if not compact else 20)
    add_texture(image, max(80, (w * h) // 7000), max(10, w // 70))
    path = OUT / "panels" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def save_title_banner() -> None:
    size = (900, 132)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((24, 18, size[0] - 25, size[1] - 12), 30, fill=rgba("#4A2C17", 248), outline=rgba("#21150D"), width=9)
    draw.rounded_rectangle((39, 29, size[0] - 40, size[1] - 23), 22, fill=rgba("#8B5725", 242), outline=rgba("#E0B45D"), width=4)
    draw.line((75, 45, size[0] - 75, 45), fill=rgba("#FFE39A", 60), width=4)
    add_bolts(draw, size, radius=8, inset=54)
    for x in (13, size[0] - 13):
        draw.ellipse((x - 11, 42, x + 11, 84), fill=rgba("#49311A"), outline=rgba("#D7A348"), width=3)
    add_texture(image, 120, 18)
    path = OUT / "banners" / "title_banner_blank.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def save_card(name: str, size: tuple[int, int], fill: str, border: str, selected: bool = False, alpha: int = 238) -> None:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    glow = rgba("#FFE37B", 100) if selected else rgba(border, 40)
    draw.rounded_rectangle((4, 4, w - 5, h - 5), 22, fill=glow)
    draw.rounded_rectangle((11, 11, w - 12, h - 12), 18, fill=rgba(fill, alpha), outline=rgba(border, 245), width=5)
    draw.rounded_rectangle((20, 20, w - 21, h - 21), 13, outline=rgba("#F9E2A1", 50), width=2)
    add_bolts(draw, size, radius=5, inset=22)
    add_texture(image, max(55, (w * h) // 6500), max(6, w // 90))
    path = OUT / "cards" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def save_slider_assets() -> None:
    track = Image.new("RGBA", (480, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(track, "RGBA")
    draw.rounded_rectangle((4, 6, 475, 27), 11, fill=rgba("#17130F", 230), outline=rgba("#B38A43"), width=3)
    track_path = OUT / "controls" / "slider_track.png"
    track_path.parent.mkdir(parents=True, exist_ok=True)
    track.save(track_path, optimize=True)

    fill = Image.new("RGBA", (480, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(fill, "RGBA")
    draw.rounded_rectangle((4, 7, 475, 26), 10, fill=rgba("#6FC45B"), outline=rgba("#D9F38A"), width=2)
    fill.save(OUT / "controls" / "slider_fill.png", optimize=True)

    knob = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(knob, "RGBA")
    draw.ellipse((8, 8, 55, 55), fill=rgba("#D49B31"), outline=rgba("#3A2513"), width=5)
    draw.ellipse((17, 17, 46, 46), fill=rgba("#F5D06A"), outline=rgba("#FFF0A0", 120), width=2)
    knob.save(OUT / "controls" / "slider_knob.png", optimize=True)

    for state, color in (("on", "#5F9D54"), ("off", "#5A4B3D")):
        toggle = Image.new("RGBA", (200, 76), (0, 0, 0, 0))
        draw = ImageDraw.Draw(toggle, "RGBA")
        draw.rounded_rectangle((5, 8, 194, 68), 30, fill=rgba("#17130F", 230), outline=rgba("#C69A4D"), width=4)
        draw.rounded_rectangle((12, 15, 187, 61), 23, fill=rgba(color, 235))
        knob_x = 155 if state == "on" else 45
        draw.ellipse((knob_x - 22, 16, knob_x + 22, 60), fill=rgba("#F0C766"), outline=rgba("#422A14"), width=4)
        toggle.save(OUT / "controls" / f"toggle_{state}.png", optimize=True)


def save_hud_assets() -> None:
    save_card("hud_panel", (760, 104), "#221B13", "#C89A4A", alpha=220)
    save_card("hud_control", (600, 104), "#1D2C20", "#78A96B", alpha=214)
    save_card("status_chip", (620, 68), "#2A2317", "#D6A94D", alpha=232)


def main() -> None:
    save_button("button_primary_idle", "#E1A83C", "#A96D1F", "#4B2B13", "#FFE399")
    save_button("button_primary_pressed", "#C9912D", "#84511A", "#3A210F", "#F5C960", pressed=True)
    save_button("button_secondary_idle", "#659B59", "#386442", "#25351F", "#D8F2A2")
    save_button("button_back_idle", "#659B59", "#386442", "#25351F", "#D8F2A2")
    save_button("button_danger_idle", "#B85C3D", "#773526", "#401B15", "#F3B07E")
    save_button("button_disabled", "#6C6559", "#413D36", "#2B2924", "#BDB5A4")
    save_button("button_compact_idle", "#D1A342", "#8D6424", "#453018", "#F6D986")
    save_title_banner()
    save_panel("panel_main", (1000, 600))
    save_panel("panel_dialog", (760, 440))
    save_panel("panel_list", (1180, 560))
    save_panel("panel_chip", (620, 76), compact=True)
    save_card("level_card_idle", (480, 240), "#B78D51", "#563719")
    save_card("level_card_selected", (480, 240), "#C79A52", "#F2CF64", selected=True)
    save_card("level_card_locked", (480, 240), "#5B554D", "#35312B", alpha=226)
    save_card("primate_card_idle", (480, 310), "#282117", "#739965", alpha=226)
    save_card("primate_card_selected", (480, 310), "#302619", "#F0D05D", selected=True, alpha=238)
    save_card("achievement_card", (720, 124), "#211C16", "#8AA071", alpha=236)
    save_card("achievement_card_locked", (720, 124), "#191A17", "#555A50", alpha=232)
    save_card("empty_state_card", (700, 180), "#2A2117", "#C79B50", alpha=236)
    save_slider_assets()
    save_hud_assets()
    print(f"Generated shared UI assets in {OUT}")


if __name__ == "__main__":
    main()
