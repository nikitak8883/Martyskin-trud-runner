# M03.1 GameRoot responsibility and binding inventory

Date: 2026-07-22  
Status: `PASS FOR M03.1 / RUNTIME UNCHANGED / M03.2 NEXT / RELEASE STILL BLOCKED`

## Accepted boundary

M03.1 is a read-only architecture package. It inventories the live `GameRoot` implementation and creates reproducible analysis tooling; it does not alter gameplay source, scenes, assets, build configuration, content identity, or runtime behavior.

- Source baseline at start: `25df6ea` on `codex/mtr-source-freeze-v3`.
- Shared content identity remains `mtr-v3-source-a5c4bdbb2fca`.
- Runtime source: `assets/scripts/GameRoot.ts`.
- Source size: `294,102` bytes / `5,428` physical lines.
- Source SHA-256: `22941AA58AF4A27DF103C5339D77D6E1D82028EE932740484CF7002B0EF507A2`.
- Scene: `assets/scenes/main.scene`, SHA-256 `DEB802A071ACFEF8E78C5A7FEC2CC80027B190E477570F4832C508DEF3FB1854`.
- Script UUID: `7e9f19dc-1467-4baf-90f0-8ad777e70111`; the serialized component is attached to `Canvas` in `main.scene`.
- No physical Android device was addressed. No emulator/browser runtime was required because runtime inputs are byte-identical.

Reproducible command:

```powershell
node tools/codex/analyze-game-root.js
```

The analyzer uses TypeScript `5.8.2` shipped with Cocos Creator `3.8.8`, parses the live source with zero diagnostics, and writes `game_root_inventory.generated.json`. It inventories methods, constructors and get/set accessors; the live class currently has zero constructors/accessors. A repeated run produced the same SHA-256 `20F1930860C00D5BB6727A32847340ED1506112E3B229504A132B639D7E3DB01`.

## Structural inventory

`GameRoot` starts at line `936` after `935` lines of imports, contracts, helper functions, constants, level data, asset maps and UI/gameplay tables. The file imports three modules (`cc`, generated themed-asset catalog, and `UITheme`) and defines 18 top-level helper functions before the class.

| Metric | Current value | Consequence |
| --- | ---: | --- |
| Class fields | 170 | 169 are mutable after initialization; one is `readonly` (`fixedDt`). |
| Methods | 267 | 264 private plus the Cocos lifecycle methods `onLoad`, `onDestroy`, `update`. |
| Internal call occurrences | 1,046 | 613 unique caller→callee pairs. |
| Serialized `@property` bindings | 0 | The scene exposes no inspector-owned dependencies for `GameRoot`. |
| Dynamic node patterns | 10 | Runtime creates background, layer, input, pooled sprite and pooled label nodes. |
| Scene graph operations | 34 | `addComponent`, `addChild` and `setSiblingIndex` are owned by `GameRoot`. |
| Listener operations | 16 | 8 registrations and 8 matching unregister operations. |
| Scheduled callbacks | 15 | All use `scheduleOnce`; no explicit `unschedule*` call exists. |
| Local-storage operations | 37 | 18 distinct keys across settings, records and achievements. |
| Resource-load sites | 4 | Audio clips, backgrounds and themed object sprites. |

### Responsibility map

The ranges below are contiguous ownership regions in the current file, not proposed modules. Method-line totals count declarations/bodies only.

| Current responsibility | Lines | Methods | Method lines | Primary owners / hotspots |
| --- | ---: | ---: | ---: | --- |
| lifecycle, responsive policy, RNG and session snapshot | 1111–1395 | 15 | 271 | `onLoad` (106), `update`, `transitionTo`, `createGameState` |
| settings persistence | 1397–1443 | 2 | 46 | `loadSettings`, `saveSettings` |
| audio load/playback | 1445–1480, 2037–2151 | 15 | 138 | `loadAudioClips`, `playVoice`, `ensureMusic` |
| asset queues, critical gates and background preload | 1482–2035 | 41 | 514 | `ensureBackgroundFrame`, `requestObjectSprite`, `beginObjectSpriteLoad` |
| records and achievements | 2153–2252 | 11 | 90 | record storage, achievement unlock/progress |
| session reset/start, startup QA and developer routes | 2254–2625 | 15 | 358 | `reset` (61), `applyStartupQuery` (104), QA spawners |
| level generation, gameplay, collisions and power-ups | 2627–3075 | 7 | 443 | `generateLevel` (152), `updateGame` (175), `activateBonus`, `damage` |
| edit boxes, background/world/player/HUD rendering | 3077–4358 | 85 | 1,198 | sprite pools, player/equipment visuals, HUD and overlays |
| menu rendering and UI actions | 4360–4852 | 19 | 475 | `drawMenu` (213), settings rows, level cards, skin preview |
| raw input, geometry and world helpers | 4854–5076 | 27 | 197 | touch/keyboard handlers, hit geometry, particles |
| render pools, buttons, text and primitives | 5078–5427 | 30 | 321 | pooled nodes, `button`, `text`, primitive drawing |

Call-graph hotspots confirm the coupling: `drawMenu` contains 164 internal call occurrences, `generateLevel` 47, `updateGame` 38, and `onLoad` 23. The most-called internal operations are `segment` (89), `text` (64), `circle` and `fillRect` (63 each), `button` (47), `drawAssetSprite` (43), and `transitionTo` (33).

## State and session ownership

- `State` has 14 values; `FsmMode` folds them into 8 presentation/gameplay modes.
- `transitionTo` at lines 1352–1366 is the only detected writer of `state`, which is a good strangler seam.
- The method accepts every typed target from every caller. There is no allowed-transition matrix, rejection result, or deterministic invalid-transition event.
- `RunnerGameState` is a derived snapshot rebuilt by `syncGameState`; the mutable class fields remain canonical.
- UI actions in `drawMenu`, startup QA, level completion, damage and pause routes all call `transitionTo` directly.
- `reset` writes 55 fields and is the broadest mutation boundary. It also resets pools, effects, bonuses, run metrics and pending QA state.

M03.2 must wrap this existing seam, preserve every currently observed valid edge, and reject only explicitly invalid edges. It must not make `RunnerGameState` a second mutable source of truth.

## Input ownership

`onLoad` registers canvas resize, one `PauseTouchZone` handler, four global touch handlers and two keyboard handlers. `onDestroy` unregisters all eight with matching source/event/handler triples.

Input is nevertheless handled through several paths:

- touch start calls `handleTouch`; otherwise it directly enables glide;
- touch move/end mutate glide directly;
- keyboard calls pause, jump and dash directly;
- HUD button callbacks created during rendering call pause, jump and dash directly;
- `PauseTouchZone` also calls pause, while the global touch route checks the same rectangle;
- duplicate pause is currently suppressed by the `220 ms` debounce in `togglePauseFromInput`.

M03.4 must preserve touch-start action timing, glide semantics and the debounce while routing all sources through one adapter. It must not register a second set of global listeners during migration.

## Collision and gameplay event order

`updateGame` owns physics integration, collision detection, scoring, achievements, audio, particles and terminal state selection in one 175-line method. Current order is observable behavior and must remain stable:

1. decrement power-up/effect clocks;
2. advance world and story stage;
3. integrate player gravity/glide;
4. resolve platform landing, then ground clamp;
5. collect bananas/coconuts/fig leaves;
6. collect and activate bonuses;
7. resolve obstacle swept collisions and damage;
8. resolve NPC stomp or NPC damage;
9. evaluate level end, persist progress/record and play terminal audio;
10. update particles.

There are no typed collision events today. M03.5 must first wrap callbacks around this exact order and payload data; moving detection or side effects into a new order is out of scope.

## Power-up ownership

Nine bonus kinds are spawned in `generateLevel`, collected in `updateGame`, activated in `activateBonus`, decremented in `updateGame`, rendered across player/HUD methods, and cleared in `reset`. The affected clocks/state include jump, dash, shield, magnet, vest, coffee, blueprint, pass and life-aura effects, plus cooldown, invincibility, HP and score side effects.

M03.6 must use an injected clock and explicit `spawn → collect → activate → tick → expire → cleanup` contract. Initial extraction must delegate to current mutation values and preserve reset/death/retry behavior before any balancing change.

## Timers, listeners and cleanup

- Listener lifecycle is symmetric at component destroy: `8 register / 8 unregister`.
- Fifteen deferred jobs use Cocos `scheduleOnce`; there are no global `setTimeout`/`setInterval` calls.
- There is no explicit `unschedule` on reset or state transition. Existing callbacks rely on idempotent preload flags or state/pending-level guards; Cocos owns final component-destroy cleanup.
- Runtime-created nodes/components are descendants of `Canvas` and inherit scene/component destruction, but per-session ownership is not explicit.

This is not a proven leak, but it is a migration hazard. M03.3/M03.6/M03.7 must introduce bounded lifecycle tokens or equivalent cancellation ownership before old paths are removed.

## Scene and persistence bindings

`main.scene` contains one `Canvas`, one child `Camera`, and the encoded `GameRoot` component on `Canvas`. `GameRoot` has zero serialized properties and constructs all additional nodes/components in code. Dynamic patterns include:

- `BG_FAR_BitmapBackground` and bitmap segments;
- one Graphics/Sprites/Labels triplet per render layer;
- `PauseTouchZone`, `DevPasswordInput`, `PlayerNameInput`;
- pooled object-sprite and label nodes.

Persistence is also owned directly by `GameRoot`: 37 accesses across 18 `mtr_*` keys for player/settings/developer flags, records and achievements. State extraction must keep the existing keys and serialization shape unchanged.

## Confirmed coupling findings

| ID | Severity | Finding | Required treatment |
| --- | --- | --- | --- |
| M03-F01 | major | One component owns session, input, collision, power-ups, persistence, assets, audio, rendering, UI and QA. | Strangler extraction only; one responsibility per accepted patch. |
| M03-F02 | major | `transitionTo` has no validity contract despite being the sole state writer. | M03.2 typed transition table/result and parity tests. |
| M03-F03 | major | UI rendering installs callbacks that directly mutate physics/session state. | M03.4 action adapter, then M03.7 UI emits intents only. |
| M03-F04 | major | Collision order and side effects are embedded in `updateGame`. | M03.5 typed events preserving exact current ordering. |
| M03-F05 | major | Power-up lifecycle spans generation, collision, clocks, damage, rendering and reset. | M03.6 service with injected clock and explicit cleanup. |
| M03-F06 | moderate | Deferred callbacks lack explicit reset/transition cancellation ownership. | Add lifecycle token/cancellation before deleting legacy paths. |
| M03-F07 | moderate | Scene and persistence dependencies are implicit because there are no serialized/injected dependencies. | Introduce narrow adapters; preserve scene UUID and storage keys. |
| M03-F08 | moderate | Pause has overlapping node/global routes and relies on time debounce. | Preserve debounce while converging on a single routed action. |

No finding is fixed in M03.1 because this package is inventory-only.

## Accepted extraction sequence

1. **M03.2 — GameSessionStateMachine:** extract `State`/`FsmMode`, current valid edges and deterministic rejection result around `transitionTo`; no UI or physics move.
2. **M03.3 — bounded dev event log:** log state/action/collision lifecycle with fixed capacity, reset ownership and production silence.
3. **M03.4 — InputActionRouter:** adapt keyboard, global touch, HUD buttons and pause zone to typed intents; preserve event timing/debounce.
4. **M03.5 — CollisionRouter:** emit typed platform/pickup/bonus/hazard/NPC/finish events in the current order; retain side effects in `GameRoot` initially.
5. **M03.6 — PowerUpLifecycle:** move bonus state and clock ownership with injected time and reset/death/retry tests.
6. **M03.7 — UI/skin physics decoupling:** UI emits actions only; prove cleanup/parity, then remove superseded direct paths.

The first implementation patch must be M03.2 only. It should reuse the prepared reference draft as advisory input, verify it against this live inventory, and keep the existing path active through an explicit adapter until parity passes.

Final development static gate `qg.20260722094323.cb31e1f5e6da` passed `8/8` mandatory checks with zero findings and stable explicitly authorized dirty source. The accepted pre-commit report SHA-256 is `55517CBA1D6E48AF4353BD6169D36AC7217D5CCDA0DC2CFBA231F1AA1BECF463`.

## Rollback

Delete `tools/codex/analyze-game-root.js` and the M03.1 generated/report files, then revert only the M03.1 index updates. No runtime rollback, asset cleanup, build rollback or device action is required.
