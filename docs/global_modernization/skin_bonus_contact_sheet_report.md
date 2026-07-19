# Skin/bonus contact sheet report — Module 3 visual evidence

Generated: 2026-07-04 13:24 +03:00  
Status: `contact_sheet_evidence_pass`  
Runtime changes: none

## Scope

This slice generated non-runtime visual evidence for the full player skin matrix:

```text
8 skins x 9 poses x 8 variants = 576 frames
```

The generated sheets are QA artifacts only. They are stored under `docs/qa/evidence/` and are not loaded by the game runtime.

## Tooling added

- `tools/render-skin-contact-sheets.py`

The tool reads:

- `docs/skins_integration/manifests/player_skins_manifest.json`
- `assets/resources/characters/player_skins/**`

The tool writes only:

- `docs/qa/evidence/20260704_module3_contact_sheets/**`

## Evidence generated

- HTML index: `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_index.html`
- Machine-readable manifest: `docs/qa/evidence/20260704_module3_contact_sheets/contact_sheet_manifest.json`

Generated PNG sheets:

- `brigadir_contact_sheet.png`
- `mudrec_contact_sheet.png`
- `cyber_makaka_contact_sheet.png`
- `red_prorab_contact_sheet.png`
- `depo_primate_contact_sheet.png`
- `orangutan_noir_contact_sheet.png`
- `lab_assistant_act_contact_sheet.png`
- `golden_brigadir_contact_sheet.png`

Summary:

```json
{
  "skinCount": 8,
  "poseCount": 9,
  "variantCount": 8,
  "frameCount": 576,
  "sheetCount": 8
}
```

## Overlay semantics

- Green rectangle: alpha bounding box.
- Cyan vertical line: current frame bbox center.
- Red horizontal line: current frame bbox bottom.
- Yellow dashed vertical line: base variant bbox center for the same pose.
- Orange dashed horizontal line: base variant bbox bottom for the same pose.

This makes variant drift, baseline drift, and broken trimming visible without modifying runtime assets.

## Commands

```powershell
python -m py_compile .\tools\render-skin-contact-sheets.py
```

```powershell
python .\tools\render-skin-contact-sheets.py --project-root . --output-dir .\docs\qa\evidence\20260704_module3_contact_sheets
```

Output verification:

```json
{
  "ok": true,
  "sheetCount": 8,
  "frameCount": 576,
  "problems": []
}
```

## Visual spot-check

Inspected:

- `brigadir_contact_sheet.png`
- `golden_brigadir_contact_sheet.png`

Result:

- bbox and anchor overlays render correctly;
- no obvious variant center/baseline drift in the inspected sheets;
- some poses include baked white VFX/smoke/star elements inside the alpha bbox, especially motion or impact poses;
- these are not edge-connected white matte artifacts in the generated contact sheets and are not treated as blockers by this static visual evidence pass.

## Current limitation

This pass is stronger than static JSON validation, but it is still not runtime QA.

It does not prove:

- scaled Cocos rendering readability;
- animation readability under real gameplay speed;
- Android/Web renderer parity;
- touch/emulator behavior.

## Next safe action

Run emulator visual QA for selected skin/bonus states using the existing dev/test hooks and log:

```text
MTR_PLAYER_POSE
MTR_EQUIPMENT_ATTACH
MTR_ASSET_USAGE
FATAL EXCEPTION absence
```

Default QA target remains emulator-only unless a separate explicit physical-device command is given.
