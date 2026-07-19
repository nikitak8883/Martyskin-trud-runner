# Control log checkpoint — M01.1 quality-gate inventory complete

Date: 2026-07-19

Status: `PASS / CHECKPOINT-READY`

## Scope boundary

- Inventoried `32/32` tracked executable files under `tools/`.
- Recorded inputs, side effects, timeout policy, outputs, evidence contract, exit semantics, dependencies and preserved command for every entry.
- Inspected package/CI/build-config surfaces.
- Did not modify runtime, assets, native code, build output or Pages.
- Did not run Cocos build, Web runtime, Android emulator or physical-device QA.

## Validation

- Inventory JSON parse/required-field/coverage/SHA audit: PASS.
- Project config: PASS.
- Cocos-compatible TypeScript: PASS.
- Assets strict: PASS (`1528` PNG, `0` blockers, `0` white-matte suspects).
- Skin matrix strict: PASS (`576/576`, `0` warnings).
- UI IR: PASS (`14/14`, `0` problems/warnings).
- Level-select icon verify-only: PASS (`15` PNG + `15` meta).
- Entrypoint quoting: PASS.
- Git topology with canonical child path: PASS.
- Syntax: Python `15/15`, PowerShell `14/14`, JavaScript `3/3`.

## Logged defects and retries

- A read-only helper initially failed because its root path was not resolved before parent arithmetic; corrected helper passed and changed no file.
- Git topology first exposed a separator-sensitive comparison with a backslash child path; canonical forward-slash invocation passed against the same clean topology.
- One orchestration payload had a JavaScript quoting error and was rejected before shell execution; corrected syntax commands all passed.
- PowerShell cleanup was rejected by command policy before execution, and one read-only metadata probe had a parser error. Exact-file patch cleanup then removed only the task-owned 475105-byte retrieval query and 2285-byte temp entrypoint log.
- Web false-green exits, optional Android strictness, unpinned Playwright, unbounded ADB/Git calls, unsafe port takeover and evidence freshness/atomicity gaps are recorded in the M01.1 inventory and not waived.

## Resume point

Read `docs/global_modernization/v3/M01/quality_gate_inventory.md` and `quality_gate_inventory.json`, then execute `M01.2` only: schema compatibility matrix, adapters and positive/negative fixtures. Release remains blocked.
