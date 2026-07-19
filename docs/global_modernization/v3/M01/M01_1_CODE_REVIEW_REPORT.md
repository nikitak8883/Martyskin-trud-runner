# M01.1 code-review report

Date: 2026-07-19  
Status: `PASS WITH BLOCKING FINDINGS ROUTED TO M01.2–M01.4`

## Reviewed scope

- all `32` tracked Python, PowerShell, PowerShell-module and JavaScript files under `tools/`;
- three active build configuration JSON files;
- `package.json`, repository workflow surface and preserved command records;
- current v3 M01 requirements and frozen source/topology anchors.

No runtime or tool source was patched. This review classifies the live implementation so later changes remain bounded and testable.

## Blocking findings

1. There is no single fail-closed profile runner or machine-readable release decision.
2. Both PowerShell Web probes can exit zero with failed runtime/marker semantics.
3. Android toolchain readiness is non-blocking unless `-FailOnNotReady` is supplied.
4. The Node Playwright runner has no pinned local dependency/lockfile environment.
5. Direct ADB operations and several Git calls lack a per-process timeout.
6. Port cleanup can terminate an unrelated listener.
7. Existing reports generally lack source/content identity, atomic writes and stale-evidence rejection.
8. JSON contracts are embedded and fragmented; positive/negative fixtures are absent.

These are not silently waived. They are explicit inputs to M01.2 schemas/fixtures, M01.3 typed runner and M01.4 profile policy.

## Important non-blocking findings

- `Test-MtrGitTopology.ps1` textually compares `ChildRelative`; the equivalent backslash form failed while the canonical forward-slash form passed.
- Two legacy wrappers still default to `C:\Test\MTRCocosCreator`.
- `validate-mtr-config.ps1` is coupled to `GameRoot.ts` source layout through regular expressions.
- `scan_and_fix_white_matte_edges.py` and the level-icon generator combine inspection with mutation/generation modes.
- Several diagnostics always exit zero after writing risks/candidates.

## Preserve decisions

The following live mechanisms are useful and must be adapted rather than replaced:

- `MtrEntrypoint.psm1` typed invocation, process-tree timeout and logging;
- configuration, asset, skin matrix and UI IR validators;
- entrypoint quoting and Git topology tests;
- Android emulator matrix and interaction harnesses;
- Web matrix/soak functions and their semantic runner after dependency pinning;
- Cocos build and local Web server scripts as infrastructure;
- deterministic source manifest and contact-sheet evidence generators.

## Exclusions from mandatory gate

All asset/background/UI/skin integration producers, portable packaging, Web build repair and white-matte mutation modes remain outside the quality profile. A gate may validate their outputs, but it must not generate or repair them implicitly.

## Review verdict

Inventory coverage and static integrity are complete. The current tools are sufficient raw material for M01, but not yet sufficient for a release claim. M01.2 is ready; runtime implementation remains out of scope until the minimum M01 gate is implemented and self-tested.
