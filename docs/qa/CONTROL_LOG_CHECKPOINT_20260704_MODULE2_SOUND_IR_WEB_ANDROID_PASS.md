# CONTROL LOG CHECKPOINT — Module 2 sound IR + Web/Android pass

Date: 2026-07-04 19:04 +03:00  
Status: `pass`  
Next safe action: continue Module 2 with `skins`

## Scope

This checkpoint closes the bounded Module 2 `sound` UI slice.

Implemented:

- Added `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`.
- Updated `assets/scripts/GameRoot.ts` sound settings controls:
  - footer buttons `ПО УМОЛЧАНИЮ`, `ПРИМЕНИТЬ`, `НАЗАД`: `240x46 @ y=558` -> `240x64 @ y=549`, preserving visual center;
  - row toggles: visual bounds remain `124x48`, touch bounds are now `124x64`;
  - compact `+/-` controls: `58x46` -> `64x64`, preserving visual centers.
- Fixed cold-start fallback on direct `sound` startup by extending critical UI preload gating/logging to non-main menu-like surfaces.

## Static validation

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_sound_pregate_fix.json
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_sound_pregate_fix.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

Result:

```json
{
  "uiIrOk": true,
  "screenCount": 6,
  "nodeCount": 99,
  "buttonCount": 40,
  "bakedButtonCount": 9,
  "assetReferenceCount": 78,
  "problemCount": 0,
  "warningCount": 0,
  "assetBlockerCount": 0,
  "whiteMatteSuspectCount": 0,
  "configOk": true
}
```

Post-hygiene validation also passed:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_post_hygiene.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_sound_post_hygiene.json`

## Web QA

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-sound-web-gatefix-20260704.log
```

Runtime route:

```text
http://127.0.0.1:9475/?mtr_screen=sound
```

Evidence:

- `logs/creator-module2-sound-web-gatefix-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.console.jsonl`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "soundUiGateReady": true,
  "consoleErrorCount": 0,
  "pageErrorCount": 0,
  "requestFailedCount": 0
}
```

## Android emulator QA

Target policy: emulator-only.  
Target used: `emulator-5554`.

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-sound-android-emulator-gatefix-20260704.log
```

Runtime route:

```powershell
adb -s emulator-5554 shell am start -n com.martyskin.trudrunner/com.cocos.game.AppActivity --es mtr_screen sound
```

Evidence:

- `logs/creator-module2-sound-android-emulator-gatefix-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "soundUiGateReady": true,
  "soundSharedPngAssetsObserved": true,
  "fatalException": false,
  "anr": false
}
```

## Issue found and fixed

Initial Android screenshot reached `sound` but showed temporary fallback outlines for footer and compact buttons because shared secondary UI PNGs were still loading. This was not accepted as final evidence.

Fix:

- `drawMenu()` now determines a `criticalSurface` for every menu-like screen.
- `preloadCriticalMenuUiSprites()`, `areCriticalMenuUiSpritesReady()`, and `missingCriticalMenuUiSprites()` now gate non-main surfaces before the first full draw.
- Logs are tracked per surface:
  - `MTR_MENU_UI_CRITICAL_PRELOAD_REQUESTED reason=menu-frame surface=sound_settings`
  - `MTR_MENU_UI_GATE_WAIT surface=sound_settings ...`
  - `MTR_MENU_UI_GATE_READY surface=sound_settings`

The accepted Web and Android screenshots were captured after the gate-ready marker and show PNG controls instead of fallback outlines.

## Files changed in this slice

- `assets/scripts/GameRoot.ts`
- `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`
- this checkpoint file

## Handoff

Do not extract UI classes yet. Continue the Module 2 sequence with `skins`, then `devpanel`, then remaining dense UI screens.

## Hygiene

- Closed local QA listeners on ports `9475`, `9375`, `9385`, and `9386`.
- Removed temporary Chrome profiles:
  - `%TEMP%\mtr-runtime-smoke-profile-sound`
  - `%TEMP%\mtr-direct-cdp-sound-profile`
  - `%TEMP%\mtr-direct-cdp-sound-gatefix-profile`
- Killed `emulator-5554`; final `adb devices` showed no connected devices.
- Removed superseded `sound` pre-gate diagnostic screenshots/logs and retained only final `gatefix` evidence:
  - `android_sound_gatefix.png`
  - `android_sound_gatefix_logcat.txt`
  - `android_sound_gatefix_summary.json`
  - `web_sound_gatefix_direct_cdp.png`
  - `web_sound_gatefix_direct_cdp_probe.json`
  - `web_sound_gatefix_direct_cdp.console.jsonl`
- No `__pycache__` folders found under the project tree.
