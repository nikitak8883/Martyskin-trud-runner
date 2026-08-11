# M03.5 — gameplay collision event routing

Date: 2026-08-11  
Status: `COMPLETE / M2_PLUS 12 OF 12 PASS / WEB AND ANDROID-EMULATOR PASS / RELEASE BLOCKED`

## Scope

M03.5 introduces one Cocos-independent, synchronous `GameplayCollisionRouter` for the existing collision callbacks. Detection remains in the same `GameRoot.updateGame` positions and side effects remain in `GameRoot.applyCollisionEvent`; this package does not reorder, batch, retry or asynchronously defer gameplay effects.

## Accepted contract

- Eight ordered kinds are accepted: `platform_land`, `ground_clamp`, `collectible_pickup`, `bonus_pickup`, `obstacle_hit`, `npc_stomp`, `npc_hit`, `level_finish`.
- Each event carries non-empty entity identity, `otherId=player`, an immutable cloned payload, monotonic sequence, lifecycle epoch and fixed-step tick.
- One callback receives each accepted event synchronously. Reentrant routing is rejected and callback errors propagate to the caller.
- Collision detection remains in the legacy order and still uses the existing hit/swept calculations.
- Side effects retain their prior order inside each case: mutation, score/counters, particles/audio/achievements and state persistence are not moved ahead of one another.
- The development collision matrix is `DEBUG` and developer-mode gated. Release Web remains free of collision QA events.

## Permanent validation

1. `node tools/codex/test-gameplay-collision-router.js`
   - executes the real TypeScript router;
   - validates all eight kinds, immutable event/payload data, sequence/epoch/tick, rejection rules, callback propagation and reentrancy guard;
   - result: `10/10 groups PASS`.
2. `python -B tools/codex/validate_gameplay_collision_router.py --project-root .`
   - verifies eight production routes, eight QA routes, one router instance, one exhaustive consumer and exact legacy order;
   - result: `PASS`.
3. The canonical development static gate includes the collision contract and passed `18/18` mandatory steps with zero findings.

## Runtime parity

Fresh release and QA Web builds were used. Pass A, Pass B and focused recovery each passed `34/34` browser matrix cases, interaction and restart `10/10`. The dedicated Web collision query emitted exactly one ready marker with all eight kinds, contiguous sequence and `8/8` effects in both independent runs.

The fresh x86_64 Android debug APK was installed only on `emulator-5554`. Pass A and Pass B each passed `28/28`; dedicated native collision queries each produced one native-query marker, one ready marker, zero failure/fatal markers and the same eight-event order. Interaction, custom-name persistence, restart `10/10` and 30-second soak also passed in both cycles.

The first focused Android recovery exposed an evidence-retention defect and a nondeterministic ADB input target. The harness now captures logcat, `dumpsys input`, `dumpsys window`, screenshot and machine-readable failure JSON. Android Pointer Location proved that the current logical `3120x1440` coordinates were correct; the stable injection contract is now explicit `input touchscreen -d 0 tap`. A fresh `pm clear` recovery then passed all touch/FSM, name persistence, restart `10/10` and `30.378 s` soak checks with zero process loss and PSS decreasing from `222560` to `200123` KiB. Corrected-failure evidence remains in ignored `temp` and is not shipped.

Only QEMU target `emulator-5554` was used. The APK is QA evidence, not a production release artifact.

## Canonical profile

`temp/m03-5-m2-profile/20260811T123659Z/m2-plus.profile.json` passed all twelve source-bound slots:

- Pass A: static, Web, Android emulator, review;
- Pass B: static, Web, Android emulator, review;
- focused recovery (applicable): static, Web, Android emulator, review.

Result: `12/12 PASS`, zero findings, profile SHA-256 `B47EF43DF95BFD0D7FA21727A973AAE0A8A449D538C67546BF654894D20408FA`.

## Rollback

Rollback is bounded: restore the direct collision side effects in `GameRoot`, remove `assets/scripts/gameplay/collision` plus its Cocos metadata, remove the collision QA startup-query bridge and validators, and remove the M03.5 static-gate entry. No scene, save schema, content asset or balance migration is involved.

## Acceptance result

M03.5 is complete. Collision detection and behavior remain in legacy order behind one typed event seam with deterministic metadata and fail-closed QA. M03.6 is next: power-up lifecycle ownership must use injected time and lifecycle epoch without balancing changes.

Release remains blocked by production signing/distribution, immutable Web deployment and final approved cleanup gates.
