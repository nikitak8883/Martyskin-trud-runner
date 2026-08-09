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

## `M03.3A`

- strict TypeScript;
- capacity/config boundary tests;
- finite-number and non-plain-object sanitation;
- immutable snapshot;
- event-count and UTF-8 byte-bounded export;
- stable serialization;
- disabled mode;
- M03.2 matrix unchanged; canonical static gate now has 11 steps, including schema-aware v4 plan validation and negative tests.

## `M03.3B`

- epoch initial/current/capture/advance/overflow tests;
- stale guard rejection;
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
