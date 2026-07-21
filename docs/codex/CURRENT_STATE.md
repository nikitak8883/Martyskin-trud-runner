# CURRENT_STATE — Martyshkin Trud Runner

Generated: 2026-07-02 15:44 +03:00  
Updated: 2026-07-21  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Purpose: compact resume point for Codex/Hermes/local-worker runs.

## Current implementation line

Status: `runtime_baseline_reported_green / source_frozen / m00_complete / m01_5_complete / release_blocked`

## 2026-07-19 v3 revalidation overlay

The sections below preserve the detailed Tasks/4 implementation history, but their old "next action" is superseded.

- M00 itself did not modify game runtime behavior; it classified, froze, fingerprinted and restore-tested the accepted working source.
- Read-only Git/Web/Android/evidence revalidation is complete under `docs/current_audit/`.
- The integrated M00-M12 plan is under `docs/global_modernization/v3/`.
- M00.1–M00.6 are complete: source commit `12670452ae4580ef5c685ff986476daf91522978`, tree `9faa768c9b81f94b7745c917b6d7d49b7cef884c`, annotated tag `mtr-source-freeze-v3-20260719`, verified source/Pages bundles and offline restore rehearsal PASS.
- Pages is now an explicit submodule pinned to `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`; the primary parent repository still has no remote.
- M01.1 is complete: `32/32` tracked tool surfaces are classified with commands, side effects, timeout and evidence contracts; static D4 checks passed without build/runtime execution.
- M01.2 is complete: 3 canonical evidence schemas, 18 classified source families, 11 active fail-closed adapters, 11 positive and 20 negative fixtures, 25 deterministic reruns and 9 current report-shape smokes pass.
- M01.3 is complete: 2 runner schemas and `tools/codex/quality-gate/` provide typed shell-free execution, complete process-tree timeout, path/output containment, atomic reports, adapter activation, source/protected-input revalidation and an isolated pinned Draft 2020-12 validator. No game-runtime file changed.
- M01.4 is complete: 3 profile schemas plus a canonical D4/P4/M2_PLUS/QA7/RC2 catalog, explicit applicability semantics and a fail-closed aggregate evaluator now compose fresh M01.3 reports. The isolated unit/integration suite passes 44/44 executable tests with 2 expected platform skips. No game-runtime file changed.
- M01.5 is complete: a delete-incapable index-first classifier reconciles 801/801 evidence files, verifies accepted anchors and records 68 protected, 207 retained_recent and 526 rotatable review-only entries. No evidence or game-runtime file was deleted, moved or rewritten.
- Current next action: resolve the primary source remote decision, then execute `M01.6` CI or documented mandatory local command parity; release recovery and runtime patches remain dependency-blocked.
- Current release status: blocked by Web/Pages drift, absence of a current arm64 artifact from the accepted source, unresolved production signing and missing embedded content version.

The latest known game runtime line is Android/Web capable and has a validated live Web build. The current task line is the Tasks/4 global modernization rollout. Module 0/10 scaffold is in place, Module 1 non-mutating asset/reference validation passes, Module 3 static skin/bonus matrix, contact sheet evidence, and selected Android emulator QA pass, and Module 2 now has `name`, `menu`, `levels`, `playing_hud`, `devgate`, `sound`, `skins`, `devpanel`, `achievements`, `records`, and `paused` UI IR pilots with Web runtime evidence plus Android emulator runtime evidence.

The latest Module 2 slice changed runtime code/assets narrowly:

- `assets/scripts/GameRoot.ts`
  - `name` screen `В МЕНЮ` touch target height raised from 58 to 64.
  - `levels` screen `НАЗАД` touch target raised from `420x46` to `420x64`, preserving its visual center.
  - `playing_hud` `ПАУЗА`, `ПРЫЖОК / ПЛАН`, and `РЫВОК` buttons raised from 50px to 64px touch height, preserving visual centers.
  - `devgate` `ПРОВЕРИТЬ` and `НАЗАД` buttons raised from 52px to 64px touch height, preserving visual centers.
  - `sound` footer buttons raised from `240x46` to `240x64`, toggle touch zones raised to `124x64`, and compact `+/-` buttons raised from `58x46` to `64x64`, preserving visual centers.
  - `skins` footer buttons raised from `300x48` to `300x64`, preserving visual centers.
  - `devpanel` 12-button debug grid raised from `300x46` to `300x64`, with rows relaid to preserve readable spacing.
  - `achievements` 10-card grid raised from `80px` cards to `86px` cards, footer buttons raised to `300x64`, and row spacing adjusted for dense Cyrillic text.
  - `achievements` critical UI gate now includes every achievement icon plus `ui_level_lock_01` before the accepted first draw.
  - `formatAchievementDate()` now uses a native-safe fallback when Android's JS runtime does not provide `Intl`, preventing partial achievement-screen renders on native builds.
  - `records` footer buttons raised from `300x48` to `300x64`.
  - `records` rows now render as fixed table columns for rank/name, score, level, and bananas; long names are fitted in the name column instead of collapsing the whole row.
  - `records` QA seeding added behind `mtr_seed_records=1`, with `MTR_RECORDS_QA_SEEDED` runtime marker for deterministic records-table QA.
  - `paused` overlay buttons raised from `420x56` to `420x64`, preserving visual centers.
  - Startup pause QA now logs `MTR_QA_SCREEN_READY screen=paused` after applying the scheduled pause.
  - Startup pause QA no longer forces touch-zone debug overlays unless `mtr_show_touch_zones=1` is explicitly passed.
  - Non-main menu-like surfaces now pass a per-surface critical UI preload gate before full first draw; this prevents cold-start fallback outlines on direct `sound` and `skins` startup.
  - `skin_select` critical UI gate now includes all eight base-idle player preview PNGs.
  - `mtr_screen` / `mtr_state` QA startup routing added for menu-like screens with `MTR_QA_SCREEN_READY`.
- `native/engine/android/app/src/com/cocos/game/AppActivity.java`
  - `mtr_seed_records` added to the Android native startup-query extras whitelist, fixing the Android QA route where `mtr_screen=records` arrived but seeded records did not.
- `assets/resources/config/ui_skin_manifest.json`
  - atomic baked interactive button exceptions documented for `menu` and `name`.
- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`
  - main menu UI IR pilot added for single PNG backdrop, baked title, and 2x3 atomic PNG button grid.
- `docs/global_modernization/manifests/ui_ir/levels.ui_ir.json`
  - level-select UI IR pilot added for panel, title, 15 card buttons, 15 themed icon slots, and footer navigation.
- `docs/global_modernization/manifests/ui_ir/playing_hud.ui_ir.json`
  - gameplay HUD UI IR pilot added for HUD panels, labels, pause touch zone, bottom controls, toast area, and developer badge.
- `docs/global_modernization/manifests/ui_ir/devgate.ui_ir.json`
  - developer gate UI IR pilot added for dialog panel, password field, hidden EditBox, status chip, and footer buttons.
- `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`
  - sound settings UI IR pilot added for settings rows, toggles, sliders, compact volume buttons, and footer controls.
- `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`
  - skin-select UI IR pilot added for 4x2 primate card grid, eight base-idle preview PNG slots, selected status chip, and footer controls.
- `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`
  - developer panel UI IR pilot added for shared list panel, status chip, and 12 debug/action controls.
- `docs/global_modernization/manifests/ui_ir/achievements.ui_ir.json`
  - achievements UI IR pilot added for shared achievements panel, title banner, profile chip, 10 achievement cards, icon slots, progress/status labels, and footer controls.
- `docs/global_modernization/manifests/ui_ir/records.ui_ir.json`
  - records UI IR pilot added for shared list panel, title banner, empty state, seven record row chips, fixed table columns, and footer navigation.
- `docs/global_modernization/manifests/ui_ir/paused.ui_ir.json`
  - paused UI IR pilot added for gameplay-world backdrop, pause dialog panel, title banner, and three pause controls.
- Removed stale unused `mtr_start_menu_button_enter_name_01.png` and `.meta`.

## Latest validated Web state

- Live URL: `https://nikitak8883.github.io/Martyskin-trud-runner/`
- GitHub Pages worktree:
  - `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`
  - branch: `main`
  - HEAD: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
  - status at snapshot: clean
- Last live runtime gate:
  - `MTR_GAMEPLAY_START_GATE_READY level=15`
- Harness note:
  - `tools\web-chrome-runtime-smoke.ps1` must be used with background/occlusion throttling disabled, as already patched.
  - For UI screen gates, the same harness now captures JS console markers through CDP `Runtime.consoleAPICalled` before page navigation.

## Latest Android release artifact

- APK: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260701-next-big-patch-release.apk`
- Size: `137968594` bytes
- SHA-256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`
- Last write: `2026-07-01T11:39:45.8777418+03:00`
- Known ABI policy:
  - final/release APK must be device-valid;
  - emulator-only `x86_64` artifacts are QA artifacts only.

## Android QA target policy

- Default Android runtime QA target: emulator only.
- Physical device testing/install requires explicit user authorization.
- If explicitly authorized, use:
  - serial: `R5CY933XP7P`
  - user profile: `--user 0`
  - install form:

```powershell
adb -s R5CY933XP7P install --user 0 -r "<release-apk>"
```

## Latest Tasks/4 audit

- Audit plan:
  - `docs\global_modernization\TASKS4_AUDIT_AND_IMPLEMENTATION_PLAN_20260702.md`
- SHA-256:
  - `0DB11FFD9F2AD61E72C111221A9BB10696FFE5A4C6EB2766841AD8BF884DDEE3`
- Tasks/4 unpacked source:
  - `C:\Projects\Monkey Work\Tasks\4\_unpacked_20260702_145527`
- Runtime PNG white-matte scan:
  - `docs\qa\evidence\20260702_tasks4_audit\white_matte_scan_20260702.json`
  - result: `checkedCount=978`, `suspectCount=0`, `fixedCount=0`

## Latest local checkpoint log

- `docs\qa\CONTROL_LOG_CHECKPOINT_20260721_M01_5_EVIDENCE_RETENTION.md`
- status: `pass`
- next safe action: resolve the primary source remote decision, then execute `M01.6` CI/local parity

## Required next implementation order

1. M01.1 complete: preserve the `32/32` inventory and its explicit false-green/timeout/side-effect findings.
2. M01.2 complete: preserve canonical schema namespace, adapter allowlist and positive/negative fixtures.
3. M01.3 complete: preserve the typed runner, isolated lock and fail-closed self-test evidence.
4. M01.4 complete: preserve typed D4/P4/M2_PLUS/QA7/RC2 profiles, explicit applicability and stale/reuse/source protections.
5. M01.5 complete: preserve the delete-incapable 801-file retention dry-run, exact output allowlist and protected/recent/rotatable classification.
6. Resolve the primary source remote decision and execute M01.6 CI or documented mandatory local parity.
7. Execute M01.7 release-blocking summary after M01.6 parity is accepted.
8. Execute M02 technical release recovery from the frozen source before any external release claim.
8. Resume M03+ runtime modernization only through the dependency-gated work-package index.

## Hard rules

- No destructive cleanup without dry-run and approval.
- No Cocos version upgrade without explicit approval.
- No `git reset --hard`, force push, or broad cleanup.
- No old/new UI systems active on the same screen.
- No release claim without Web + Android smoke evidence.
- Web and Android must share a content manifest version before the next release claim.
- Run QA before and after optimization.

## Current known tails

- `Tasks/4/_unpacked_20260702_145527/` is an input working copy, not a runtime asset.
- `docs\qa\evidence\20260702_tasks4_audit\` contains read-only audit evidence.
- Python `__pycache__` folders under `tools\` were removed during the 2026-07-04 hygiene gate.
- `tools\validate-assets.py` is the current non-mutating Module 1 validator.
- `tools\validate-skin-bonus-matrix.py` is the current non-mutating Module 3 validator.
- `tools\render-skin-contact-sheets.py` creates non-runtime Module 3 visual evidence.
- `docs\global_modernization\skin_bonus_emulator_qa_report.md` is the current selected Android emulator QA report for Module 3.
- `tools\validate-ui-ir.py` is the current non-mutating Module 2 UI IR validator.
- `docs\global_modernization\manifests\ui_ir\name_entry.ui_ir.json` is the first UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\menu.ui_ir.json` is the second UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\levels.ui_ir.json` is the third UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\playing_hud.ui_ir.json` is the fourth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\devgate.ui_ir.json` is the fifth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\sound.ui_ir.json` is the sixth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\skins.ui_ir.json` is the seventh UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\devpanel.ui_ir.json` is the eighth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\achievements.ui_ir.json` is the ninth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\records.ui_ir.json` is the tenth UI IR pilot.
- `docs\global_modernization\manifests\ui_ir\paused.ui_ir.json` is the eleventh UI IR pilot.
- Latest validator evidence:
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_emulator_gate.json`
  - `docs\qa\evidence\20260704_module3_skin_bonus_matrix\skin_bonus_matrix_20260704.json`
  - `docs\qa\evidence\20260704_module3_skin_bonus_matrix\skin_bonus_matrix_20260704_emulator_gate.json`
  - `docs\qa\evidence\20260704_module3_contact_sheets\contact_sheet_manifest.json`
  - `docs\qa\evidence\20260704_module3_emulator_skin_bonus\module3_emulator_skin_bonus_qa_20260704_final.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_final.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_levels_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_levels_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_playing_hud_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_playing_hud_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_devgate_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_devgate_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_sound_pregate_fix.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_sound_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_sound_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_skins_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_skins_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704_skins_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_devpanel_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_devpanel_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_devpanel_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_achievements_after_intl_fix.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_achievements_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_achievements_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_records_native_bridge.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_records_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_records_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_paused_pilot.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_paused_final_after_docs.json`
  - `docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260706_paused_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_module2_final.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_levels_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_levels_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_playing_hud_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_playing_hud_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_devgate_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_devgate_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_sound_pregate_fix.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_sound_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_sound_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_skins_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_skins_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704_skins_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_devpanel_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_devpanel_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_devpanel_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_achievements_after_intl_fix.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_achievements_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_achievements_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_records_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_records_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_records_post_hygiene.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_paused_gate.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_paused_final_after_docs.json`
  - `docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260706_paused_post_hygiene.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_name_screen_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_levels_screen_clean_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_playing_hud_direct_cdp_probe.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_playing_hud_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_devgate_playwright_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_devgate_screen_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_sound_gatefix_direct_cdp_probe.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_sound_gatefix_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_skins_direct_cdp_probe.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_skins_screen_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_devpanel_direct_cdp_probe.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_devpanel_screen_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_achievements_after_intl_fix_direct_cdp_probe.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_achievements_after_intl_fix_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_records_table_visual_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_records_table_native_bridge_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\web_paused_screen_visual_summary.json`
  - `docs\qa\evidence\20260704_module2_ui_runtime\android_paused_screen_summary.json`
- Historical root `creator-*.log` files are cleanup candidates only after evidence preservation review.
- Root git sees nested `_github\Martyskin-trud-runner` as modified because it is a nested worktree; do not stage it from the parent repo by accident.
- Latest hygiene gate for the achievements slice removed temporary Web server logs, stale pre-fix achievements evidence, stopped the local `9478` server, and stopped the Android emulator. Post-hygiene checks showed no listened ports on `9358/9359/9478`, no `__pycache__`, no `web_achievements_server*.log`, and no attached ADB devices.

## Latest Module 1 reference validator evidence

```json
{
  "pngCount": 1529,
  "manifestReferenceCount": 1088,
  "missingManifestReferenceCount": 0,
  "invalidManifestReferenceCount": 0,
  "proceduralRuntimeKeys": [
    "foreground_safe_area_matte",
    "story_banner_component"
  ],
  "blockerCount": 0
}
```

## Last recorded Hermes checkpoint before v3 M00

```json
{
  "id": 608,
  "trigger": "20260706-module-02-paused-ir-web-android-pass-final-stop",
  "token_count": 197589,
  "threshold_ratio": 0.95,
  "threshold_tokens": 245100,
  "markdown": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\019edad0-65fd-7e22-8e94-21e18afa5d07\\20260706T125853Z-20260706-module-02-paused-ir-web-android-pass-final-stop.md",
  "latest": "C:\\Users\\nikit\\.hermes-proagents\\checkpoints\\by-project\\MTRCocosCreator-d20b07d42eaf7ab3\\LATEST.md",
  "doctor": "ok"
}
```

## Latest Module 3 skin/bonus matrix evidence

```json
{
  "skinCount": 8,
  "poseCount": 9,
  "variantCount": 8,
  "expectedFrameCount": 576,
  "checkedFrameCount": 576,
  "blockerCount": 0,
  "warningCount": 0,
  "frameSizes": [
    "256x256"
  ],
  "bboxBottomRange": [
    228,
    231
  ],
  "maxNearWhiteOpaqueRatio": 0.053744
}
```

## Latest Module 3 contact sheet evidence

```json
{
  "skinCount": 8,
  "poseCount": 9,
  "variantCount": 8,
  "frameCount": 576,
  "sheetCount": 8,
  "htmlIndex": "docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_index.html",
  "manifestJson": "docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_manifest.json"
}
```

## Latest Module 3 selected emulator QA evidence

```json
{
  "serial": "emulator-5554",
  "caseCount": 4,
  "passed": 4,
  "failed": 0,
  "fatalExceptionCount": 0,
  "poseMissingCount": 0,
  "safeFallbackMissingCount": 0,
  "totalEquipmentAttach": 108,
  "summaryJson": "docs/qa/evidence/20260704_module3_emulator_skin_bonus/module3_emulator_skin_bonus_qa_20260704_final.json",
  "report": "docs/global_modernization/skin_bonus_emulator_qa_report.md"
}
```

## Latest Module 2 UI IR/runtime evidence

```json
{
  "screen": "paused",
  "screens": ["name", "menu", "levels", "playing_hud", "devgate", "sound", "skins", "devpanel", "achievements", "records", "paused"],
  "uiIrProblemCount": 0,
  "uiIrScreenCount": 11,
  "assetBlockerCount": 0,
  "webBuildFinished": true,
  "webVisualRecordsPass": true,
  "webRecordsKnownCdpConsoleCaptureFalseNegative": true,
  "webCdpProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json",
  "webCdpConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl",
  "webMenuCdpProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json",
  "webMenuCdpConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.console.jsonl",
  "webLevelsCdpProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json",
  "webLevelsCdpConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl",
  "webPlayingHudProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json",
  "webPlayingHudConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.console.jsonl",
  "webDevgateSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json",
  "webDevgateConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.console.jsonl",
  "webSoundGatefixProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json",
  "webSoundGatefixConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.console.jsonl",
  "webSkinsProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json",
  "webSkinsConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.console.jsonl",
  "webDevpanelProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json",
  "webDevpanelConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.console.jsonl",
  "webAchievementsProbe": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json",
  "webAchievementsConsoleLog": "docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.console.jsonl",
  "webRecordsVisualSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json",
  "webRecordsScreenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png",
  "webPausedVisualSummary": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json",
  "webPausedScreenshot": "docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png",
  "androidEmulatorBuildFinished": true,
  "androidQaScreenReady": true,
  "androidMenuUiGateReady": true,
  "androidLevelsCleanQaScreenReady": true,
  "androidLevelsAllIconsObserved": true,
  "androidLevelsIconUsageCount": 15,
  "androidPlayingHudGameplayReady": true,
  "androidPlayingHudFatalException": false,
  "androidDevgateQaScreenReady": true,
  "androidDevgateFatalException": false,
  "androidSoundQaScreenReady": true,
  "androidSoundUiGateReady": true,
  "androidSoundSharedPngAssetsObserved": true,
  "androidSoundFatalException": false,
  "androidSkinsQaScreenReady": true,
  "androidSkinsUiGateReady": true,
  "androidSkinsPreviewUsageObserved": true,
  "androidSkinsFatalException": false,
  "androidDevpanelQaScreenReady": true,
  "androidDevpanelUiGateReady": true,
  "androidDevpanelSharedPngAssetsObserved": true,
  "androidDevpanelFatalException": false,
  "androidAchievementsQaScreenReady": true,
  "androidAchievementsUiGateReady": true,
  "androidAchievementsIconUsageCount": 7,
  "androidAchievementsIntlErrorCount": 0,
  "androidAchievementsFatalException": false,
  "androidRecordsQaScreenReady": true,
  "androidRecordsGateReady": true,
  "androidRecordsSeeded": true,
  "androidRecordsFatalException": false,
  "androidRecordsSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json",
  "androidPausedQaScreenReady": true,
  "androidPausedGateReady": true,
  "androidPausedTouchZoneDebugLayerVisible": false,
  "androidPausedFatalException": false,
  "androidPausedSummary": "docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json",
  "androidFatalException": false,
  "oldEnterNameAssetLoaded": false
}
```

## Fast validation commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704.json
```

```powershell
python .\tools\validate-skin-bonus-matrix.py --project-root . --report .\docs\qa\evidence\20260704_module3_skin_bonus_matrix\skin_bonus_matrix_20260704.json
```

```powershell
python .\tools\render-skin-contact-sheets.py --project-root . --output-dir .\docs\qa\evidence\20260704_module3_contact_sheets
```

```powershell
python .\tools\validate-ui-ir.py --project-root . --report .\docs\qa\evidence\20260704_module2_ui_ir\ui_ir_validation_20260704.json
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\web-chrome-runtime-smoke.ps1 `
  -Url "https://nikitak8883.github.io/Martyskin-trud-runner/?mtr_dev=1&mtr_autostart=1&mtr_level=15&mtr_qa_bonuses=1" `
  -BrowserPath "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  -WaitForLogPattern "MTR_GAMEPLAY_START_GATE_READY level=15" `
  -WaitForLogPatternTimeoutSeconds 75
```
