# Skin/bonus emulator QA report — Module 3 selected runtime gate

Generated: 2026-07-04 13:35 +03:00  
Status: `selected_emulator_qa_pass`  
Runtime changes: none  
Target: `emulator-5554` only

## Scope

This is the selected Android runtime QA gate for the Module 3 player skin, bonus, and animation-frame pipeline.

The goal was to verify that the static matrix and contact-sheet evidence survive the actual Cocos Android renderer:

- forced QA startup enters gameplay;
- selected skin/bonus pose aliases resolve to runtime resource keys;
- equipment anchors are emitted;
- no fatal Android crash appears in logcat;
- no missing-pose or missing safe-fallback signal appears;
- screenshots show actual gameplay, not only menu/start state.

No runtime PNG, TypeScript, native Android file, package config, build output, or release artifact was changed by this QA slice.

## Evidence

Final normalized QA summary:

- `docs/qa/evidence/20260704_module3_emulator_skin_bonus/module3_emulator_skin_bonus_qa_20260704_final.json`

Raw first-pass QA summary:

- `docs/qa/evidence/20260704_module3_emulator_skin_bonus/module3_emulator_skin_bonus_qa_20260704.json`

Per-case logcat and screenshot evidence:

| Case | Skin | Variant | Pose alias | Resource pose | Level | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `case1b_brigadir_helmet_vest_boots_run2_longwait` | `brigadir` | `helmet_vest_boots` | `run2` | `run_2` | 1 | pass |
| `case2_golden_brigadir_shield_victory` | `golden_brigadir` | `shield` | `victory` | `victory` | 1 | pass |
| `case3_cyber_makaka_magnet_crouch_dash` | `cyber_makaka` | `magnet` | `crouchDash` | `crouch_dash` | 8 | pass |
| `case4_lab_assistant_act_vest_idle` | `lab_assistant_act` | `vest` | `idle` | `idle` | 3 | pass |

## Final summary

```json
{
  "caseCount": 4,
  "passed": 4,
  "failed": 0,
  "fatalExceptionCount": 0,
  "poseMissingCount": 0,
  "safeFallbackMissingCount": 0,
  "totalEquipmentAttach": 108
}
```

## Important correction made during QA

The first `case1_brigadir_helmet_vest_boots_run2` capture was not accepted as final evidence because the screenshot was taken before gameplay was ready.

It was replaced by:

- `case1b_brigadir_helmet_vest_boots_run2_longwait.logcat.txt`
- `case1b_brigadir_helmet_vest_boots_run2_longwait.png`

That rerun entered gameplay and emitted:

```text
MTR_SKIN_QA_FORCED skin=brigadir variant=helmet_vest_boots pose=run2
MTR_PLAYER_POSE skin=brigadir variant=helmet_vest_boots pose=run_2
MTR_EQUIPMENT_ATTACH count=72
```

## Visual QA note

Screenshots were manually inspected for the selected set.

Observed:

- gameplay screens loaded for levels 1, 3, and 8;
- player debug anchor boxes were visible as intended for QA;
- skin/bonus sprites were visible in the actual scene;
- level backgrounds and nearby platforms loaded;
- no obvious white matte chunks or broken platform substitutions were visible in this selected pass.

The debug anchor overlay is expected in this QA route and is not a production visual defect.

## Limitations

This is a selected runtime gate, not the full exhaustive skin x bonus x level matrix.

It proves that representative runtime wiring is healthy, but it does not yet replace:

- full all-level visual traversal;
- Android/Web parity playback;
- release APK rebuild and install verification;
- production-mode screenshot capture without debug overlays.

## Next safe action

Continue implementation with the next bounded module slice:

1. Module 2 UI inventory and one-screen UI IR pilot.
2. Broaden Module 3 emulator matrix only if a future patch touches skin/bonus runtime assets.
3. Keep physical-device installs disabled unless explicitly requested.
