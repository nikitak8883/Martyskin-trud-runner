# Independent audit of the integrated v3 plan

Итог: `PASS_WITH_EXPLICIT_RELEASE_BLOCKERS`.

План пригоден для последовательной реализации после M00 source freeze. Он не разрешает немедленный release, cleanup или архитектурный patch.

## Post-execution overlay — 2026-07-19

M00.1–M00.6 выполнены и независимо перепроверены. Принятый source baseline закреплён commit `12670452ae4580ef5c685ff986476daf91522978` и annotated tag `mtr-source-freeze-v3-20260719`; source/Pages bundles прошли `git bundle verify`, offline restore и повторные статические gates. Утверждения ниже о ещё не созданном commit/tag отражают состояние первоначального аудита до выполнения M00 и сохранены как историческая трассировка.

Обновлённый план остаётся непротиворечивым: M00 закрывает входной dependency M01, M01.1 inventory и M01.2 schema/adapter seam завершены, а release остаётся fail-closed. Следующая операция — `M01.3` typed runner без game-runtime patch.

## Audit pass 1 — полнота входных данных

- ZIP checksum: PASS.
- Safe extraction: PASS, 93 файла, unsafe paths = 0.
- Внутренний manifest: 91/91 PASS.
- Полный checksum list: 92/92 PASS.
- Upstream Python unit tests на Windows: 2/2 PASS.
- JSON/YAML/Python/PowerShell syntax: PASS.
- 8 TypeScript reference files: strict no-emit compile PASS через TypeScript из Cocos 3.8.8.
- Project-only TypeScript: принятая Cocos-compatible команда с `--skipLibCheck --lib es2020,dom --isolatedModules false` — PASS; прямой `tsc -p` — ожидаемо непригоден и записан как toolchain conflict.
- `tools/validate-mtr-config.ps1`: PASS, 15 levels/15 bitmap backgrounds/shared Android-Web QA query parity.
- Full JSON Schema validation: NOT REPRODUCED, потому что optional `jsonschema` отсутствует; это записано как M01 dependency task, а не скрыто как PASS.

## Audit pass 2 — live compatibility

- Ключевые факты отчёта 14 июля перепроверены по живому Git, build, APK signatures/ABIs, Web/Pages trees, Cocos install и evidence.
- 25 конфликтов/ограничений записаны с решениями.
- Existing v2 results не обнулены.
- Draft schemas/reference code физически изолированы от runtime под `docs/.../library/drafts`.
- External tools/workflows не были установлены в `tools/` или `.github/`.

Результат: PASS_WITH_ADAPTATIONS.

## Audit pass 3 — dependency and decomposition integrity

Машинная проверка:

```yaml
modules: 13
work_packages: 95
unique_work_package_ids: 95
dependency_cycle: false
topological_order:
  - M00
  - M01
  - M02
  - M03
  - M04
  - M06
  - M05
  - M07
  - M08
  - M09
  - M10
  - M11
  - M12
invalid_statuses: 0
invalid_gate_references: 0
invalid_entry_gate_references: 0
```

Все 20 upstream findings отображены на существующие work-package IDs; unmapped findings = 0.

Результат: PASS.

## Коррекции после первого варианта плана

1. M01 minimum fail-closed gate перенесён перед release recovery.
2. M03 больше не ждёт полного закрытия production signing/AAB/Pages; он ждёт только технический baseline M02.2–M02.5.
3. M08 и M09 упорядочены после M07, чтобы content-service batches не шли одновременно через монолит.
4. M11 исключён из release blockers и оставлен optional/feature-flagged.
5. Commit/tag и restore rehearsal переведены из runtime P4 в D4, потому что они не меняют игру.
6. M10 завершает module regression через QA7/M2_PLUS; RC2 оставлен только финальному release.
7. Сырые Web/Android manifests разделены; parity определяется по logical shared content, а не по byte identity платформенных файлов.
8. Production signing/AAB отделены от технической current-arm baseline, чтобы неизвестное решение магазина не заморозило архитектуру.
9. Физическое устройство явно сделано conditional и не запускается по умолчанию.
10. Четырёхцикловое правило, QA7, M2_PLUS и RC2 объединены без ослабления любого из них.
11. TypeScript gate закреплён как project-specific Cocos command; upstream `npx tsc` и прямой bundled `tsc -p` запрещены как неподтверждённые эквиваленты.

## Audit pass 4 — библиотека и воспроизводимость плана

```yaml
project_v3_json_yaml_files_parsed: 14
copied_upstream_files_checked: 23
copied_upstream_hash_matches: 23
draft_schemas: 9
draft_typescript_seams: 8
adopted_templates: 6
runtime_files_changed: 0
build_or_emulator_started: false
commit_or_push_performed: false
```

Current audit indexes:

- Git state: создан;
- build/artifact state: создан;
- evidence: 801/801 файлов с SHA-256;
- Web/Pages diff: зафиксирован;
- Android ABI/signing: перепроверены.

Результат: PASS.

## Остаточные блокеры, не являющиеся дефектами плана

| Blocker | Владелец решения | Что разрешает |
| --- | --- | --- |
| primary source remote | пользователь | remote CI in M01.6; local mandatory equivalent remains available |
| direct APK / Play / both | пользователь | M02.1, conditional M02.6 |
| signing identity/backup | пользователь | production release |
| physical-device run | только явная команда пользователя | M10.3/final device evidence |
| pinned JSON Schema validator | M01 implementation | canonical schema activation |

## Риски, которые остаются под контролем gate

- 1.05 GB local raw evidence защищены индексом, но ещё не имеют полной M01 retention classification;
- stale runtime evidence после 14 июля;
- монолитный GameRoot;
- current arm artifact старее принятой линии;
- отсутствие main source remote.

Ни один из этих рисков не замаскирован статусом green.

## Финальный вердикт

Декомпозиция полна, внутренне непротиворечива и покрывает upstream findings. M00 завершён; следующая исполнимая операция — `M01.1`: инвентаризировать validators/harnesses и закрепить их реальные контракты. Build/publish/runtime refactor остаются запрещены до соответствующих dependency gates.
