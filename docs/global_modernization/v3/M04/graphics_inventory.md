# M04-A canonical graphics and runtime-asset inventory

Date: `2026-08-13`  
Execution unit: `M04-A` (`M04.1 + M04.2`)  
Status: `PASS / CONTRACT-ONLY / NO RUNTIME REPACK`  
Physical device used: `NO`

## Inventory boundary

The canonical source root is `assets/resources`. Inventory and selector paths are POSIX paths relative to that root. Provenance, Cocos metadata and report paths are POSIX paths relative to the project root. The two governance JSON files and their metadata are excluded only from their own recursive fingerprint; they remain in the Cocos pair/orphan/UUID graph.

| Class | Count | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Runtime source payload excluding the two self-referential governance JSON files | 1,635 | 116,453,941 | `9C68E11B117FF03F261B4170BAF50C1CB9BDA2B1BD515C27F64AE7AAE6A16408` |
| Cocos metadata excluding the matching two governance `.meta` files | 1,882 | 4,574,788 | `4DE87CF49754E2206204F9F44FAEBB827118BBAAE99F91A68AA6341769E32763` |
| PNG | 1,528 | 107,146,623 | validated individually |
| JPG | 30 | 5,999,213 | selector-covered |
| JSON payload | 35 | 1,163,846 | fingerprinted with LF normalization |
| WAV / MP3 | 40 / 1 | 2,018,006 / 116,284 | raw-byte fingerprinted |

Text files with `.html`, `.json` and `.meta` extensions normalize CRLF/CR to LF before size and SHA calculation. Binary files are hashed as raw bytes. Sorted records use `utf8_path<NUL>decimal_size<NUL>UPPER_SHA256<LF>`.

## PNG and Cocos integrity

- PNG decode errors: `0`.
- Missing PNG `.meta`: `0`.
- Oversize images beyond 2,048 px: `0`.
- White-matte suspects under the strict scan: `0`.
- Alpha PNG: `1,527`; intentionally opaque RGB main-menu background: `1`.
- Cocos source/metadata pairs: missing `0`, orphan `0`, invalid JSON `0`, invalid UUID `0`, duplicate UUID `0`.
- Physical Auto Atlas descriptors (`.pac`, `.plist`, `.atlas`, `.spriteatlas`): `0`; M04-A did not create any.

## Ownership result

All `1,635/1,635` runtime source files resolve to exactly one of `24` ownership scopes. Unowned files: `0`; overlapping scopes: `0`. Thematically generated level assets are intentionally split by family. `objectives/themed/last_iteration/ui` belongs to `ui_ux_design_system`, while the eleven playable theme families belong to `levels_backgrounds_content_pipeline`; this prevents the earlier broad-scope cross-owner ambiguity.

Primary owners are:

- `audio_vfx_pipeline`: audio;
- `character_skin_bonus_animation_pipeline`: player skins, bonuses and equipment;
- `cross_module_content_governance`: runtime config payloads;
- `gameplay_core_mechanics`: collectibles and objective catalog;
- `levels_backgrounds_content_pipeline`: backgrounds, previews, NPCs and non-UI level themes;
- `save_achievements_telemetry`: achievements/objective UI;
- `ui_ux_design_system`: shared UI, main-menu background and themed UI.

The exact paths, counts, byte totals, provenance and fallback policies are machine-readable in `assets/resources/config/atlas_manifest.json`.

## Validation and runtime evidence

- Canonical M04-A validator: PASS, findings `0`.
- Direct tests: `8/8 PASS`; negative manifest fixtures: `11/11` rejected with their expected codes.
- Existing asset validator: `1,528` PNG, blockers `0`, missing referenced runtime assets `0`.
- Fresh Web QA build includes the manifest UUID payload; Web matrix cycle A/B: `34/34` each, interaction PASS, restart `10/10` each.
- Fresh Android x86_64 debug APK includes the same manifest UUID payload; emulator matrix A/B: `28/28` each.
- Android interaction A/B: touch/name persistence/restart/soak PASS, `20/20` restarts, two 60-second soaks, process losses `0`.
- Visual sample: menu, name entry, level selection and level 15 are consistent without missing layers or white fragments.

## Boundary and next action

This inventory is a governance baseline, not proof that packing improves performance. No texture, pivot, trim, compression, bundle placement or runtime load path changed. `M04-B` may extend fail-visible pre-import checks and generate contact sheets. Actual packing is forbidden until `M04-C-PILOT` captures before/after draw-call, waste, load, memory and build-size evidence with rollback.
