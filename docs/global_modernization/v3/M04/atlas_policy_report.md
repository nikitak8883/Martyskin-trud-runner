# M04 atlas, bundle and provenance policy

Date: `2026-08-21`  
Verdict: `CANONICAL POLICY ACCEPTED; OBJECTIVE_NPC PILOT ACCEPTED; REMAINING RUNTIME PACKING DEFERRED`

## Canonical contract

`assets/resources/config/atlas_manifest.json` is governed by `docs/global_modernization/v3/M04/schemas/atlas_manifest.schema.json` and the fail-closed `tools/codex/validate_m04_a_asset_contract.py` validator.

The contract requires:

- one owner and one fallback policy for every runtime source file;
- one atlas-policy group for every PNG/JPG, with no selector overlap;
- group owner equality with the matched source ownership scope;
- project-contained, existing provenance files;
- explicit bundle ID, packing mode, max texture size, padding, Web/Android compression status, trim/pivot policy and dynamic-atlas decision;
- exact source/content checkpoint and Cocos metadata integrity;
- `runtime_effect: false` for every M04-A group.

## Current policy groups

| Group | Images | Mode | Implementation |
| --- | ---: | --- | --- |
| `ui_shared_core` | 28 | static atlas candidate | policy only |
| `main_menu_background` | 1 | standalone | existing standalone |
| `player_skins_selected` | 960 | unpacked family | existing unpacked |
| `bonus_items` | 12 | static atlas candidate | policy only |
| `runner_collectibles` | 14 | static atlas candidate | policy only |
| `objective_npc` | 10 | static atlas | `M04-C-PILOT` accepted and measured |
| `level_theme_families` | 280 | unpacked family | existing unpacked |
| `last_iteration_ui` | 214 | unpacked family | existing unpacked |
| `achievement_ui` | 9 | static atlas candidate | policy only |
| `level_backgrounds` | 15 | standalone | existing standalone |
| `level_background_previews` | 15 | standalone | existing standalone |

Coverage is `1,558/1,558` PNG/JPG, uncovered `0`, overlaps `0`. A `static_atlas_candidate` label is not authorization to pack it.

## Bundle policy at this checkpoint

The existing Cocos `resources` bundle remains unchanged: `isBundle=true`, `bundleName=resources`, priority `8`. Load/preload/release ownership is explicitly deferred to `M04.7 / M04-E`; optional packs must not be moved or eagerly loaded in M04-A.

Dynamic atlas remains disabled for the accepted `objective_npc` group and is otherwise deferred until `M04.6 / M04-D` has a measured allowlist. The pilot uses the Cocos Auto Atlas PNG descriptor on both Web and Android; this is a measured group-specific result, not a project-wide Android texture-compression claim. Every remaining group retains `platform_default_pending_measurement` until its own emulator memory/build/runtime evidence exists.

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

No open correctness finding remains. M04-B enforces naming, trim, pivot, alpha/null-frame, metadata/reference, bundle, provenance, quarantine and resolved-path contracts across all `1,558` governed images. Its deterministic seven-category index covers every image exactly once and links each entry to its atlas group, ownership scope and provenance.

`M04-C-PILOT` accepted only `objective_npc`: ten co-visible decorative sources are packed into one static atlas. The final comparator passed `63/63`; Android emulator median draw calls fell from `26` to `17` (`-34.6154%`) while Web remained at `17`, and automated plus manual parity found no white matte, missing source, trim or pivot regression. The durable decision is recorded in `M04_C_PILOT_ACCEPTANCE.json`. Broader repacking is still unauthorized and must proceed family-by-family under `M04-C-FAMILIES` with the same fail-closed measurement contract.
