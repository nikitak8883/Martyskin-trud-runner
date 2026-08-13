# M03.6 completion checkpoint — power-up lifecycle

Timestamp: `2026-08-13T15:50:00+03:00`  
Branch: `codex/mtr-source-freeze-v3`  
Pre-completion HEAD: `c381bc7cd32ed95ca297be2c301d9dd621fb0198`  
Scope: M03.6 epoch-aware power-up lifecycle.  
Physical device used: `NO`.

## Acceptance status

- status: `complete`
- implementation: `complete`
- validation: `complete`
- release: `blocked` by M02.1, M02.7 and M12.7 outside this unit
- final source fingerprint: `CE174DBF392C72EDB2D6D9490436384254C746867E4B72FC911847604B0341DC`

## Files changed

- Runtime: `assets/scripts/GameRoot.ts`, `assets/scripts/gameplay/powerups/PowerUpLifecycle.ts` and Cocos metadata.
- Android startup routing: `native/engine/android/app/src/com/cocos/game/AppActivity.java`.
- Validation: power-up unit/structural/Web/Android harnesses, collision regressions, config parity and the 19-step static manifest.
- Corrective validation fix: `tools/codex/validate_game_root_dev_event_adapter.py` now verifies named guarded routes and scopes the exact dev-event reset writer instead of imposing obsolete whole-file cardinalities.
- Reports/roadmaps: M03.6 report, review, machine summary, current state, v3 work-package index, v4 execution index and integrated roadmap.
- Unrelated root AGENTS, agent monitor, Tasks, sticker and project-library changes were preserved and excluded.

## Backups and rollback

- No duplicate backup files were created.
- Rollback anchor: `bef8470f04dc7f9dd30a7280b88572b951c3704f` plus the 15-entry source fingerprint in `M03_6_VALIDATION_SUMMARY.json`.
- No destructive cleanup or historical checkpoint pruning was performed.

## Commands and tests

| Gate | Result |
| --- | --- |
| Power-up unit / structural | `14/14 PASS`; 9 kinds; 10 effects; structural PASS |
| Collision regression | `10/10 PASS`; 8 kinds / 8 production routes |
| Config and startup-query parity | `PASS`; 15 levels; Web/Android parity |
| GameRoot analyzer | `PASS`; 6001 lines; zero parse diagnostics |
| Fresh QA Web build | `buildFinished=true`; post-process PASS |
| Fresh production Web build | `buildFinished=true`; post-process PASS |
| Web lifecycle A/B | exact `8/8`; one READY each; zero diagnostics |
| Web matrix A/B/recovery | each `34/34`; interaction PASS; restart `10/10` |
| Fresh Android emulator build/install | toolchain/export/Gradle/payload/install PASS |
| Android lifecycle A/B | exact `8/8`; one READY each; zero FAIL/fatal |
| Android matrix A/B | each `28/28` |
| Android interaction A/B/recovery | touch/name/restart/soak PASS; `30/30` restarts; zero process loss |
| Canonical static gate | `19/19 PASS`; findings `0` |
| M2_PLUS | `12/12 PASS`; findings `0` |
| Final code review / hygiene | PASS; open findings `0`; port `18766` closed |

Product-test failures remaining after correction: `0`.

## Metrics

- APK: `142901828` bytes; SHA-256 `B33B9DDD364E91D042C134A574DCA5DD0C00533BC001C3DF6C1EFD188D7B8F68`; emulator debug only.
- Static report SHA-256: `6FDC952C2DDB11C3ECF2D63F0724A69BBBD879DBEDF1622C12B6985ADA574462` (`qg.20260813125709.210862549deb`, `19/19 PASS`).
- M2_PLUS SHA-256: `B7DDB6D35B2E0BBDA64DFE06DE1DC7A1CF6D595F126486BA7515B7860E65536F`.
- Android focused recovery: soak `30.212 s`, process losses `0`, PSS `233718 -> 196998 KiB`.

## Risks

- APK is x86_64 emulator QA evidence and is not a production-valid arm64 release.
- Web production build is local evidence and is not an authorized Pages deployment.
- Production signing/distribution, immutable Web deployment and final owner-selected cleanup remain blocked decisions.
- M03.7B deletion remains forbidden until M03.7A proves ownership/cleanup and M2_PLUS parity.

## Roadmap position

- Execution units: `8/65 complete`; `57` mandatory remain, plus `7` conditional.
- Source packages: `23/95 complete`; `62` mandatory remain, plus `10` conditional.
- Completed unit: `M03.6`.
- Next ready unit: `M03.7A`.

## Next steps

1. Inventory remaining UI/skin mutation authority and cleanup paths without deleting legacy code.
2. Implement M03.7A ownership/cleanup proof as a bounded patch.
3. Run P4 and M2_PLUS before considering M03.7B deletion.
4. Preserve release blockers until their explicit decision gates are resolved.
