# Control log checkpoint — Module 2 playing HUD IR/Web/Android pass

Generated: 2026-07-04 17:46 +03:00  
Status: `working / pass`  
Scope: bounded Module 2 continuation for the `playing_hud` screen.  
Next safe action: continue Module 2 with `devgate`.

## Summary

The gameplay HUD now has a UI IR contract and has been verified on Web plus Android emulator.

The HUD control touch targets were raised to the project minimum without changing gameplay mechanics:

- `ПАУЗА`: `150x50` at `y=90` -> `150x64` at `y=83`
- `ПРЫЖОК / ПЛАН`: `350x50` at `y=626` -> `350x64` at `y=619`
- `РЫВОК`: `270x50` at `y=626` -> `270x64` at `y=619`

No physical phone was used in this checkpoint. Android runtime QA stayed emulator-only.

## Files changed

Runtime:

- `assets/scripts/GameRoot.ts`

Contracts/docs:

- `docs/global_modernization/manifests/ui_ir/playing_hud.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`

Evidence:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_playing_hud_pilot.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_playing_hud_gate.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json`
- `logs/creator-module2-playing-hud-web-20260704.log`
- `logs/creator-module2-playing-hud-android-emulator-20260704.log`
- `logs/web-playing-hud-direct-cdp-browser-20260704.log`

## Commands run

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_playing_hud_pilot.json
```

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_playing_hud_gate.json
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-playing-hud-web-20260704.log
```

```text
Direct Chrome DevTools smoke:
http://127.0.0.1:9477/?mtr_dev=1&mtr_autostart=1&mtr_level=1&mtr_qa_skin=lab_assistant_act&mtr_qa_variant=default
wait: MTR_GAMEPLAY_START_GATE_READY level=1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-playing-hud-android-emulator-20260704.log
```

```powershell
adb -s emulator-5554 install -r .\build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
adb -s emulator-5554 shell pm clear com.martyskin.trudrunner
adb -s emulator-5554 shell am start -n com.martyskin.trudrunner/com.cocos.game.AppActivity --es mtr_dev 1 --es mtr_autostart 1 --es mtr_level 1 --es mtr_qa_skin lab_assistant_act --es mtr_qa_variant default
```

## Tests passed

- UI IR validator: pass.
- Asset/reference validator: pass.
- Project config validator: pass.
- Web Cocos build: pass.
- Web direct-CDP runtime smoke for gameplay/HUD: pass.
- Android emulator Cocos build/APK package: pass.
- Android emulator clean runtime smoke for gameplay/HUD: pass.

## Metrics

```json
{
  "uiIr": {
    "screenCount": 4,
    "okCount": 4,
    "nodeCount": 67,
    "buttonCount": 29,
    "bakedButtonCount": 9,
    "assetReferenceCount": 55,
    "problemCount": 0,
    "warningCount": 0
  },
  "webPlayingHud": {
    "runtimeReady": true,
    "gameplayReady": true,
    "consoleEventCount": 307,
    "consoleErrors": 0,
    "hudPanelUsageCount": 2,
    "hudControlUsageCount": 1
  },
  "androidPlayingHud": {
    "serial": "emulator-5554",
    "avd": "MTR_Pixel_8_Pro_API_35",
    "cleanAppData": true,
    "runtimeReady": true,
    "gameplayReady": true,
    "fatalException": false,
    "hudPanelUsageCount": 2,
    "hudControlUsageCount": 1,
    "playerPoseLabAssistant": true
  }
}
```

## Diagnostic note

`tools/web-chrome-runtime-smoke.ps1` timed out waiting for CDP `Page.navigate` on the gameplay startup route. The wrapper was not modified in this final state. The successful Web gameplay evidence uses a direct-CDP startup-URL smoke path, avoiding `Page.navigate`.

Failed intermediate wrapper evidence was removed during hygiene cleanup.

## Risks

- Additional aspect-ratio traversal is still pending.
- `devgate` has not yet been migrated to UI IR.
- `GameRoot.ts` remains a monolith; no UI class extraction should happen until the remaining high-risk UI screens also have IR and runtime snapshots.

## Next steps

1. Continue Module 2 with `devgate`.
2. Repeat the same gate: UI IR validator, asset validator, Web route smoke, Android emulator route smoke where relevant, code review, hygiene, checkpoint.
3. Separately harden `tools/web-chrome-runtime-smoke.ps1` for gameplay `Page.navigate` only if a future slice needs to reuse the generic wrapper for gameplay routes.
