# Code review report — Module 2 name/menu/levels/playing HUD/devgate/sound/skins/devpanel/achievements/records/paused UI IR pilots

Generated: 2026-07-04 14:20 +03:00  
Updated: 2026-07-06 16:05 +03:00  
Status: `pass`

## Reviewed diff scope

Runtime:

- `assets/scripts/GameRoot.ts`
- `native/engine/android/app/src/com/cocos/game/AppActivity.java`
- `assets/resources/config/ui_skin_manifest.json`

Docs/tools/evidence:

- `tools/validate-ui-ir.py`
- `tools/web-chrome-runtime-smoke.ps1`
- `docs/global_modernization/manifests/ui_ir/name_entry.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/levels.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/playing_hud.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/devgate.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/achievements.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/records.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/paused.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/codex/CURRENT_STATE.md`

Cleanup:

- removed stale `mtr_start_menu_button_enter_name_01.png`
- removed stale `mtr_start_menu_button_enter_name_01.png.meta`

## Findings

### CR-001 — Touch target policy mismatch fixed

Severity: medium  
Status: fixed

`name` screen back button had runtime bounds `442x58`, below the Module 2 minimum `64px` touch-target height.

Fix:

- changed runtime height to `64`;
- updated `name_entry.ui_ir.json` to match.

### CR-002 — UI manifest text policy contradicted live runtime

Severity: medium  
Status: fixed

The manifest said all interactive text must be runtime labels, but main/start menu buttons are intentionally atomic baked PNG buttons.

Fix:

- changed policy to `runtime-label-preferred`;
- added documented atomic baked interactive exceptions for `menu` and `name`.

### CR-003 — Stale start-menu asset removed

Severity: low  
Status: fixed

`mtr_start_menu_button_enter_name_01.png` was no longer referenced by current runtime code or manifests.

Fix:

- removed PNG and `.meta`;
- reran asset validator successfully.

### CR-004 — Web smoke harness marker capture was incomplete

Severity: medium  
Status: fixed

Web screenshot reached the `name` screen, but the previous harness only waited on Chrome file logging, so JS console marker `MTR_QA_SCREEN_READY screen=name` was not available as a reliable gate.

Fix:

- updated `tools/web-chrome-runtime-smoke.ps1` to attach CDP before page navigation;
- capture `Runtime.consoleAPICalled` / `Log.entryAdded` evidence into `*.console.jsonl`;
- keep Chrome file logging as a fallback only;
- use a fresh page socket after marker capture for stable `Runtime.evaluate` and screenshot commands.

Evidence:

```json
{
  "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json",
  "consoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl",
  "runtimeReady": true,
  "waitForLogPatternReady": true,
  "consoleErrors": 0
}
```

### CR-005 — Main menu IR pilot added without runtime mutation

Severity: low  
Status: fixed

`menu` now has a static UI IR contract for the single PNG backdrop, baked title, and six atomic baked PNG buttons. The contract matches live runtime bounds in `GameRoot.ts` and uses the existing documented baked-button exception for `menu`.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_menu_pilot.json",
  "webProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_summary.json",
  "problemCount": 0,
  "warningCount": 0
}
```

### CR-006 — Level-select icon coverage and back-button touch target fixed

Severity: medium  
Status: fixed

The `levels` screen was high-risk because of the prior report that icons after level 8 were missing. The runtime already had themed icon bindings, but the screen had no IR contract and its footer `НАЗАД` button used a `46px` touch height.

Fix:

- added `levels.ui_ir.json` with all 15 level cards and all 15 themed icon slots;
- adjusted the footer `НАЗАД` runtime bounds to `420x64` while keeping the visual center stable;
- validated Web CDP runtime evidence and Android emulator clean-pass evidence.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_pilot.json",
  "webProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json",
  "androidCleanSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "allLevelIconsObserved": true,
  "levelIconUsageCount": 15
}
```

### CR-007 — Gameplay HUD touch targets and IR coverage added

Severity: medium  
Status: fixed

The gameplay HUD was still outside the UI IR coverage and had three visible controls below the `64px` touch-target policy: `ПАУЗА`, `ПРЫЖОК / ПЛАН`, and `РЫВОК`.

Fix:

- added `playing_hud.ui_ir.json`;
- raised visible control hitboxes from `50px` to `64px`, preserving their visual centers;
- validated Web direct-CDP gameplay route and Android emulator clean gameplay route.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_playing_hud_pilot.json",
  "webProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "gameplayReady": true,
  "fatalException": false
}
```

### CR-008 — Devgate password screen touch targets and IR coverage added

Severity: medium  
Status: fixed

The developer password gate was outside UI IR coverage and had two footer controls below the `64px` touch-target policy: `ПРОВЕРИТЬ` and `НАЗАД`.

Fix:

- added `devgate.ui_ir.json`;
- raised both controls from `52px` to `64px`, preserving their visual centers;
- kept password validation unchanged and non-logging;
- validated Web Playwright route and Android emulator clean route.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_pilot.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "qaScreenReady": true,
  "fatalException": false
}
```

### CR-009 — Sound settings cold-start fallback and touch targets fixed

Severity: medium  
Status: fixed

The sound settings screen was outside UI IR coverage and had several controls below the `64px` touch-target policy. Android cold-start QA also exposed a transient fallback-outline state: the route reached `sound` before shared slider/button PNGs had finished loading.

Fix:

- added `sound.ui_ir.json`;
- raised footer, toggle, and compact `+/-` hitboxes to the `64px` touch-target policy while preserving visual centers;
- extended critical UI preload gating/logging to non-main menu-like surfaces, so `sound_settings` waits for shared PNG controls before accepted first draw;
- validated Web direct-CDP route and Android emulator clean route after rebuilding both artifacts.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_pregate_fix.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "qaScreenReady": true,
  "soundUiGateReady": true,
  "sharedPngAssetsObserved": true,
  "fatalException": false
}
```

### CR-010 — Skin-select preview gate and footer touch targets fixed

Severity: medium  
Status: fixed

The skin-select screen was outside UI IR coverage. Its footer controls used `48px` touch height, below the `64px` policy, and direct startup could reach `skins` before all base-idle primate preview PNGs were available for the accepted first draw.

Fix:

- added `skins.ui_ir.json`;
- raised footer `ВЫБРАТЬ` and `НАЗАД` controls to `300x64`, preserving visual centers;
- added all eight base-idle preview keys to the `skin_select` critical UI gate;
- validated Web direct-CDP route and Android emulator clean route after rebuilding both artifacts.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_pilot.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "qaScreenReady": true,
  "skinSelectGateReady": true,
  "previewUsageObserved": true,
  "fatalException": false
}
```

### CR-011 — Devpanel dense debug grid touch targets fixed

Severity: medium  
Status: fixed

The developer panel was outside UI IR coverage and all 12 debug/action controls used `46px` touch height, below the `64px` policy. This was especially risky because the grid is dense and used during QA.

Fix:

- added `devpanel.ui_ir.json`;
- raised all 12 developer controls to `300x64`;
- relaid the four rows with safe spacing inside the existing shared list panel;
- validated Web direct-CDP route and Android emulator clean route after rebuilding both artifacts.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_pilot.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "qaScreenReady": true,
  "developerGateReady": true,
  "sharedPngAssetsObserved": true,
  "fatalException": false
}
```

### CR-012 — Achievements native runtime `Intl` crash fixed

Severity: high  
Status: fixed

The achievements route initially passed Web build/runtime but Android emulator QA showed only the first card and then stopped rendering the rest of the achievement list. Logcat contained repeated `ReferenceError: Intl is not defined` entries from `formatAchievementDate()`. Browser/Web has `Intl`, but the Cocos native JS runtime used by the Android build does not expose it.

Fix:

- added `achievements.ui_ir.json` with 10 cards, icon slots, progress/status labels, and `300x64` footer controls;
- raised achievement card height from `80` to `86` and footer controls to `300x64`;
- added achievement icons and locked-state fallback to the critical UI gate;
- changed `formatAchievementDate()` to use `Intl.DateTimeFormat` only when available and fall back to `DD.MM.YYYY` formatting otherwise;
- rebuilt Web and Android emulator artifacts and reran runtime QA on both.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_after_intl_fix.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "qaScreenReady": true,
  "achievementsGateReady": true,
  "intlErrorCount": 0,
  "fatalException": false
}
```

### CR-013 — Records long-row layout and Android seed bridge fixed

Severity: medium  
Status: fixed

The records route had two issues before acceptance. First, every leaderboard row was rendered as one long centered string, so long primate names could collide with score/level/banana data. Second, the Android native startup-query whitelist did not include `mtr_seed_records`, so `mtr_screen=records` reached the route but deterministic records data did not arrive on native emulator launches.

Fix:

- added `records.ui_ir.json` for shared panel, title, row chips, table columns, empty state, and footer controls;
- raised `ДОСТИЖЕНИЯ` and `НАЗАД` footer controls to `300x64`;
- split row rendering into rank/name, score, level, and bananas columns;
- used `fitText()` for the name column to protect long Russian names;
- added `seedRecordsForQa()` behind `mtr_seed_records=1`;
- added `mtr_seed_records` to Android `QA_QUERY_KEYS`;
- rebuilt Web and Android emulator artifacts and reran runtime QA.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_records_native_bridge.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "recordsSeeded": true,
  "recordsGateReady": true,
  "fatalException": false
}
```

### CR-014 — Paused overlay touch targets and QA marker fixed

Severity: medium  
Status: fixed

The paused overlay was outside UI IR coverage and its three controls used `56px` touch height, below the Module 2 `64px` policy. The startup-pause QA path also reached the paused state without a screen-specific `MTR_QA_SCREEN_READY screen=paused` marker, and it forced touch-zone debug overlays even when visual UI QA did not request them.

Fix:

- added `paused.ui_ir.json` for the gameplay-world overlay, shared dialog panel, title banner, and three controls;
- raised `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, and `В МЕНЮ` to `420x64`, preserving their visual centers;
- added `MTR_QA_SCREEN_READY screen=paused` after scheduled startup pause is applied;
- changed startup-pause QA to enable touch-zone overlays only when `mtr_show_touch_zones=1` is explicit;
- rebuilt Web and Android emulator artifacts and reran runtime QA.

Evidence:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_paused_pilot.json",
  "webSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json",
  "androidSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json",
  "problemCount": 0,
  "warningCount": 0,
  "startupPauseApplied": true,
  "pauseGateReady": true,
  "touchZoneDebugLayerVisible": false,
  "fatalException": false
}
```

## Review verdict

```json
{
  "verdict": "pass",
  "runtimeRisk": "low",
  "followUpRequired": [
    "Continue Module 2 IR pilot for over"
  ],
  "blocksCheckpoint": false
}
```
