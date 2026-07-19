# CONTROL LOG CHECKPOINT — Module 2 skins IR + Web/Android pass

Date: 2026-07-04 19:34 +03:00  
Status: `pass`  
Next safe action: continue Module 2 with `devpanel`

Hermes checkpoint:

```json
{
  "id": 597,
  "trigger": "20260704-module-02-skins-ir-web-android-pass-final-stop",
  "token_count": 125613,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260704T164600Z-20260704-module-02-skins-ir-web-android-pass-final-stop.md",
  "latest": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\by-project\\MTRCocosCreator-d20b07d42eaf7ab3\\LATEST.md",
  "doctor": "ok"
}
```

## Scope

This checkpoint closes the bounded Module 2 `skins` UI slice.

Implemented:

- Added `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`.
- Updated `assets/scripts/GameRoot.ts` skin-select controls:
  - footer buttons `ВЫБРАТЬ` and `НАЗАД`: `300x48 @ y=624` -> `300x64 @ y=616`, preserving visual center;
  - `skin_select` critical UI gate now includes all eight base-idle primate preview PNGs;
  - direct `skins` startup now waits for the `skin_select` gate before accepted first draw.

No physical phone was used in this checkpoint. Android runtime QA stayed emulator-only.

## Static validation

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_skins_pilot.json
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_skins_gate.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

Result:

```json
{
  "uiIrOk": true,
  "screenCount": 7,
  "nodeCount": 121,
  "buttonCount": 50,
  "bakedButtonCount": 9,
  "assetReferenceCount": 99,
  "problemCount": 0,
  "warningCount": 0,
  "assetBlockerCount": 0,
  "whiteMatteSuspectCount": 0,
  "configOk": true
}
```

Post-documentation and post-hygiene validation also passed:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_final_after_docs.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_post_hygiene.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_skins_final_after_docs.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_skins_post_hygiene.json`

## Web QA

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-skins-web-20260704.log
```

Runtime route:

```text
http://127.0.0.1:9476/?mtr_screen=skins
```

Evidence:

- `logs/creator-module2-skins-web-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.console.jsonl`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "skinSelectGateReady": true,
  "previewUsageLogged": true,
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
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-skins-android-emulator-20260704.log
```

Runtime route:

```powershell
adb -s emulator-5554 shell am start -n com.martyskin.trudrunner/com.cocos.game.AppActivity --es mtr_screen skins
```

Evidence:

- `logs/creator-module2-skins-android-emulator-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "skinSelectGateReady": true,
  "previewUsageObserved": true,
  "fatalException": false,
  "anr": false
}
```

## Issue fixed

The previous `sound` slice proved that secondary menu-like screens can briefly show fallback outlines if accepted before their shared PNG controls finish loading. The `skins` route is heavier because it also renders eight player preview sprites.

Fix:

- `criticalMenuUiSpriteKeys('skin_select')` now includes every `playerSkinPreviewAssetKey(index)`.
- The accepted Web and Android screenshots are captured only after:
  - `MTR_QA_SCREEN_READY screen=skins`
  - `MTR_MENU_UI_GATE_READY surface=skin_select`
  - `MTR_ASSET_USAGE ... reason=menu_skin_preview`

## Files changed in this slice

- `assets/scripts/GameRoot.ts`
- `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`
- this checkpoint file

## Handoff

Do not extract UI classes yet. Continue the Module 2 sequence with `devpanel`, then `achievements`, then `records` and the remaining dense UI screens.

## Hygiene

- Closed local QA listeners on ports `9476`, `9475`, `9387`, `9375`, `9385`, and `9386`.
- Removed temporary Chrome profile:
  - `%TEMP%\mtr-direct-cdp-skins-profile`
- Killed `emulator-5554`; final `adb devices` showed no connected devices.
- Removed superseded local web-server helper logs:
  - `web_skins_server.out.log`
  - `web_skins_server.err.log`
- No `__pycache__` folders were found under the project tree during this slice.
- Post-hygiene validators passed.
