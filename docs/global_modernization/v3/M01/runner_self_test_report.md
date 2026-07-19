# M01.3 typed quality-gate runner — self-test report

Дата: 2026-07-19  
Статус: `PASS / M01.3 COMPLETE / RELEASE REMAINS BLOCKED`  
Ветка: `codex/mtr-source-freeze-v3`  
Исходный HEAD до M01.3 commit: `c6434c9bdbcc09842cc24d66f41763122743bb51`

## Bounded scope

Реализован только project-local quality tooling под `tools/codex/quality-gate/`. Game runtime, Cocos assets, Web/Android builds, Pages, signing, emulator и physical device не изменялись и не запускались. Для tool-only пакета runtime-targeted части P4 являются `not_applicable_by_scope`; четыре независимых инженерных цикла сохранены.

## Принятый контракт

- команды задаются как `executable` + `arguments[]`, запускаются с `shell=False`;
- config/cwd/report/captures/native reports/declared artifacts проходят containment, traversal, UNC, ADS, Windows device/root и output-collision guards;
- timeout завершает полное process tree: `taskkill /T /F` на Windows и отдельную process group на POSIX;
- stdout/stderr сохраняются раздельно, каждый artifact получает SHA-256 и размер;
- native evidence обязано быть новым/изменённым, привязано к реально вызванному tool path и declared strict flags;
- M01.2 adapter registry активирован только через runner; envelope и итоговый report валидируются Draft 2020-12;
- source commit нельзя подменить CLI-аргументом; HEAD/dirty state повторно проверяются после шагов;
- config/schema/adapter/registry/tool inputs snapshot-ятся до запуска и hash-проверяются после;
- dirty source, mandatory skip, timeout, missing tool/report, stale evidence, malformed JSON, source drift и in-run input mutation блокируют gate;
- report заменяется только после полной валидации через atomic `fsync` + `os.replace`.

## Isolated schema engine

| Поле | Результат |
| --- | --- |
| Engine | `jsonschema==4.26.0` |
| Draft | `2020-12` |
| Registry | local/offline `referencing.Registry` |
| Lock SHA-256 | `B22864F672907A3E850FFAF916CF2A2E0C1185A0C024738D755DFCF16DC47D7C` |
| Environment | `%LOCALAPPDATA%\MTR\quality-gate\venv-py313-b22864f67290` |
| Global Python mutation | none |
| Arbitrary bootstrap modules | blocked; allowlist currently contains only `unittest` |

## Four validation cycles

### Cycle 1 — schema, syntax and unit behavior

- JSON parse: 5/5 canonical quality schemas PASS.
- Python compile: runner/bootstrap/schema engine/fixtures/tests PASS.
- Unit discovery: 27 total, 25 PASS, 2 platform/privilege skips, 0 FAIL.
- Covered: expected/non-zero exits, missing executable, mandatory/optional skip, malformed config, path guards, output collision, source mismatch/drift, dirty authorization, fresh/stale evidence, stale artifacts, protected-input mutation, deterministic projection, atomic write and false-green mutations.
- Windows process-tree timeout: PASS; delayed child marker did not appear after parent timeout.
- Windows symlink privilege was unavailable (`WinError 1314`); equivalent junction escape was executed separately and returned `PATH_OUTSIDE_PROJECT`.
- POSIX executable-bit branch is present but is not runtime-executed on this Windows host.

### Cycle 2 — real entrypoint and bootstrap

- PowerShell wrapper with explicit development dirty override: `PASS`, exit `0`.
- Same wrapper without override on dirty tree: valid `BLOCKED`, exit `2`, finding `DIRTY_SOURCE_NOT_AUTHORIZED`.
- Unapproved `--module pip`: `BLOCKED`, exit `3`, code `UNAPPROVED_BOOTSTRAP_MODULE`.
- Two simultaneous cold bootstraps: exits `[0,0]`, marker count `1`, environment count `1`, remaining lock count `0`.
- Bootstrap waiter timeout was increased above the exact-package install timeout after independent review; foreign locks are never deleted by waiters.

### Cycle 3 — compatibility and project regression

- M01.2 regression: 5 schemas, 11 positive + 20 negative fixtures, 25 deterministic envelope reruns, 3 runtime-guard mutations and 9 representative report shapes PASS.
- Project config: PASS, 15 levels / 15 bitmap backgrounds / shared Android-Web QA query parity.
- Cocos 3.8.8 bundled TypeScript project-only no-emit: PASS.
- Assets strict: PASS, 1528 PNG, 0 blockers, 0 white-matte suspects.
- Skin matrix strict: PASS, 576/576 frames, 0 blockers, 0 warnings.
- UI IR: PASS, 14/14 screens, 0 problems, 0 warnings.
- Level-select icons verify-only: PASS, 15 PNG + 15 meta.
- Git/Pages topology: PASS; parent gitlink equals clean Pages HEAD.
- Initial topology invocation used unsupported `-ReportPath` and failed before validation; corrected canonical `-OutputPath`/stdout-capable invocation passed. No product defect was hidden.

### Cycle 4 — independent review and hygiene

- Local coder review identified bootstrap lock/install timeout asymmetry; accepted, fixed and regression-tested.
- Manual line-level review found a stronger source/input TOCTOU risk; post-run Git and protected-input revalidation were added with negative tests.
- Reviewer concerns about symlink containment and process-tree absence were checked against actual code and Windows junction/process-child tests; no residual defect reproduced.
- Requested legacy profile name `coder` was rejected by local-worker; retry through its current default profile succeeded.
- One heavy local review attempt timed out and produced no evidence; it is not counted as PASS.
- CodeRabbit CLI is unavailable on this host; deterministic tests, local-worker review and Codex manual review are the accepted bounded review evidence.

## Verdict and boundary

M01.3 satisfies its typed fail-closed runner objective. No blocking finding remains inside this work package. Production release remains blocked by the existing Web/Pages, current arm64, signing and embedded content-version decisions. The only next safe package is M01.4 typed profile composition; no runtime/release claim follows from this report.

