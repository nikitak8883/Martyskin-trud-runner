# CONTROL LOG CHECKPOINT — Module 2 devpanel IR + Web/Android pass

Date: 2026-07-06 11:42 +03:00  
Status: `pass`  
Next safe action: continue Module 2 with `achievements`

Hermes checkpoint:

```json
{
  "id": 602,
  "trigger": "20260706-module-02-devpanel-ir-web-android-pass-final-stop",
  "token_count": 56380,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T084252Z-20260706-module-02-devpanel-ir-web-android-pass-final-stop.md",
  "latest": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\by-project\\MTRCocosCreator-d20b07d42eaf7ab3\\LATEST.md",
  "doctor": "ok"
}
```

## Scope

This checkpoint closes the bounded Module 2 `devpanel` UI slice.

Implemented:

- Added `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`.
- Updated `assets/scripts/GameRoot.ts` developer panel controls:
  - 12 debug/action buttons raised from `300x46` to `300x64`;
  - row layout normalized to `178`, `252`, `326`, `400`;
  - existing developer-gate/password behavior was not changed.
- Verified that the direct `devpanel` startup path renders through shared PNG UI assets instead of legacy fallback button layers.

No physical phone was used in this checkpoint. Android runtime QA stayed emulator-only.

## Static validation

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_devpanel_pilot.json
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_devpanel_gate.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

Result:

```json
{
  "uiIrOk": true,
  "screenCount": 8,
  "okCount": 8,
  "nodeCount": 136,
  "buttonCount": 62,
  "bakedButtonCount": 9,
  "assetReferenceCount": 114,
  "problemCount": 0,
  "warningCount": 0,
  "assetBlockerCount": 0,
  "whiteMatteSuspectCount": 0,
  "configOk": true
}
```

Post-documentation and post-hygiene validation also passed:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_final_after_docs.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_post_hygiene.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_devpanel_final_after_docs.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_devpanel_post_hygiene.json`

## Web QA

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-devpanel-web-20260706.log
```

Runtime route:

```text
http://127.0.0.1:9477/?mtr_screen=devpanel&mtr_dev=1
```

Evidence:

- `logs/creator-module2-devpanel-web-20260706.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.console.jsonl`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "developerGateReady": true,
  "sharedPanelObserved": true,
  "statusChipObserved": true,
  "primaryButtonObserved": true,
  "dangerButtonObserved": true,
  "backButtonObserved": true,
  "consoleErrorCount": 0
}
```

Diagnostic note:

- The generic `web-chrome-runtime-smoke.ps1` route probe produced a false-negative on this screen with `runtimeReady=false` and zero console events while still capturing a visually correct screenshot.
- Accepted evidence is therefore the direct-CDP smoke listed above, which observed runtime markers, shared PNG UI assets, and zero console errors.
- Diagnostic screenshot kept for comparison: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_screen_cdp.png`.

## Android emulator QA

Target policy: emulator-only.  
Target used: `emulator-5554`.

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-devpanel-android-emulator-20260706.log
```

Runtime route:

```powershell
adb -s emulator-5554 shell am start -n com.martyskin.trudrunner/com.cocos.game.AppActivity --es mtr_screen devpanel --es mtr_dev 1
```

Evidence:

- `logs/creator-module2-devpanel-android-emulator-20260706.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json`

Result:

```json
{
  "runtimeReady": true,
  "qaScreenReady": true,
  "developerGateReady": true,
  "sharedPngAssetsObserved": true,
  "fatalException": false,
  "anr": false
}
```

## Issue fixed

The `devpanel` screen still used compact text-era button geometry. Its 12 controls were below the project touch-target floor and were not represented in the UI IR inventory.

Fix:

- Added a dedicated `devpanel` UI IR manifest with shared panel, title banner, status chip, and all 12 developer controls.
- Raised developer buttons to the same 64px minimum target height used by the newer menu surfaces.
- Preserved the screen's existing debug actions and routing contract.

## Files changed in this slice

- `assets/scripts/GameRoot.ts`
- `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`
- this checkpoint file

## Handoff

Do not extract UI classes yet. Continue the Module 2 sequence with `achievements`, then `records`, `paused`, `over`, `clear`, and `finished`.

## Hygiene

- Closed local QA listeners on ports `9477`, `9388`, `9389`, `9476`, `9475`, `9387`, `9375`, `9385`, and `9386`.
- Removed temporary Chrome profiles:
  - `%TEMP%\mtr-runtime-smoke-profile-devpanel`
  - `%TEMP%\mtr-direct-cdp-devpanel-profile`
- Killed `emulator-5554`; final `adb devices` showed no connected devices.
- Removed superseded local web-server helper logs:
  - `web_devpanel_server.out.log`
  - `web_devpanel_server.err.log`
- No `__pycache__` folders were found under the project tree during this slice.
- Post-hygiene validators passed.
