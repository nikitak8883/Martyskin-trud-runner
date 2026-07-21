# M01.4 code review report

Дата: 2026-07-21  
Итог: `PASS FOR BOUNDED M01.4 / RELEASE BLOCKED`

## Scope reviewed

- canonical D4/P4/M2_PLUS/QA7/RC2 catalog and three Draft 2020-12 schemas;
- exact topology, mandatory/optional/conditional resolution and explicit `NOT_APPLICABLE` semantics;
- child-report source, freshness, schema, config, artifact and independence binding;
- aggregate output containment, collision prevention, atomic write and exit codes;
- emulator-only default and explicit physical-device authorization;
- bootstrap/profile entrypoint, PowerShell argument forwarding and regression fixtures.

## Accepted findings and fixes

| Finding | Severity | Resolution |
| --- | --- | --- |
| JSON input identity and JSON parsing used separate reads, leaving a narrow swap-and-restore TOCTOU opportunity | high | Added one read-and-hash snapshot path for catalog, scope and child reports; final protected-input revalidation remains in place. |
| The first snapshot implementation emitted lowercase SHA-256 while the accepted evidence contract uses uppercase | medium | Restored canonical uppercase hashes; the full suite caught and verified the correction. |
| A wrapper integration test invoked bootstrap through the already-active target venv; an invalid probe could attempt to rebuild files loaded by the current process | high | Bootstrap now binds markers to the base interpreter and refuses in-place repair of its active environment. The test launches through the base Python. |
| PowerShell forwarding of explicit switches was questioned by an advisory reviewer | medium | Line review showed both switches were already appended; a live wrapper integration test now proves forwarding and exit-code propagation. |
| The inherited false-green mutation test set `dirty_authorized=false` without setting `dirty=true`, making that mutation a no-op on a clean HEAD | medium | The fixture now creates the actual invalid pair `dirty=true` plus `dirty_authorized=false`; dirty-development and clean-source runs both pass. |

## Reviewed concerns not reproduced as defects

- Stale child evidence is blocked when `generated_at` predates profile scope start; expired/future scopes and future child reports are separately rejected.
- Aggregate output is checked against catalog, scope, every canonical schema/tool input, every child report, every child config and every child artifact.
- Copied reports, duplicate run IDs and reused artifact paths are rejected across slots.
- A false-green aggregate mutation is rejected by the canonical report schema.

## Reviewer and test evidence

- Local-worker performed three sequential narrowed read-only reviews; Codex validated each reported concern directly against code and tests.
- One confirmed TOCTOU concern and the bootstrap self-service risk were fixed and re-reviewed.
- Canonical isolated suite: `46` discovered, `44` passed, `0` failed, `2` expected platform skips.
- PowerShell AST parse: PASS.
- Live `run-profile.ps1` forwarding/exit integration: PASS.
- Post-commit clean-source suite: PASS with no development dirty override in profile fixtures.
- Post-commit M01.2 through M01.3 runner: PASS with `source_dirty=false`, `dirty_authorized=false` and stable source.
- M01.2 through accepted M01.3 runner: PASS.
- Direct M01.2 contract regression: 8 schemas, 11 positive fixtures, 20 negative fixtures, 25 deterministic reruns, 3 mutation guards and 9 representative report shapes: PASS.

## Residual boundaries

- POSIX execute-bit behavior is platform-guarded and skipped on this Windows host.
- Symlink creation lacks the required Windows privilege; the existing containment implementation and non-privileged tests remain accepted.
- No game runtime, build, Web runtime, Android emulator, physical device, deployment or signing action occurred.
- Release blockers outside M01.4 are unchanged.

No blocking defect remains inside the bounded M01.4 implementation.
