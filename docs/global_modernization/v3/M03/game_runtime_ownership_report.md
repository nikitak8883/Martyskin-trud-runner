# M03.7A runtime ownership report

Date: 2026-08-13  
Execution unit: `M03.7A`  
Verdict: `COMPLETE / P4 PASS / M2_PLUS PASS / RELEASE BLOCKED`

## Objective and boundary

M03.7A removes direct gameplay mutation authority from rendered UI callbacks and proves deterministic ownership of component listeners and scheduled work. Legacy methods remain available behind the adapters; deleting superseded paths is deliberately deferred to M03.7B.

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

## Deferred work and rollback

- M03.7B must inventory hidden references and produce a rollback map before deleting any superseded path.
- The accepted rollback anchor before this unit is `78d85a9a04dc04ca1ebe106a22e9ce4b5945b643`; the exact new-source identity is in `M03_7A_VALIDATION_SUMMARY.json`.
- Release remains blocked by M02.1, M02.7 and M12.7.

