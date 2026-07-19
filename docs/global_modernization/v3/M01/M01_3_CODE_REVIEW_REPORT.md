# M01.3 code review report

Дата: 2026-07-19  
Итог: `PASS FOR BOUNDED M01.3 / RELEASE BLOCKED`

## Scope reviewed

- canonical typed config/report schemas;
- isolated exact-version bootstrap and offline Draft 2020-12 engine;
- shell-free process runner, process-tree timeout and capture lifecycle;
- path/output containment and executable resolution;
- native evidence freshness, adapter binding and report invariants;
- Git source identity, dirty authorization and protected-input stability;
- fixture/unit tests and PowerShell entrypoint.

## Accepted findings and fixes

| Finding | Severity | Resolution |
| --- | --- | --- |
| Concurrent bootstrap waiter could expire before the allowed 600-second exact-package install | medium | Wait window now equals install timeout plus 120-second setup margin; unit and two-process cold-start tests pass. |
| Explicit `--source-commit` could previously declare a value without proving current Git HEAD | high | Explicit value is compared with Git HEAD; mismatch raises `SOURCE_DECLARATION_MISMATCH`. |
| Source/protected inputs could drift while commands were running | high | Post-run HEAD/dirty revalidation plus SHA-256 before/after snapshots for config, schemas, adapter, registry, lock and evidence tools; drift is `BLOCKED`. |
| Ambiguous Windows root/device namespace and POSIX non-executable file handling could be clearer | medium | Added explicit device/root rejection and POSIX `X_OK` guard. |
| Output/native/artifact/capture paths could collide with one another or protected inputs | high | Complete pre-execution output topology registry rejects both collision classes. |

## Reviewed concerns not reproduced as defects

- `Path.resolve(strict=False)` resolves existing symlink/junction components before `relative_to(root)`; Windows junction escape returned `PATH_OUTSIDE_PROJECT`.
- ADS uses `:` and NUL/control variants are separately rejected. UNC and Windows device namespaces have dedicated guards.
- Timeout is schema-constrained to `1..86400` before parsing and process start.
- Evidence report path is materialized whenever `evidence` exists; missing native output becomes a blocking finding.
- Windows process flags use guarded constants, and the child-process survival fixture proves process-tree termination on the current host.
- A concurrently modified native report is conservatively treated as changed evidence, but cannot by itself become trusted: tool identity, flags, source, target, timestamps, adapter and schema invariants still apply. Full profile provenance belongs to M01.4.

## Reviewer/tool evidence

- Local-worker default reviewer: completed two narrowed reviews.
- One obsolete explicit profile name (`coder`) was rejected and corrected.
- One heavy local review timed out and returned no usable output; no PASS was inferred from it.
- CodeRabbit CLI: unavailable on this Windows host.
- Final authority: deterministic test evidence plus Codex line-level review and reruns.

## Residual boundaries

- POSIX execute-bit code is not runtime-executed on this Windows host; its platform-guarded unit is skipped here.
- Windows symlink creation lacked privilege, so a no-admin junction was used for the live containment smoke.
- M01.3 supplies execution mechanics, not D4/P4/M2_PLUS/QA7/RC2 profile policy; that is M01.4.
- No game runtime, Web build, Android build/emulator, physical device, Pages or signing action occurred.

No blocking defect remains inside M01.3. Existing release blockers are unchanged.

