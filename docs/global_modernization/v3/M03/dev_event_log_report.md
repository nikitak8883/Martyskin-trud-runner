# M03.3A — pure bounded development event log

Date: 2026-08-09  
Status: `COMPLETE / PURE CONTRACT / STATIC 12 OF 12 PASS / NO RUNTIME WIRING / RELEASE BLOCKED`

## Scope

M03.3A adds a Cocos-independent development-diagnostics contract under
`assets/scripts/qa`. It does not import `cc`, read a clock, write console or
storage, perform network access, or connect to `GameRoot`. Default logging is
disabled. Lifecycle epoch and stale-callback ownership remain M03.3B; the one
allowed runtime adapter and Web/Android parity remain M03.3C.

Added runtime-source contracts:

- `DevEventTypes.ts`: exact 12-code registry, immutable JSON-like record/input
  types and disabled default policy;
- `DevEventLog.ts`: validated fixed-capacity ring, monotonic per-instance
  sequence, immutable snapshots, safe plain-data copy and count/UTF-8 bounded
  export;
- manually authored Cocos directory/TypeScript metadata with three new unique
  UUIDs. Cocos Creator/import was not run.

No diff was made to `GameRoot.ts`, `GameSessionState.ts`, `main.scene`,
`assets/resources`, generated catalogs, package/lock or build settings.

## Contract

- `enabled:false` is the default; disabled or capacity-zero append returns
  `undefined` without inspecting input or consuming a sequence.
- Sequence begins at 1, advances only after a successful append, survives
  `clear()` and fails closed before unsafe-integer overflow.
- Snapshot order is oldest to newest. Snapshot arrays, records and copied
  array/plain-object payloads are frozen.
- Config and event input must be plain/null-prototype objects with own data
  properties. Unknown keys, symbols and accessors are rejected without invoking
  getters.
- Epoch/tick must be non-negative safe integers; code must be one of 12 fixed
  values; state/reason/string values are code-point bounded.
- Non-finite numbers become `null`; bigint becomes a bounded decimal string;
  function/symbol/undefined become `null`; non-plain objects become markers.
- Plain-object keys are enumerable-own only, sorted and copied into a
  null-prototype object. Array indices are read from descriptors, so accessors
  are marked rather than executed. Circular/depth/node limits are deterministic.
- Payload overflow always produces JSON within `maxPayloadBytes`, including the
  schema minimum of 2 bytes. Export returns the newest contiguous suffix that
  fits both event-count and serialized UTF-8 byte limits.

## Reference corrections

The v4 reference was advisory and was not copied blindly. The implementation
corrects these review findings:

1. `"[payload-byte-limit]"` can exceed a configured 2-byte payload maximum;
   the live fallback selects a marker only when it fits and otherwise uses the
   two-byte JSON string `""`.
2. `Array.slice()` can invoke accessor-backed indices; the live sanitizer walks
   own descriptors and never calls those getters.
3. `Object.getOwnPropertyDescriptors` requires a newer standard library than
   the project's ES2015 target; the live helper uses ES2015-compatible
   `getOwnPropertyNames/getOwnPropertyDescriptor`.
4. Re-reading accessor-backed event input can validate one value and store
   another; the live input boundary takes one descriptor-safe normalized copy.
5. Non-enumerable plain-object fields are excluded from diagnostic payloads.

## Validation

Permanent checks follow the accepted M03.2 dual pattern:

- `node tools/codex/test-dev-event-log.js` executes the real TypeScript modules
  through Cocos-bundled TypeScript 5.8.2 at target ES2015: 16 behavioral groups,
  12 event codes, PASS.
- `python -B tools/codex/validate_dev_event_log.py --project-root .` is the
  standard-library Windows/Linux structural guard: exact registry/schema/default
  parity, forbidden dependencies, bounded algorithms, meta uniqueness,
  no-GameRoot-wiring and static-gate registration, PASS.
- targeted strict ES2015 TypeScript: PASS.
- accepted complete-source no-emit command with the existing M03 baseline flags
  `--skipLibCheck --lib es2020,dom --isolatedModules false`: PASS.
- raw `tsc -p tsconfig.json` remains an acknowledged project/Cocos declaration
  baseline failure (`74` diagnostic lines), with `0` diagnostics under
  `assets/scripts/qa`; it is not represented as a green gate.
- M03.2 regression remains `14 states / 58 accepted / 138 rejected / 1 writer`;
  Python player contract remains `8 states / 44 transitions`.
- canonical typed static gate run `qg.20260809121228.3d1e228ddd20` passed all
  `12/12` mandatory steps with zero findings on source commit
  `737b0c4d06d57948148c0c6f460903e7f0c27d62` and explicit dirty-source
  authorization for this bounded shared-worktree diff.

Hosted static runners install Python but not Cocos/TypeScript. Therefore the
canonical step is deliberately structural; it does not claim to execute the
TypeScript behavioral suite. Executable behavior is a separate Cocos-pinned
receipt, exactly as stated above.

## Known limits

- JavaScript own-key discovery materializes the supplied object's own names
  before output slicing. Recursive output, traversal and serialized bytes are
  bounded, but hostile objects with enormous key sets can still cost
  proportional discovery work. M03.3C must pass only small allowlisted literal
  payloads, never arbitrary errors, Cocos objects or user data.
- Shape sanitation is not semantic PII detection. M03.3C must use fixed reason
  codes and explicit payload schemas.
- `enabled:true` is available only for the future explicit development adapter;
  M03.3A alone cannot detect a release build and is not wired anywhere.
- No Web/Android/editor/build/import result is claimed because this unit changes
  no live behavior. Full P4 becomes mandatory in M03.3C.

## Rollback

Remove `assets/scripts/qa` and its directory meta, the JS/Python validators, the
`dev-event-log-contracts` static-gate entry and M03.3A evidence/status overlay.
No scene rebind, save migration, asset reimport, package rollback or runtime
state restoration is involved.

## Acceptance

M03.3A is complete as a pure, disabled-by-default development event contract.
The source package M03.3 remains pending until M03.3B and M03.3C pass. Next safe
unit is M03.3B; TC-01 proceeds in parallel and remains required before M03.3C.

