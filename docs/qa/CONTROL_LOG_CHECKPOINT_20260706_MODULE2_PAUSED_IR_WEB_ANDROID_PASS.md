# CONTROL LOG CHECKPOINT — Module 2 paused IR/Web/Android pass

Generated: 2026-07-06 16:05 +03:00  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Status: `pass`  
Next safe action: Module 2 `over` UI IR pilot

## Scope

Completed the Module 2 `paused` UI IR/runtime slice.

This checkpoint covers:

- paused UI IR contract;
- pause overlay touch-target policy;
- deterministic startup-pause QA marker;
- debug touch-zone overlay suppression by default;
- Web build + screenshot/probe evidence;
- Android emulator build + strict runtime telemetry;
- hygiene cleanup of temporary server logs and emulator process.

## Files changed in this slice

- `assets/scripts/GameRoot.ts`
  - Added `pendingQaPauseShowTouchZones`.
  - Added `MTR_QA_SCREEN_READY screen=paused` after scheduled startup pause.
  - Raised `ПРОДОЛЖИТЬ`, `ЗВУК И НАСТРОЙКИ`, and `В МЕНЮ` paused buttons from `420x56` to `420x64`.
- `docs/global_modernization/manifests/ui_ir/paused.ui_ir.json`
  - Added paused screen contract.
- Reports updated:
  - `docs/codex/CURRENT_STATE.md`
  - `docs/global_modernization/ui_ir_migration_report.md`
  - `docs/global_modernization/module_execution_index.md`
  - `docs/global_modernization/code_review_report.md`
  - `docs/global_modernization/ui_inventory.md`
  - `docs/global_modernization/ui_snapshot_report.md`
  - `docs/global_modernization/agent_execution_report.md`

## QA evidence

Static validators:

```json
{
  "uiIr": {
    "report": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_paused_post_hygiene.json",
    "screenCount": 11,
    "okCount": 11,
    "nodeCount": 191,
    "buttonCount": 69,
    "bakedButtonCount": 9,
    "assetReferenceCount": 156,
    "problemCount": 0,
    "warningCount": 0
  },
  "assets": {
    "report": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_paused_post_hygiene.json",
    "pngCount": 1528,
    "blockerCount": 0,
    "whiteMatteSuspectCount": 0
  },
  "config": "MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present."
}
```

Web:

```json
{
  "buildLog": "logs/creator-module2-paused-web-20260706.log",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png",
  "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp_probe.json",
  "visualSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json",
  "pausePanelVisible": true,
  "gameplayWorldVisibleBehindOverlay": true,
  "touchZoneDebugLayerVisible": false,
  "ghostLabelsVisible": false,
  "knownCdpNavigateOrConsoleCaptureFalseNegative": true
}
```

Android emulator:

```json
{
  "buildLog": "logs/creator-module2-paused-android-emulator-20260706.log",
  "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen.png",
  "logcat": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_logcat.txt",
  "nativeStartupQueryReady": true,
  "gameplayStartReady": true,
  "startupPauseApplied": true,
  "qaScreenReady": true,
  "pauseGateReady": true,
  "touchZoneLabelObserved": false,
  "appJsErrorCount": 0,
  "fatalOrAnrCount": 0
}
```

## Issues found and handled

1. The paused buttons were below the 64px touch-target policy. Fixed by raising all three controls to `420x64`.
2. Startup pause QA previously had no screen-specific marker. Fixed with `MTR_QA_SCREEN_READY screen=paused`.
3. Startup pause QA previously forced touch-zone debug overlays. Fixed by enabling that overlay only when `mtr_show_touch_zones=1` is explicit.
4. The first temporary Web server launch failed because a path with spaces was not quoted. The server was restarted with correct quoting and the temporary log was cleaned.
5. Generic Web CDP marker capture remained unstable for this route. Web acceptance is build + visual screenshot/probe; strict runtime markers are accepted from Android emulator telemetry.

## Hygiene result

Removed temporary paused server logs:

- `web_paused_server.out.log`
- `web_paused_server.err.log`

Post-hygiene checks:

- no listening temp ports on `9380/9381/9480`;
- no attached ADB devices;
- no root `web_paused_server*.log`;
- no `__pycache__` folders reported by the post-hygiene scan;
- UI IR, asset, and config validators remain green.

## Next safe action

Continue Module 2 with the `over` UI IR pilot. Do not start extraction from `GameRoot.ts` until the remaining end-state screens have IR and runtime snapshots.

## Hermes checkpoint

```json
{
  "id": 608,
  "trigger": "20260706-module-02-paused-ir-web-android-pass-final-stop",
  "token_count": 197589,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T125853Z-20260706-module-02-paused-ir-web-android-pass-final-stop.md",
  "json": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T125853Z-20260706-module-02-paused-ir-web-android-pass-final-stop.json",
  "latest": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\by-project\\MTRCocosCreator-d20b07d42eaf7ab3\\LATEST.md",
  "doctor": "ok"
}
```
