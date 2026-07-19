# UI snapshot report — Module 2 name + menu + levels + playing HUD + devgate + sound + skins + devpanel + achievements + records + paused pilots

Generated: 2026-07-04 14:05 +03:00  
Updated: 2026-07-06 16:05 +03:00  
Status: `selected_runtime_snapshot_android_web_pass`

## Scope

This report tracks visual/runtime evidence for the Module 2 UI pilot.

Current pilots:

- screen: `name`
- route: `menu -> name`
- runtime state: `state:name`
- screen: `menu`
- route: `mtr_screen=menu`
- runtime state: `state:menu`
- screen: `levels`
- route: `mtr_screen=levels&mtr_dev=1`
- runtime state: `state:levels`
- screen: `playing_hud`
- route: `mtr_dev=1&mtr_autostart=1&mtr_level=1`
- runtime state: `state:playing`
- screen: `devgate`
- route: `mtr_screen=devgate`
- runtime state: `state:devgate`
- screen: `sound`
- route: `mtr_screen=sound`
- runtime state: `state:sound`
- screen: `skins`
- route: `mtr_screen=skins`
- runtime state: `state:skins`
- screen: `devpanel`
- route: `mtr_screen=devpanel&mtr_dev=1`
- runtime state: `state:devpanel`
- screen: `achievements`
- route: `mtr_screen=achievements&mtr_unlock_achievements=1`
- runtime state: `state:achievements`
- screen: `records`
- route: `mtr_screen=records&mtr_seed_records=1`
- runtime state: `state:records`
- screen: `paused`
- route: `mtr_screen=paused&mtr_autostart=1&mtr_level=1`
- runtime state: `state:paused`

## Historical evidence inspected

Existing historical screenshots/logs:

- `docs/qa/evidence/20260621_skin_bonus_overlayfix/startmenu_name_submenu.png`
- `docs/qa/evidence/20260621_skin_bonus_overlayfix/startmenu_name_submenu_logcat.txt`
- `docs/qa/evidence/20260621_skin_bonus_overlayfix/startmenu_forward_gameplay.png`
- `docs/qa/evidence/20260621_skin_bonus_overlayfix/startmenu_forward_gameplay_logcat.txt`

Historical logs confirm the start/name route existed before this Module 2 pass, but they are not sufficient as final evidence because the current patch changed the runtime touch target and UI manifest contract.

## Fresh static evidence

Static validators:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_module2_gate.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_final.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_menu_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_playing_hud_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_pregate_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_after_intl_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_records_native_bridge.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_paused_pilot.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_module2_final.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_levels_gate.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_sound_pregate_fix.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_skins_gate.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_devpanel_gate.json`

Current static result:

```json
{
  "uiIrProblemCount": 0,
  "uiIrScreenCount": 11,
  "assetBlockerCount": 0
}
```

## Fresh runtime evidence

### Web

- Build log: `logs/creator-module2-ui-web-r2-20260704.log`
- Name screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.png`
- Name probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json`
- Name CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl`
- Menu screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.png`
- Menu probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json`
- Menu CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.console.jsonl`
- Levels build log: `logs/creator-module2-levels-web-20260704.log`
- Levels screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.png`
- Levels probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json`
- Levels CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl`
- Playing HUD build log: `logs/creator-module2-playing-hud-web-20260704.log`
- Playing HUD screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.png`
- Playing HUD probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json`
- Playing HUD console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.console.jsonl`
- Devgate build log: `logs/creator-module2-devgate-web-20260704.log`
- Devgate screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.png`
- Devgate summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json`
- Devgate console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.console.jsonl`
- Sound build log: `logs/creator-module2-sound-web-gatefix-20260704.log`
- Sound screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.png`
- Sound probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json`
- Sound direct-CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.console.jsonl`
- Skins build log: `logs/creator-module2-skins-web-20260704.log`
- Skins screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.png`
- Skins probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json`
- Skins direct-CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.console.jsonl`
- Devpanel build log: `logs/creator-module2-devpanel-web-20260706.log`
- Devpanel accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.png`
- Devpanel accepted probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json`
- Devpanel accepted direct-CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.console.jsonl`
- Devpanel generic CDP diagnostic screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_screen_cdp.png`
- Achievements build log: `logs/creator-module2-achievements-web-20260706-after-intl-fix.log`
- Achievements accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.png`
- Achievements accepted probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json`
- Achievements accepted direct-CDP console log: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.console.jsonl`
- Records build log: `logs/creator-module2-records-web-20260706-table.log`
- Records accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png`
- Records visual summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json`
- Records generic CDP probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp_probe.json`
- Paused build log: `logs/creator-module2-paused-web-20260706.log`
- Paused accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png`
- Paused visual summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json`
- Paused generic CDP probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp_probe.json`

Runtime marker summary:

```json
{
  "runtimeReady": true,
  "waitForLogPattern": "MTR_QA_SCREEN_READY screen=name",
  "waitForLogPatternReady": true,
  "consoleEventCount": 165,
  "consoleErrorCount": 0,
  "menuUiGateReady": true,
  "levelsQaScreenReady": true,
  "levelsConsoleEventCount": 187,
  "playingHudRuntimeReady": true,
  "playingHudGameplayReady": true,
  "playingHudConsoleErrors": 0,
  "devgateRuntimeReady": true,
  "devgateQaScreenReady": true,
  "devgateConsoleErrors": 0,
  "soundRuntimeReady": true,
  "soundQaScreenReady": true,
  "soundUiGateReady": true,
  "soundConsoleErrors": 0,
  "skinsRuntimeReady": true,
  "skinsQaScreenReady": true,
  "skinsUiGateReady": true,
  "skinsPreviewUsageLogged": true,
  "skinsConsoleErrors": 0,
  "devpanelRuntimeReady": true,
  "devpanelQaScreenReady": true,
  "devpanelUiGateReady": true,
  "devpanelSharedPngAssetsObserved": true,
  "devpanelConsoleErrors": 0,
  "achievementsRuntimeReady": true,
  "achievementsQaScreenReady": true,
  "achievementsUiGateReady": true,
  "achievementsConsoleErrors": 0,
  "achievementsIntlErrors": 0,
  "recordsVisualScreenshotPass": true,
  "recordsRowsVisible": true,
  "recordsTableColumnsReadable": true,
  "recordsKnownCdpConsoleCaptureFalseNegative": true,
  "pausedVisualScreenshotPass": true,
  "pausedPanelVisible": true,
  "pausedTouchZoneDebugLayerVisible": false,
  "pausedKnownCdpNavigateOrConsoleCaptureFalseNegative": true
}
```

Observed visually:

- `name` screen opened from `?mtr_screen=name`.
- `СОХРАНИТЬ`, `ВПЕРЁД, ПРИМАТЫ!`, and `В МЕНЮ` appear as atomic PNG buttons.
- The visible player name appears once.
- Old `ВВЕСТИ ИМЯ` / `enter_name` button is not visible.
- `menu` screen opened from `?mtr_screen=menu`.
- `НАЧАТЬ ИГРУ`, `ВЫБЕРИ СВОЕГО ПРИМАТА`, `МАРТЫШКИНЫ РЕКОРДЫ`, `ВЫБОР УРОВНЯ`, `ЗВУК`, and `РЕЖИМ РАЗРАБОТЧИКА` appear as single atomic PNG buttons.
- No runtime ghost labels are visible under the main menu PNG buttons.
- `levels` screen opened from `?mtr_screen=levels&mtr_dev=1`.
- All 15 level cards are visible in the inspected Web screenshot.
- CDP console evidence contains load/use events for `mtr_level_select_theme_icon_01` through `mtr_level_select_theme_icon_15`, including every icon after level 8.
- `playing_hud` route reached gameplay through `?mtr_dev=1&mtr_autostart=1&mtr_level=1`.
- Web direct-CDP screenshot shows readable top HUD panels, pause control, and bottom jump/dash controls without blocking the core gameplay field.
- `devgate` screen opened from `?mtr_screen=devgate`.
- Web Playwright screenshot shows the developer access title, password field, and `ПРОВЕРИТЬ` / `НАЗАД` buttons as single shared PNG-styled buttons with no old background labels.
- `sound` screen opened from `?mtr_screen=sound`.
- Web direct-CDP screenshot shows the settings panel, three sound rows, slider PNGs, compact `+/-` PNG buttons, and footer PNG-styled controls without ghost labels or fallback outlines.
- Web direct-CDP console evidence reaches `MTR_MENU_UI_GATE_READY surface=sound_settings` before the accepted screenshot.
- `skins` screen opened from `?mtr_screen=skins`.
- Web direct-CDP screenshot shows the 4x2 primate card grid, eight base-idle preview PNGs, selected status chip, and footer PNG-styled controls without ghost labels or fallback outlines.
- Web direct-CDP console evidence reaches `MTR_MENU_UI_GATE_READY surface=skin_select` and logs `reason=menu_skin_preview` before the accepted screenshot.
- `devpanel` screen opened from `?mtr_screen=devpanel&mtr_dev=1`.
- Web direct-CDP screenshot shows the developer panel title, status chip, and 3x4 grid of PNG-styled debug buttons without ghost labels or fallback outlines.
- Web direct-CDP console evidence reaches `MTR_QA_SCREEN_READY screen=devpanel` and `MTR_MENU_UI_GATE_READY surface=developer` before the accepted screenshot.
- `achievements` screen opened from `?mtr_screen=achievements&mtr_unlock_achievements=1`.
- Web direct-CDP screenshot shows the achievements title, profile chip, 10 achievement cards, icon slots, rarity/date/status labels, progress lines, and `РЕКОРДЫ` / `НАЗАД` footer buttons without ghost labels or fallback outlines.
- Web direct-CDP console evidence reaches `MTR_QA_SCREEN_READY screen=achievements` and `MTR_MENU_UI_GATE_READY surface=achievements` before the accepted screenshot.
- `records` screen opened from `?mtr_screen=records&mtr_seed_records=1`.
- Web accepted screenshot shows the records title, seven seeded row chips, fixed score/level/banana columns, and `ДОСТИЖЕНИЯ` / `НАЗАД` footer buttons without ghost labels or fallback outlines.
- The longest seeded primate name is truncated in the name column without colliding with score/level/banana labels.
- `paused` screen opened from `?mtr_dev=1&mtr_autostart=1&mtr_level=1&mtr_screen=paused`.
- Web accepted screenshot shows the pause title, gameplay world behind the dimmed overlay, shared pause panel, and `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, `В МЕНЮ` controls without ghost labels or fallback outlines.
- The gameplay story toast `Вход на объект` can be visible under the title during startup pause and is accepted as a live gameplay overlay, not a stale under-label.

Harness note:

- `web-chrome-runtime-smoke.ps1` now captures JS console markers through CDP `Runtime.consoleAPICalled`.
- The harness opens Chrome on `about:blank`, attaches CDP before navigation, records console evidence, and then uses a fresh page socket for probe/screenshot stability.
- For this `devgate` slice the generic CDP wrapper produced a false negative (`runtimeReady=false`) despite a correct screenshot; final Web pass therefore uses Playwright console/screenshot QA and records the wrapper failure as diagnostic evidence, not acceptance evidence.
- For the `sound` slice, final Web acceptance uses a direct-CDP startup URL smoke because the local Playwright package lacked `playwright-core`; this route captured runtime markers and a clean screenshot without package dependency.
- For the `skins` slice, final Web acceptance uses the same direct-CDP startup URL smoke so the heavier preview-grid route is judged by runtime markers, screenshot, and console asset-usage evidence.
- For the `devpanel` slice, the generic CDP wrapper again produced a marker-capture false negative, so final acceptance uses a direct-CDP smoke that enables console capture before navigation.
- For the `achievements` slice, final Web acceptance uses a direct-CDP smoke plus visual screenshot review. The route-specific panel/title asset reasons are `shared_achievements_panel` and `shared_achievements_title`.
- For the `records` slice, the generic CDP wrapper produced a marker-capture false negative (`runtimeReady=false`, `consoleEventCount=0`) despite a correct canvas screenshot and complete page state. Final Web acceptance is therefore build + screenshot visual review + probe, with strict runtime-marker acceptance delegated to Android emulator telemetry.
- For the `paused` slice, the first temporary web server launch failed because a path with spaces was not quoted; after corrected launch, the generic CDP wrapper still produced navigation/marker capture instability. Final Web acceptance is build + screenshot visual review + probe, with strict runtime-marker acceptance delegated to Android emulator telemetry.

### Android emulator

- Build log: `logs/creator-module2-ui-android-emulator-20260704.log`
- APK: `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`
- Screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen.png`
- Logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen_logcat.txt`
- Summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen_summary.json`
- Menu screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen.png`
- Menu logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_logcat.txt`
- Menu summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_summary.json`
- Levels build log: `logs/creator-module2-levels-android-emulator-20260704.log`
- Levels clean screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean.png`
- Levels clean logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_logcat.txt`
- Levels clean summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_summary.json`
- Playing HUD build log: `logs/creator-module2-playing-hud-android-emulator-20260704.log`
- Playing HUD screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_screen.png`
- Playing HUD logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_logcat.txt`
- Playing HUD summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json`
- Devgate build log: `logs/creator-module2-devgate-android-emulator-20260704.log`
- Devgate screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen.png`
- Devgate logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_logcat.txt`
- Devgate summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json`
- Sound build log: `logs/creator-module2-sound-android-emulator-gatefix-20260704.log`
- Sound screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix.png`
- Sound logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_logcat.txt`
- Sound summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json`
- Skins build log: `logs/creator-module2-skins-android-emulator-20260704.log`
- Skins screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen.png`
- Skins logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_logcat.txt`
- Skins summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json`
- Devpanel build log: `logs/creator-module2-devpanel-android-emulator-20260706.log`
- Devpanel screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen.png`
- Devpanel logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_logcat.txt`
- Devpanel summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json`
- Achievements build log: `logs/creator-module2-achievements-android-emulator-20260706-after-intl-fix.log`
- Achievements screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix.png`
- Achievements logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_logcat.txt`
- Achievements summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json`
- Records build log: `logs/creator-module2-records-android-emulator-20260706-native-bridge.log`
- Records screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge.png`
- Records logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_logcat.txt`
- Records summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json`
- Paused build log: `logs/creator-module2-paused-android-emulator-20260706.log`
- Paused screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen.png`
- Paused logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_logcat.txt`
- Paused summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json`

Runtime summary:

```json
{
  "serial": "emulator-5554",
  "qaScreenReady": true,
  "menuUiGateReady": true,
  "nativeStartupReady": true,
  "fatalException": false,
  "oldEnterName": false,
  "saveNameAsset": true,
  "levelsCleanAppData": true,
  "levelsAllLevelIconsObserved": true,
  "levelsIconUsageCount": 15,
  "playingHudCleanAppData": true,
  "playingHudGameplayReady": true,
  "playingHudFatalException": false,
  "devgateCleanAppData": true,
  "devgateQaScreenReady": true,
  "devgateFatalException": false,
  "soundCleanAppData": true,
  "soundQaScreenReady": true,
  "soundUiGateReady": true,
  "soundSharedPngAssetsObserved": true,
  "soundFatalException": false,
  "skinsCleanAppData": true,
  "skinsQaScreenReady": true,
  "skinsUiGateReady": true,
  "skinsPreviewUsageObserved": true,
  "skinsFatalException": false,
  "devpanelCleanAppData": true,
  "devpanelQaScreenReady": true,
  "devpanelUiGateReady": true,
  "devpanelSharedPngAssetsObserved": true,
  "devpanelFatalException": false,
  "achievementsCleanAppData": true,
  "achievementsQaScreenReady": true,
  "achievementsUiGateReady": true,
  "achievementsIconUsageCount": 7,
  "achievementsIntlErrorCount": 0,
  "achievementsFatalException": false,
  "recordsCleanAppData": true,
  "recordsNativeStartupQueryReady": true,
  "recordsRuntimeReady": true,
  "recordsQaScreenReady": true,
  "recordsSeeded": true,
  "recordsGateReady": true,
  "recordsFatalException": false,
  "pausedCleanAppData": true,
  "pausedNativeStartupQueryReady": true,
  "pausedGameplayStartReady": true,
  "pausedStartupPauseApplied": true,
  "pausedQaScreenReady": true,
  "pausedGateReady": true,
  "pausedTouchZoneDebugLayerVisible": false,
  "pausedFatalException": false
}
```

## Acceptance criteria

Current selected pass:

- [x] fresh screenshots show the `name` screen;
- [x] `СОХРАНИТЬ ИМЯ`, `ВПЕРЁД, ПРИМАТЫ!`, and `В МЕНЮ` are visible as single atomic PNG buttons;
- [x] the player-name text is visible once in inspected screenshots;
- [x] no old `ВВЕСТИ ИМЯ` or stale `enter_name` button appears;
- [x] no Android fatal logcat marker appears;
- [x] project validators remain green after cleanup;
- [x] web harness captures JS console markers through CDP.
- [x] fresh screenshots show the `menu` screen on Web and Android emulator;
- [x] `menu` screen reaches `MTR_MENU_UI_GATE_READY surface=main_menu`;
- [x] no main-menu ghost labels are visible in inspected screenshots.
- [x] fresh screenshots show the `levels` screen on Web and Android emulator;
- [x] `levels` screen reaches `MTR_QA_SCREEN_READY screen=levels`;
- [x] all 15 themed level icons are observed in runtime logs;
- [x] level icons after level 8 are loaded/used on Web and Android emulator;
- [x] Android clean-pass after `pm clear` has no debug touch-zone overlay marker.
- [x] fresh screenshots show the `playing_hud` gameplay HUD on Web and Android emulator;
- [x] `playing_hud` reaches `MTR_GAMEPLAY_START_GATE_READY level=1`;
- [x] top HUD panels and bottom controls remain readable after 64px touch-target adjustment;
- [x] Android `playing_hud` logcat has no fatal exception.
- [x] fresh screenshots show the `devgate` screen on Web and Android emulator;
- [x] `devgate` reaches `MTR_QA_SCREEN_READY screen=devgate`;
- [x] password field is styled through shared PNG chrome while password input itself remains hidden/native;
- [x] `ПРОВЕРИТЬ` and `НАЗАД` meet the 64px touch-target policy;
- [x] Android `devgate` logcat has no fatal exception or ANR.
- [x] fresh screenshots show the `sound` screen on Web and Android emulator;
- [x] `sound` reaches `MTR_QA_SCREEN_READY screen=sound`;
- [x] Web and Android both reach `MTR_MENU_UI_GATE_READY surface=sound_settings` before accepted screenshots;
- [x] slider track/fill/knob and shared button PNG assets are observed in runtime logs;
- [x] `ПО УМОЛЧАНИЮ`, `ПРИМЕНИТЬ`, `НАЗАД`, and compact `+/-` controls meet the 64px touch-target policy;
- [x] Android `sound` logcat has no fatal exception or ANR.
- [x] fresh screenshots show the `skins` screen on Web and Android emulator;
- [x] `skins` reaches `MTR_QA_SCREEN_READY screen=skins`;
- [x] Web and Android both reach `MTR_MENU_UI_GATE_READY surface=skin_select` before accepted screenshots;
- [x] all eight base-idle primate preview PNGs are covered by the critical UI gate;
- [x] `ВЫБРАТЬ` and `НАЗАД` meet the 64px touch-target policy;
- [x] Android `skins` logcat has no fatal exception or ANR.
- [x] fresh screenshots show the `devpanel` screen on Web and Android emulator;
- [x] `devpanel` reaches `MTR_QA_SCREEN_READY screen=devpanel`;
- [x] Web and Android both reach `MTR_MENU_UI_GATE_READY surface=developer` before accepted screenshots;
- [x] developer panel/status/button PNG assets are observed in runtime logs;
- [x] all 12 developer controls meet the 64px touch-target policy;
- [x] Android `devpanel` logcat has no fatal exception or ANR.
- [x] fresh screenshots show the `achievements` screen on Web and Android emulator;
- [x] `achievements` reaches `MTR_QA_SCREEN_READY screen=achievements`;
- [x] Web and Android both reach `MTR_MENU_UI_GATE_READY surface=achievements` before accepted screenshots;
- [x] achievement panel/title/status/card/icon/footer PNG assets are observed in runtime logs;
- [x] `РЕКОРДЫ` and `НАЗАД` meet the 64px touch-target policy;
- [x] Android `achievements` logcat has no `Intl is not defined`, fatal exception, or ANR.
- [x] fresh screenshots show the seeded `records` screen on Web and Android emulator;
- [x] `records` reaches `MTR_QA_SCREEN_READY screen=records` on Android emulator;
- [x] Android reaches `MTR_RECORDS_QA_SEEDED` and `MTR_MENU_UI_GATE_READY surface=records`;
- [x] `records` row layout uses fixed columns and preserves score/level/banana readability for long primate names;
- [x] `ДОСТИЖЕНИЯ` and `НАЗАД` meet the 64px touch-target policy;
- [x] Android `records` logcat has no app JS error, fatal exception, or ANR.
- [x] fresh screenshots show the startup `paused` screen on Web and Android emulator;
- [x] Android reaches `MTR_GAMEPLAY_START_GATE_READY level=1`, `MTR_QA_STARTUP_PAUSE_APPLIED level=1`, and `MTR_QA_SCREEN_READY screen=paused`;
- [x] Android reaches `MTR_MENU_UI_GATE_READY surface=pause`;
- [x] `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, and `В МЕНЮ` meet the 64px touch-target policy;
- [x] startup paused QA does not show the touch-zone debug label unless explicitly requested;
- [x] Android `paused` logcat has no app JS error, fatal exception, or ANR.
