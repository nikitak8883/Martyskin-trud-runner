# MTR global modernization v3 — project entry point

Статус: `m03_complete_m04_a_complete_m04_b_next_release_blocked`  
Дата интеграции: 2026-07-23  
Последнее обновление: 2026-08-13  
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
- M01.7: fail-closed `M2_PLUS` summary завершён; текущий release корректно `BLOCKED` из-за 8 отсутствующих mandatory Web/Android/static/review evidence slots двух циклов.
- M02.2: одна immutable logical content identity встроена в Web/Android build preflight/report; 3/3 target preflights и локальная/Windows/Linux матрица проходят 8/8. Platform artifact manifests остаются раздельными; build/runtime не запускались.
- M02.3: свежая Web Mobile сборка из shared identity содержит 4 815 файлов / 120 421 881 байт; aliases/payload проходят. Browser matrix 34/34, interaction PASS, restart 10/10 и soak 300.561 s без console warnings/errors проходят на pinned `playwright-core@1.61.1`.
- M02.4: свежий x86_64 debug APK установлен только на `emulator-5554`; Android matrix 28/28, interaction/name persistence, restart 10/10 и soak 300.623 s проходят без unexpected diagnostics. Репрезентативная визуальная выборка чистая.
- M02.5: свежий ABI-valid APK содержит проверенные ELF64/AArch64 и ELF32/ARM payloads, валидные package/version и v1/v2 debug signature; это статическое evidence совместимости, физическая установка не выполнялась. Технический entry gate M02.2–M02.5 для M03 закрыт.
- M03.1: воспроизводимый TypeScript AST inventory зафиксировал 170 полей, 267 методов, 613 уникальных internal call edges, 8/8 listener register/unregister, 15 `scheduleOnce`, 37 storage operations и 10 dynamic-node patterns. Runtime не менялся; восемь coupling findings разнесены по M03.2–M03.7.
- M03.2: typed `GameSessionState` contract сохраняет 14 live states, 44 changed edges и 14 idempotent self-edges, а остальные 138 пар отклоняет детерминированно при единственном writer. Declarative player schema фиксирует 8 states/44 transitions без второго runtime owner. Static gate `9/9`, итоговый CodeRabbit — 0 findings, свежие Android emulator `28/28` и Web `34/34` матрицы с restart `10/10` и пятиминутными soak проходят.
- M03.3: pure `DevEventLog` и `LifecycleEpoch` подключены через один release-off `GameRootDevEventAdapter`; writer состояния остаётся единственным. DEBUG Web и Android-emulator дают ровно 33 уникальных события для 10 reset-loop, release Web даёт 0 событий. Свежие Web `34/34` и Android-emulator `28/28` матрицы, interaction/name persistence и restart `10/10` проходят; physical device не использовался. Build router теперь fail-closed принимает Cocos exit `36` только вместе с новым terminal success marker. Canonical pre-commit gate — `15/15 PASS`.
- M03.4: jump, glide, dash и pause направлены через один `GameplayInputAdapter` с общим pause debounce `220 ms`, одним glide writer и неизменной listener topology. Node contract `10/10`, static gate `17/17`, Web Pass A/Pass B/recovery `34/34`, Android-emulator Pass A/Pass B `28/28` и холодный recovery проходят; canonical `M2_PLUS` — `12/12 PASS`, physical device не использовался.
- M03.5: восемь platform/ground/pickup/bonus/obstacle/NPC/finish callbacks направлены через один синхронный `GameplayCollisionRouter`; detection и exact legacy side-effect order сохранены в `GameRoot`. Node contract `10/10`, static gate `18/18`, Web Pass A/Pass B/recovery `34/34`, Android-emulator Pass A/Pass B `28/28`, collision query и холодный recovery проходят; canonical `M2_PLUS` — `12/12 PASS`, physical device не использовался.
- M03.6: power-up spawn/activate/tick/expire/cleanup переданы epoch-aware owner с injected tick; Web/Android parity и lifecycle recovery подтверждены.
- M03.7A/M03.7B: единый runtime scheduling/UI ownership принят, семь дублирующих callback wrappers удалены после rollback/hidden-reference gate; M03 закрыт, physical device не использовался.
- M04-A: канонический inventory фиксирует 1 635 source-файлов и 1 882 metadata-файла, 24 непересекающихся ownership scopes и 11 atlas-policy groups; runtime textures не перепаковывались. Schema/validator, 8 direct tests и 11 negative fixtures проходят; свежие Web `34/34 × 2` плюс recovery и Android-emulator `28/28 × 2` плюс recovery, touch/name/restart/soak циклы проходят.

## Следующее безопасное действие

Выполнить `M04-B` (`M04.3 + M04.4`): расширить fail-visible pre-import validator и создать manifest-linked contact sheets. Перепаковка runtime textures остаётся запрещена до измеренного `M04-C-PILOT`; release остаётся blocked.
