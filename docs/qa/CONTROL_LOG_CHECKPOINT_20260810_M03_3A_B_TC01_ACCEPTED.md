# Control log checkpoint — M03.3A + M03.3B + TC-01 accepted

Date: 2026-08-10 13:49 +03:00

**Status:** `completed` — прерванный незакоммиченный кластер независимо
переаудирован и принят. Pure contracts M03.3A/M03.3B и fail-closed Android
toolchain TC-01 готовы к фиксации; GameRoot/runtime/release в этот кластер не
входят.

**Roadmap position:** P0 `TC-01` complete; P1 `M03.3A` complete;
P1 `M03.3B` complete; `M03.3C` ready. Source package `M03.3` остаётся pending
до завершения C и полного P4.

**Progress:** execution ledger `4/65` complete (`6.2%`), остаётся `61`
обязательная execution unit и `7` conditional. Source ledger остаётся
`19/95`: mandatory `19/85`, обязательный остаток `66`, conditional `10`.
Знаменатель execution ledger остаётся provisional до создания child batches
M04/M05/M10.

## Acceptance evidence

- DevEventLog: `16/16` Node groups PASS; `12` event codes; TypeScript 5.8.2,
  ES2015; Python structural validator PASS; GameRoot wiring отсутствует.
- LifecycleEpoch: `16/16` Node groups PASS; synchronous-entry-only stale guard;
  Python structural validator PASS; GameRoot wiring отсутствует.
- Android toolchain: `35/35` PowerShell groups и `15/15` Python negative cases
  PASS; schema applied; build Java — exact Adoptium JDK 17.0.20; ambient
  Adoptium JDK 21 обнаружен, но не выбран.
- Два прямых и два wrapper no-build preflight PASS для arm64 и emulator:
  Cocos Creator 3.8.8, Gradle 8.11.1, AGP 8.10.1, compile SDK 36, target SDK
  35, build-tools 36.0.0, NDK 23.2.8568313.
- Accepted full-source TypeScript no-emit PASS; M03.2 Node/Python regressions
  PASS (`14` states, `58` accepted, `138` rejected, `14` idempotent,
  one writer; `8` player states and `44` transitions).
- PowerShell parser audit для всего затронутого toolchain scope: `0` errors.
- Receipt-to-file SHA-256 сравнения M03.3A/M03.3B/TC-01: все `Match=True`.
- Canonical final pre-commit gate: `14/14 PASS`, zero findings, source stable;
  run `qg.20260810105211.ee34f3f3acbc`; report SHA-256
  `0F66335B3C0B99890ECC4325B846AE7463A06FAA9B67404D1356E48FD98DD803`;
  dirty-source override был явно ограничен этим приемочным аудитом.
- Protected runtime files `GameRoot.ts`, `main.scene`, `GameSessionState.ts` и
  `PlayerStateSchema.ts` не изменены.
- Инструкция физической установки исправлена: команды требуют явный serial
  `R5CY933XP7P` и `--user 0`; это документационная страховка, физическое
  устройство в этом цикле не использовалось.

## Review dispositions

- Skill Compass предложил нерелевантный primary route для static encyclopedia;
  маршрут отклонён Codex и заменён bounded retrieval + safe patch review.
- Локальный профиль `coding` отсутствовал; повторный advisory review выполнен
  через доступный default profile.
- Первый повторный запуск canonical gate был корректно остановлен до тестов:
  restart-команда ошибочно указала отсутствующий project-local `.venv`.
  Маршрут заменён на закреплённый для проекта `python`; повторный полный gate
  прошёл `14/14`, а ложный запуск не создавал приемочного evidence.
- Первая read-only команда инвентаризации staging не выполнилась из-за
  недопустимого PowerShell pipeline после `foreach`; команда исправлена через
  промежуточный массив, повтор прошёл, Git-состояние не изменялось.
- Три advisory finding перепроверены по строкам. Два не соответствовали коду,
  третье относилось к неисполняемой JSON-строке; ни одно не принято как defect.
- Реальный документационный drift `ambient Java 26` исправлен на наблюдаемый
  JDK 21 с явным запретом включать ambient Java в build identity.

## Scope and exclusions

- Не запускались Cocos build/export, Gradle, adb, emulator, physical device,
  Web publish, Git push или release.
- В этот checkpoint не входят посторонние изменения верхнего workspace,
  agent-monitor, Tasks, Stiker pack и project-library/corpora.
- Release logging остаётся hard-off; новый state writer не добавлен.

**Remaining:** `M03.3C` GameRoot adapter, затем свежий Web build и
Android-emulator build/install/runtime parity; после этого — закрытие source
package `M03.3` и переход к `M03.4`.

**Next:** на чистой Git-базе составить exact-file mini-plan M03.3C, внедрить
единственный release-off adapter без второго owner/state writer и пройти полный
P4 только на Web + Android emulator.

## Restart receipt

1. Проверить, что Git commit с M03.3A/M03.3B/TC-01 существует и project scope
   чист.
2. Повторить clean-source canonical gate без `--allow-dirty-source`.
3. Перед M03.3C перечитать фактические transition/reset entrypoints GameRoot и
   определить один adapter boundary.
4. После runtime patch выполнить targeted tests, fresh Web build и полный
   Android emulator P4; physical device не использовать без отдельной команды.
