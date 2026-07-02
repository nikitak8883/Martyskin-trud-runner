# Main Menu Background 10.1 Audit

Date: 2026-06-12

## Result

Status: passed.

The main menu now uses a dedicated layered background set from `nessesary/10.1`, not the gameplay level background renderer and not a single pasted collage.

## Integrated Files

- `assets/resources/ui/main_menu_background/main_menu_bg_far.png`
- `assets/resources/ui/main_menu_background/main_menu_bg_mid.png`
- `assets/resources/ui/main_menu_background/main_menu_bg_near_left.png`
- `assets/resources/ui/main_menu_background/main_menu_bg_near_right.png`
- `assets/resources/ui/main_menu_background/main_menu_bg_top_hanging.png`
- `assets/resources/ui/main_menu_background/main_menu_bg_bottom_foreground.png`
- `assets/resources/ui/main_menu_background/main_menu_grade_overlay.png`
- `assets/resources/ui/main_menu_background/main_menu_decor_props_sheet.png`

## Pipeline Rules Verified

- All 8 files are separate PNG assets.
- Far and mid layers are opaque 2048x1152 backgrounds.
- Near-left, near-right, top, bottom, grade overlay, and prop sheet use real RGBA alpha.
- The prop sheet remains a source sheet for future slicing and is not rendered as a scene.
- The grade overlay is generated as a soft alpha atmosphere layer, not a white/checkerboard-backed image.
- The central menu area is intentionally quieter and readable.
- Old level bitmap menu flash is removed: quiet menu states draw only the menu background layers.

## Runtime Integration

- `GameRoot.ts` preloads critical menu background layers for `main_menu`.
- Menu background layers are drawn through render layers instead of a stale level-background fallback.
- The start button is visible above the new background and starts gameplay.
- Android and Web still share the same Cocos configs and level data.

## Evidence

- Asset report: `qa/main-menu-background-10-1/main_menu_background_10_1_report.json`
- Web menu: `qa/main-menu-background-10-1/screenshots/web-menu-1280x720-final-20260612.png`
- Web gameplay: `qa/main-menu-background-10-1/screenshots/web-after-start-1280x720-final-20260612.png`
- Android menu: `qa/main-menu-background-10-1/screenshots/android/09-menu-final-20260612.png`
- Android gameplay: `qa/main-menu-background-10-1/screenshots/android/10-after-start-final-20260612.png`

## Known Note

The Android emulator first boot can take tens of seconds while Cocos initializes release assets. During that wait the old menu is not shown; the new menu appears once the critical menu assets are ready.
