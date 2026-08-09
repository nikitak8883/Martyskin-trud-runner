# Live drift и конфликты внешнего v4

## Итог

`MATERIAL_PLAN_DRIFT / NO_RUNTIME_DRIFT / ADAPTATION_REQUIRED`

| ID | Наблюдение | Решение |
|---|---|---|
| V4-C01 | External snapshot `f9940815`; live pre-RDX HEAD `95648b97`. | Дрейф только документационный: один commit с browser-audit bundle; M03.2 source hashes совпали. Продолжение разрешено. |
| V4-C02 | External audit трактует отсутствие merge-base с `origin/main` как нерешённую canonical lineage. | Исправлено: `main` по принятому ADR — Pages artifact line, а `mtr-source-v3` — source projection. Обычные merge/rebase всё равно запрещены, но новый owner choice canonical URL/branches не нужен. |
| V4-C03 | Parent history и `origin/mtr-source-v3` также не имеют общего ancestry. | Это ожидаемый subtree-root projection. Tree `c2cd1b50:<project-prefix>` точно равен tree `e4e412dd` (`59f2b565...`). Нужен технический `PUB-01` projection/parity gate, не выбор новой линии. |
| V4-C04 | Current parent subtree отличается от published source branch на `50` paths. | Это накопленный непубликованный M02.3–M03.2 + audit docs scope. Push не выполняется; публикация только после bounded tree projection review. |
| V4-C05 | `runtime_started: false` после M03.2. | Исправлено на `true`. |
| V4-C06 | `MODULE_EXECUTION_INDEX.source_head` был старым freeze commit. | Семантика исправлена: хранится последний принятый runtime checkpoint, а docs basis — отдельно. Это устраняет невозможную самоссылку «файл содержит hash собственного commit». |
| V4-C07 | M02.7 ссылался на уже complete M00.3. | Blocker заменён на approval механизма immutable Pages deployment и fresh artifact-to-live parity. |
| V4-C08 | Android configs указывают отсутствующий JDK `17.0.19`; установлен `17.0.20`, ambient PATH — JDK `21`. | Новый обязательный `TC-01`: exact JDK 17 discovery, no silent fallback, config/preflight/build validation до M03.3C. |
| V4-C09 | External `capture-environment.ps1` не ищет фактический Cocos path `C:\ProgramData\cocos\editors\Creator\3.8.8`. | Не принят. Toolchain lock сформирован по живым путям; будущий probe должен поддерживать ProgramData и различать ambient/build Java. |
| V4-C10 | External quality/release schemas проще и несовместимы с canonical M01.3/M01.4 schemas. | Не приняты; canonical schemas остаются source of truth. |
| V4-C11 | `create-source-bundles.ps1 -WhatIf` всё равно создаёт directory/report; одинаковые leaf names могут столкнуться. | Не принят до исправления side-effect и collision guards. |
| V4-C12 | External `verify-android-artifact.ps1` не доказывает package/version/content identity и недостаточно fail-closed. | Не принят; будущая работа остаётся за каноническим M02 verifier backlog. |
| V4-C13 | Reference `DevEventLog` обещает byte/event limits, но ограничивает только event count; config limits почти не валидируются. | Подготовлена усиленная v4 reference draft и config schema; runtime integration пока отсутствует. |
| V4-C14 | DevEvent schema не ограничивает payload string/depth/serialized bytes. | Добавлены согласованные runtime/schema limits; max depth/bytes остаются обязательными runtime validator checks. |
| V4-C15 | External dependency graph — module-level; source work packages почти не имеют machine dependencies. | Создан explicit 72-unit DAG с source-package coverage и validator. |
| V4-C16 | External loose `requirements-optional.txt` конфликтует с pinned isolated M01 environment. | Не устанавливать project `.venv-tools`; использовать существующий exact lock/bootstrap. |
| V4-C17 | M02.1 считает весь distribution decision неизвестным. | Уточнено: direct APK — обязательный локальный delivery path по принятым требованиям; Play/AAB остаётся conditional. Production signing/backup/upgrade policy остаётся blocked. |

## Git-модель после коррекции

```text
parent development history
  └─ project subtree tree ── deterministic projection ──> origin/mtr-source-v3

origin/main
  └─ immutable Pages artifact line (не merge-target для source)
```

Нельзя использовать ahead/behind между этими корнями как показатель пропущенных commits. Сравнение выполняется по tree/path/content и manifest identity.

## Блокеры

- Production signing identity, backup ownership и upgrade policy.
- Выбор/approval точного immutable Pages deployment механизма.
- Cleanup apply после final accepted build.

Git URL и раздельные роли веток не считаются новым owner blocker: они уже приняты M00 amendment.

