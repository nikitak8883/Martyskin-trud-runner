# M03.4 — gameplay input ownership

Date: 2026-08-10  
Status: `COMPLETE / M2_PLUS 12 OF 12 PASS / WEB AND ANDROID-EMULATOR PASS / RELEASE BLOCKED`

## Scope

M03.4 routes jump, glide, dash and pause through one Cocos-independent `GameplayInputAdapter`. The adapter owns action validation, session-state admission, shared pause debounce and glide release. Existing physics, audio, session transitions and drawing remain in `GameRoot`; collision and power-up ownership are deferred to M03.5 and M03.6.

## Accepted ownership

- `GameplayInputAdapter` is instantiated exactly once by `GameRoot`.
- Four typed actions are accepted: `jump`, `glide`, `dash`, `pause`.
- Input phases are `trigger`, `start` and `stop`; six sources distinguish keyboard, global touch, HUD button, pause zone, QA and session reset.
- Jump/dash/glide admission is limited to `playing`; pause is limited to `playing` or `paused`.
- All pause sources share one `220 ms` monotonic debounce and one accepted-count sequence.
- `GameRoot` retains one mutable `gliding` writer through the adapter callback.
- Existing Cocos listener topology remains six global listener pairs plus one pause-zone pair; no listener registration moved or duplicated.
- Reset releases glide through the same adapter instead of bypassing input ownership.

## Permanent validation

1. `node tools/codex/test-gameplay-input-adapter.js`
   - executes the real TypeScript adapter through the Cocos TypeScript runtime;
   - covers action/phase validation, state admission, shared debounce, overlapping source release and reset behavior;
   - result: `10/10 groups PASS`.
2. `python -B tools/codex/validate_gameplay_input_adapter.py --project-root .`
   - verifies one adapter instance, one glide writer, fourteen dispatch routes, three explicit release routes and unchanged listener topology;
   - result: `PASS`.
3. The canonical static gate now includes both the adapter contract and syntax validation for the reusable Web matrix CLI; final development run passed `17/17` mandatory steps.

## Runtime parity

Pass A, Pass B and focused recovery were independently exercised. Both full Web cycles passed `34/34`, portrait/interaction and restart `10/10`; the focused Web recovery passed the same matrix. Android Pass A and Pass B each passed `28/28`, touch jump/dash/pause/resume, custom-name persistence, restart `10/10` and a 30-second soak without process loss or unexpected diagnostics.

The first cold Android recovery attempt exposed a real QA sequencing race: jump was exercised before dash, allowing an ordinary collision to clear `dashTimer` before a `crouch_dash` frame was observed. The harness was corrected to assert dash immediately after the gameplay-ready gate, then jump. A fresh `pm clear` retry passed with dash `381 ms`, jump `372 ms`, pause `409 ms`, resume `436 ms`, restart `10/10`, 30.156-second soak, zero process loss and decreasing PSS (`227048` to `199244` KiB). The failed attempt is retained as corrected-failure evidence rather than hidden.

Only QEMU target `emulator-5554` was used. The fresh x86_64 debug APK is QA evidence, not a production release artifact.

## Canonical profile

The `M2_PLUS` profile at `temp/m03-4-m2-profile/20260810T144944Z/m2-plus.profile.json` passed all twelve source-bound slots:

- Pass A: static, Web, Android emulator, review;
- Pass B: static, Web, Android emulator, review;
- focused recovery (applicable): static, Web, Android emulator, review.

Result: `12/12 PASS`, zero findings, profile SHA-256 `D2CA3C0FE56D1DEA198584EC80D7CF4E440667B0DB38BD430B7A27B530DE3EB4`.

## Rollback

Rollback is bounded: restore the direct input calls in `GameRoot`, remove `assets/scripts/gameplay/input` plus its Cocos metadata, remove the two adapter validators and remove the two M03.4 static-gate entries. No scene, save schema, asset or content migration is involved.

## Acceptance result

M03.4 is complete. Input routing has one typed boundary, shared pause debounce, deterministic reset release and preserved runtime behavior on Web and Android emulator. M03.5 is next: typed collision events must preserve the exact existing side-effect order.

Release remains blocked by production signing/distribution, immutable Web deployment and final approved cleanup gates.
