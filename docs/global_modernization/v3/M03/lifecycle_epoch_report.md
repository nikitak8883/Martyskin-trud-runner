# M03.3B lifecycle epoch report

Date: 2026-08-09 18:11 +03:00

## Scope

M03.3B adds one pure TypeScript lifecycle primitive at
`assets/scripts/qa/LifecycleEpoch.ts`. It has no Cocos import, clock, scheduler,
storage, network or GameRoot wiring. The Cocos metadata file was written
manually; the editor/import pipeline was not started.

## Contract

- `capture()` returns a numeric snapshot of the current non-negative safe
  integer epoch;
- `advance()` increments monotonically and throws before `MAX_SAFE_INTEGER`
  could wrap;
- `guard(callback)` captures internally, returns `false` for stale entry and
  forwards arguments only while current;
- guard ownership is synchronous-entry-only. An async continuation must
  re-check ownership after every `await`;
- raw numeric tokens are captured snapshots, never synthesized future guards.

## Acceptance

- Node behavioral + strict TypeScript suite: `16/16` groups PASS, Cocos
  TypeScript `5.8.2`, target `ES2015`;
- source plus adopted reference strict no-emit: PASS;
- cross-platform Python structural validator: PASS, unique Cocos UUID,
  cumulative static-gate count `14`;
- accepted full-source no-emit: PASS;
- M03.3A regression: `16/16` PASS; M03.2 regression remains `14` states,
  `58` accepted, `138` rejected and one writer;
- `GameRoot.ts` remains unwired with SHA-256
  `BBD19424A1B1E13ABDC0A9FA689E234AD738E8DC687F267EE3624B7961BD28F1`.

The hosted canonical step is structural Python. Executable TypeScript behavior
is therefore retained as a separate Cocos-pinned local receipt; neither result
is represented as proving the other.

## Known limits

LifecycleEpoch suppresses stale callback entry; it does not cancel scheduled
work or an already-running async continuation. M03.3C may use guards for
synchronous Cocos callbacks and must explicitly re-check async completion.

## Rollback

Remove `LifecycleEpoch.ts` and its `.meta`, the Node/Python tests, the
`lifecycle-epoch-contracts` static step and these M03.3B evidence/status
overlays. No scene, save, asset import or runtime state migration is involved.

## Result

M03.3B is complete as a pure contract. Source package M03.3 remains pending
until the separately approved M03.3C runtime adapter passes full P4.
