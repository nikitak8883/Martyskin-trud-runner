# Control log / checkpoint — 2026-07-04 — Module 2 name + menu IR runtime pass

Status: `pass`

## Summary

Continued Module 2 UI/UX modernization from the `name` screen pilot.

Closed the previously open Web harness gap:

- `tools/web-chrome-runtime-smoke.ps1` now captures JS console markers through CDP `Runtime.consoleAPICalled` before page navigation.
- Probe/screenshot stability is protected by switching to a fresh page socket after marker capture.
- Chrome file logging remains a fallback, not the primary gate.

Added the second UI IR pilot:

- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`

No runtime code was changed for the `menu` pilot. It documents the live main menu:

- single full-canvas menu PNG backdrop;
- baked title PNG;
- six atomic baked PNG buttons in the live 2x3 layout.

## Files changed in this slice

- `tools/web-chrome-runtime-smoke.ps1`
- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`
- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/codex/CURRENT_STATE.md`

This slice also preserves previous Module 2 changes:

- `assets/scripts/GameRoot.ts`
- `assets/resources/config/ui_skin_manifest.json`
- deletion of stale `mtr_start_menu_button_enter_name_01.png` and `.meta`

## Validation

```json
{
  "uiIr": {
    "report": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_name_menu_final_after_docs.json",
    "screenCount": 2,
    "okCount": 2,
    "problemCount": 0,
    "warningCount": 0
  },
  "assets": {
    "report": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_name_menu_final.json",
    "pngCount": 1528,
    "blockerCount": 0,
    "whiteMatteSuspectCount": 0
  },
  "config": "MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present.",
  "webHarnessSyntax": "PowerShell syntax OK"
}
```

## Web runtime evidence

Name screen:

- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl`

Menu screen:

- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.console.jsonl`

Observed markers:

```text
MTR_RUNTIME_CORE_READY
MTR_QA_SCREEN_READY screen=name
MTR_QA_SCREEN_READY screen=menu
MTR_MENU_UI_GATE_READY surface=main_menu
```

## Android emulator evidence

Target policy: emulator only. No physical device was used.

AVD:

```text
MTR_Pixel_8_Pro_API_35
```

Menu runtime evidence:

- `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_logcat.txt`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_summary.json`

Summary:

```json
{
  "serial": "emulator-5554",
  "runtimeReady": true,
  "qaScreenReady": true,
  "menuUiGateReady": true,
  "fatalException": false,
  "oldEnterName": false
}
```

## Hygiene

- No `__pycache__` folders remain under the project root after this slice.
- No emulator remains attached in `adb devices`.
- No Chrome/emulator/qemu process remains from the smoke runs.
- Local HTTP server ports were stopped by the smoke wrapper commands.

## Next safe action

Continue Module 2 with:

1. `levels` UI IR pilot and visual/runtime traversal.
2. `playing_hud` UI IR pilot.

Keep using:

- CDP-backed Web runtime smoke for console marker gates;
- Android emulator-only QA unless the user explicitly authorizes physical-device testing;
- small patches with validator and visual evidence before moving to the next screen.
