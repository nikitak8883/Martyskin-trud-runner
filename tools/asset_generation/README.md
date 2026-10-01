# Reviewed raster-source replacements

`reviewed_runtime_sources.json` pins the imagegen source, normalized runtime PNG,
Cocos image metadata, transparent test regions and generation prompt. Sources
stay outside `assets/` so they are not packaged into the game.

The logistics lifebuoy replaces an enclosed opaque checkerboard matte. Its
244x232 canvas, trim rectangle, UUID, pivot, path, category and level affinities
are preserved. Original sheet/source/bounds remain in the content manifest;
`reviewedSourceOverride` records the replacement separately.

## Checks (non-mutating by default)

```powershell
python -B tools/asset_generation/reviewed_runtime_sources.py
python -B -m unittest discover -s tools/codex/tests -p test_reviewed_runtime_sources.py -v
```

The mandatory static gate executes the same positive/negative tests. It rejects
wrong hashes, path traversal, duplicate/missing entries, opaque hole pixels,
identity drift and stale provenance. All pins are validated before any runtime
target is written; this is not a multi-file transactional publication protocol.
An interrupted apply is detectable by the check and safely repeatable.

The two reviewed Cocos metadata paths have explicit `eol=crlf` attributes to
preserve their original pinned bytes independent of host `core.autocrlf`. A Git
clean/smudge roundtrip is tested under both settings in isolated temporary repos.
This does not certify the full legacy asset inventory or a native Linux build.

## Explicit restoration

```powershell
python -B tools/asset_generation/reviewed_runtime_sources.py --apply
```

The full `mtr_last_iteration_asset_pipeline.py` preflights reviewed pins before
its legacy extraction/clean phase and restores reviewed replacements after
sheet cutting, before validation/contact-sheet generation. Do not run the full
cut/clean pipeline merely to repair this one sprite: use the narrow restoration.
This patch tests the narrow operation and preflight ordering; it does not claim
a full regeneration of the original sheet drop.

## Repeatable normalization of the approved generated cutout

```powershell
python -B tools/asset_generation/normalize_reviewed_sprite.py --source tools/asset_generation/source_assets/logistics/lifebuoy-generated-20261001.png --target tools/asset_generation/source_assets/logistics/lifebuoy-runtime.png --canvas 244 232 --box 6 6 238 226
```

Normalization only crops fully transparent margins and resizes the approved
cutout. It does not remove matte with heuristic color flooding. Generated source
and prompt are retained, so restoration never requires another model call.
New replacements require a reviewed image, new hash pins, region checks,
inventory/contact-sheet refresh and Web + silent Android-emulator QA.
