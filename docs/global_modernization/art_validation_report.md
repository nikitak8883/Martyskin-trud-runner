# Art validation report — Module 1

Generated: 2026-07-02 15:52 +03:00  
Updated: 2026-07-04 12:53 +03:00  
Status: reference-aware pass / visual matrix validators still required

## Checks performed

### PNG decode and dimensions

- Runtime PNGs scanned: 1529
- Decode errors: 0
- Oversized images over 2048 px edge: 0

### Alpha presence

- PNGs with alpha: 1528
- PNGs without alpha: 1
- Non-alpha file:
  - `ui/main_menu_background/main_menu_bg_far.png`

This is expected for the single full-screen menu background.

### `.meta` pairing

- PNGs checked: 1529
- Missing `.png.meta`: 0

### White-matte scan

Existing read-only scan:

- Evidence: `docs/qa/evidence/20260702_tasks4_audit/white_matte_scan_20260702.json`
- Checked: 978
- Suspect: 0
- Fixed: 0

### Runtime reference integrity

Reference-aware validator:

- Evidence: `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704.json`
- Player skin manifest references: 576 checked, 0 missing.
- UI skin manifest references: 28 checked, 0 missing.
- Current objective runtime usage references: 10 checked, 0 missing, 2 procedural runtime ids.
- Last-iteration generated runtime references: 474 checked, 0 missing.
- Total checked references across these manifests: 1088.

Procedural runtime ids recognized by the validator:

- `foreground_safe_area_matte`
- `story_banner_component`

These are telemetry/drawing ids from `GameRoot.ts`, not PNG resource keys.

## Important limitations

The current scan does not prove:

- correct player-skin pivots;
- frame baseline stability;
- correct helmet/vest/boots/magnet/radio/blueprint placement;
- platform geometry consistency;
- visual readability under motion;
- atlas packing efficiency.

Those must be validated in Module 3 and Module 5 with contact sheets and runtime matrix QA.

## Required stricter validators

Module 1 should next add or extend validators for:

1. alpha bounding box and trim margin;
2. checkerboard/fake-transparent background detection;
3. per-group allowed dimensions;
4. alpha bounding box quality under animation;
5. atlas group ownership;
6. generated-vs-human source provenance;
7. Android/Web content manifest version.

## Current decision

No art files were changed. No quarantine was created because this pass found no read/decode/meta/matte/reference blockers.

## Validator implementation

Added non-mutating validator:

- `tools/validate-assets.py`

Run:

```powershell
python .\tools\validate-assets.py --project-root . --report docs/qa/evidence/20260702_module1_assets/validate_assets_20260702.json
```

Result:

```json
{
  "ok": true,
  "summary": {
    "pngCount": 1529,
    "totalBytes": 107264037,
    "alphaCount": 1528,
    "noAlphaCount": 1,
    "decodeErrorCount": 0,
    "missingMetaCount": 0,
    "oversizeCount": 0,
    "whiteMatteSuspectCount": 0,
    "blockerCount": 0
  }
}
```

Report:

- `docs/qa/evidence/20260702_module1_assets/validate_assets_20260702.json`

Reference-aware rerun:

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704.json
```

Result:

```json
{
  "ok": true,
  "summary": {
    "pngCount": 1529,
    "decodeErrorCount": 0,
    "missingMetaCount": 0,
    "oversizeCount": 0,
    "whiteMatteSuspectCount": 0,
    "blockerCount": 0
  },
  "referenceChecks": {
    "blockerCount": 0
  }
}
```
