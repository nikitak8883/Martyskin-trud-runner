# UI IR migration report — Module 2 name + menu + levels + playing HUD + devgate + sound + skins + devpanel + achievements + records + paused pilots

Generated: 2026-07-04 14:05 +03:00  
Updated: 2026-07-06 16:05 +03:00  
Status: `name_menu_levels_playing_hud_devgate_sound_skins_devpanel_achievements_records_paused_ir_runtime_pass`  
Runtime changes: ten touch-target/layout correction groups in `GameRoot.ts`; non-main menu-like surfaces now use a critical UI preload gate; `skins` also preloads all base-idle preview PNGs for direct startup; `achievements` preloads its card icons and uses an Android-native-safe date formatter; `records` uses fixed table columns plus deterministic QA seeding; `paused` has 64px controls and strict startup-pause QA marker; Android native startup extras whitelist deterministic QA params; `menu` pilot is contract/evidence only

## Goal

Create project-specific UI IR screen contracts without rewriting the UI system.

Selected pilot screens:

- `name`
- `menu`
- `levels`
- `playing_hud`
- `devgate`
- `sound`
- `skins`
- `devpanel`
- `achievements`
- `records`
- `paused`

Why this screen:

- It is small enough for a safe pilot.
- It contains the highest-risk UI pattern: hidden input field plus visible Cocos text mirror.
- It directly relates to the user-facing name/profile flow.
- It uses atomic baked PNG buttons, so it exercises the no-ghost-label policy.
- `menu` is the canonical atomic baked PNG button grid and must remain ghost-label-free on Web and Android.
- `levels` directly covers the previous user concern that themed level icons disappeared after level 8.
- `playing_hud` protects the gameplay field and mobile control hit targets before UI extraction.
- `devgate` protects the developer password gate and its hidden EditBox/runtime-label pairing before dev-panel extraction.
- `sound` protects shared slider/toggle/button styling and cold-start secondary UI preload before broader settings/audio work.
- `skins` protects the primate selection grid, base-idle preview sprites, selected badge, and footer controls before deeper character-pipeline UI extraction.
- `devpanel` protects the dense developer tool grid before remaining achievement/records/modal UI extraction.
- `achievements` protects the dense achievement card grid, icon/status bindings, footer navigation, and native date formatting before records/save-system extraction.
- `records` protects the leaderboard table, long-name text fitting, deterministic save-data seeding, and achievements-records navigation before modal screens.
- `paused` protects the pause overlay over live gameplay, resume/settings/menu navigation, and debug touch-zone suppression before remaining end-state modals.

## Files changed

Runtime:

- `assets/scripts/GameRoot.ts`
  - Changed the `name` screen `В МЕНЮ` button height from `58` to `64` to meet the UI touch target policy.
  - Changed the `levels` screen `НАЗАД` button from `420x46` at `y=634` to `420x64` at `y=625`, preserving the visual center while meeting the same policy.
  - Changed `playing_hud` `ПАУЗА`, `ПРЫЖОК / ПЛАН`, and `РЫВОК` controls from `50px` to `64px` height while preserving visual centers.
  - Changed `devgate` `ПРОВЕРИТЬ` and `НАЗАД` controls from `52px` to `64px` height while preserving visual centers.
  - Changed `sound` footer controls from `240x46` to `240x64`, toggle hitboxes from `124x48` visual-only to `124x64` touch zones, and compact `+/-` controls from `58x46` to `64x64`, preserving visual centers.
  - Changed `skins` footer controls from `300x48` to `300x64`, preserving visual centers.
  - Changed `devpanel` 12 developer/debug controls from `300x46` to `300x64` and relaid the four rows with safe vertical breathing room.
  - Changed `achievements` card layout from `80px` cards to `86px` cards, adjusted spacing, and raised `РЕКОРДЫ` / `НАЗАД` footer controls to `300x64`.
  - Changed `records` footer controls from `300x48` to `300x64`.
  - Changed `records` row rendering from one long centered string to four fixed table columns so long primate names cannot collapse score/level/banana labels.
  - Added deterministic `records` QA seeding behind `mtr_seed_records=1`.
  - Changed `paused` `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, and `В МЕНЮ` controls from `420x56` to `420x64`.
  - Added `MTR_QA_SCREEN_READY screen=paused` after scheduled startup pause is applied.
  - Kept touch-zone overlays off for startup paused QA unless `mtr_show_touch_zones=1` is explicit.
  - Added per-surface critical UI preload logging/gating so direct `sound` and `skins` startup waits for shared PNG controls before first full screen draw.
  - Added `skin_select` preview PNGs to the critical UI gate so every base-idle primate preview is ready before the accepted first draw.
  - Added `achievements` icon/lock PNGs to the critical UI gate so every achievement card icon is available before the accepted first draw.
  - Added an `Intl`-safe fallback formatter for achievement dates, because Android native JS runtime does not provide `Intl`.
  - Added `mtr_screen` / `mtr_state` QA startup routing for menu-like screens and marker `MTR_QA_SCREEN_READY screen=<state>`.
- `native/engine/android/app/src/com/cocos/game/AppActivity.java`
  - Added `mtr_seed_records` to `QA_QUERY_KEYS`, so Android native test launches can pass deterministic records seed data into the Cocos startup query.

Contracts/tools:

- `assets/resources/config/ui_skin_manifest.json`
  - Reconciled live runtime behavior with the UI text policy.
  - Added documented atomic baked interactive button exceptions for `menu` and `name`.
- `docs/global_modernization/manifests/ui_ir/name_entry.ui_ir.json`
  - Added first screen-level UI IR pilot.
- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`
  - Added second screen-level UI IR pilot for the main menu PNG background, title, and 2x3 baked-button grid.
- `docs/global_modernization/manifests/ui_ir/levels.ui_ir.json`
  - Added third screen-level UI IR pilot for the level-select panel, title banner, 15 card buttons, 15 themed icon slots, and footer back button.
- `docs/global_modernization/manifests/ui_ir/playing_hud.ui_ir.json`
  - Added fourth screen-level UI IR pilot for gameplay HUD panels, runtime labels, pause touch zone, bottom controls, toast area, and developer badge.
- `docs/global_modernization/manifests/ui_ir/devgate.ui_ir.json`
  - Added fifth screen-level UI IR pilot for developer access panel, password field, hidden EditBox, status chip, and footer buttons.
- `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`
  - Added sixth screen-level UI IR pilot for settings panel, three sound rows, toggle touch zones, sliders, compact volume buttons, and footer controls.
- `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`
  - Added seventh screen-level UI IR pilot for primate card grid, selected badge, eight preview slots, and footer controls.
- `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`
  - Added eighth screen-level UI IR pilot for developer list panel, status chip, and 12 debug/action controls.
- `docs/global_modernization/manifests/ui_ir/achievements.ui_ir.json`
  - Added ninth screen-level UI IR pilot for achievements panel, profile chip, 10 card rows, icon slots, status/progress labels, and footer controls.
- `docs/global_modernization/manifests/ui_ir/records.ui_ir.json`
  - Added tenth screen-level UI IR pilot for records panel, title banner, empty state, seven row chips, fixed table columns, and footer navigation.
- `docs/global_modernization/manifests/ui_ir/paused.ui_ir.json`
  - Added eleventh screen-level UI IR pilot for gameplay-world backdrop, shared pause panel, title banner, and three pause controls.
- `tools/validate-ui-ir.py`
  - Added non-mutating validator for UI IR manifests and referenced UI assets.

Cleanup:

- Removed stale `mtr_start_menu_button_enter_name_01.png` and `.meta`.

## Contract reconciliation

The previous manifest rule was too strict for the live project because it disallowed interactive baked text completely.

The corrected rule is:

```json
{
  "interactiveText": "runtime-label-preferred",
  "bakedTextAllowed": "documented-atomic-interactive-exceptions",
  "legacyUiRuntimeAllowed": false
}
```

This means:

- use runtime labels by default;
- allow baked text only when the button is an atomic final PNG component;
- require the exception to be listed in the manifest;
- draw no runtime label on top of or under atomic baked buttons.

## Pilot screen structures

`name_entry.ui_ir.json` defines:

- shared dialog panel;
- title banner with runtime title label;
- instruction label;
- profile box PNG;
- hidden player-name EditBox;
- visible runtime name mirror;
- three atomic baked PNG buttons:
  - `СОХРАНИТЬ ИМЯ`;
  - `ВПЕРЁД, ПРИМАТЫ!`;
  - `В МЕНЮ`.

`menu.ui_ir.json` defines:

- single full-canvas main menu PNG backdrop;
- baked main title PNG;
- six atomic baked PNG buttons:
  - `НАЧАТЬ ИГРУ`;
  - `ВЫБЕРИ СВОЕГО ПРИМАТА`;
  - `МАРТЫШКИНЫ РЕКОРДЫ`;
  - `ВЫБОР УРОВНЯ`;
  - `ЗВУК И НАСТРОЙКИ`;
  - `РЕЖИМ РАЗРАБОТЧИКА`.

`levels.ui_ir.json` defines:

- shared list panel;
- title banner with runtime `ВЫБОР УРОВНЯ` label;
- 5x3 level-card grid;
- 15 runtime-label level buttons;
- 15 themed PNG icon slots:
  - `mtr_level_select_theme_icon_01` ... `mtr_level_select_theme_icon_15`;
- footer `НАЗАД` button with a `64px` touch target.

`devgate.ui_ir.json` defines:

- shared dialog panel;
- title banner with runtime `ДОСТУП РАЗРАБОТЧИКА` label;
- non-logging password notice;
- password field chip PNG;
- hidden password EditBox with visible placeholder/mirror behavior;
- optional status chip;
- runtime-label `ПРОВЕРИТЬ` and `НАЗАД` buttons with `64px` touch targets.

`sound.ui_ir.json` defines:

- shared settings panel;
- title banner with runtime `ЗВУК И НАСТРОЙКИ` label;
- three shared row panels for music, effects, and primate voice;
- toggle controls with `124x64` touch zones while preserving `124x48` visual bounds;
- slider track/fill/knob asset references;
- six compact `+/-` controls with `64x64` touch targets;
- footer `ПО УМОЛЧАНИЮ`, `ПРИМЕНИТЬ`, and `НАЗАД` buttons with `240x64` touch targets.

`skins.ui_ir.json` defines:

- shared list panel;
- title banner with runtime `ВЫБЕРИ СВОЕГО ПРИМАТА` label;
- 4x2 primate card grid;
- eight runtime-label card buttons;
- eight base-idle player preview PNG slots;
- selected status chip;
- footer `ВЫБРАТЬ` and `НАЗАД` buttons with `300x64` touch targets.

`devpanel.ui_ir.json` defines:

- shared list panel;
- title banner with runtime `МАРТЫШКИН ПУЛЬТ` label;
- developer status chip for colliders/taps/perf toggles;
- 3x4 developer/debug action grid:
  - `КОЛЛАЙДЕРЫ`;
  - `ЗОНЫ ТАПА`;
  - `FPS / УЗЛЫ`;
  - `ВСЕ ПРЕПЯТСТВИЯ`;
  - `ВСЕ БОНУСЫ`;
  - `ОТКРЫТЬ ДОСТИЖЕНИЯ`;
  - `ЗАКРЫТЬ ДОСТИЖЕНИЯ`;
  - `УРОВЕНЬ 1`;
  - `УРОВЕНЬ 15`;
  - `ПРОВЕРКА ПАУЗЫ`;
  - `СКРИН: ADB / WEB`;
  - `В МЕНЮ`;
- every developer control has a `300x64` touch target.

`achievements.ui_ir.json` defines:

- shared achievements list panel;
- title banner with runtime `МАРТЫШКИНЫ ДОСТИЖЕНИЯ` label;
- profile/status chip;
- 2x5 achievement card grid with 10 cards;
- icon slots for every achievement card plus locked-state fallback;
- runtime rarity/date/status/progress labels;
- footer `РЕКОРДЫ` and `НАЗАД` controls with `300x64` touch targets.

`records.ui_ir.json` defines:

- shared list panel;
- title banner with runtime `МАРТЫШКИНЫ РЕКОРДЫ` label;
- empty-state card for first-run saves;
- seven record row chip slots;
- fixed runtime-label columns for rank/name, score, level, and bananas;
- footer `ДОСТИЖЕНИЯ` and `НАЗАД` controls with `300x64` touch targets.

`paused.ui_ir.json` defines:

- gameplay world plus shared dimmed menu backdrop;
- shared dialog panel and title banner with runtime `ПЕРЕРЫВ НА БАНАН` label;
- `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, and `В МЕНЮ` controls with `420x64` touch targets;
- QA route `mtr_screen=paused&mtr_autostart=1&mtr_level=1`;
- expected runtime markers for gameplay start, startup pause, pause screen readiness, and pause surface UI gate.

## Validator behavior

The validator checks:

- JSON parse;
- schema id;
- safe-area flag;
- canvas fit mode;
- node type validity;
- referenced PNG existence;
- button touch target size;
- documented baked-button exceptions;
- no runtime label on atomic baked buttons;
- hidden EditBox strategy.

Command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704.json
```

Final command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_final.json
```

Initial name-only result: green. Superseded by the cumulative `name + menu` result below.

Menu pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_menu_pilot.json
```

Menu pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 2,
    "okCount": 2,
    "nodeCount": 17,
    "buttonCount": 9,
    "bakedButtonCount": 9,
    "assetReferenceCount": 14,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Levels pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_levels_pilot.json
```

Levels pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 3,
    "okCount": 3,
    "nodeCount": 51,
    "buttonCount": 25,
    "bakedButtonCount": 9,
    "assetReferenceCount": 47,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Playing HUD pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_playing_hud_pilot.json
```

Playing HUD pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 4,
    "okCount": 4,
    "nodeCount": 67,
    "buttonCount": 29,
    "bakedButtonCount": 9,
    "assetReferenceCount": 55,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Devgate pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_devgate_pilot.json
```

Devgate pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 5,
    "okCount": 5,
    "nodeCount": 76,
    "buttonCount": 31,
    "bakedButtonCount": 9,
    "assetReferenceCount": 61,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Sound pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_sound_pregate_fix.json
```

Sound pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 6,
    "okCount": 6,
    "nodeCount": 99,
    "buttonCount": 40,
    "bakedButtonCount": 9,
    "assetReferenceCount": 78,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Skins pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_skins_pilot.json
```

Skins pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 7,
    "okCount": 7,
    "nodeCount": 121,
    "buttonCount": 50,
    "bakedButtonCount": 9,
    "assetReferenceCount": 99,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Devpanel pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_devpanel_pilot.json
```

Devpanel pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 8,
    "okCount": 8,
    "nodeCount": 136,
    "buttonCount": 62,
    "bakedButtonCount": 9,
    "assetReferenceCount": 114,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Achievements pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_achievements_after_intl_fix.json
```

Achievements pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 9,
    "okCount": 9,
    "nodeCount": 172,
    "buttonCount": 64,
    "bakedButtonCount": 9,
    "assetReferenceCount": 139,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Records pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_records_native_bridge.json
```

Records pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 10,
    "okCount": 10,
    "nodeCount": 185,
    "buttonCount": 66,
    "bakedButtonCount": 9,
    "assetReferenceCount": 151,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

Paused pilot command:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_paused_pilot.json
```

Paused pilot cumulative result:

```json
{
  "ok": true,
  "summary": {
    "screenCount": 11,
    "okCount": 11,
    "nodeCount": 191,
    "buttonCount": 69,
    "bakedButtonCount": 9,
    "assetReferenceCount": 156,
    "problemCount": 0,
    "warningCount": 0
  }
}
```

## Issue found and fixed during validator loop

First asset validation after manifest update failed because the manifest exception `reason` contained `Start/name`, and the existing asset validator treats slash-containing strings in `ui_skin_manifest.json` as candidate resource keys.

Fix:

- changed `Start/name` to `Start name`;
- changed `DOM/Cocos` to `DOM and Cocos`;
- reran the same validator successfully.

This is now captured as a manifest-writing rule:

```text
Human-readable prose inside runtime manifests must avoid slash-looking pseudo paths unless the field is explicitly excluded from asset-reference scanning.
```

## Android/Web contract verdict

```json
{
  "skill": "android-web-contract-check",
  "verdict": "approve",
  "summary": "The UI contract is shared by Android and Web because the same Cocos GameRoot and resources are used. Static IR passes. Web build and Android emulator build pass. Android emulator runtime reached name, menu, levels, playing_hud, devgate, sound, skins, devpanel, achievements, records, and paused routes.",
  "risk": "medium",
  "requires_worktree": false,
  "requires_model": "none"
}
```

## Runtime QA evidence

Web build/runtime:

```json
{
  "buildFinished": true,
  "log": "logs/creator-module2-ui-web-r2-20260704.log",
  "name": {
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.png",
    "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json",
    "consoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl",
    "runtimeReady": true,
    "qaScreenReady": true,
    "consoleEventCount": 165
  },
  "menu": {
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.png",
    "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json",
    "consoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.console.jsonl",
    "runtimeReady": true,
    "qaScreenReady": true,
    "menuUiGateReady": true,
    "consoleEventCount": 164
  }
}
```

Android emulator build and runtime:

```json
{
  "buildFinished": true,
  "apkPayloadOk": true,
  "serial": "emulator-5554",
  "nameQaScreenReady": true,
  "menuQaScreenReady": true,
  "menuUiGateReady": true,
  "fatalException": false,
  "oldEnterName": false
}
```

Web CDP harness fix:

```json
{
  "file": "tools/web-chrome-runtime-smoke.ps1",
  "status": "fixed",
  "method": "CDP Runtime.consoleAPICalled capture before page navigation, then fresh page socket for probe/screenshot",
  "marker": "MTR_QA_SCREEN_READY screen=name",
  "runtimeReady": true,
  "waitForLogPatternReady": true,
  "consoleErrors": 0
}
```

Levels Web build/runtime:

```json
{
  "buildFinished": true,
  "log": "logs/creator-module2-levels-web-20260704.log",
  "levels": {
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.png",
    "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json",
    "consoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl",
    "runtimeReady": true,
    "qaScreenReady": true,
    "consoleEventCount": 187,
    "iconsAfterLevel8Observed": true
  }
}
```

Levels Android emulator clean pass:

```json
{
  "buildFinished": true,
  "log": "logs/creator-module2-levels-android-emulator-20260704.log",
  "serial": "emulator-5554",
  "avd": "MTR_Pixel_8_Pro_API_35",
  "cleanAppData": true,
  "runtimeReady": true,
  "qaScreenReady": true,
  "fatalException": false,
  "touchZoneMarkerInLog": false,
  "levelIconUsageCount": 15,
  "allLevelIconsObserved": true
}
```

Playing HUD Web/Android runtime:

```json
{
  "web": {
    "method": "direct-CDP startup URL smoke",
    "buildLog": "logs/creator-module2-playing-hud-web-20260704.log",
    "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.png",
    "runtimeReady": true,
    "gameplayReady": true,
    "consoleErrors": 0
  },
  "android": {
    "buildLog": "logs/creator-module2-playing-hud-android-emulator-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_screen.png",
    "runtimeReady": true,
    "gameplayReady": true,
    "fatalException": false
  }
}
```

Devgate Web/Android runtime:

```json
{
  "web": {
    "method": "Playwright console/screenshot smoke",
    "buildLog": "logs/creator-module2-devgate-web-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "consoleErrors": 0,
    "pageErrors": 0,
    "failedRequests": 0
  },
  "android": {
    "buildLog": "logs/creator-module2-devgate-android-emulator-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "fatalException": false,
    "anr": false
  }
}
```

Sound Web/Android runtime:

```json
{
  "web": {
    "method": "direct-CDP startup URL smoke",
    "buildLog": "logs/creator-module2-sound-web-gatefix-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "soundUiGateReady": true,
    "consoleErrors": 0,
    "pageErrors": 0,
    "failedRequests": 0
  },
  "android": {
    "buildLog": "logs/creator-module2-sound-android-emulator-gatefix-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "soundUiGateReady": true,
    "sharedPngAssetsObserved": true,
    "fatalException": false,
    "anr": false
  }
}
```

Skins Web/Android runtime:

```json
{
  "web": {
    "method": "direct-CDP startup URL smoke",
    "buildLog": "logs/creator-module2-skins-web-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "skinSelectGateReady": true,
    "previewUsageLogged": true,
    "consoleErrors": 0,
    "pageErrors": 0,
    "failedRequests": 0
  },
  "android": {
    "buildLog": "logs/creator-module2-skins-android-emulator-20260704.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "skinSelectGateReady": true,
    "previewUsageObserved": true,
    "fatalException": false,
    "anr": false
  }
}
```

Devpanel Web/Android runtime:

```json
{
  "web": {
    "method": "direct-CDP startup URL smoke",
    "buildLog": "logs/creator-module2-devpanel-web-20260706.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "developerGateReady": true,
    "consoleErrors": 0,
    "sharedPngAssetsObserved": true
  },
  "android": {
    "buildLog": "logs/creator-module2-devpanel-android-emulator-20260706.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "developerGateReady": true,
    "sharedPngAssetsObserved": true,
    "fatalException": false,
    "anr": false
  }
}
```

Achievements Web/Android runtime:

```json
{
  "web": {
    "method": "direct-CDP startup URL smoke",
    "buildLog": "logs/creator-module2-achievements-web-20260706-after-intl-fix.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "achievementsGateReady": true,
    "consoleErrors": 0,
    "intlErrors": 0
  },
  "android": {
    "buildLog": "logs/creator-module2-achievements-android-emulator-20260706-after-intl-fix.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix.png",
    "runtimeReady": true,
    "qaScreenReady": true,
    "achievementsGateReady": true,
    "achievementIconUsageCount": 7,
    "intlErrors": 0,
    "fatalException": false
  }
}
```

Records Web/Android runtime:

```json
{
  "web": {
    "method": "web build plus visual CDP screenshot/probe",
    "buildLog": "logs/creator-module2-records-web-20260706-table.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png",
    "recordsRowsVisible": true,
    "longNameTruncated": true,
    "tableColumnsReadable": true,
    "knownCdpConsoleCaptureFalseNegative": true
  },
  "android": {
    "buildLog": "logs/creator-module2-records-android-emulator-20260706-native-bridge.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge.png",
    "nativeStartupQueryReady": true,
    "runtimeReady": true,
    "qaScreenReady": true,
    "recordsSeeded": true,
    "recordsGateReady": true,
    "fatalException": false
  }
}
```

Paused Web/Android runtime:

```json
{
  "web": {
    "method": "web build plus visual CDP screenshot/probe",
    "buildLog": "logs/creator-module2-paused-web-20260706.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png",
    "pausePanelVisible": true,
    "touchZoneDebugLayerVisible": false,
    "knownCdpNavigateOrConsoleCaptureFalseNegative": true
  },
  "android": {
    "buildLog": "logs/creator-module2-paused-android-emulator-20260706.log",
    "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json",
    "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen.png",
    "nativeStartupQueryReady": true,
    "gameplayStartReady": true,
    "startupPauseApplied": true,
    "qaScreenReady": true,
    "pauseGateReady": true,
    "touchZoneDebugLayerVisible": false,
    "fatalException": false
  }
}
```

## Next migration step

After runtime QA passes, add IR manifests in this order:

1. `over`
2. `clear`
3. `finished`

Do not extract UI code into separate classes until at least `name`, `menu`, `levels`, `playing_hud`, `devgate`, `sound`, `skins`, `devpanel`, `achievements`, and `records` have passing IR and runtime snapshots.
