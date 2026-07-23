# M03.2 code and runtime review

Date: 2026-07-23  
Verdict: `PASS FOR BOUNDED STATE CONTRACT / RELEASE REMAINS BLOCKED`

## Review boundary

- Runtime changes are limited to the typed session-state contract and the existing `GameRoot.transitionTo` adapter.
- The player-state YAML is declarative evidence only and does not introduce a second mutable runtime state machine.
- UI drawing, input routing, physics, collisions, power-up ownership, persistence format, assets and scenes remain outside this patch.
- Review input contained only staged M03.2 files; untracked and unrelated root/widget changes were excluded.

## Review checks

| Risk | Result |
| --- | --- |
| Existing live transition removed | Rejected: 44 changed edges and 14 idempotent self-edges preserve every observed/current route. |
| Invalid transition mutates state | Rejected: all 138 invalid pairs return the typed rejection result before the sole writer. |
| Duplicate mutable session state | Rejected: `GameRoot.state` remains the only mutable source and `transitionTo` the only writer. |
| Exit/entry side-effect order changed | Rejected: name commit, skin selection, sync and logging remain in their previous order after contract acceptance. |
| Player YAML presented as runtime enforcement | Rejected: it is explicitly declarative and runtime routing remains M03.4. |
| Asynchronous background gates broken | Rejected: broad non-playing-to-playing compatibility edges remain until lifecycle ownership is migrated. |
| New release log spam | Rejected: only invalid transitions emit `MTR_FSM_REJECT`; bounded development logging remains M03.3. |
| Android QA used a physical device | Rejected: build installation and all runtime tests used only `emulator-5554`. |
| Web and Android behavior diverged | Rejected: fresh full matrices, restart loops and five-minute soaks passed on both runtime planes. |
| QA debug APK represented as release | Rejected: the x86_64 artifact is explicitly debug/emulator-only and release remains blocked. |

## Independent advisory

- Privacy preflight: PASS; ten staged files under the Cocos project, no untracked files and no detected sensitive-data pattern.
- Initial CodeRabbit review: two findings.
  - Accepted and fixed: report wording now separates 44 changed edges from 14 self-pairs.
  - Rejected after source reconciliation: the review assumed dependent files were absent even though all referenced files were included in the same staged scope.
- Re-review of the reconciled implementation: zero findings.
- No CodeRabbit suggestion was auto-applied; Codex inspected and decided each finding.

## Validation evidence

- Exhaustive TypeScript contract execution: `14 states / 58 accepted / 138 rejected / PASS`.
- Independent structural validator: `14 session states / 8 player states / 44 player transitions / 1 writer / PASS`.
- Pure module strict TypeScript: PASS.
- Complete project TypeScript: PASS.
- Reconciled canonical static gate: `9/9 PASS`, zero findings.
- Android emulator: `28/28`, interaction and persistence PASS, restart `10/10`, soak `300.369 s`, zero unexpected diagnostics.
- Web: `34/34`, portrait/interaction PASS, restart `10/10`, soak `300.525 s`, zero console errors/warnings.
- Runtime `MTR_FSM_REJECT` count: zero; invalid pairs are exercised by the exhaustive pure contract test.

## Verdict

M03.2 meets its bounded contract objective and is safe to checkpoint. M03.3 may add the deterministic development event log without moving gameplay ownership.

Production release remains blocked by signing/distribution and approved Pages deployment evidence, independently of this package.
