# M03.6 — epoch-aware power-up lifecycle

Date: 2026-08-13  
Status: `COMPLETE / M2_PLUS 12 OF 12 PASS / WEB AND ANDROID-EMULATOR PASS / RELEASE BLOCKED`

## Scope

M03.6 extracts power-up spawn, collect, activation, timer tick, expiration, cleanup and per-run counters into one synchronous Cocos-independent `PowerUpLifecycle`. `GameRoot` remains the owner of rendering and one-shot game mutations, but no longer writes the ten power-up effect channels or run counters directly.

No duration, score, healing, invincibility, cooldown, collision-order, save-schema or content change is part of this package.

## Accepted contract

- Nine power-up kinds and ten effect channels retain their legacy values.
- Entity phases are `spawned -> collected -> active -> expired -> cleaned`.
- Epoch and fixed-step tick are injected; wall clock, timers, storage, networking and Cocos APIs are forbidden in the owner.
- Spawn IDs are validated and duplicate instances are rejected.
- Collect/activate reject missing, stale, closed-session, wrong-phase and type-mismatched events without partial mutation.
- Reset starts a fresh epoch, clears effects/counters/entities and rejects stale callbacks.
- Terminal transitions clean the session; retry starts a fresh owner epoch; component destruction invalidates the owner.
- Events and snapshots are immutable and monotonically sequenced.
- QA mutation is DEBUG-gated and the Android harness refuses non-QEMU targets.

Final 15-file source fingerprint: `CE174DBF392C72EDB2D6D9490436384254C746867E4B72FC911847604B0341DC`.

## Permanent validation

1. `node tools/codex/test-powerup-lifecycle.js`
   - real TypeScript owner executed under strict TypeScript 5.8.2;
   - `14/14` behavior groups, 9 kinds, 10 effects, ordered phases: PASS.
2. `python -B tools/codex/validate_powerup_lifecycle.py --project-root .`
   - one owner, no direct legacy writers, exact GameRoot routes, metadata and Web/Android query parity: PASS.
3. Collision and GameRoot regressions
   - collision behavior `10/10`, structural routes `8/8`, GameRoot parse diagnostics `0`: PASS.
4. Canonical development static gate
   - `19/19 PASS`, findings `0`.

## Web acceptance

- Fresh `web-mobile-qa` build: `buildFinished=true`, required artifacts valid, post-process PASS.
- Fresh production `web-mobile` build: `buildFinished=true`, required artifacts valid, post-process PASS.
- Dedicated lifecycle cycles 1 and 2: one exact `MTR_POWERUP_QA_READY` each, `checks=8/8`, expected phases, stale rejection, zero console/page/request diagnostics.
- Full matrix cycles 1 and 2: each `34/34 PASS`, interaction PASS, restart `10/10`.
- Independent focused-recovery matrix cycle 3: `34/34 PASS`, interaction PASS, restart `10/10`.

## Android-emulator acceptance

- Target: only `emulator-5554`, QEMU `1`, ABI `x86_64`, API 35; physical device used: `NO`.
- Fresh Cocos export and Gradle `clean assembleDebug`: PASS under JDK 17.0.20, Cocos Creator 3.8.8, NDK 23.2.8568313 and Gradle 8.11.1.
- Fresh APK: `142901828` bytes, SHA-256 `B33B9DDD364E91D042C134A574DCA5DD0C00533BC001C3DF6C1EFD188D7B8F68`; install and package clear on the emulator: PASS.
- Dedicated lifecycle cycles 1 and 2: exact marker, one READY, zero FAIL/fatal: PASS.
- Matrix cycles 1 and 2: each `28/28 PASS`, covering 13 screens and all 15 levels.
- Interaction cycles 1 and 2: touch/FSM, custom-name cold persistence, restart `10/10` and 30-second soak: PASS.
- Focused recovery cycle 3: the same interaction contract, restart `10/10`, soak `30.212 s`, process losses `0`; PSS decreased from `233718` to `196998` KiB.

The APK is emulator QA evidence, not a production-signed release artifact.

## Canonical profile

`temp/m03-6-m2-profile/20260813T124231Z/m2-plus.profile.json` passed all twelve source-bound slots:

- Pass A: static, Web, Android emulator and review;
- Pass B: static, Web, Android emulator and review;
- focused recovery: static, Web, Android emulator and review.

Result: `12/12 PASS`, findings `0`, profile SHA-256 `B7DDB6D35B2E0BBDA64DFE06DE1DC7A1CF6D595F126486BA7515B7860E65536F`.

## Corrective finding

The first final static run correctly failed because the older M03.3C validator required exactly five guarded callbacks and exactly one textual `qa_reset_loop` occurrence in all of `GameRoot`. M03.6 legitimately adds one guarded lifecycle probe and two isolated reset exercises. The validator was repaired to require every named guarded route and to scope the one dev-event reset writer to `runDevEventResetLoopForQa`. Its behavior suite and the full `19/19` gate then passed.

## Rollback

Rollback is bounded to the parent checkpoint `bef8470f04dc7f9dd30a7280b88572b951c3704f`: restore direct effect/counter ownership in `GameRoot`, remove `assets/scripts/gameplay/powerups` and its metadata, remove the startup-query bridge/harnesses, and remove the M03.6 static-gate entry. No scene, save data, content assets or balance migration is involved.

## Acceptance result

M03.6 is implementation- and validation-complete. M03.7A is the next ready execution unit: prove remaining UI/skin ownership and cleanup boundaries while retaining legacy paths.

Release remains blocked independently by M02.1 production signing/distribution identity, M02.7 immutable Web deployment topology and M12.7 owner-approved final cleanup.
