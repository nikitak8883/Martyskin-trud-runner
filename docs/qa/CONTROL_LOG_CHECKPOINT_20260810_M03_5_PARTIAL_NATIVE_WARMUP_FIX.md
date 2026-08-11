# Control log checkpoint — M03.5 partial after native warmup fix

Date: 2026-08-10  
Branch: `codex/mtr-source-freeze-v3`  
Base commit: `43816119b04c04ce95ef03e8e49c72085f4bce08`

## Status

- M03.5 implementation: `PARTIAL`; it is not counted complete in the roadmap.
- Nearest bounded action completed: post-fix static gate `18/18 PASS`, zero findings.
- Latest native warmup correction has not yet been rebuilt or runtime-tested.
- Physical device used: `NO`; Android work remained on `emulator-5554` (`x86_64`).
- Release status remains blocked independently by the accepted signing/distribution, immutable Web deployment and final cleanup decision gates.

## Implemented boundary

- Added one pure synchronous `GameplayCollisionRouter` with eight typed event kinds and immutable payload snapshots.
- Preserved the existing production detection order: platform, ground, collectible, bonus, obstacle, NPC stomp, NPC hit, level finish.
- Kept all gameplay side effects in one exhaustive `GameRoot.applyCollisionEvent` callback and permanently forbade recursive router calls from that callback.
- Added deterministic recorded-order tests plus dev-only Web and Android-emulator runtime probes.
- Added a separate `debug=true` Web QA build; production `build-web-mobile.json` remains `debug=false`.
- Added Android/Web startup-query parity for `mtr_qa_collisions`.

## Completed evidence on current source

- Cocos-compatible full TypeScript compile: PASS.
- Collision Node suite: `10/10 PASS`.
- Collision Python integration validator: PASS (`8` production routes + `8` isolated QA routes).
- Project config validator: PASS.
- Static gate: `temp/quality-gate-m03-5/report-native-warmup-fix-static.json`, `18/18 PASS`, SHA-256 `08279E9DD47842DD13B97A1ECA3F85383516B192164A89928ECE342D204D36BC`.

## Failure found and correction applied

The first Android interaction cycle functionally passed touch controls, typed and persisted `QAPrimateC1`, `10/10` restart iterations and the 30-second soak. The gate correctly failed because cold name entry emitted eight unexpected `MTR_OBJECT_SPRITE_LOAD_SLOW` warnings for NPC and player-variant assets (`2289–2923 ms`).

Root cause: native boot scheduled non-critical utility and full selected-skin variant warmup immediately after the first background, even while the user remained on the name screen. The source now retains only critical first-screen assets at native boot and starts utility/variant warmup after gameplay begins. Static and type contracts pass after this correction, but runtime acceptance is intentionally pending a fresh rebuild.

Failed evidence is retained at `temp/m03-5-android-pass-a-interaction/android_interaction_cycle1_summary.json` with SHA-256 `086B22CA3184E54E0A6DCEC64070FA541CB84D92DBC615476475EC143A705D0A`.

## Evidence that is now pre-fix and non-closing

- Web Pass A: `34/34`, interaction PASS, restart `10/10`.
- Web Pass B: `34/34`, interaction PASS, restart `10/10`.
- Web collision runtime probe: two PASS cycles.
- Android collision probe A: PASS.
- Android matrix A: `28/28 PASS`.
- APK before the warmup correction: `142896248` bytes, SHA-256 `AA81561B2EE7C4A90ED4D99DABCD3E5BF61D4258C7413434198994C0C9913D45`.

These results prove the collision seam before the last source edit but must not be used as final M03.5 acceptance.

## Roadmap position

- Execution units: `6/65 complete`; `59` mandatory remain, plus `7` conditional.
- M03.5 remains the active unit and is not included in the completed numerator.
- M03.6 and later work must not begin until M03.5 receives fresh final-source Web/Android evidence, review and a clean checkpoint commit.

## Exact resume sequence

1. Verify branch, base commit and hashes in `docs/global_modernization/v3/M03/M03_5_PAUSE_STATE.json`; preserve unrelated workspace changes.
2. Build fresh production Web and `web-mobile-qa` from the current source. Repeat both collision probes and both full `34/34 + interaction + 10/10 restart` matrices.
3. Build a fresh `build-android-emulator.json` APK, install with explicit `adb -s emulator-5554`, and clear only `com.martyskin.trudrunner` in the emulator.
4. Run Android collision A/B, matrix A/B and interaction A/B. The cold name flow must retain the value and persistence checks and report zero unexpected slow-load diagnostics; each interaction cycle keeps a 30-second soak.
5. Run final M2_PLUS, bounded code review and hygiene gate. Only then create M03.5 reports, update the roadmap, commit the unit and run the clean post-commit static gate.
6. Do not use the physical phone unless a later user command explicitly authorizes it.
