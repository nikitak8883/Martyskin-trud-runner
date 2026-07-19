# UI inventory — Module 2 baseline

Generated: 2026-07-04 14:05 +03:00  
Updated: 2026-07-06 16:05 +03:00  
Status: `name_menu_levels_playing_hud_devgate_sound_skins_devpanel_achievements_records_paused_ir_runtime_pass`  
Runtime scope: small touch-target/layout patches on `name`, `levels`, `playing_hud`, `devgate`, `sound`, `skins`, `devpanel`, `achievements`, `records`, and `paused`; cold-start critical UI gate added for non-main menu-like surfaces including skin previews, developer surfaces, and achievement icons; deterministic records QA seeding and Android native startup-query bridge fixed; paused startup QA marker and touch-zone overlay behavior fixed; one stale unused PNG asset removed; `menu` IR added without runtime code changes

## Scope

This document inventories the current Cocos UI surfaces before broader UI/UX modernization.

The project currently uses a hybrid UI strategy:

- Cocos runtime labels for most body text, HUD text, status chips, cards, achievements, records, and gameplay overlays.
- Shared PNG skins for panels, cards, sliders, toggles, HUD controls, and generic buttons.
- Atomic baked PNG buttons for the main menu and start/name submenu where the PNG already contains final Russian text.
- Hidden Cocos/Web `EditBox` nodes for password/name input, mirrored by visible Cocos labels to avoid duplicate DOM/Cocos label layers.

This is not yet a full UI refactor. It is the first bounded Module 2 slice: inventory, contract reconciliation, and `name` + `menu` + `levels` + `playing_hud` + `devgate` + `sound` + `skins` + `devpanel` + `achievements` + `records` + `paused` UI IR pilots.

## Source files inspected

| Area | Live source |
| --- | --- |
| UI runtime monolith | `assets/scripts/GameRoot.ts` |
| UI theme constants | `assets/scripts/ui/UITheme.ts` |
| UI skin manifest | `assets/resources/config/ui_skin_manifest.json` |
| Typography manifest | `assets/resources/config/ui_typography.json` |
| UI IR schema source | `docs/global_modernization/library/schemas/ui_ir.schema.yaml` |
| Module plan | `docs/global_modernization/TASKS4_AUDIT_AND_IMPLEMENTATION_PLAN_20260702.md` |

## Screen inventory

| State | FSM mode | Runtime source | Primary UI assets | Current risk |
| --- | --- | --- | --- | --- |
| `menu` | `MENU` | `GameRoot.ts:4226-4261` | main-menu background, title PNG, atomic baked PNG buttons | Medium: baked-button exception must stay documented to avoid ghost labels. |
| `name` | `CHARACTER_SELECT` | `GameRoot.ts:4283-4294` | `panel_dialog`, `title_banner_blank`, start-menu profile box, atomic baked PNG buttons, hidden EditBox | High: EditBox must stay visually hidden and mirrored; chosen for first UI IR pilot. |
| `skins` | `CHARACTER_SELECT` | `GameRoot.ts:4407-4433`, `1589-1590` | primate cards, selected badge, base-idle preview PNGs, runtime labels | Medium/low: IR, Web direct-CDP, and Android emulator cold-start gate pass; broader aspect-ratio traversal still pending. |
| `levels` | `LEVEL_SELECT` | `GameRoot.ts:4408-4420`, `4516-4699` | themed level cards/icons, runtime labels | Medium: IR, Web CDP, and Android emulator clean-pass now prove all 15 themed icons are loaded/used; broader aspect-ratio traversal still pending. |
| `sound` | `PAUSED` | `GameRoot.ts:4316-4329`, `4467-4496` | shared rows, slider track/fill/knob, toggles, runtime labels | Medium/low: IR, Web direct-CDP, and Android emulator cold-start gate pass; broader aspect-ratio traversal still pending. |
| `records` | `ACHIEVEMENTS` | `GameRoot.ts:4309-4323` | empty-state/card rows, runtime labels | Low: IR, fixed table columns, Web visual probe, and Android emulator seeded route pass; broader aspect-ratio traversal still pending. |
| `achievements` | `ACHIEVEMENTS` | `GameRoot.ts:4324-4362` | achievement cards, locks, icons, progress bars | Medium/low: IR, Web direct-CDP, and Android emulator route pass after native-safe date formatter fix; broader aspect-ratio traversal still pending. |
| `paused` | `PAUSED` | `GameRoot.ts:4363-4366` | dialog panel + shared buttons | Low: IR, Web visual probe, and Android emulator startup-pause route pass; broader aspect-ratio traversal still pending. |
| `clear` | `RUNNING` | `GameRoot.ts:4367-4370` | dialog panel + runtime summary/buttons | Low/medium: completion loop QA pending. |
| `over` | `GAME_OVER` | `GameRoot.ts:4371-4376` | empty-state card + runtime summary/buttons | Medium: fail reason wrapping pending. |
| `finished` | `RUNNING` | `GameRoot.ts:4377-4380` | dialog panel + runtime text/buttons | Low/medium: final level flow pending. |
| `devgate` | `DEV_MODE` | `GameRoot.ts:4283-4289` | dialog panel, hidden password EditBox + runtime mirror, shared buttons | Medium/low: IR, Web Playwright, and Android emulator clean route pass; password flow remains intentionally gated. |
| `devpanel` | `DEV_MODE` | `GameRoot.ts:4295-4308`, `4601-4624` | list panel, status chip, 12 developer/debug buttons | Medium/low: IR, Web direct-CDP, and Android emulator route pass; dense QA-only surface remains intentionally developer-only. |
| `playing` HUD | `RUNNING` | `GameRoot.ts:4132-4156` | HUD panels, controls, runtime labels, debug overlays | Medium: IR, Web direct-CDP, and Android emulator clean gameplay route pass; broader device/aspect traversal still pending. |

## Current UI contract decision

The old `ui_skin_manifest.json` policy said:

```json
{
  "interactiveText": "runtime-label-only",
  "bakedTextAllowed": "decorative-non-interactive-only"
}
```

That was no longer true for the live runtime because `GameRoot.ts` intentionally returns early after drawing atomic baked PNG buttons on `menu` and `name`.

The policy was updated to:

```json
{
  "interactiveText": "runtime-label-preferred",
  "bakedTextAllowed": "documented-atomic-interactive-exceptions"
}
```

The documented exceptions are:

- `menu`
- `name`

This matches the current visual direction: if a button family is intentionally authored as final PNG art with Russian text, do not draw an extra runtime label under or over it. This directly protects against the old ghost-label problem.

## Confirmed cleanup

Removed stale asset pair:

- `assets/resources/objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_button_enter_name_01.png`
- `assets/resources/objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_button_enter_name_01.png.meta`

Evidence:

- Current `GameRoot.ts` references `mtr_start_menu_button_save_name_01`, `mtr_start_menu_button_forward_01`, and `mtr_start_menu_button_back_menu_01`.
- `rg` found `mtr_start_menu_button_enter_name_01` only in historical QA logs and its own `.meta`.
- `tools/validate-assets.py` passed after removal.

## Pilot artifacts

Added:

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
- `tools/validate-ui-ir.py`

Validation evidence:

- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_final.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_menu_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_levels_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_playing_hud_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_devgate_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_sound_pregate_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260704_skins_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_devpanel_pilot.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_achievements_after_intl_fix.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_records_native_bridge.json`
- `docs/qa/evidence/20260704_module2_ui_ir/ui_ir_validation_20260706_paused_pilot.json`

Current result:

```json
{
  "screenCount": 11,
  "okCount": 11,
  "nodeCount": 191,
  "buttonCount": 69,
  "bakedButtonCount": 9,
  "assetReferenceCount": 156,
  "problemCount": 0,
  "warningCount": 0
}
```

## Fresh runtime evidence

Web:

- build: `logs/creator-module2-ui-web-r2-20260704.log`
- name screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp.png`
- name probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_name_screen_cdp_probe.json`
- menu screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp.png`
- menu probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_menu_screen_cdp_probe.json`
- levels build: `logs/creator-module2-levels-web-20260704.log`
- levels screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.png`
- levels probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp_probe.json`
- levels console: `docs/qa/evidence/20260704_module2_ui_runtime/web_levels_screen_cdp.console.jsonl`
- playing HUD build: `logs/creator-module2-playing-hud-web-20260704.log`
- playing HUD screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.png`
- playing HUD probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp_probe.json`
- playing HUD console: `docs/qa/evidence/20260704_module2_ui_runtime/web_playing_hud_direct_cdp.console.jsonl`
- devgate build: `logs/creator-module2-devgate-web-20260704.log`
- devgate screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.png`
- devgate summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright_summary.json`
- devgate console: `docs/qa/evidence/20260704_module2_ui_runtime/web_devgate_playwright.console.jsonl`
- sound build: `logs/creator-module2-sound-web-gatefix-20260704.log`
- sound screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.png`
- sound probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp_probe.json`
- sound console: `docs/qa/evidence/20260704_module2_ui_runtime/web_sound_gatefix_direct_cdp.console.jsonl`
- skins build: `logs/creator-module2-skins-web-20260704.log`
- skins screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.png`
- skins probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp_probe.json`
- skins console: `docs/qa/evidence/20260704_module2_ui_runtime/web_skins_direct_cdp.console.jsonl`
- devpanel build: `logs/creator-module2-devpanel-web-20260706.log`
- devpanel accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.png`
- devpanel accepted probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp_probe.json`
- devpanel accepted console: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_direct_cdp.console.jsonl`
- achievements build: `logs/creator-module2-achievements-web-20260706-after-intl-fix.log`
- achievements accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.png`
- achievements accepted probe: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp_probe.json`
- achievements accepted console: `docs/qa/evidence/20260704_module2_ui_runtime/web_achievements_after_intl_fix_direct_cdp.console.jsonl`
- records build: `logs/creator-module2-records-web-20260706-table.log`
- records accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_cdp.png`
- records accepted visual summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_records_table_visual_summary.json`
- paused build: `logs/creator-module2-paused-web-20260706.log`
- paused accepted screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_cdp.png`
- paused accepted visual summary: `docs/qa/evidence/20260704_module2_ui_runtime/web_paused_screen_visual_summary.json`
- devpanel diagnostic generic harness screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/web_devpanel_screen_cdp.png`
- final asset gate: `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_module2_final.json`
- levels asset gate: `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_levels_gate.json`
- skins asset gate: `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704_skins_gate.json`
- devpanel asset gate: `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260706_devpanel_gate.json`

Android emulator:

- build: `logs/creator-module2-ui-android-emulator-20260704.log`
- APK: `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`
- screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen.png`
- logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen_logcat.txt`
- summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_name_screen_summary.json`
- menu screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen.png`
- menu logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_logcat.txt`
- menu summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_menu_screen_summary.json`
- levels build: `logs/creator-module2-levels-android-emulator-20260704.log`
- levels clean screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean.png`
- levels clean logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_logcat.txt`
- levels clean summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_levels_screen_clean_summary.json`
- playing HUD build: `logs/creator-module2-playing-hud-android-emulator-20260704.log`
- playing HUD screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_screen.png`
- playing HUD logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_logcat.txt`
- playing HUD summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_playing_hud_summary.json`
- devgate build: `logs/creator-module2-devgate-android-emulator-20260704.log`
- devgate screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen.png`
- devgate logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_logcat.txt`
- devgate summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_devgate_screen_summary.json`
- sound build: `logs/creator-module2-sound-android-emulator-gatefix-20260704.log`
- sound screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix.png`
- sound logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_logcat.txt`
- sound summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_sound_gatefix_summary.json`
- skins build: `logs/creator-module2-skins-android-emulator-20260704.log`
- skins screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen.png`
- skins logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_logcat.txt`
- skins summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_skins_screen_summary.json`
- devpanel build: `logs/creator-module2-devpanel-android-emulator-20260706.log`
- devpanel screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen.png`
- devpanel logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_logcat.txt`
- devpanel summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_devpanel_screen_summary.json`
- achievements build: `logs/creator-module2-achievements-android-emulator-20260706-after-intl-fix.log`
- achievements screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix.png`
- achievements logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_logcat.txt`
- achievements summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_achievements_after_intl_fix_summary.json`
- records build: `logs/creator-module2-records-android-emulator-20260706-native-bridge.log`
- records screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge.png`
- records logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_logcat.txt`
- records summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_records_table_native_bridge_summary.json`
- paused build: `logs/creator-module2-paused-android-emulator-20260706.log`
- paused screenshot: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen.png`
- paused logcat: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_logcat.txt`
- paused summary: `docs/qa/evidence/20260704_module2_ui_runtime/android_paused_screen_summary.json`

Android result:

```json
{
  "serial": "emulator-5554",
  "qaScreenReady": true,
  "menuUiGateReady": true,
  "nativeStartupReady": true,
  "fatalException": false,
  "oldEnterName": false,
  "saveNameAsset": true,
  "levelsCleanAppData": true,
  "levelsAllLevelIconsObserved": true,
  "levelsIconUsageCount": 15,
  "playingHudGameplayReady": true,
  "playingHudFatalException": false,
  "playingHudCleanAppData": true,
  "devgateCleanAppData": true,
  "devgateQaScreenReady": true,
  "devgateFatalException": false,
  "soundCleanAppData": true,
  "soundQaScreenReady": true,
  "soundUiGateReady": true,
  "soundSharedPngAssetsObserved": true,
  "soundFatalException": false,
  "skinsCleanAppData": true,
  "skinsQaScreenReady": true,
  "skinsUiGateReady": true,
  "skinsPreviewUsageObserved": true,
  "skinsFatalException": false,
  "devpanelCleanAppData": true,
  "devpanelQaScreenReady": true,
  "devpanelUiGateReady": true,
  "devpanelSharedPngAssetsObserved": true,
  "devpanelFatalException": false,
  "achievementsCleanAppData": true,
  "achievementsQaScreenReady": true,
  "achievementsUiGateReady": true,
  "achievementsIconUsageCount": 7,
  "achievementsIntlErrorCount": 0,
  "achievementsFatalException": false,
  "recordsCleanAppData": true,
  "recordsQaScreenReady": true,
  "recordsSeeded": true,
  "recordsGateReady": true,
  "recordsFatalException": false,
  "pausedCleanAppData": true,
  "pausedStartupPauseApplied": true,
  "pausedQaScreenReady": true,
  "pausedUiGateReady": true,
  "pausedTouchZoneDebugLayerVisible": false,
  "pausedFatalException": false
}
```

## Known remaining risks

1. The current pilots cover only the `name`, `menu`, `levels`, `playing_hud`, `devgate`, `sound`, `skins`, `devpanel`, `achievements`, `records`, and `paused` screens. Other screens still need UI IR manifests.
2. `GameRoot.ts` remains a monolith; do not extract UI code until every target screen has an IR and runtime snapshots.
3. Main menu and level select still need visual QA across additional aspect ratios.
4. Android emulator QA verified the `name`, `menu`, clean `levels`, clean `playing_hud`, clean `devgate`, clean `sound`, clean `skins`, clean `devpanel`, clean `achievements`, clean seeded `records`, and clean startup `paused` routes after the runtime touch-target, preview preload, achievement icon preload, native date fallback, records-table, native seed bridge, pause marker, and UI-gate patches were built into the tested artifact.

## Next safe action

Continue Module 2 with the next UI IR pilot:

1. `over`
2. `clear`
3. `finished`

Before extracting UI classes, keep using the CDP-backed web smoke harness plus Android emulator gates for every screen with runtime behavior.
