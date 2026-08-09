# Кодовая база и архитектурная карта

## Technical baseline

| Property | Live value |
| --- | --- |
| Engine | Cocos Creator 3.8.8 |
| Targets | Web Mobile and Android |
| Design resolution | 960 × 640 |
| Direct runtime TypeScript files | 4 |
| Runtime TypeScript lines | 6,427 |
| Scenes | 1 (`assets/scenes/main.scene`) |
| Resource files | 3,518 |
| Project source files excluding build/temp/log/library/QA indexes | 5,986 |
| Project source size under that scope | 2,011,828,888 bytes |

The source-size value is dominated by 2,714 PNGs (about 1.13 GB). It is an inventory metric, not a runtime memory measurement.

## Runtime TypeScript map

| File | Lines | Role |
| --- | ---: | --- |
| `assets/scripts/GameRoot.ts` | 5,434 | Main Cocos component: session, gameplay, rendering, UI, input, assets, audio, persistence and QA hooks. |
| `assets/scripts/generated/ThemeAssetCatalog.generated.ts` | 786 | Generated themed-asset catalog. |
| `assets/scripts/gameplay/state/GameSessionState.ts` | 129 | M03.2 immutable state/transition contract. |
| `assets/scripts/ui/UITheme.ts` | 78 | UI visual constants and screen titles. |

## Main architectural finding

`GameRoot` is intentionally being decomposed through strangler seams. The M03.1 AST inventory found 170 fields, 267 methods, 613 unique internal caller→callee edges, 8 listener registrations with 8 matching removals, 15 `scheduleOnce` callbacks, 37 local-storage accesses and 10 dynamic-node patterns.

This is not a claim of a currently broken game. It identifies concentration of responsibilities and migration risk. Full rewrite is explicitly rejected: every M03 package must preserve observable ordering and retain rollback.

## M03 state seam

M03.2 introduced the smallest live seam:

- 14 session states;
- 44 accepted changed transitions;
- 14 idempotent self-transitions;
- 138 deterministic rejections;
- one mutable writer: `GameRoot.transitionTo`.

The contract does not yet route actions, collisions or power-ups. It validates state edges only. The selected source excerpt is in `06_KEY_SOURCE_EXCERPTS.md`.

## Current responsibility hotspots

| Area | Present ownership | Planned extraction |
| --- | --- | --- |
| Session state | `GameRoot.transitionTo` | M03.2 complete |
| Diagnostics/lifecycle trace | scattered `MTR_*` logs | M03.3 |
| Keyboard/touch/HUD/pause actions | multiple direct routes | M03.4 |
| Platforms/pickups/obstacles/NPC/finish | `updateGame` ordering | M03.5 |
| Bonus spawn/tick/expire/cleanup | generation, update, render and reset | M03.6 |
| UI/skin physics mutations | rendering callbacks can mutate runtime | M03.7 |
| Asset atlas/bundle ownership | generated catalog + direct resources | M04 |
| UI responsive ownership | immediate-mode drawing in GameRoot | M05 |
| Skin/bonus visual pipeline | manifest and runtime coupling | M06 |

## Important invariants for an external reviewer

- There is one Cocos scene and `GameRoot` is attached to `Canvas`; there are no serialized `@property` dependencies.
- Local persistence currently consists of 18 `mtr_*` keys and must preserve storage shape during extraction.
- Input has multiple paths; pause safety currently relies on a 220 ms debounce. A new adapter must not register a second listener set.
- Collision order is observable: power-up clocks → world/player motion → platform/ground → collectibles → bonuses → obstacles → NPCs → finish → particles.
- The project uses dynamically created nodes/pools; reset/transition cancellation ownership is a migration hazard, not a proven memory leak.

## Active tooling

- `tools/codex/quality-gate/` — typed shell-free static/profile runner with source/evidence guards.
- `tools/codex/analyze-game-root.js` — Cocos TypeScript AST inventory.
- `tools/codex/test-game-session-state.js` and `validate_game_session_state.py` — M03.2 contract validation.
- `Run-MtrAndroidEmulator*Qa.ps1` — Android emulator matrices/interaction.
- Playwright helpers — Web matrix and soak.

The ZIP includes `static-gates.json` and selected reports, but intentionally not raw build outputs or all generated assets.
