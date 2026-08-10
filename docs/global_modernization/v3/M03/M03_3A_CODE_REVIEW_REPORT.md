# M03.3A code review

Date: 2026-08-09  
Verdict: `PASS AFTER FIXES / PURE CONTRACT ONLY / RELEASE BLOCKED`

## Review boundary

Reviewed: DevEvent types/log, Cocos metadata, executable Node test,
cross-platform Python validator, canonical static-gate entry and M03.3A roadmap
status/evidence. `GameRoot`, scenes, resources, package/lock, build configs,
editor import and runtime planes are excluded and unchanged.

## Findings and disposition

| Finding | Severity | Disposition |
|---|---|---|
| Reference overflow marker exceeds `maxPayloadBytes=2` | P1 | Fixed with an always-fitting fallback and exact UTF-8 tests. |
| Reference array `slice()` can execute index accessors | P1 | Fixed with descriptor-based array copy and zero-call adversarial test. |
| Event input getters can return different validation/storage values | P1 | Fixed with one plain-object own-data snapshot; unknown/symbol/accessor inputs fail closed. |
| Initial test target ES2020 hid ES2015 API incompatibility | P1 | Fixed: source no longer uses `getOwnPropertyDescriptors`; strict and executable compilation both target ES2015. |
| Plain-object non-enumerable fields could enter diagnostics | P2 | Fixed: only enumerable own fields are copied. |
| String slicing could split astral code points | P2 | Fixed with bounded code-point traversal and test. |
| Hosted static gate cannot execute Cocos-pinned TypeScript | P2 | Accepted evidence boundary, not represented as behavioral CI PASS. Python structural gate is permanent; separate local executable suite is hash/version/target bound. No package/lock dependency was added. |
| Own-key discovery cost precedes output limits | P2 | Documented. M03.3C must pass small allowlisted literals; no attacker-safe CPU-bound claim is made. |
| Raw project tsconfig is not green | Baseline | Qualified: raw command has 74 pre-existing Cocos/legacy diagnostic lines and zero qa diagnostics; accepted full-source command and targeted strict module both pass. |

## Determinism and privacy review

- No clock, randomness, console, storage, network, Cocos object or closure is
  captured by the module.
- Object keys are deterministic; payload references are copied and frozen.
- Non-plain objects, accessors, cycles and non-finite numbers are replaced with
  deterministic values.
- Byte limits use serialized UTF-8 length, not JavaScript character count.
- Payload shape controls do not infer PII. Runtime reason/payload allowlists are
  a mandatory M03.3C integration rule.

## Scope and rollback review

`GameRoot.ts` remains 5 434 lines with SHA-256
`BBD19424A1B1E13ABDC0A9FA689E234AD738E8DC687F267EE3624B7961BD28F1`;
the M03.2 state contract remains SHA-256
`2867D8126196E05EE62B3B42900D1C32E8A1825FC10D6F3C5A8397C34C3034B6`.
There is no scene/package/resource/build diff. Rollback is an isolated removal of
the qa module, tests/gate registration and M03.3A evidence/status overlay.

## Verdict

All correctness blockers found during independent review were fixed and
retested. The remaining own-key discovery and hosted structural-only boundaries
are explicit P2 limitations with M03.3C controls. M03.3A is acceptable as a
pure contract; it is not runtime or release acceptance.

