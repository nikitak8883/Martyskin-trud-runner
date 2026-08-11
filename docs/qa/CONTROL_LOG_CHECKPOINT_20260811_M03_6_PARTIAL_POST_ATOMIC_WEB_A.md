# M03.6 partial checkpoint — post-atomicity Web Pass A

Timestamp: `2026-08-11T17:18:26.5865917+03:00`  
Branch: `codex/mtr-source-freeze-v3`  
Parent HEAD: `bef8470f04dc7f9dd30a7280b88572b951c3704f`  
Scope: M03.6 epoch-aware power-up lifecycle.  
Physical device used: `NO`.

## Acceptance status

- status: `partially_working`
- M03.6 is **not complete** and is not added to either roadmap numerator.
- The bounded action requested before pausing is complete: the fresh post-fix Web Pass A finished `34/34 PASS`, interaction `PASS`, restart `10/10`.
- Release status remains blocked independently by M02.1 signing/distribution, M02.7 immutable Web deployment topology and M12.7 owner-approved final cleanup.

## Implemented source slice

- Added one pure Cocos-independent `PowerUpLifecycle` owner for nine kinds, ten effect timers and `spawned → collected → active → expired → cleaned` entity phases.
- Routed production spawn, collect, activation, timer tick, armor consumption, reset, terminal cleanup and component invalidation through the owner.
- Preserved all legacy durations, one-shot effects and raw timer subtraction semantics.
- Added epoch/stale-session rejection, injected epoch/tick readers, immutable snapshots/events and DEBUG-gated QA mutation.
- Added symmetric Web/Android `mtr_qa_powerups` startup-query routing and dedicated runtime probes.
- Code-review correction moved tick validation before activation/QA-seed mutation, preventing partial state writes when the injected tick provider is invalid.
- `BONUS_LABELS.length` now compile-time binds to the literal nine-kind contract.

Exact source fingerprint and per-file hashes are in `docs/global_modernization/v3/M03/M03_6_PAUSE_STATE.json`; aggregate SHA-256 is `F9042AFE4BB5E0899105ECF63AD179C9068007AFB3261E5DCF63177B5CBBF2A1`.

## Files changed

- Production: `assets/scripts/GameRoot.ts`, `assets/scripts/gameplay/powerups/PowerUpLifecycle.ts` and Cocos `.meta`, Android `AppActivity.java`.
- Validation/runtime QA: power-up unit/structural/Web/Android probes, collision-regression validators, config parity and static-gate manifest.
- Generated current inventory: `docs/global_modernization/v3/M03/game_root_inventory.generated.json`.
- Checkpoint only: this log, `M03_6_PAUSE_STATE.json`, and the compact current-state overlay.
- Unrelated root-level AGENTS, agent-monitor, Tasks, sticker and corpus changes were preserved and excluded.

## Backups and rollback

- No duplicate backup files were created.
- Rollback anchor is immutable parent commit `bef8470f04dc7f9dd30a7280b88572b951c3704f` plus the machine-readable per-file SHA-256 receipt.
- No destructive cleanup and no Hermes checkpoint pruning were performed because M03.6 is partial.

## Post-fix tests passed

| Gate | Result |
| --- | --- |
| Power-up pure unit | `PASS`, 14 groups, 9 kinds, 10 effect channels |
| Power-up structural validator | `PASS`, zero errors |
| M03.5 collision unit/structural regression | `PASS`, 10 groups / 8 kinds / 8 production routes |
| Shared config and startup-query parity | `PASS`, 15 levels and Web/Android query parity |
| GameRoot analyzer | `PASS`, 6,001 lines, zero parse diagnostics |
| Targeted `git diff --check` | `PASS` |
| Fresh Cocos `web-mobile-qa` build | `PASS`, `buildFinished=true`; Cocos log SHA-256 `7D5FEE4E56B5C7D36FDCF3DFCF25A3B6DA135E29C8E546009EBDE45D81BB1C3C` |
| Fresh Web power-up lifecycle | `PASS`, exact 8/8 marker, zero console/page/request diagnostics; report SHA-256 `9DC09F55B79C27B62A2FC7D2C929EF2776489E3D33EF58DBE7D601AE1C7D5575` |
| Fresh Web Pass A | `PASS 34/34`, interaction `PASS`, restart `10/10`; report SHA-256 `F3C1B46B22EA8AB2E44937CAA40D08A134AED8A459400FECCC0468ADF52D4354` |

Product-test failures after the atomicity correction: `0`.

## Evidence that is diagnostic-only

The earlier two Web and two Android cycles under `temp/m03-6-web/` and `temp/m03-6-android/`, plus the existing emulator APK, were produced before the last source correction. They remain useful diagnostic history but are forbidden as final M03.6 acceptance evidence.

The local coder advisory returned only non-specific suspicions. A later heavy-review timed out at 300 seconds and has no acceptance value. Its heavy model was subsequently confirmed unloaded; Lemonade recovered healthy with only the embedding model resident.

## Hygiene result

- No conflict markers, TODO/FIXME/HACK/XXX tails or direct legacy power-up writers were found in the touched source.
- The localhost QA server on port `18766` was stopped (`PID 24808`).
- The heavy local model was confirmed unloaded; the retrieval embedding model intentionally remains available.
- Build output, screenshots and machine reports remain ignored evidence and are not staged as source.
- No old checkpoints were removed while the unit is partial.

## Risks and remaining work

- Fresh post-fix Web Pass B and production Web build are still missing.
- Fresh post-fix Android export/build/install and both complete emulator cycles are still missing.
- Canonical static `19/19`, M2_PLUS, final Codex review, final hygiene, M03.6 reports and roadmap mutations are still missing.
- Therefore M03.6 cannot yet be called implementation-complete, validation-complete or release-ready.

## Roadmap position

- Execution units: `7/65 complete`; `58` mandatory remain, plus `7` conditional.
- Source packages: `22/95 complete`; `63` mandatory remain, plus `10` conditional.
- Active unit: `M03.6 partial`.
- Next unit M03.7A must not start until M03.6 receives fresh final-source Web/Android evidence, M2_PLUS, reports and a clean completion commit.

## Exact resume sequence

1. Verify the checkpoint commit/parent and aggregate source SHA-256 from `M03_6_PAUSE_STATE.json`; preserve all unrelated workspace changes.
2. Serve `build/web-mobile-qa` only on the isolated localhost port and run the dedicated lifecycle probe plus full Web Pass B; then stop the server.
3. Build fresh production `web-mobile` from the same source.
4. Build `build-android-emulator.json` with pinned JDK 17, Cocos Creator 3.8.8 and NDK 23.2; install only on `emulator-5554` and clear only `com.martyskin.trudrunner`.
5. Run fresh Android lifecycle A/B, matrix A/B and interaction A/B with name persistence, restart `10/10` and soak; do not use a physical device.
6. Run static `19/19`, fresh M2_PLUS, final bounded review and hygiene. Repair and rerun any affected gate.
7. Create final M03.6 reports, update both roadmap indexes/current state, commit completion and run the clean post-commit gate.

