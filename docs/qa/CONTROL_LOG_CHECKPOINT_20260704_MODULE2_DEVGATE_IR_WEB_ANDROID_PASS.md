# Control log checkpoint — Module 2 devgate IR/Web/Android pass

Generated: 2026-07-04 18:20 +03:00  
Status: `working / pass`  
Scope: bounded Module 2 continuation for the `devgate` developer password screen.  
Next safe action: continue Module 2 with `sound`.

## Summary

The developer password gate now has a UI IR contract and has been verified on Web plus Android emulator.

Runtime change was deliberately narrow:

- `ПРОВЕРИТЬ`: `240x52` at `y=420` -> `240x64` at `y=414`
- `НАЗАД`: `240x52` at `y=420` -> `240x64` at `y=414`

The visual center remains at `y=446`. Password validation stayed unchanged and still accepts `primatal` without logging the entered password.

No physical phone was used in this checkpoint. Android runtime QA stayed emulator-only.

## Files changed

Runtime:

- `assets/scripts/GameRoot.ts`

Contracts/docs:

- `docs/global_modernization/manifests/ui_ir/devgate.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`

Evidence:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_final_after_docs.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_devgate_gate.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_devgate_final_after_docs.json`
- `logs/creator-module2-devgate-web-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.console.jsonl`
- `logs/creator-module2-devgate-android-emulator-20260704.log`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json`

Diagnostic, not acceptance:

- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_direct_cdp.events.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_direct_cdp.console.jsonl`

## Commands run

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_devgate_pilot.json
```

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_devgate_gate.json
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-devgate-web-20260704.log
```

```text
Web Playwright smoke:
http://127.0.0.1:9473/?mtr_screen=devgate
wait: MTR_RUNTIME_CORE_READY + MTR_QA_SCREEN_READY screen=devgate
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-devgate-android-emulator-20260704.log
```

```powershell
adb -s emulator-5554 install -r .\build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
adb -s emulator-5554 shell pm clear com.martyskin.trudrunner
adb -s emulator-5554 shell am start -n com.martyskin.trudrunner/com.cocos.game.AppActivity --es mtr_screen devgate
```

Final post-docs gate:

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_devgate_final_after_docs.json
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_devgate_final_after_docs.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

## Tests passed

- UI IR validator: pass.
- Asset/reference validator: pass.
- Project config validator: pass.
- Web Cocos build: pass.
- Web Playwright runtime smoke for `devgate`: pass.
- Android emulator Cocos build/APK package: pass.
- Android emulator clean runtime smoke for `devgate`: pass.

## Metrics

```json
{
  "uiIr": {
    "screenCount": 5,
    "okCount": 5,
    "nodeCount": 76,
    "buttonCount": 31,
    "bakedButtonCount": 9,
    "assetReferenceCount": 61,
    "problemCount": 0,
    "warningCount": 0
  },
  "webDevgate": {
    "runtimeReady": true,
    "qaScreenReady": true,
    "consoleEventCount": 154,
    "consoleErrors": 0,
    "pageErrors": 0,
    "failedRequests": 0
  },
  "androidDevgate": {
    "serial": "emulator-5554",
    "avd": "MTR_Pixel_8_Pro_API_35",
    "cleanAppData": true,
    "runtimeReady": true,
    "qaScreenReady": true,
    "fatalException": false,
    "anr": false,
    "buttonPrimaryUsage": true,
    "buttonBackUsage": true,
    "passwordFieldUsage": true
  }
}
```

## Diagnostic note

The generic CDP wrapper produced a false negative for this route: a correct screenshot was captured, but `runtimeReady=false` and console events were empty. The final acceptance evidence uses Playwright because it captured runtime and screen markers reliably. The false-negative CDP artifacts are retained as diagnostic evidence for future harness hardening.

## Risks

- Additional aspect-ratio traversal is still pending.
- `sound`, `skins`, and `devpanel` have not yet been migrated to UI IR.
- `GameRoot.ts` remains a monolith; no UI class extraction should happen until the remaining high-risk UI screens also have IR and runtime snapshots.

## Next steps

1. Continue Module 2 with `sound`.
2. Prefer Playwright console/screenshot QA when generic CDP marker capture is unstable on a route.
3. Keep Android runtime QA emulator-only unless the user explicitly authorizes a physical device.
