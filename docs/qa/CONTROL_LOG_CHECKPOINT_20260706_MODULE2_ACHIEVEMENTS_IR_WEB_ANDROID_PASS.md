# Control log checkpoint — Module 2 achievements IR Web/Android pass

Generated: 2026-07-06 12:23 +03:00  
Status: `pass`  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

## Scope completed

Module 2 UI/UX design-system rollout advanced from `devpanel` to `achievements`.

Implemented:

- Added `docs/global_modernization/manifests/ui_ir/achievements.ui_ir.json`.
- Updated `assets/scripts/GameRoot.ts` for the achievements route:
  - achievement icon and locked-state PNGs are part of the critical UI preload gate;
  - 10-card layout uses safer `86px` card height and adjusted row spacing;
  - `РЕКОРДЫ` and `НАЗАД` footer controls use `300x64` touch targets;
  - achievement date formatting now falls back to native-safe `DD.MM.YYYY` when `Intl` is unavailable.
- Updated modernization reports and current-state handoff docs.

## Issue found and fixed

Android native QA initially rendered only the first achievement card. Logcat showed `ReferenceError: Intl is not defined`.

Root cause:

- Web/browser runtime provides `Intl`.
- Android Cocos native JS runtime used in the emulator build did not provide `Intl`.

Fix:

- `formatAchievementDate()` now checks for `globalThis.Intl?.DateTimeFormat` and falls back to manual `DD.MM.YYYY` formatting.

## Validation passed

Static:

```json
{
  "uiIrReport": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_after_intl_fix.json",
  "uiIrScreenCount": 9,
  "uiIrProblemCount": 0,
  "uiIrWarningCount": 0,
  "assetReport": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_achievements_after_intl_fix.json",
  "assetBlockerCount": 0,
  "assetWhiteMatteSuspectCount": 0,
  "projectConfig": "MTR config OK"
}
```

Post-documentation and post-hygiene validators:

```json
{
  "uiIrFinalAfterDocs": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_final_after_docs.json",
  "assetFinalAfterDocs": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_achievements_final_after_docs.json",
  "uiIrPostHygiene": "docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_post_hygiene.json",
  "assetPostHygiene": "docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_achievements_post_hygiene.json",
  "projectConfigPostHygiene": "MTR config OK"
}
```

Web:

```json
{
  "buildLog": "logs/creator-module2-achievements-web-20260706-after-intl-fix.log",
  "summary": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.png",
  "console": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.console.jsonl",
  "runtimeReady": true,
  "qaScreenReady": true,
  "achievementsGateReady": true,
  "consoleErrorCount": 0,
  "intlErrorCount": 0
}
```

Android emulator:

```json
{
  "serial": "emulator-5554",
  "buildLog": "logs/creator-module2-achievements-android-emulator-20260706-after-intl-fix.log",
  "summary": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json",
  "screenshot": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix.png",
  "logcat": "docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_logcat.txt",
  "runtimeReady": true,
  "qaScreenReady": true,
  "achievementsGateReady": true,
  "achievementIconUsageCount": 7,
  "intlErrorCount": 0,
  "fatalOrAnrCount": 0
}
```

## Next safe action

Continue Module 2 with the `records` UI IR pilot.

Recommended order:

1. Retrieve bounded context for `records` in `GameRoot.ts`.
2. Add `records.ui_ir.json`.
3. Apply only necessary runtime/touch-target/preload fixes.
4. Run static validators.
5. Rebuild Web and Android emulator artifacts.
6. Run Web direct-CDP QA and Android emulator QA.
7. Update reports, run hygiene, and checkpoint.

## Hygiene and Hermes

Cleanup completed:

- stopped the local Web server on port `9478`;
- removed temporary `web_achievements_server*.log`;
- removed stale pre-fix achievements evidence files that could be confused with accepted evidence;
- stopped the Android emulator after QA.

Post-hygiene state:

```json
{
  "ports9358_9359_9478": [],
  "pycache": [],
  "serverLogs": [],
  "adbDevices": []
}
```

Hermes checkpoint:

```json
{
  "id": 604,
  "trigger": "20260706-module-02-achievements-ir-web-android-pass-final-stop",
  "token_count": 136382,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "doctor": "ok",
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T093043Z-20260706-module-02-achievements-ir-web-android-pass-final-stop.md"
}
```

## Stop/guard notes

- Keep Android runtime QA emulator-only unless the user explicitly authorizes physical-device work.
- Do not push or create a release artifact from this checkpoint alone; this is an internal Module 2 slice.
- Preserve accepted evidence files listed above.
