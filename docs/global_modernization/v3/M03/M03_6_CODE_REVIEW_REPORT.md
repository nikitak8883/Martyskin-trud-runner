# M03.6 code and runtime review

Date: 2026-08-13  
Verdict: `PASS FOR BOUNDED POWER-UP LIFECYCLE / RELEASE REMAINS BLOCKED`

## Review boundary

- Runtime mutation is limited to moving power-up entity phases, effect timers and run counters behind one synchronous owner.
- `GameRoot` still applies score, healing, invincibility, dash cooldown, rendering, sound and achievement side effects returned as immutable activation commands.
- Collision detection/order, physics, duration constants, UI, assets, storage and content identity are unchanged.
- QA additions are DEBUG-gated; Android runtime evidence is emulator-only.
- Production signing, Pages deployment, physical-device QA and destructive cleanup are outside this unit.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Invalid injected tick could leave partial activation state | Fixed before the checkpoint: tick validation now occurs before counters, effects or entity phase mutate; unit and runtime probes pass. |
| Effect-kind labels could drift from the nine-kind contract | Fixed with a compile-time literal count binding and structural validation. |
| Stale callbacks could collect or activate a new-session entity | Prevented by injected epoch comparison on every operation; Web/Android probes confirm stale rejection. |
| Reset/terminal/retry could leave timers or instances alive | Prevented by `beginEpoch`, `cleanupSession` and `invalidate`; both runtime platforms pass reset, terminal cleanup and retry checks. |
| Owner could become a second source of one-shot game state | Rejected: owner returns immutable one-shot commands; only `GameRoot` mutates score/HP/invincibility/cooldown. |
| Legacy direct timer/counter writers could coexist | Rejected by structural scans over all ten effect keys plus run counters; getters are read-only adapters. |
| QA route could leak into release or a physical device | Prevented by DEBUG/developer/query gates, production Web debug=false, native QEMU guard and explicit `emulator-5554`. |
| M03.3C static validator rejected the added safe routes | Fixed in the validator: named-route minimums replace brittle global exact counts, while the dev-event reset writer remains scoped and exact. Behavior test PASS; static `19/19` PASS. |

## Evidence

- Source owner: 511 lines, SHA-256 `293BE590E3CA335FEE15BE4989725513E411A3ADCD110729CE81FE6E5CFDE724`.
- GameRoot: 6001 lines, zero parse diagnostics, SHA-256 `A4D6BB0F211D12FF94072279420F8F3098B6C77BF42F7D489320945CE7A390EE`.
- Unit/structural: power-up `14/14`, nine kinds, ten effects; collision regression `10/10` and `8/8`; config parity 15 levels.
- Static gate: `19/19 PASS`, zero findings; SHA-256 `AE51B2A3CBFDE6179D8E92E04794BA79D78C38B00277E353C3DB166F6A489446`.
- Web: lifecycle A/B exact, matrix A/B/recovery each `34/34`, interaction PASS, restart `10/10`.
- Android emulator: lifecycle A/B exact, matrix A/B each `28/28`, interaction/name/restart/soak A/B/recovery PASS.
- Fresh APK payload and install: PASS; SHA-256 `B33B9DDD364E91D042C134A574DCA5DD0C00533BC001C3DF6C1EFD188D7B8F68`.
- M2_PLUS: `12/12 PASS`, zero findings; SHA-256 `B7DDB6D35B2E0BBDA64DFE06DE1DC7A1CF6D595F126486BA7515B7860E65536F`.
- `android-web-contract-check`: approve; shared owner/query semantics accepted on both targets.

## Hygiene and residual limits

- No conflict markers, unresolved task/debug markers, direct legacy power-up writers or tracked build/temp artifacts remain in the touched scope.
- Localhost QA port `18766` is closed.
- Generated builds, screenshots and detailed machine reports remain ignored evidence and are not staged.
- Historical partial checkpoint and pre-fix diagnostic evidence remain immutable; they are not used as final acceptance.
- M03.7A must prove UI/skin ownership and cleanup before M03.7B may delete superseded paths.
- Release blockers M02.1, M02.7 and M12.7 remain unchanged.

## Verdict

M03.6 is safe to checkpoint. No accepted code-review finding remains open inside this unit.
