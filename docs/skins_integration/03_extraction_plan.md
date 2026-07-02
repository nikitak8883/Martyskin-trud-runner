# Skin-pack extraction and integration plan

Current phase completed: safety checkpoint, source inventory, and alpha validation.

Next phase is intentionally gated because source filenames are generic ChatGPT export names and do not encode canonical skin IDs or poses.

## Proposed next steps

1. Confirm whether each timestamp group is one skin, one pose sheet, or an A/B visual variant.
2. Confirm target skin IDs and ordering. Existing active skin IDs are listed in `source_inventory.json`.
3. For each accepted source, define cut boxes or sheet layout before any generated sprite replacement.
4. Generate into a staging namespace first, then wire runtime manifests only after Web and Android screenshot QA.
5. Keep only the code-level `player_skins_v2` compatibility redirect until Web and Android screenshot QA pass; the active asset namespace is `assets/resources/characters/player_skins`.

## Candidate mapping JSON

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\assets\resources\characters\player_skins\_shared\manifests\source_file_mapping_candidates.json`
