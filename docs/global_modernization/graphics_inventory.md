# Graphics inventory — Module 1

Generated: 2026-07-02 15:52 +03:00  
Scope: `assets/resources/**/*.png`  
Mode: read-only inventory

## Summary

| Metric | Value |
| --- | ---: |
| Runtime PNG count | 1529 |
| Total PNG bytes | 107264037 |
| PNGs with alpha | 1528 |
| PNGs without alpha | 1 |
| Oversized PNGs over 2048 px edge | 0 |
| PNG read errors | 0 |
| Missing `.png.meta` files | 0 |

## Top-level groups

| Group | PNGs | Bytes | Alpha PNGs | Max W | Max H |
| --- | ---: | ---: | ---: | ---: | ---: |
| `characters` | 960 | 54169544 | 960 | 256 | 256 |
| `objectives` | 540 | 49428982 | 540 | 968 | 457 |
| `ui` | 29 | 3665511 | 28 | 2048 | 1152 |

## Runtime co-visibility candidates

| Candidate group | PNGs | Bytes | Notes |
| --- | ---: | ---: | --- |
| `characters/player_skins` | 960 | 54169544 | Largest count; must remain manifest-driven and should be bundled/loaded by selected skin, not all at startup. |
| `objectives/themed` | 495 | 43265007 | Mixed UI/level/platform themed content; needs sub-group atlas policy before any movement. |
| `ui/main_menu_background` | 1 | 3527889 | Single non-alpha 2048x1152 background; keep as standalone background, not UI atlas. |
| `ui/shared` | 28 | 137622 | Good candidate for shared menu/HUD UI atlas or 9-slice component policy. |
| `objectives/bonuses` | 8 | 975198 | Candidate for `bonus_items` atlas/bundle; must match bonus resolver. |
| `objectives/collectibles` | 14 | 1071680 | Candidate for `runner_core` or `collectibles` atlas. |
| `objectives/equipment` | 4 | 763190 | Candidate for skin/bonus validation; avoid runtime clothing placement without anchors. |
| `objectives/npc` | 10 | 1566620 | Decorative/obstacle content; should be level/content-manifest owned. |
| `objectives/ui` | 9 | 1787287 | Achievement/avatar/badge UI; avoid duplication with `ui/shared`. |

## Largest runtime PNGs

| Rank | Path | Bytes | Size | Alpha |
| ---: | --- | ---: | --- | --- |
| 1 | `ui/main_menu_background/main_menu_bg_far.png` | 3527889 | 2048x1152 | false |
| 2 | `objectives/themed/last_iteration/ui/records/card/mtr_last_records_ui_records_card_01.png` | 477272 | 668x405 | true |
| 3 | `objectives/themed/last_iteration/ui/developer/card/mtr_last_developer_ui_developer_card_04.png` | 462547 | 587x438 | true |
| 4 | `objectives/themed/last_iteration/ui/records/title/mtr_last_records_ui_records_title_01.png` | 374936 | 968x252 | true |
| 5 | `objectives/themed/last_iteration/ui/developer/card/mtr_last_developer_ui_developer_card_02.png` | 337685 | 668x286 | true |
| 6 | `objectives/themed/last_iteration/ui/developer/title/mtr_last_developer_ui_developer_title_01.png` | 307667 | 939x242 | true |
| 7 | `objectives/themed/last_iteration/ui/pause/card/mtr_last_pause_ui_pause_card_05.png` | 306609 | 506x348 | true |
| 8 | `objectives/themed/last_iteration/ui/death/title/mtr_last_death_ui_death_primary_title_01.png` | 300014 | 756x209 | true |
| 9 | `objectives/themed/last_iteration/ui/death/title/mtr_last_death_ui_death_primary_title_02.png` | 288312 | 761x211 | true |
| 10 | `objectives/themed/last_iteration/ui/pause/card/mtr_last_pause_ui_pause_card_01.png` | 286662 | 668x256 | true |

## Observations

- The runtime resource tree is PNG-heavy but structurally readable: no missing `.meta` pairs and no PNG decode failures.
- `characters/player_skins` dominates count and size; Module 3 must prevent startup-wide loading of optional skins.
- `objectives/themed` is the main mixed-content risk because it contains UI, level visuals, platforms, titles, cards, and decorative content under one broad tree.
- `ui/main_menu_background/main_menu_bg_far.png` is correctly a standalone large background and should not be packed into small UI atlases.
- No file movement is recommended until a reference scan and manifest-based loader plan exist.

## Next Module 1 action

Create or extend validators that check:

1. alpha/checkerboard/white-matte artifacts;
2. `.meta` pairing;
3. atlas group ownership;
4. runtime reference existence;
5. Android/Web content manifest version alignment.

