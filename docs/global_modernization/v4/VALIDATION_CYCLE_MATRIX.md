# Validation cycle matrix v4

Канонические M01 profiles остаются единственным исполняемым source of truth. Этот файл добавляет routing для v4 units, но не создаёт второй runner.

| Unit type | Обязательный цикл | Runtime evidence |
|---|---|---|
| audit/docs/schema/index | D4 | не требуется, если runtime inputs неизменны |
| pure TypeScript contract | D4 + strict no-emit + pure tests + canonical static gate | не требуется до runtime wiring |
| runtime ownership patch | P4 | свежие Web targeted + Android emulator targeted |
| module integration/legacy removal | M2_PLUS | два свежих прохода, recovery после failure |
| major visual/content integration | QA7 | все применимые 7 domains |
| release candidate | RC2 | два независимых QA7 cycles и artifact/live parity |

## D4

1. Integrity: hashes, safe extraction, manifest coverage.
2. Contract: JSON/YAML/schema/fixtures/scripts.
3. Compatibility: live paths, owner/dependency/index reconciliation.
4. Independent plan review: contradictions, rollback, stop conditions, next action.

## `TC-01`

```text
T1 discovery: configured/ambient/candidate tools and paths
T2 fail-closed contract: missing configured JDK cannot fall through silently
T3 no-build preflight: config, path, major version, SDK/NDK/Gradle identity
T4 first Android-dependent P4: fresh export/build/install only on emulator
T5 review: no version upgrade, no global environment mutation
```

TC-01 closeout: `T1`, `T2`, `T3` и `T5` — PASS. `T4` имеет статус
`DEFERRED_TO_FIRST_ANDROID_P4`, а не PASS: требовать fresh build для закрытия
TC-01 означало бы цикл зависимости с M03.3C. No-build preflight проверяет exact
Adoptium 17.0.20 + hashes, Cocos 3.8.8, SDK/API/NDK/CMake, существующий export
если он есть, Java/Gradle overrides и process-only environment binding. Он не
запускает Cocos, Gradle, adb или emulator.

## `M03.3A`

- strict TypeScript;
- capacity/config boundary tests;
- finite-number and non-plain-object sanitation;
- immutable snapshot;
- event-count and UTF-8 byte-bounded export;
- stable serialization;
- disabled mode;
- M03.2 matrix unchanged; cumulative canonical static gate now has 14 steps, including the cross-platform M03.3A, M03.3B and TC-01 structural contracts, schema-aware v4 plan validation and negative tests. Executable TypeScript/PowerShell behavioral suites remain separate local receipts because hosted static runners do not install Cocos TypeScript or provide the bound Windows host toolchain.

## `M03.3B`

- epoch initial/current/capture/advance/overflow tests;
- stale guard rejection;
- `guard(callback)` captures internally; numeric tokens are captured snapshots, not synthesized future guards;
- guard checks synchronous entry only; async continuations must re-check ownership after every await;
- overflow throws before mutation and never wraps;
- no GameRoot integration unless the package is promoted to full P4;
- no callback cancellation claim beyond touched paths.

## `M03.3C` P4

1. Static/contracts: one state writer, no Cocos objects/private data, release disabled.
2. Web: start/pause/resume/menu/reset, unique events, bounded export, zero diagnostics.
3. Android emulator: fresh x86_64 build, install/launch, 10 reset loops, exact epoch increments, bounded logcat.
4. Regression/review: name/skin/background/order/listener/timer behavior, hygiene, rollback.

## QA7 domains

1. build/static/bootstrap;
2. visual/UI — 14 screens × 5 viewports;
3. gameplay/state/physics;
4. assets/skins/content;
5. audio/VFX;
6. performance/lifecycle;
7. release/cleanup evidence.

`not_executed` никогда не равен `pass`. Physical-device slot — `NOT_APPLICABLE` по умолчанию и становится mandatory только после отдельной команды пользователя.
