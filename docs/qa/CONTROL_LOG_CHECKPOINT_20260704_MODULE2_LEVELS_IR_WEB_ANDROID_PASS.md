# Control log checkpoint — Module 2 levels IR/Web/Android pass

Generated: 2026-07-04 15:35 +03:00  
Status: `working / pass`  
Scope: bounded Module 2 continuation for the `levels` screen.  
Next safe action: continue Module 2 with `playing_hud`.

## Summary

The `levels` screen is now covered by a UI IR contract and verified on Web plus Android emulator.

The prior risk — themed icons missing after level 8 — is covered by runtime evidence: all 15 level-select themed icons were observed in Web CDP console evidence and Android emulator clean-pass log summary.

No physical phone was used in this checkpoint. Android runtime QA stayed emulator-only.

## Files changed

Runtime:

- `assets/scripts/GameRoot.ts`
  - `levels` footer `НАЗАД` button touch target changed from `420x46` at `y=634` to `420x64` at `y=625`, preserving the visual center.

Contracts/docs:

- `docs/global_modernization/manifests/ui_ir/levels.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/codex/CURRENT_STATE.md`

Evidence:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_final_after_docs.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_levels_gate.json`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_levels_final_after_docs.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_summary.json`
- `logs/creator-module2-levels-web-20260704.log`
- `logs/creator-module2-levels-android-emulator-20260704.log`

## Commands run

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_levels_pilot.json
```

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_levels_gate.json
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -LogDest .\logs\creator-module2-levels-web-20260704.log
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -LogDest .\logs\creator-module2-levels-android-emulator-20260704.log
```

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_levels_final_after_docs.json
```

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_levels_final_after_docs.json
```

```powershell
$errors = $null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path '.\tools\web-chrome-runtime-smoke.ps1'), [ref]$null, [ref]$errors)
```

## Tests passed

- UI IR validator: pass.
- Asset/reference validator: pass.
- Project config validator: pass.
- Web Cocos build: pass.
- Web CDP runtime smoke for `?mtr_screen=levels&mtr_dev=1`: pass.
- Android emulator Cocos build/APK package: pass.
- Android emulator clean runtime smoke for `mtr_screen=levels`: pass.
- Hygiene checks:
  - no `__pycache__` directories found;
  - `adb devices` shows no attached devices after QA;
  - no active `chrome`, `emulator`, or `qemu-system-x86_64` processes from this task.
  - targeted `TODO|FIXME|HACK|TEMP|DEBUG` scan found only expected existing/intentional markers:
    - `$ProfileDir` in `tools/web-chrome-runtime-smoke.ps1`, used as a temporary isolated Chrome profile path;
    - `PLAYER DEBUG BOX` in `assets/scripts/GameRoot.ts`, an existing QA overlay marker outside this patch scope.

## Metrics

```json
{
  "uiIr": {
    "screenCount": 3,
    "okCount": 3,
    "nodeCount": 51,
    "buttonCount": 25,
    "bakedButtonCount": 9,
    "assetReferenceCount": 47,
    "problemCount": 0,
    "warningCount": 0
  },
  "assets": {
    "pngCount": 1528,
    "blockerCount": 0,
    "whiteMatteSuspectCount": 0
  },
  "webLevels": {
    "runtimeReady": true,
    "qaScreenReady": true,
    "consoleEventCount": 187
  },
  "androidLevelsClean": {
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
}
```

## Risks

- Additional aspect-ratio visual traversal is still pending.
- `playing_hud` has not yet been migrated to UI IR.
- `GameRoot.ts` remains a monolith; no UI class extraction should happen until `playing_hud` also has IR and runtime snapshots.

## Next steps

1. Continue Module 2 with `playing_hud`.
2. Repeat the same gate: UI IR validator, asset validator, Web CDP runtime smoke, Android emulator clean runtime smoke, code review, hygiene, checkpoint.
3. Only after `name`, `menu`, `levels`, and `playing_hud` are all green, consider UI class extraction.
