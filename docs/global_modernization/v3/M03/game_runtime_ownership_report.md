# M03.7 runtime ownership and cleanup report

Date: 2026-08-13  
Execution units: `M03.7A + M03.7B`  
Verdict: `COMPLETE / P4 PASS / M2_PLUS PASS / RELEASE BLOCKED`

## Objective and boundary

M03.7A removed direct gameplay mutation authority from rendered UI callbacks and established deterministic ownership of component listeners and scheduled work. M03.7B then proved rollback and hidden-reference coverage and removed only the duplicate callback-guard layer; gameplay mutation methods and the single scheduling owner remain intact.

No balance values, physics constants, content IDs, persistence schema, production signing, Pages deployment or release artifacts changed. Android runtime QA used `emulator-5554` only; no physical device was used.

## Implemented ownership seams

### Typed UI intent bridge

`GameplayUiIntentAdapter` exposes exactly six actions:

1. `navigate`;
2. `start_level`;
3. `preview_skin`;
4. `confirm_skin`;
5. `open_developer_gate`;
6. `submit_developer_gate`.

Rendered controls now emit these intents. One `GameRoot` adapter applies the accepted command to existing transition, level-start, skin and developer-gate owners. Invalid state, level and skin requests are rejected before mutation.

### Runtime lifecycle owner

`GameRuntimeLifecycleOwner` owns:

- eight input/view listener subscriptions and their exact unsubscribe callbacks;
- session callbacks, rejected after epoch change and cancelled on accepted state transitions or reset;
- component callbacks, retained across ordinary state changes but cancelled on destroy;
- a monotonic epoch and read-only snapshots for deterministic tests and QA telemetry.

The GameRoot integration has one injected Cocos scheduler boundary. All other scheduling routes through the owner; destroy cancels scheduled work and removes every registered listener.

## Acceptance evidence

- Unit behavior: `14/14 PASS`; all six UI actions and lifecycle ownership cases covered.
- Structural validator: `PASS`; six actions, eight listener routes, eleven session schedule routes, twelve component schedule routes and one injected direct scheduler boundary.
- GameRoot analyzer: `PASS`; 6181 lines, zero parse diagnostics, 167 properties, 299 methods, 12 accessors and 1084 call edges.
- Config/startup parity: 15 levels; Web and Android ownership-query parity `PASS`.
- Dedicated runtime marker on both targets: `MTR_OWNERSHIP_QA_READY checks=8/8 listeners=8 sessionCancelled=1 componentSurvived=1 uiTransition=1 state=playing`.
- Web ownership cycles A/B: exact one READY marker each, zero failures and zero unexpected diagnostics.
- Web full matrix A/B/recovery: each `34/34`; interaction `PASS`; restart `10/10`.
- Android ownership A/B/recovery: exact one READY marker each, zero failures and zero fatals.
- Android matrix A/B: each `28/28` across 13 UI screens and all 15 levels.
- Android interaction A/B/recovery: touch/FSM, custom-name cold persistence, restart `10/10` and approximately 30-second soak all `PASS`; zero process losses.
- Static gate: `20/20 PASS`, findings `0`.
- Canonical `M2_PLUS`: `12/12 PASS`, findings `0`.

## Source identity

- 16-entry aggregate SHA-256: `328C0AA1847190DB7C8EB4E46CFCA759390B015B6C3EE470AFCF3A17CAA1C679`.
- `GameplayUiIntentAdapter.ts`: `BBEE6015F5F55A8201520F31634EC2BDDBDBE5C12D629626960A5AE8F2CE1786`.
- `GameRuntimeLifecycleOwner.ts`: `96E5ED2C37592BA56BAD04AAC8E90677B6BF3AC3D585A7CE3124DFC0A44917B3`.
- `GameRoot.ts`: `913CFA8790232845420994A85058C375AEE8FB6DE9FC96CBA86571284138B480`.

## M03.7B cleanup closure

- Removed `LifecycleEpoch.capture`, `LifecycleEpoch.guard`, `GameRootDevEventAdapter.guardSessionCallback` and seven nested wrappers only.
- `GameRuntimeLifecycleOwner` remains the sole scheduling/stale-suppression owner; all 11 session and 12 component routes remain covered.
- Hidden active legacy references: `0`; exact rollback blobs: `10/10`; rollback anchor: `08a55a5aaebbbac8592e2e662618ccfc8101a43c`.
- Fresh acceptance: static `21/21`, QA7 `7/7`, M2_PLUS `12/12`, Web visual `70/70`, Web/Android recovery and `30/30` restarts pass.
- Exact current-source and evidence identities are in `M03_7B_VALIDATION_SUMMARY.json`.
- Release remains blocked by M02.1, M02.7 and M12.7.
