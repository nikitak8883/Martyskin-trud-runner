# MTR global modernization v4 — точка входа

Статус: `M04_C_THEME_LOGISTICS_PARTIAL / ATLAS_ATTEMPT01_REJECTED / RELEASE_BLOCKED`  
Дата аудита: `2026-08-09`  
Checkpoint перед текущим logistics slice: `d9175adcdbb5a6fe072063fd7ffd9275b364daf8`; живой статус — `../../codex/CURRENT_STATE.md`.  
Документационная база до RDX-01: `95648b978117b8964469ad4fb236829d9540c239`

## Назначение

Эта папка — проектная адаптация внешней библиотеки v4. Внешний ZIP остаётся защищённым upstream-источником в `Tasks`; в рабочий проект перенесены только проверенные и совместимые контракты. Runtime, assets, сцена, Android build config и публикация в рамках RDX-01 не изменялись.

## Приоритет источников

```text
живой source + AGENTS + принятые проектные ADR
→ канонические v3 quality/evidence contracts
→ эта v4 execution roadmap
→ внешний v4 ZIP как advisory/upstream reference
```

Внешние fallback-инструменты не заменяют более строгий действующий M01 runner.

## Два независимых счётчика

- Требования проекта: `95` source work packages; `28` complete, `54` pending, `3` blocked, `10` conditional. Обязательный остаток: `57`.
- Исполнение от текущей точки: `73` обязательных v4 execution units, включая новый, ещё не принятый `M04-C-FAMILY-THEME-LOGISTICS`; `20/73` завершены (`27.3973%`), `53` остаётся. Ещё `7` units условные. Знаменатель увеличен на один для явной QA/rollback-границы logistics; completed не увеличен.

Эти знаменатели нельзя смешивать: один считает требования, другой — инженерные rollback/QA-границы.

## Читать в таком порядке

1. `AUDIT_INGEST_REPORT_20260809.md`
2. `LIVE_DRIFT_AND_CONFLICT_REPORT_20260809.md`
3. `INTEGRATED_ROADMAP_20260809.md`
4. `EXECUTION_UNIT_INDEX.json`
5. `VALIDATION_CYCLE_MATRIX.md`
6. `TIME_AND_CAPACITY_FORECAST.md`
7. `LIBRARY_ADOPTION_MANIFEST.yaml`
8. `PLAN_AUDIT_20260809.md`

## Следующие безопасные действия

1. Продолжить `M04-C-FAMILY-THEME-LOGISTICS`: reviewed alpha-fix сохраняется; первый atlas attempt отклонён `61/63` и убран. Завершить rollback QA, изолировать performance-прогоны от сборок/других QA и заморозить следующий эксперимент до мутации. Не подменять первый failed result более быстрым repeat.
2. Для каждого child выполнить frozen before/after, Web/Android-emulator P4, M2_PLUS, visual parity и rollback.
3. Не закрывать aggregate source package `M04.5` и не менять dynamic-atlas policy до завершения соответствующих execution units.

## Запреты до соответствующих gates

- не merge/rebase `origin/main`: это намеренно отдельная Pages-линия;
- не копировать внешний fallback quality runner поверх канонического M01;
- не запускать physical-device QA без отдельной команды;
- не публиковать Web, не push и не выпускать production artifact без соответствующего ADR/gate;
- не удалять legacy paths в одном патче с введением нового owner.
