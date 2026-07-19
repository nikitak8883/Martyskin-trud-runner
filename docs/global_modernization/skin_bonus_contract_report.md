# Skin/bonus contract report — Module 3 baseline

Generated: 2026-07-04 12:58 +03:00  
Updated: 2026-07-04 13:35 +03:00  
Status: `selected_emulator_qa_pass`  
Runtime changes: none

## Scope

This is the first non-mutating Module 3 slice for the player skin, bonus, and animation-frame pipeline.

The slice added a dedicated validator for the manifest-declared runtime matrix:

```text
skin x pose x bonus variant
```

It does not regenerate, move, delete, crop, or modify any PNG asset.

## Applied workflow rule

`game-studio:sprite-pipeline` was used as the workflow guard for future visual fixes:

- keep one approved in-game frame as identity anchor;
- normalize full strips with one shared scale;
- keep bottom-center anchor stable;
- preview before approving any regenerated or edited sprite set.

This baseline validator is the precondition for those later edits.

## Validator

Added:

- `tools/validate-skin-bonus-matrix.py`

Run:

```powershell
python .\tools\validate-skin-bonus-matrix.py --project-root . --report .\docs\qa\evidence\20260704_module3_skin_bonus_matrix\skin_bonus_matrix_20260704.json
```

Result:

```json
{
  "ok": true,
  "summary": {
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
}
```

Evidence:

- `docs/qa/evidence/20260704_module3_skin_bonus_matrix/skin_bonus_matrix_20260704.json`

## Checks covered

- All canonical skin IDs from `player_skins_manifest.json` exist in the matrix.
- Every declared pose exists for every skin.
- Every declared variant exists for every skin/pose pair.
- Every runtime PNG exists and decodes.
- Every runtime PNG has a matching `.png.meta`.
- Every frame is `256x256`.
- Every frame has alpha and a non-empty alpha bounding box.
- No visible pixels touch the canvas edge.
- Variant bbox center and baseline do not drift from the base variant beyond the configured thresholds.
- Per-pose bbox baseline spread is within the configured threshold.
- White-chunk heuristics did not flag any runtime skin frame.

## Important limitation

This is a static runtime-asset gate, not a replacement for emulator QA.

It does not prove:

- animation readability under motion;
- correct perceived equipment placement during gameplay;
- absence of visual artifacts in scaled Cocos rendering;
- Android/Web parity under the actual renderer.

Those must be expanded in later full-matrix runtime QA if a future patch changes skin/bonus runtime assets.

## Hygiene

- `python -m py_compile .\tools\validate-skin-bonus-matrix.py` passed.
- The temporary `tools\__pycache__` created by `py_compile` was removed immediately after verification.

## Contact sheet evidence

Added non-runtime contact sheet renderer:

- `tools/render-skin-contact-sheets.py`

Generated:

- `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_index.html`
- `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_manifest.json`
- 8 PNG sheets, one per skin.

Result:

```json
{
  "skinCount": 8,
  "poseCount": 9,
  "variantCount": 8,
  "frameCount": 576,
  "sheetCount": 8
}
```

Detailed report:

- `docs/global_modernization/skin_bonus_contact_sheet_report.md`

## Selected emulator QA evidence

Target:

- `emulator-5554`

Final normalized evidence:

- `docs/qa/evidence/20260704_module3_emulator_skin_bonus/module3_emulator_skin_bonus_qa_20260704_final.json`

Detailed report:

- `docs/global_modernization/skin_bonus_emulator_qa_report.md`

Result:

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

The selected emulator pass covered:

- `brigadir` + `helmet_vest_boots` + `run2`/`run_2`;
- `golden_brigadir` + `shield` + `victory`;
- `cyber_makaka` + `magnet` + `crouchDash`/`crouch_dash`;
- `lab_assistant_act` + `vest` + `idle`.

## Next safe action

Continue with the next bounded module slice:

```text
Module 2 UI inventory and one-screen UI IR pilot.
```

Only broaden Module 3 runtime QA again when a future patch changes skin/bonus assets or renderer binding.
