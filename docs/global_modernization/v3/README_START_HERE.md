# MTR global modernization v3 — project entry point

Статус: `m00_complete_m01_6_complete_m01_7_next_runtime_not_started`  
Дата интеграции: 2026-07-21  
Источник: `C:\Projects\Monkey Work\Tasks\5\MTR_CODEX_CURRENT_STATE_AUDIT_AND_MODERNIZATION_LIBRARY_v3_20260715.zip`  
SHA-256: `85639CC7C93D4C1A2541D47DE5057B62BC6E555053827D72D74CC8F41AA04AA2`

## Назначение

Эта папка — каноническая проектная адаптация внешнего аудита v3. Она не заменяет Tasks/4/v2 и не является готовым runtime patch. Её задача:

1. закрепить живые факты 19 июля;
2. устранить конфликты внешнего плана с текущим проектом;
3. разложить M00–M12 на исполнимые bounded work packages;
4. подготовить схемы, reference seams, templates и QA-профили;
5. не допустить начала runtime-модернизации до завершения source freeze.

## Приоритет источников

```text
живой source + AGENTS/lore
→ docs/current_audit/*
→ принятый Tasks/4/v2 evidence
→ этот интегрированный v3 plan
→ внешний Tasks/5 пакет как upstream reference
```

При расхождении внешний пакет никогда не перезаписывает рабочую механику, lore, Android/Web parity rules или принятый QA baseline.

## Читать в таком порядке

1. `../../current_audit/revalidation_summary.md`
2. `COMPATIBILITY_AND_CONFLICT_REPORT_20260719.md`
3. `INTEGRATED_MASTER_PLAN_20260719.md`
4. `WORK_PACKAGE_INDEX.yaml`
5. `VALIDATION_CYCLE_MATRIX.md`
6. `TOOL_AND_CODE_ADAPTATION_BACKLOG.md`
7. `PLAN_AUDIT_20260719.md`
8. `library/README.md`

## Текущее разрешённое состояние

- M00.1–M00.6: завершены.
- Immutable source commit: `12670452ae4580ef5c685ff986476daf91522978`.
- Annotated tag: `mtr-source-freeze-v3-20260719`.
- Source и Pages Git bundles: созданы, проверены и восстановлены без сети.
- Restore rehearsal: PASS после обязательного `core.longpaths=true` и восстановления игнорируемых Cocos generated declarations.
- Build/runtime/emulator/Pages publish/signing: в рамках M00 не запускались и не изменялись.
- Architecture/assets/UI/gameplay patches: в рамках M00 не начинались.
- M01.1: завершён полный инвентарь `32/32` tracked validators/harnesses/producers; статический D4-срез прошёл, runtime/build QA не запускался.
- Принятые инструменты и обнаруженные false-green/timeout/schema/path/port риски закреплены в `M01/quality_gate_inventory.md` и `.json`.
- M01.2: завершены canonical evidence schemas, 18-source registry, 11 active adapters, 11 positive/20 negative fixtures и deterministic self-test.
- M01.3: завершён project-local typed runner с shell-free argument arrays, process-tree timeout, containment/output-collision guards, atomic reports, source/protected-input revalidation и isolated pinned Draft 2020-12 engine. Game runtime не менялся.
- M01.4: завершены typed-профили D4/P4/M2_PLUS/QA7/RC2, explicit mandatory/conditional/not-applicable semantics, stale/reuse/source guards, profile wrapper и 46-test isolated suite. Game runtime не менялся.
- M01.5: завершён delete-incapable index-first retention dry-run; 801/801 evidence files прошли path/size/mtime reconciliation и получили protected/retained_recent/rotatable review-only classification. Удаление не выполнялось, game runtime не менялся.
- M01.6: source branch `mtr-source-v3` опубликована в единственный утверждённый GitHub repository; один typed static command используется локально и в Windows/Linux Actions matrix. Чистый локальный прогон — 7/7 PASS; runtime/build/device не запускались.

## Следующее безопасное действие

Выполнить `M01.7`: сформировать M2_PLUS release-blocking summary, который не принимает missing, failed, skipped или stale mandatory evidence. Release остаётся blocked.
