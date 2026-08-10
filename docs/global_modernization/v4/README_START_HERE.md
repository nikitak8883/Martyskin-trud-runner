# MTR global modernization v4 — точка входа

Статус: `M03.3A_B_AND_TC-01_COMPLETE / M03.3C_READY / RELEASE_BLOCKED`  
Дата аудита: `2026-08-09`  
Живой runtime checkpoint: `f99408151c98cf8806e269307fe5e552f5b185c9`  
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

- Требования проекта: `95` source work packages; `19` complete, `63` pending, `3` blocked, `10` conditional. Обязательный остаток: `66`.
- Исполнение от текущей точки: `65` обязательных v4 execution units, включая `RDX-01` и `TC-01`; `4/65` завершены, `61` остаётся. Ещё `7` units условные. Знаменатель provisional до инвентаризации child batches M04/M05/M10.

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

1. `M03.3C`: один release-off GameRoot adapter для transition/reset/epoch.
2. Выполнить полный P4: fresh Web + Android-emulator build/install/runtime parity.
3. Не продвигать source package `M03.3` до завершения M03.3C.

## Запреты до соответствующих gates

- не merge/rebase `origin/main`: это намеренно отдельная Pages-линия;
- не копировать внешний fallback quality runner поверх канонического M01;
- не запускать physical-device QA без отдельной команды;
- не публиковать Web, не push и не выпускать production artifact без соответствующего ADR/gate;
- не удалять legacy paths в одном патче с введением нового owner.
