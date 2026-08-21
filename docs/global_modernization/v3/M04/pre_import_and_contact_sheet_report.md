# M04-B pre-import validation and contact-sheet report

Date: `2026-08-21`  
Verdict: `PASS / RUNTIME UNCHANGED / RELEASE REMAINS BLOCKED`

## Pre-import validator

`tools/validate-assets.py` remains non-mutating and now fail-closes on:

- unsafe names, extension case and casefold collisions;
- missing/invalid Cocos image metadata, UUIDs and internal redirects;
- invalid trim bounds/types, pivots, alpha declaration and fully transparent frames;
- missing or escaping provenance, atlas/ownership ambiguity and bundle drift;
- runtime quarantine leakage, escaped quarantine paths and hidden dangling UUID references;
- traversal plus symlink/junction escapes for assets, metadata, manifests, provenance, references and report output.

Strict repository result: `1,558` images, `1,528` PNGs, decode/missing-meta/oversize/white-matte/null-frame/pre-import blockers all `0`. Trim distribution is `auto=585`, `none=973`; all `1,558` pivots are `0.5,0.5`. Bundle `resources` remains valid at priority `8`.

Eight negative fixture families plus direct null-frame, malformed-manifest, containment and resource-escape cases are exercised. The combined M04-B suite passes `14/14`.

## Contact-sheet contract

`tools/codex/render_m04_b_contact_sheets.py` computes every page deterministically, displays alpha over a checkerboard, links each source to canonical atlas/ownership/provenance records and never changes runtime assets or `.meta` files. Generate mode removes only stale generator-owned files directly under its bounded temp output root; check mode writes nothing.

| Category | Assets | Pages |
| --- | ---: | ---: |
| HUD | 11 | 1 |
| Menu | 240 | 4 |
| Runner | 84 | 2 |
| Bonuses | 900 | 15 |
| Obstacles/platforms | 290 | 5 |
| Backgrounds/previews | 31 | 1 |
| VFX | 2 | 1 |
| **Total** | **1,558** | **29** |

Unclassified assets: `0`; duplicate classifications: `0`. Canonical index: `docs/global_modernization/v3/M04/contact_sheet_index.json`, SHA-256 `CBD9D7F2DBD4E2200681068F1A31E6CB99B321824E20DB3E9448A18EFE61BF7C`.

## Cross-platform acceptance

- Static quality gate: `25/25 PASS`, findings `0`.
- Web: fresh Cocos build; two matrix cycles `34/34`, interactions PASS and restart `10/10` each.
- Android: fresh x86_64 emulator build/install to user `0`; two matrix cycles `28/28`.
- Android interaction: touch/FSM PASS, custom name persisted over cold restart, restart `10/10`, soak `300.104 s`, `322` input bursts, `17` state actions, process losses `0`.
- Visual samples across menu, name, level 15 and soak are coherent on Web and Android; no white fragments, ghost layers, missing background or broken platform was observed.

No physical device, production signing, Pages deployment, runtime atlas migration or bundle lifecycle change was performed. Those remain behind their dedicated decisions and gates.
