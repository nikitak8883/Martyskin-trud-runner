# Control log checkpoint — M03.4 complete

Date: 2026-08-10  
Branch: `codex/mtr-source-freeze-v3`  
Base before M03.4: `80b823799c9b82bf8510b98d1ecf3d818e47fa47`

## Status

- M03.4 implementation: `COMPLETE`.
- Canonical M2_PLUS: `12/12 PASS`, zero findings.
- Web: Pass A, Pass B and recovery each `34/34 PASS`, interaction and restart `10/10` PASS.
- Android emulator: Pass A and Pass B each `28/28 PASS`; interaction/name/restart/soak PASS; cold recovery PASS.
- Physical device used: `NO`.
- Release status: `BLOCKED` independently by production signing/distribution, immutable Web deployment and approved final cleanup.

## Implemented boundary

- Added one pure typed `GameplayInputAdapter` for jump, glide, dash and pause.
- Routed keyboard, global touch, HUD, pause zone, QA and session reset through it.
- Preserved one mutable glide writer, existing physics methods, listener topology and side-effect order.
- Centralized pause debounce at `220 ms` across all sources.
- Added permanent Node/Python contract checks and a reusable guarded Web matrix CLI.
- Corrected the Android interaction harness so dash is asserted before collision can clear its short pose timer.

## Acceptance evidence

- Static report: `temp/quality-gate-m03-4/report-recovery-static.json`, `17/17 PASS`, SHA-256 `CB2DA585A36746F63E57FFD2CDF0EBD8E450EACEA28FC67721EFAB1E8D84148B`.
- M2_PLUS report: `temp/m03-4-m2-profile/20260810T144944Z/m2-plus.profile.json`, `12/12 PASS`, SHA-256 `D2CA3C0FE56D1DEA198584EC80D7CF4E440667B0DB38BD430B7A27B530DE3EB4`.
- Pass B Web: `temp/m03-4-web-pass-b/web_matrix_pass_b_summary.json`, SHA-256 `CC9CADD0E93DAA0F64784CF308405748E68BABDCB4BB1DDDC284901CF58F3B59`.
- Pass B Android matrix: `temp/m03-4-android-pass-b-matrix/android_matrix_cycle5_summary.json`, SHA-256 `A10899EE4ABD92F1C69F5B95F769F9067AC99829215729D9B39876894B4B4FFE`.
- Pass B Android interaction: `temp/m03-4-android-pass-b-interaction/android_interaction_cycle5_summary.json`, SHA-256 `E21A3BF739819A212B856958B5096FB8DCFE6BDE47C66A920FC78A1FB06CED12`.
- Cold recovery: `temp/m03-4-android-recovery-interaction-retry/android_interaction_cycle7_summary.json`, SHA-256 `2B71A78C8FD805B3982E59666D1A9DF3D8249BC6168259644A20B11488BA0AF1`.
- QA APK: `142892688` bytes, SHA-256 `3C692EA18959CE18FBFE310C6322760340274EE3ACB6CCDA5D62E55E2F63FF79`.

## Corrected failure

The first post-`pm clear` recovery attempt failed to observe `crouch_dash`. Product inspection showed that the harness waited after jump long enough for a normal collision to clear `dashTimer`. The QA order was corrected, the PowerShell parser revalidated and a new cold recovery cycle passed all actions, persistence, restart and soak checks. The failed evidence is retained under ignored `temp/m03-4-android-recovery-interaction` for traceability.

## Roadmap position

- Execution units: `6/65 complete`, `59 mandatory remaining`, plus `7 conditional`.
- Source packages: `21/95 complete`, `64 mandatory remaining`, plus `10 conditional`.
- Next unit: `M03.5` typed collision event routing with exact legacy side-effect order.

## Resume command sequence

1. Verify `git status --short --branch` and the M03.4 checkpoint commit.
2. Run the clean canonical static gate and confirm `17/17 PASS` if not already attached to the commit.
3. Retrieve the bounded `GameRoot` collision call graph and current side-effect ordering.
4. Implement M03.5 as a pure typed event seam; do not reorder pickup, obstacle, platform, trigger or finish effects.
5. Execute P4 plus applicable M2_PLUS Web and Android-emulator cycles; do not address a physical device.
