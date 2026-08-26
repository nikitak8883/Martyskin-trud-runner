# M04 atlas, bundle and provenance policy

Date: `2026-08-26`  
Verdict: `CANONICAL POLICY ACCEPTED; OBJECTIVE_NPC, ACHIEVEMENT_UI, RUNNER_COLLECTIBLES, BONUS_ITEMS AND UI_SHARED_CORE ACCEPTED; REMAINING RUNTIME PACKING DEFERRED`

## Canonical contract

`assets/resources/config/atlas_manifest.json` is governed by `docs/global_modernization/v3/M04/schemas/atlas_manifest.schema.json` and the fail-closed `tools/codex/validate_m04_a_asset_contract.py` validator.

The contract requires:

- one owner and one fallback policy for every runtime source file;
- one atlas-policy group for every PNG/JPG, with no selector overlap;
- group owner equality with the matched source ownership scope;
- project-contained, existing provenance files;
- explicit bundle ID, packing mode, max texture size, padding, Web/Android compression status, trim/pivot policy and dynamic-atlas decision;
- exact source/content checkpoint and Cocos metadata integrity;
- `runtime_effect: false` for policy-only groups; a measured family may set it true only with contained descriptors, any explicit standalone remainder, and accepted contract/evidence links.

## Current policy groups

| Group | Images | Mode | Implementation |
| --- | ---: | --- | --- |
| `ui_shared_core` | 28 | mixed static atlas | `M04-C-FAMILY-UI-SHARED-CORE` accepted as four measured directory-local descriptors plus one explicit standalone banner |
| `main_menu_background` | 1 | standalone | existing standalone |
| `player_skins_selected` | 960 | unpacked family | existing unpacked |
| `bonus_items` | 12 | static atlas | `M04-C-FAMILY-BONUS-ITEMS` accepted as two measured directory-local descriptors |
| `runner_collectibles` | 14 | static atlas | `M04-C-FAMILY-RUNNER-COLLECTIBLES` accepted and measured |
| `objective_npc` | 10 | static atlas | `M04-C-PILOT` accepted and measured |
| `level_theme_families` | 280 | unpacked family | existing unpacked |
| `last_iteration_ui` | 214 | unpacked family | existing unpacked |
| `achievement_ui` | 9 | static atlas | `M04-C-FAMILY-ACHIEVEMENT-UI` accepted and measured |
| `level_backgrounds` | 15 | standalone | existing standalone |
| `level_background_previews` | 15 | standalone | existing standalone |

Coverage is `1,558/1,558` PNG/JPG, uncovered `0`, overlaps `0`. A `static_atlas_candidate` label is not authorization to pack it.

## Bundle policy at this checkpoint

The existing Cocos `resources` bundle remains unchanged: `isBundle=true`, `bundleName=resources`, priority `8`. Load/preload/release ownership is explicitly deferred to `M04.7 / M04-E`; optional packs must not be moved or eagerly loaded in M04-A.

Dynamic atlas remains disabled for the accepted `objective_npc`, `achievement_ui`, `runner_collectibles`, `bonus_items` and `ui_shared_core` groups and is otherwise deferred until `M04.6 / M04-D` has a measured allowlist. The five accepted groups use Cocos Auto Atlas PNG descriptors on Web and Android; `bonus_items` uses two directory-local descriptors, while `ui_shared_core` uses four directory-local descriptors and keeps its no-op singleton banner as one explicit standalone texture. Cards and panels alone permit MaxRects rotation because that measured policy removed the Android texture-memory regression without changing resource keys or frame geometry. These are family-specific results, not a project-wide Android texture-compression claim. Every remaining candidate retains `platform_default_pending_measurement` until its own emulator memory/build/runtime evidence exists.

## Fail-closed rules

- Missing/overlapping ownership or atlas coverage blocks the gate.
- Cross-owner atlas membership blocks the gate.
- Missing/escaping provenance blocks the gate.
- Source or metadata fingerprint drift blocks the gate.
- Invalid/missing/orphan/duplicate Cocos metadata blocks the gate.
- Divergence of the immutable pre-metadata baseline from `origin/mtr-source-v3` blocks the gate; a later descendant source publication is accepted.
- Policy-only packing with runtime effect blocks the gate.
- Destructive cleanup and runtime repacking are forbidden in M04-A.

## Accepted corrections during review

1. The schema was moved from the closed shared-library schema namespace into the M04 module namespace after the full static gate correctly rejected the original placement.
2. The broad themed ownership scope was split into eleven playable families plus themed UI, and owner equality is now validated.
3. Explicit path conventions removed ambiguity between source-root-relative selectors and project-root-relative provenance/meta paths.
4. Direct unit tests now prove text/binary canonicalization, metadata pairing/orphan detection, path containment and post-publication Git ancestry.
5. The measured-family schema now models descriptor-local rotation and an explicit standalone remainder; validation fails closed on rotation drift, missing standalone files, or a descriptor-plus-standalone source-count mismatch.

No open correctness finding remains. M04-B enforces naming, trim, pivot, alpha/null-frame, metadata/reference, bundle, provenance, quarantine and resolved-path contracts across all `1,558` governed images. Its deterministic seven-category index covers every image exactly once and links each entry to its atlas group, ownership scope and provenance.

`M04-C-PILOT` accepted only `objective_npc`: ten co-visible decorative sources are packed into one static atlas. The final comparator passed `63/63`; Android emulator median draw calls fell from `26` to `17` (`-34.6154%`) while Web remained at `17`, and automated plus manual parity found no white matte, missing source, trim or pivot regression. The durable decision is recorded in `M04_C_PILOT_ACCEPTANCE.json`. Broader repacking is still unauthorized and must proceed family-by-family under `M04-C-FAMILIES` with the same fail-closed measurement contract.

`M04-C-FAMILY-ACHIEVEMENT-UI` then accepted exactly nine bounded non-gameplay UI sources. Its comparator passed `63/63`; Android emulator median draw calls fell from `24` to `16` (`-33.3333%`) while Web remained at `16`. Automated and manual parity found no matte, missing-source, trim or pivot regression. The durable decision is recorded in `M04_C_FAMILY_ACHIEVEMENT_UI_ACCEPTANCE.json`; every other family remains closed.

`M04-C-FAMILY-RUNNER-COLLECTIBLES` then accepted exactly 14 gameplay-critical collectible sources. Its comparator passed `63/63`; Android emulator median draw calls fell from `34` to `21` (`-38.2353%`) while Web remained at `21`. Automated and manual parity found no matte, missing-source, trim or pivot regression. The durable decision is recorded in `M04_C_FAMILY_RUNNER_COLLECTIBLES_ACCEPTANCE.json`; every remaining family remains closed.

`M04-C-FAMILY-BONUS-ITEMS` accepted exactly 12 gameplay bonus/equipment sources through two non-overlapping directory-local descriptors. Its final comparator passed `63/63`; Android emulator median draw calls fell from `30` to `20` (`-33.3333%`) while Web moved from `19` to `20`, within the frozen absolute non-regression budget. Automated and manual parity found no matte, missing-source, trim or pivot regression. The preserved first comparison (`62/63`) proved that the original `50%` relative total-draw gate was mathematically unreachable because 18 baseline draws were outside this family; the gate alone was corrected to the established `30%` family threshold before acceptance, with every absolute, texture, runtime, artifact and visual gate unchanged. The durable decision is recorded in `M04_C_FAMILY_BONUS_ITEMS_ACCEPTANCE.json`; every remaining family remains closed.

`M04-C-FAMILY-UI-SHARED-CORE` accepted all 28 shared UI sources through four non-overlapping directory-local descriptors and one explicit standalone banner. The final comparator passed `63/63`; Android emulator median draw calls fell from `62` to `40` (`-35.4839%`), Web fell from `54` to `40`, and dynamic-atlas copies fell from `10` to `0` on Web. Rotation limited to cards/panels reduced the candidate texture area to `3,733,352 px` and kept Android texture memory at `28.99 MiB` versus `28.01 MiB` baseline. Automated parity introduced zero near-white pixels, manual review found no matte/missing/pivot/trim/rotation defect, and fresh Web plus Android repeats matched the accepted screenshots pixel-for-pixel. The durable decision is recorded in `M04_C_FAMILY_UI_SHARED_CORE_ACCEPTANCE.json`; every unmeasured family remains closed.
