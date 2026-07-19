# Global modernization module execution index

Generated: 2026-07-02 15:44 +03:00  
Updated: 2026-07-19  
Source package: `C:\Projects\Monkey Work\Tasks\4\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2.zip`  
Source unpacked root: `C:\Projects\Monkey Work\Tasks\4\_unpacked_20260702_145527\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2`

## v3 integration notice

This file remains the historical Tasks/4/v2 execution record. Current dependency/status/next-action data is maintained in:

- `docs/global_modernization/v3/MODULE_EXECUTION_INDEX.yaml`
- `docs/global_modernization/v3/WORK_PACKAGE_INDEX.yaml`
- `docs/current_audit/revalidation_summary.md`

Completed v2 UI/skin/graphics work is preserved as `revalidate_then_extend`. The immediate action is M00 source-freeze review, not another UI pilot.

## Execution policy

Every module must follow:

```text
retrieve bounded context
inspect live files
write module mini-plan
checkpoint
patch minimal slice
run module validators
run Android/Web parity checks when relevant
fix failures
retest
write module report
code review
hygiene dry-run
checkpoint
stop or request next approval
```

No module may claim success from documentation alone when runtime behavior is in scope.

## Module status table

| Order | Module | Priority | Status | First artifact | Runtime risk |
| --- | --- | --- | --- | --- | --- |
| 0 | Repository inventory and safety scaffold | P0 | scaffold_pass | `docs/codex/CURRENT_STATE.md` | none |
| 10 | Agent tooling, CI, QA, code review | P0 | scaffold_pass | `docs/global_modernization/library/` | low |
| 1 | Graphics/rendering/atlas/asset pipeline | P0 | reference_validator_pass | `graphics_inventory.md` | medium |
| 3 | Character skin/bonus/animation pipeline | P0 | selected_emulator_qa_pass | `skin_bonus_contract_report.md` | high |
| 2 | UI/UX design system | P0 | name_menu_levels_playing_hud_devgate_sound_skins_devpanel_achievements_records_paused_ir_runtime_pass | `ui_inventory.md` | high |
| 9 | Android/Web release/performance | P0 | pending | `release_build_report.md` | medium |
| 4 | Gameplay core/state machines | P0 | pending | `gameplay_state_report.md` | high |
| 5 | Levels/backgrounds/content pipeline | P1 | pending | `level_manifest_report.md` | medium |
| 7 | Audio/VFX/feedback | P1 | pending | `audio_vfx_inventory.md` | medium |
| 8 | Save/achievements/telemetry | P1 | pending | `save_migration_report.md` | medium |
| 6 | PCG/difficulty validation | P1 | pending | `pcg_validation_report.md` | medium |

## Required reports by module

### Module 0/10 scaffold

- `docs/codex/CURRENT_STATE.md`
- `docs/global_modernization/module_execution_index.md`
- `docs/global_modernization/cleanup_dry_run_20260702.md`
- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/MODULE_00_10_SCAFFOLD_REPORT_20260702.md`

### Module 1

- `docs/global_modernization/graphics_inventory.md`
- `docs/global_modernization/atlas_policy_report.md`
- `docs/global_modernization/art_validation_report.md`
- `docs/global_modernization/manifests/atlas_manifest.draft.json`
- `docs/global_modernization/MODULE_01_GRAPHICS_INVENTORY_REPORT_20260702.md`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704.json`
- `tools/validate-assets.py`

### Module 2

- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`
- `docs/global_modernization/manifests/ui_ir/name_entry.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/menu.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/levels.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/playing_hud.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/devgate.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/sound.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/skins.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/devpanel.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/achievements.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/records.ui_ir.json`
- `docs/global_modernization/manifests/ui_ir/paused.ui_ir.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_final.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_menu_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_playing_hud_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_pregate_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_after_intl_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_records_native_bridge.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_paused_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.console.jsonl`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png`
- `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json`
- `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json`
- `tools/validate-ui-ir.py`

### Module 3

- `docs/skins_integration/source_inventory.md`
- `docs/skins_integration/frame_mapping_report.md`
- `docs/skins_integration/skin_bonus_qa_report.md`
- `docs/global_modernization/skin_bonus_contract_report.md`
- `docs/global_modernization/skin_bonus_contact_sheet_report.md`
- `docs/global_modernization/skin_bonus_emulator_qa_report.md`
- `docs/qa/evidence/20260704_module3_skin_bonus_matrix/skin_bonus_matrix_20260704.json`
- `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_manifest.json`
- `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_index.html`
- `docs/qa/evidence/20260704_module3_emulator_skin_bonus/module3_emulator_skin_bonus_qa_20260704_final.json`
- `tools/validate-skin-bonus-matrix.py`
- `tools/render-skin-contact-sheets.py`

### Module 4

- `docs/global_modernization/gameplay_state_report.md`
- `docs/global_modernization/powerup_lifecycle_report.md`

### Module 5

- `docs/global_modernization/level_manifest_report.md`
- `docs/global_modernization/visual_readability_report.md`

### Module 6

- `docs/global_modernization/pcg_validation_report.md`
- `docs/global_modernization/difficulty_telemetry_report.md`

### Module 7

- `docs/global_modernization/audio_vfx_inventory.md`
- `docs/global_modernization/feedback_qa_report.md`

### Module 8

- `docs/global_modernization/save_migration_report.md`
- `docs/global_modernization/achievements_records_report.md`

### Module 9

- `docs/global_modernization/release_build_report.md`
- `docs/global_modernization/android_device_qa_report.md`
- `docs/global_modernization/performance_baseline.md`

## Stop conditions

- Any fatal Web console/runtime error.
- Any Android `FATAL EXCEPTION` or startup black screen.
- Missing runtime asset binding.
- Android/Web content manifest version mismatch.
- Visual QA shows ghost UI layer, double label, white matte block, or wrong bonus placement.
- Cleanup dry-run proposes deleting runtime assets or required QA evidence.

## Current next safe action

Review and approve M00.2 source-freeze classification plus Git/Pages topology. Do not resume runtime modernization until an immutable source checkpoint exists. Android runtime QA remains emulator-only unless the user explicitly authorizes a physical device.
