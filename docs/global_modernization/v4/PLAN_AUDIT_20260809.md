# Повторный аудит плана v4

## Проход 1 — найденные дефекты

1. Git risk был привязан к неправильной точке сравнения `origin/main`.
2. Source HEAD внутри индексного файла трактовался как всегда равный текущему commit, что создаёт самоссылочную невозможность.
3. Не был учтён missing JDK path и silent ambient-Java fallback.
4. External fallback schemas могли ослабить canonical M01 contracts.
5. Work-package catalogue не задавал достаточный execution DAG.
6. DevEvent reference не выполнял byte-bound и config-bound требования.
7. Distribution target был описан как полностью неизвестный, хотя direct APK уже является обязательным delivery path.
8. Grouping не имело отдельного denominator и могло смешаться с `19/95`.
9. DevEvent payload был ограничен при export, но не при append; plain-object accessor мог быть вызван во время sanitation.
10. Первый roadmap validator проверял DAG, но не валидировал полную JSON Schema форму до обхода графа.

## Внесённые коррекции

- Git разделён на parent history, source-tree projection и Pages artifact line.
- Runtime checkpoint и documentation basis получили разные поля.
- Добавлен `TC-01`, блокирующий Android-dependent runtime gate до fail-closed JDK repair.
- Создан adoption manifest: canonical M01 сохраняется, weak fallback не активируется.
- Создан explicit execution DAG: `65` mandatory + `7` conditional units.
- Source ledger `95` сохранён без искусственного изменения denominator.
- Подготовлены усиленные DevEvent config/schema/reference drafts.
- Добавлены payload node/byte budgets, accessor-safe descriptors и prototype-pollution-safe output object.
- Roadmap validator переведён на schema-first fail-closed обработку; PyYAML `6.0.3` добавлен в exact isolated lock.
- Release decisions разделены на direct APK, conditional Play и blocked signing identity.

## Проход 2 — проверки

- ZIP/package integrity: PASS.
- Live M03.2 contracts: PASS.
- Pre-adaptation clean static gate: `9/9 PASS`, run `qg.20260809080815.0f3e1728c410`.
- Integrated precommit static gate: `11/11 PASS`, `0` findings, run `qg.20260809083957.d3b1eea46ddc`; source stable, explicit development-only dirty authorization.
- JSON/YAML/Python/PowerShell/TypeScript syntax: PASS для upstream.
- V4 execution DAG: PASS; `72` units, `0` dependency cycles, `0` findings.
- Source-package coverage: `66/66` mandatory remaining и `10/10` conditional.
- Negative roadmap tests: `9/9 PASS`; bootstrap lock tests: `7/7 PASS`.
- V4 JSON Schemas: `4/4` meta-validation PASS; bound instances: `3/3 PASS`.
- Project-only diff and `git diff --check`: PASS.

## Вердикт

`PLAN_ACCEPTED_MACHINE_VALIDATED / RELEASE_BLOCKED`

Runtime implementation не начат. Следующий implementation boundary — `M03.3A`; `TC-01` является параллельным обязательным prerequisite для `M03.3C`.
