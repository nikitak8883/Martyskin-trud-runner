# UI allowed assets

Canonical contract: `docs/UI_ALLOWED_ASSETS.md`.

This root file is kept as a compatibility pointer for older notes/tools that
referenced `UI_ALLOWED_ASSETS.md` from the project root.

Key runtime rules:

- Interactive UI uses blank/base PNG assets plus runtime Cocos labels.
- The canonical skin-pack main menu buttons under
  `assets/resources/objectives/themed/last_iteration/ui/main_menu/button/*.png`
  are the only current baked-text button exception; render them atomically
  without runtime label/text overlays.
- New baked text inside other interactive buttons is forbidden unless it is
  promoted into a documented canonical atomic skin-pack element.
- `UI_SKIN.assets.buttonLabelPlate` is fallback/HUD-only; do not draw it over a valid blank/base menu PNG button.
- Level-select theme icons are allowed only as the canonical 15 PNG set:
  `assets/resources/objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_01..15.png`.
- Main menu background uses only one dimmed far PNG backdrop
  `assets/resources/ui/main_menu_background/main_menu_bg_far.png` plus one
  runtime haze layer. The far PNG must stay a cohesive scenic illustration, not
  a locally patched or onion-layered collage. Readable ghost labels, old UI
  props, text-like artifacts, numbers, logos, and baked UI signs are forbidden
  across the whole backdrop. Lore must be expressed through the illustration
  itself: jungle construction, bananas, tools, rails, bamboo scaffolds, and
  silhouettes. Old mid/near/foreground menu background layers and the old decor
  props sheet are archived outside runtime resources and must not re-enter
  active runtime drawing without a fresh UI QA checkpoint.
- Old legacy UI cutouts remain blocked for active runtime use unless explicitly whitelisted in `docs/UI_ALLOWED_ASSETS.md`.
