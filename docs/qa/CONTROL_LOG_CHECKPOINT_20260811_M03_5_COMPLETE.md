# Control log checkpoint — M03.5 complete

Date: 2026-08-11  
Branch: `codex/mtr-source-freeze-v3`  
Base before M03.5: `43816119b04c04ce95ef03e8e49c72085f4bce08`

## Status

- Acceptance status: `working`.
- M03.5 implementation: `COMPLETE`.
- Canonical M2_PLUS: `12/12 PASS`, zero findings.
- Web: Pass A, Pass B and recovery each `34/34 PASS`, interaction and restart `10/10` PASS; collision query `8/8` effects in both runs.
- Android emulator: Pass A and Pass B each `28/28 PASS`; collision query, interaction/name/restart/soak and cold recovery PASS.
- Physical device used: `NO`.
- Release status: `BLOCKED` independently by production signing/distribution, immutable Web deployment and approved final cleanup.

## Files changed

- Added `GameplayCollisionRouter` and Cocos metadata.
- Routed eight existing collision outcomes and one exhaustive consumer in `GameRoot`.
- Added permanent Node/Python contracts plus Web and Android-emulator collision QA entrypoints.
- Added explicit display-0 touchscreen injection, input-channel admission and atomic failure evidence to the Android interaction harness.
- Deferred non-critical native utility/selected-skin warmup until gameplay after fresh-build warnings; critical level admission remains intact.
- Updated M03 reports and v3/v4 execution ledgers.
- Unrelated root workspace changes were preserved and excluded.

## Backups created

- No source backup copy was created; rollback is Git-bounded and documented in `gameplay_collision_report.md`.
- Corrected failure evidence is retained under ignored `temp`; no failed evidence was promoted into runtime assets.
- The local safety layer rejected deletion of verified ignored-temp/cache paths; those files remain untracked and excluded from Git, APK and Web artifacts. No protected or tracked file was deleted.

## Commands run

- Permanent router Node/Python contract checks and JavaScript/PowerShell syntax checks.
- Fresh release/QA Web builds, two full Web matrices and one focused recovery matrix.
- Fresh Android debug build/install on `emulator-5554`, two full matrices, two interaction cycles and a clean focused recovery after `pm clear`.
- Dedicated Web and native collision queries.
- Canonical static quality gate and M2_PLUS profile.
- `git diff --cached --check`, bounded code review and hygiene scans.

## Tests passed

- Collision contract: `10/10` behavior groups; 8 kinds, 8 production routes, 8 QA routes.
- Static: `18/18 PASS`, zero findings.
- Web: three `34/34` matrices, three interactions and three `10/10` restart loops.
- Android: two `28/28` matrices; two full interactions; focused recovery with touch/FSM, name persistence, `10/10` restart and `30.378 s` soak.
- M2_PLUS: `12/12 PASS`, zero findings.

## Tests failed and corrected

- One pre-instrumentation recovery failed before preserving evidence; this exposed and fixed the harness logging gap.
- The reproduced recovery failure captured `ActivityRecordInputSink ... NO_INPUT_CHANNEL`. Pointer Location proved logical coordinates were correct; explicit `input touchscreen -d 0 tap` fixed source/display targeting.
- The final clean recovery passed with zero process loss and zero unexpected diagnostics. Failed evidence remains retained for traceability.

## Metrics and acceptance evidence

- Static report: `temp/quality-gate-m03-5/report-post-recovery-static.json`, `18/18 PASS`, SHA-256 `4CF2C4FD31084C2B7587088501AA599CCBA6835DD963060F861E91608EF6DD27`.
- M2_PLUS: `temp/m03-5-m2-profile/20260811T123659Z/m2-plus.profile.json`, `12/12 PASS`, SHA-256 `B47EF43DF95BFD0D7FA21727A973AAE0A8A449D538C67546BF654894D20408FA`.
- Web Pass B: `temp/m03-5-postfix-web/matrix-b/web_matrix_cycle2_summary.json`, SHA-256 `027F747D98AECF14C890B5F5320DC583B1C43F0A7A699C1675A579ACD18304FB`.
- Android Pass B matrix: `temp/m03-5-postfix-android/matrix-b/android_matrix_cycle2_summary.json`, SHA-256 `E6C9120CACB74E6CC7B029BA26EA8756C1353965FD65DDAC78DD837B15DFAA57`.
- Android Pass B interaction: `temp/m03-5-postfix-android/interaction-b/android_interaction_cycle2_summary.json`, SHA-256 `163D5447925D1F3BE208C1BFF7F2A4690A3880AA5A08D04DB91DE5648A4F5080`.
- Focused Android recovery: `temp/m03-5-postfix-android/focused-recovery-explicit-input/android_interaction_cycle5_summary.json`, SHA-256 `DA40620EB5B566FCF8361E6282A035BD35582FF0A098964570777FFA421CF209`.
- QA APK: `142896264` bytes, SHA-256 `5FD85C440C41BB0190126CBF90C506FF7F9C39108565C813E05A7A6CE9EBC6C1`.

## Risks

- The APK is x86_64/debug emulator evidence, not a production-signed arm64 release.
- M03.6 still owns power-up timers and lifecycle cleanup; M03.5 deliberately does not rebalance them.
- Immutable Web deployment and live parity remain unapproved/unexecuted.
- Destructive final cleanup remains blocked until M12.7 owner approval.
- A small set of ignored local Python caches and coordinate-probe evidence remains because the execution safety layer denied deletion; this is hygiene debt only and does not enter source or release artifacts.

## Roadmap position

- Execution units: `7/65 complete`, `58 mandatory remaining`, plus `7 conditional`.
- Source packages: `22/95 complete`, `63 mandatory remaining`, plus `10 conditional`.
- Next unit: `M03.6` epoch-aware power-up lifecycle with injected time.

## Resume sequence

1. Verify the M03.5 commit and clean post-commit `18/18` static report.
2. Retrieve only the power-up fields/methods/call graph and M03.6 acceptance contract.
3. Define one pure lifecycle owner with injected time and lifecycle epoch; preserve all current constants and effect order.
4. Migrate `spawn → collect → activate → tick → expire → cleanup` in bounded slices with reset/death/retry tests.
5. Execute P4 plus applicable M2_PLUS Web and Android-emulator cycles; do not use a physical device.
