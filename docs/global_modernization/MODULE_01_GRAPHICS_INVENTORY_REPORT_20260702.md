# Module 1 graphics inventory report

Generated: 2026-07-02 15:58 +03:00  
Module: graphics/rendering/atlas/asset pipeline  
Status: `reference_validator_pass`  
Runtime changes: none

Updated: 2026-07-04 12:53 +03:00 — reference-aware validator slice completed.

## Scope

Implemented the first read-only Module 1 slice:

- runtime PNG inventory;
- `.meta` pairing check;
- manifest JSON syntax check for key existing config/manifests;
- atlas policy draft;
- art validation summary;
- draft atlas manifest with no runtime effect;
- non-mutating asset validator script;
- reference-aware checks for player skins, UI skin manifest, current objective runtime usage, and generated last-iteration runtime keys.

No assets were moved, deleted, compressed, repacked, or regenerated.

## Files added

- `docs/global_modernization/graphics_inventory.md`
- `docs/global_modernization/atlas_policy_report.md`
- `docs/global_modernization/art_validation_report.md`
- `docs/global_modernization/manifests/atlas_manifest.draft.json`
- `tools/validate-assets.py`
- `docs/global_modernization/MODULE_01_GRAPHICS_INVENTORY_REPORT_20260702.md`
- `docs/qa/evidence/20260704_module1_reference_assets/validate_assets_reference_20260704.json`

## Evidence

Runtime PNG inventory:

```json
{
  "png_count": 1529,
  "total_bytes": 107264037,
  "alpha_count": 1528,
  "no_alpha_count": 1,
  "oversize_count": 0,
  "read_errors": 0,
  "missing_meta_count": 0
}
```

Key existing manifest parse checks:

```json
{
  "last_iteration_asset_manifest.generated.json": true,
  "ui_skin_manifest.json": true,
  "levels.json": true,
  "background_manifest_texture10.json": true,
  "player_skins_manifest.json": true
}
```

Draft atlas manifest:

```json
{
  "ok": true,
  "sha256": "F483D41050DFDE72CE23D6DEE1D75A738A1653CA5C62B9FBD4F1604801387D8D"
}
```

Project validator:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present.
```

Runtime-change guard:

```json
{
  "runtimeChangedCount": 0
}
```

Non-mutating asset validator:

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

Reference-aware validator:

```powershell
python .\tools\validate-assets.py --project-root . --report .\docs\qa\evidence\20260704_module1_reference_assets\validate_assets_reference_20260704.json
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
  },
  "referenceChecks": {
    "playerSkinsManifest": {
      "referenceCount": 576,
      "missingCount": 0
    },
    "uiSkinManifest": {
      "referenceCount": 28,
      "missingCount": 0
    },
    "objectiveRuntimeUsage": {
      "referenceCount": 10,
      "resolvedCount": 8,
      "proceduralCount": 2,
      "missingCount": 0,
      "proceduralKeys": [
        "foreground_safe_area_matte",
        "story_banner_component"
      ]
    },
    "lastIterationAssetManifest": {
      "referenceCount": 474,
      "missingCount": 0
    }
  }
}
```

Script syntax check:

```powershell
python -m py_compile .\tools\validate-assets.py
```

Result: `pass`.

Cleanup:

- the temporary `tools\__pycache__` created by `py_compile` was removed immediately after verification;
- stale Python cache folders under `tools\asset_generation\__pycache__` and `tools\skins\__pycache__` were removed during the 2026-07-04 hygiene gate.

## Findings

1. Runtime PNG tree is structurally healthy enough to proceed to stricter validators.
2. `characters/player_skins` is the largest count group and must not be fully loaded at startup in future optimization.
3. `objectives/themed` is the main mixed-content risk and needs sub-classification before any atlas movement.
4. `ui/main_menu_background/main_menu_bg_far.png` is the only non-alpha runtime PNG and should remain standalone.
5. Manifest references are currently structurally healthy: 1088 checked references, 0 missing, 0 invalid.
6. `foreground_safe_area_matte` and `story_banner_component` are procedural runtime ids, not PNG keys; the validator records them explicitly instead of masking genuine missing assets.
7. Existing white-matte scan found no suspects, but it does not cover pivot/baseline/bonus placement.

## Next safe action

Proceed to Module 3 skin/bonus matrix validation. Recommended next slice:

```text
Create non-mutating skin/bonus validator:
- verify every skin x pose x bonus variant frame can be resolved;
- emit per-skin contact sheet candidates;
- check frame dimension, alpha bbox, pivot baseline, and variant coverage;
- keep runtime files unchanged until the report identifies a bounded patch.
```

Do not move or regenerate skin assets until the Module 3 validator exists and passes.
