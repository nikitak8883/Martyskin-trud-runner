# CONTROL LOG CHECKPOINT — Module 2 records IR/Web/Android pass

Generated: 2026-07-06 13:35 +03:00  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Status: `pass`  
Next safe action: Module 2 `paused` UI IR pilot

## Scope

Completed the Module 2 `records` UI IR/runtime slice.

This checkpoint covers:

- records UI IR contract;
- records footer touch-target policy;
- long-name records row layout;
- deterministic records QA seed;
- Android native startup-query bridge for `mtr_seed_records`;
- Web build + screenshot/probe evidence;
- Android emulator build + strict runtime telemetry;
- hygiene cleanup of stale records diagnostics.

## Files changed in this slice

- `assets/scripts/GameRoot.ts`
  - Added `seedRecordsForQa()` behind `mtr_seed_records=1`.
  - Rendered records rows as fixed table columns instead of one long centered string.
  - Applied `fitText()` to the records name column.
  - Raised `ДОСТИЖЕНИЯ` and `НАЗАД` records footer controls to `300x64`.
- `native/engine/android/app/src/com/cocos/game/AppActivity.java`
  - Added `mtr_seed_records` to `QA_QUERY_KEYS`.
- `docs/global_modernization/manifests/ui_ir/records.ui_ir.json`
  - Added records screen contract.
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
    "report": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_records_post_hygiene.json",
    "screenCount": 10,
    "okCount": 10,
    "nodeCount": 185,
    "buttonCount": 66,
    "bakedButtonCount": 9,
    "assetReferenceCount": 151,
    "problemCount": 0,
    "warningCount": 0
  },
  "assets": {
    "report": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_records_post_hygiene.json",
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
  "buildLog": "logs/creator-module2-records-web-20260706-table.log",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png",
  "probe": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp_probe.json",
  "visualSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json",
  "recordsRowsVisible": true,
  "tableColumnsReadable": true,
  "longNameTruncated": true,
  "ghostLabelsVisible": false,
  "knownCdpConsoleCaptureFalseNegative": true
}
```

Android emulator:

```json
{
  "buildLog": "logs/creator-module2-records-android-emulator-20260706-native-bridge.log",
  "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge.png",
  "logcat": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_logcat.txt",
  "nativeStartupQueryReady": true,
  "runtimeReady": true,
  "recordsSeeded": true,
  "qaScreenReady": true,
  "recordsGateReady": true,
  "appJsErrorCount": 0,
  "fatalOrAnrCount": 0
}
```

## Issue found and fixed

First Android records QA showed the empty state because the native app passed `mtr_screen=records` but did not pass `mtr_seed_records`. This was fixed by adding `mtr_seed_records` to `AppActivity.QA_QUERY_KEYS`, then rebuilding and rerunning Android emulator QA.

## Hygiene result

Removed stale failed records diagnostics:

- pre-native-bridge Android empty-state screenshot/logcat/summary;
- black/false direct-CDP records screenshot/probe;
- pre-table records screenshot/probe;
- temporary records web server logs.

Kept accepted records evidence only:

- `web_records_table_cdp.png`
- `web_records_table_cdp_probe.json`
- `web_records_table_visual_summary.json`
- `android_records_table_native_bridge.png`
- `android_records_table_native_bridge_logcat.txt`
- `android_records_table_native_bridge_summary.json`

Post-hygiene checks:

- no listening temp ports on `9360/9361/9371/9372/9373/9479`;
- no attached ADB devices;
- no root `web_records_server*.log`;
- no `__pycache__` folders reported by the post-hygiene scan;
- UI IR, asset, and config validators remain green.

## Next safe action

Continue Module 2 with the `paused` UI IR pilot. Do not start extraction from `GameRoot.ts` until the remaining modal/end-state screens have IR and runtime snapshots.

## Hermes checkpoint

```json
{
  "id": 606,
  "trigger": "20260706-module-02-records-ir-web-android-pass-final-stop",
  "token_count": 119836,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T102421Z-20260706-module-02-records-ir-web-android-pass-final-stop.md",
  "json": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T102421Z-20260706-module-02-records-ir-web-android-pass-final-stop.json",
  "latest": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\by-project\\MTRCocosCreator-d20b07d42eaf7ab3\\LATEST.md",
  "doctor": "ok"
}
```
