# M03.7A completion checkpoint — runtime ownership

Timestamp: `2026-08-13T17:30:00+03:00`  
Branch: `codex/mtr-source-freeze-v3`  
Pre-completion HEAD: `78d85a9a04dc04ca1ebe106a22e9ce4b5945b643`  
Scope: M03.7A typed UI intents plus timer/listener/state cleanup ownership.  
Physical device used: `NO`.

## Acceptance status

- status: `complete`
- implementation: `complete`
- validation: `complete`
- release: `blocked` by M02.1, M02.7 and M12.7 outside this unit
- final source fingerprint: `328C0AA1847190DB7C8EB4E46CFCA759390B015B6C3EE470AFCF3A17CAA1C679`

## Files changed

- Runtime: `GameplayUiIntentAdapter.ts`, `GameRuntimeLifecycleOwner.ts`, `GameRoot.ts` and Cocos metadata.
- Android startup routing: ownership QA query allowlist in `AppActivity.java`.
- Validation: unit/structural/Web/Android ownership harnesses, config parity and the 20-step static manifest.
- Reports/roadmaps: M03.7A implementation report, code review, machine summary, current state and canonical v3/v4 indexes.
- Unrelated root AGENTS, agent monitor, Tasks, sticker and project-library changes were preserved and excluded.

## Backups and rollback

- No duplicate backup files were created.
- Rollback anchor: `78d85a9a04dc04ca1ebe106a22e9ce4b5945b643` plus the 16-entry fingerprint in `M03_7A_VALIDATION_SUMMARY.json`.
- M03.7A retained legacy methods; no destructive legacy deletion was performed.

## Commands and tests

| Gate | Result |
| --- | --- |
| UI/lifecycle unit behavior | `14/14 PASS`; six UI intents; stale/cancel/destroy cases covered |
| Structural ownership | `PASS`; listeners 8; session routes 11; component routes 12; direct scheduler boundary 1 |
| Config and startup-query parity | `PASS`; 15 levels; Web/Android parity |
| GameRoot analyzer | `PASS`; 6181 lines; zero parse diagnostics |
| Fresh QA Web build | `buildFinished=true`; post-process PASS |
| Web ownership A/B | exact `8/8`; one READY each; zero diagnostics |
| Web matrix A/B/recovery | each `34/34`; interaction PASS; restart `10/10` |
| Fresh Android emulator build/install | Cocos export/Gradle/payload/install PASS on `emulator-5554` |
| Android ownership A/B/recovery | exact `8/8`; one READY each; zero FAIL/fatal |
| Android matrix A/B | each `28/28` |
| Android interaction A/B/recovery | touch/name/restart/soak PASS; `30/30` restarts; zero process loss |
| Canonical static gate | `20/20 PASS`; findings `0` |
| M2_PLUS | `12/12 PASS`; findings `0` |
| Final code review / hygiene | PASS; open findings `0`; ports `18767/18768` closed |

Product-test failures remaining after correction: `0`.

## Metrics

- APK: `142905915` bytes; SHA-256 `5E8AEB4783E4F418DACC3BCE31FA36175353D668A734D7FC666EC6A7A6CA6FCC`; emulator debug only.
- Static report SHA-256: `0CF2B086C3B508B1B3C0F3B81D22FF21338FE4D80DD5CADBAE06F119B08BDB2E` (`qg.20260813143314.00504ec290b1`, `20/20 PASS`).
- M2_PLUS SHA-256: `49DCB3CE3D0BC31862798404BE2799EB130636DBD045DFE5F907085459A94C2F`.
- Android focused recovery: soak `30.466 s`, process losses `0`, PSS `185787 -> 200543 KiB`.

## Risks

- APK is x86_64 emulator QA evidence and is not a production-valid arm64 release.
- Web QA build is local evidence and is not an authorized Pages deployment.
- Legacy methods remain intentionally present until the M03.7B hidden-reference and rollback proof.
- Production signing/distribution, immutable Web deployment and final owner-selected cleanup remain blocked decisions.

## Roadmap position

- Execution units: `9/65 complete`; `56` mandatory remain, plus `7` conditional.
- Source packages: `23/95 complete`; `62` mandatory remain, plus `10` conditional.
- Completed unit: `M03.7A`; aggregate source package M03.7 remains pending.
- Next ready unit: `M03.7B`.

## Next steps

1. Build a bounded hidden-reference inventory and rollback map for superseded M03 paths.
2. Remove only proven-dead paths in M03.7B.
3. Run QA7 and M2_PLUS after removal.
4. Preserve release blockers until their explicit decision gates are resolved.
