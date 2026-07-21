# Integrated MTR implementation plan v3

Статус: `m00_complete_m01_4_complete_m01_5_next`, runtime implementation не начат.

## Цель

Сохранить принятую рабочую игру, восстановить воспроизводимый source/release baseline и затем постепенно завершить архитектуру, assets/UI/skins, levels/audio/save, performance и optional PCG без big-bang rewrite.

## Не-цели следующего bounded-шага

- не изменять и не перезаписывать принятый source-freeze commit/tag;
- не собирать и не устанавливать приложение;
- не синхронизировать и не публиковать Pages;
- не менять signing;
- не переносить reference TypeScript в runtime;
- не чистить файлы;
- не переписывать `GameRoot.ts` целиком.

## Исправленный dependency graph

```text
R0.A live inventory [DONE]
  → R0.B reviewed source freeze [DONE]
    → F0 project-native quality gate [M01.1 + M01.2 + M01.3 + M01.4 DONE; NEXT: M01.5]
      → R1 reproducible Web + emulator + current arm64 release recovery
        → A0 GameRoot seams after technical M02.2–M02.5 baseline
          → A1 M04 assets → M06 skins → M05 UI
            → C0 M07 levels → M08 audio/VFX → M09 save/telemetry
              → P0 M10 measured optimization
                → R2 final release

M11 PCG/DDA starts after M07+M09+M10 and remains optional/non-blocking for R2.
```

Коррекция v3: F0 минимальный fail-closed runner ставится перед R1, иначе release recovery нельзя доказать одной машинно-читаемой процедурой. Полный CI/evidence-retention слой M01 может продолжаться параллельно, но release gate обязан существовать до внешнего release claim. M03 ждёт технический baseline M02.2–M02.5, но не блокируется более поздними решениями о production signing, AAB или публикации Pages.

## Состояние модулей после сопоставления v2 и live repo

| Module | Live status | Что сохраняется | Что ещё требуется |
| --- | --- | --- | --- |
| M00 | complete | classification, topology ADR, source commit/tag, source/Pages bundles, manifest, evidence anchor, offline restore PASS | none; preserve immutable source anchor |
| M01 | M01.1 + M01.2 + M01.3 + M01.4 complete | полный инвентарь 32/32, canonical quality schemas, 18-source registry, 11 active adapters, positive/negative fixtures, typed fail-closed runner и D4/P4/M2_PLUS/QA7/RC2 profile layer | retention, CI/local parity, release summary |
| M02 | release blocked | Web/emulator artifacts и старый arm APK | immutable source/content version, current arm64, Pages parity, signing decision, conditional AAB |
| M03 | not started | существующая рабочая логика | state/input/collision/power-up seams и bounded log |
| M04 | revalidate then extend | asset validators, draft atlas, selected contact sheets | final ownership/atlas/bundle contracts и metrics |
| M05 | revalidate then extend | 14 UI IR, выбранные runtime pilots | shared tokens/components/SafeArea/Layout/9-slice, full regression |
| M06 | revalidate then extend | 576 static matrix, contact sheets, selected emulator QA | registry/resolver, full lifecycle matrix, bundle cleanup |
| M07 | product works / ownership pending | 15 levels and current visuals | manifest, pilots, streaming, readability/size metrics |
| M08 | product works / routing pending | current audio/VFX | maps, buses, limits, adapters, pools, persistence |
| M09 | product works / durability pending | nickname/records/achievements behavior | schema/profile/migration/recovery/local telemetry |
| M10 | partial baseline | Web/emulator soak evidence | budgets, reproducible percentiles/load/memory, measured patches |
| M11 | not started, optional | none | deterministic offline foundation only after prerequisites |
| M12 | not started | cleanup rules and existing evidence | RC2, artifact parity, approved cleanup, final reports |

## Фазы реализации

### Phase 0 — Source truth

M00.A и M00.B завершены 19 июля 2026 года:

1. классифицировать tracked/untracked source, docs, evidence и generated output;
2. решить Pages topology;
3. создать минимальный source checkpoint, annotated tag и Git bundle;
4. создать logical content fingerprint и evidence anchor;
5. восстановить bundle в temp и повторить static gates;
6. актуализировать CURRENT_STATE и module index.

Результат: source commit `12670452ae4580ef5c685ff986476daf91522978`, annotated tag `mtr-source-freeze-v3-20260719`, отдельные verified source/Pages bundles и offline restore PASS. Exit достигнут: принятую игру можно восстановить без builds/secrets/raw corpus; клонирование на Windows требует `core.longpaths=true`.

### Phase 1 — Quality system and release recovery

Сначала M01 minimum viable gate, затем M02:

- M01.1 завершён: все 32 tool surfaces классифицированы, рабочие команды сохранены, false-green и side-effect risks не замаскированы;
- M01.2 завершён: canonical evidence contracts, registry, adapters и fixture matrix приняты;
- M01.3 завершён: shell-free typed runner, process-tree timeout, source/protected-input revalidation и atomic Draft 2020-12 reports приняты без runtime patch;
- сохранить существующие рабочие validators вместо замены внешними упрощёнными скриптами;
- M01.4 завершён: typed gate profiles композируют свежие M01.3 reports без второго произвольного command runner;
- M01.5 следующий: evidence classification и index-first retention dry-run с path guards;
- общий logical content version;
- Web, emulator x86_64 и current arm64 из одного checkpoint;
- Pages artifact parity;
- signing/distribution ADR;
- AAB только при Play target;
- RC evidence и artifact hashes.

Exit: воспроизводимая техническая release line. Production release остаётся blocked, пока signing/target не утверждены.

### Phase 2 — Gameplay seams

M03 выполняется strangler-патчами: inventory → state transitions/log → input → collision → power-up → UI/physics decoupling. Старый путь удаляется только после parity gate. Один patch — одна ответственность.

### Phase 3 — Presentation pipeline

1. M04 final asset ownership/atlas/bundle policy и метрики.
2. M06 SkinRegistry/BonusVisualResolver и полный lifecycle.
3. M05 shared UI runtime на базе уже существующего UI IR.

Визуальный канон, русский текст, реальные PNG-фоны и запрет ghost/double layers остаются hard gates.

### Phase 4 — Content services

M07 переводит 15 уровней на manifests и streaming, M08 централизует audio/VFX, M09 версионирует local data. Для M09 migration backup и corrupt fixtures обязательны до записи нового формата.

### Phase 5 — Measured optimization

M10 сначала фиксирует budgets и baseline, затем принимает по одной optimization family. Качество, память и load time сравниваются до/после. Emulator/Web обязательны; physical device — только по отдельному разрешению.

### Phase 6 — Optional experiments

M11 не входит в критический release path. Handcrafted segments сначала валидируются тем же deterministic validator; 1000-seed fuzz и DDA появляются только после telemetry baseline. DDA выключен по умолчанию.

### Phase 7 — Final release and cleanup

M12 замораживает RC, выполняет QA7 + RC2, создаёт Web/current arm64/(conditional AAB), проверяет deployment, затем делает cleanup dry-run. Удаление — отдельными approved batches с rebuild/retest и rollback mapping.

## Общие инженерные инварианты

- Android/Web используют один logical content source; platform manifests не обязаны быть byte-identical.
- Runtime QA Android по умолчанию только на эмуляторе.
- Финальный Android artifact обязан быть device-valid arm64, даже если physical install не разрешён.
- Ни один warning/failure не скрывается fallback-ом как PASS.
- Ни один old path не удаляется в том же patch, где впервые вводится replacement.
- Все timers/listeners/assets/native resources имеют cleanup ownership.
- Каждый substantial patch проходит P4; modules — M2+ и relevant QA7; release — RC2.
- Evidence индексируется, а не копируется в summaries.
- Cleanup всегда dry-run first и не касается protected anchors.

## Решения, которые можно принять позже без блокировки архитектурных contracts

- Google Play/AAB target;
- production keystore ownership;
- physical-device performance run;
- CI hosting details после source remote;
- включение experimental PCG/DDA.

## Definition of done программы

1. clean, restorable, tagged source и документированная Git topology;
2. единый fail-closed quality/release gate;
3. Web и current device-valid Android из одного source/content anchor;
4. завершённые M03–M10 contracts и отсутствие активных bypass/legacy paths;
5. full QA7 + RC2 без stale evidence;
6. signing/distribution состояние честно указано;
7. cleanup выполнен только после accepted final build и повторной QA;
8. final reports, hashes, manifests и rollback доступны локально.

Детальная декомпозиция каждого пункта находится в `WORK_PACKAGE_INDEX.yaml`.
