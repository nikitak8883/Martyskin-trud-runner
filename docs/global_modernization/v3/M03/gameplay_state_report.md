# M03.2 — gameplay state contracts

Date: 2026-07-23  
Status: `COMPLETE / STATIC 9 OF 9 PASS / CODERABBIT RECONCILED / ANDROID AND WEB QA PASS / RELEASE BLOCKED`

## Scope

M03.2 introduces the smallest parity-preserving state seam around the existing `GameRoot.transitionTo` writer. It does not move UI drawing, player physics, input handlers, collision callbacks, power-up ownership, timers or event logging.

The runtime adapter, player schema, both validators and the ninth static-gate entry described below were reviewed and validated as one bounded M03.2 scope. The final evidence includes exhaustive contract tests, the complete project TypeScript check, the canonical static gate, two CodeRabbit passes, a fresh Android emulator build and full Android/Web runtime matrices.

Changed runtime ownership:

- `assets/scripts/gameplay/state/GameSessionState.ts` owns the immutable session-state names, mode mapping, allowed transition table and pure transition decision.
- `GameRoot.state` remains the sole mutable session-state source of truth.
- `GameRoot.transitionTo` remains the sole `this.state` writer and keeps the existing name commit, skin-selection, synchronization and logging order.
- Invalid edges now return `{ accepted: false, changed: false, code: "invalid_transition" }`, leave state unchanged, refresh the existing snapshot and emit one `MTR_FSM_REJECT` warning.
- Self-transitions remain idempotent: they are accepted, do not run exit/entry side effects and only refresh the snapshot, matching the previous behavior.

## Session-state contract

The live game has 14 states, not the seven-state upstream sketch. Renaming or collapsing them in this patch would change UI/runtime behavior, so the accepted contract preserves the live names:

`menu`, `playing`, `paused`, `clear`, `over`, `finished`, `skins`, `levels`, `sound`, `records`, `achievements`, `name`, `devgate`, `devpanel`.

| From | Allowed changed targets |
|---|---|
| `menu` | `playing`, `clear`, `over`, `finished`, `skins`, `levels`, `sound`, `records`, `achievements`, `name`, `devgate`, `devpanel` |
| `playing` | `paused`, `clear`, `over`, `finished` |
| `paused` | `playing`, `sound`, `menu` |
| `clear`, `over` | `playing`, `menu` |
| `finished` | `playing`, `records` |
| `skins`, `levels`, `sound`, `name`, `devpanel` | `playing`, `menu` |
| `records` | `playing`, `achievements`, `menu` |
| `achievements` | `playing`, `records`, `menu` |
| `devgate` | `playing`, `devpanel`, `menu` |

The target table contains 44 changed edges. Separately, every state accepts one idempotent self-transition. The exhaustive 14 × 14 check therefore has 58 accepted pairs in total (44 changed edges plus 14 self-pairs) and rejects the remaining 138 pairs deterministically.

The broad `playing` target from non-playing screens is an explicit compatibility edge. Existing background, skin and hazard gates may complete asynchronously after the visible menu state changes. Cancelling or re-owning those pending starts would be a separate behavior change; it is deferred until the input/lifecycle packages can prove parity.

## Player-state schema

`player_state_machine.yaml` is a JSON-compatible YAML 1.2 document so the canonical Windows/Linux gate can validate it without adding a YAML package or changing lockfiles.

It records eight current semantic player states:

`grounded`, `jumping`, `double_jumping`, `falling`, `gliding`, `dashing`, `hit`, `victory`.

The 44 declared transitions describe the current precedence and guards derived from `onGround`, `vy`, `doubleJump`, `gliding`, `dashTimer`, `hitPoseTimer`, `secondJumpPoseTimer` and session completion. This is a declarative baseline only. M03.4 still owns runtime input routing for jump/glide/dash/pause; M03.2 does not create a second mutable player-state machine.

## Permanent validation

Two independent checks cover the seam:

1. `node tools/codex/test-game-session-state.js`
   - transpiles and executes the real TypeScript module with the Cocos 3.8.8 TypeScript runtime;
   - exhaustively checks all 196 state pairs, mode mapping, runtime immutability and sole-writer integration;
   - result: `14 states / 58 accepted / 138 rejected / 1 writer / PASS`.
2. `python -B tools/codex/validate_game_session_state.py --project-root .`
   - performs platform-independent structural validation of the TypeScript contract, `GameRoot` adapter and player-state schema;
   - result: `14 session states / 8 player states / 44 player transitions / PASS`.

`game-session-state-contracts` is now a mandatory ninth step in `tools/codex/quality-gate/static-gates.json`. It uses only Python standard-library features and therefore preserves the existing Windows/Linux CI topology.

Additional targeted gates already passed:

- pure state module: Cocos TypeScript `--noEmit --strict --target ES2020`;
- complete project: Cocos-bundled TypeScript with the accepted project command;
- `git diff --check`.

The final development static gate `qg.20260723060528.0f3e1728c410` passed `9/9` mandatory steps with zero findings. Source stability and the exact expected commit were verified; dirty-source authorization was required only because this shared repository contains unrelated user-owned tracked changes outside M03.2.

## Independent review

- The privacy gate included only the ten staged M03.2 files under the Cocos project, excluded all untracked files and found no sensitive-data patterns.
- The first CodeRabbit pass returned two findings. The valid wording issue was fixed by distinguishing 44 changed edges from 14 idempotent self-pairs.
- The second finding assumed that dependent files were absent, but all referenced runtime, schema and validator files were present in the same reviewed staged scope; Codex rejected that premise and clarified the evidence boundary.
- The final CodeRabbit re-review covered the complete reconciled scope and returned zero findings.

## Android emulator evidence

- A fresh Cocos Android build and Gradle `clean assembleDebug` completed successfully.
- The x86_64 debug APK (`142,883,719` bytes, SHA-256 `0AA6363DBABA12F25ACDF01DCC6C34E1A2949D34EF8BA0AD9378E2F036E2E448`) was installed only on `emulator-5554`.
- Full matrix: `28/28 PASS` (`13` UI routes and `15` levels).
- Interaction/name persistence: PASS; restart loop: `10/10 PASS`; soak: `300.369 s`, `323` input bursts and `17` state actions without process loss.
- Fatal, deprecation, product-warning and unexpected Cocos diagnostic counts were all zero.
- Five representative screenshots (`menu`, `paused`, `clear`, `over`, `finished`) were visually inspected and contained no white fragments, stale text layers or composition regressions.

## Web parity evidence

- A fresh Web Mobile build completed successfully with the required favicon post-process.
- Playwright matrix: `34/34 PASS`; portrait and interaction flows: PASS; restart loop: `10/10 PASS`.
- Soak: `300.525 s`, `39` input bursts, three clear-route actions, zero console errors and zero console warnings.
- The final soak screenshot was visually inspected and remained consistent with the accepted Android composition.

Across both runtime planes, only valid edges were observed and `MTR_FSM_REJECT` occurred zero times. Invalid-edge behavior is covered exhaustively by the pure 14 × 14 contract test rather than by injecting an impossible production UI route.

## Behavior and ownership review

- No valid live edge was removed.
- No call site bypasses `transitionTo`.
- No second mutable session state was introduced.
- No event log was added; bounded logging remains M03.3.
- No input, collision, power-up, asset or UI ownership moved.
- The reference `GameSessionStateMachine.ts` draft was treated as advisory only and is not imported into runtime.
- The player schema does not claim runtime enforcement before M03.4.

## Rollback

Rollback is one bounded revert:

1. restore the local `State`/`FsmMode` aliases and previous `modeForState`/`transitionTo` bodies in `GameRoot.ts`;
2. remove `assets/scripts/gameplay/state`, its Cocos metadata, the two validators and the ninth static-gate entry;
3. retain this report as rejected evidence only if the revert is required.

No data migration, save-format change, asset mutation or scene rebinding is involved.

## Acceptance result

M03.2 is complete. The typed session contract preserves all live valid transitions, deterministically rejects every invalid pair, keeps one mutable state writer and adds no duplicate player-state runtime.

M03.3 is the next bounded package: add a deterministic, reset-owned development event log without release spam or a second gameplay state owner.

Release remains blocked independently by the unresolved production signing/distribution decision and approved Pages topology/deployment evidence. The debug emulator APK produced for this package is QA evidence, not a production release artifact.
