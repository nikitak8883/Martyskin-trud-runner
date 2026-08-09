# MTR — библиотека для внешнего аудита в browser GPT

Дата среза: 2026-08-09 (Asia/Jerusalem)  
Проект: **Martyshkin Trud Runner**, Cocos Creator 3.8.8, Web + Android  
Статус: `AUDIT PACKAGE / IMPLEMENTATION PAUSED AT M03.2 / RELEASE BLOCKED`

## Как использовать

1. Загрузите в browser GPT весь ZIP-архив, не отдельные файлы.
2. Сначала прочитайте этот файл, затем `01_CURRENT_STATUS_AND_LOG.md`, `02_ROADMAP_STATUS_AND_FORECAST.md` и `05_RISKS_BLOCKERS_AND_AUDIT_QUESTIONS.md`.
3. Используйте YAML/JSON из раздела `source_documents/` как первичные доказательства, а не как устаревшие планы.
4. Сверяйте дату каждого утверждения. Последняя подтверждённая runtime QA — 2026-07-23; на дату пакета исходники проекта не менялись, но новых runtime-прогонов не выполнялось.

## Цель внешнего аудита

Независимо оценить:

- реалистичность оставшейся дорожной карты и её порядка;
- риски монолитного `GameRoot` и корректность уже введённого session-state seam;
- достаточность Android/Web QA и границы её применимости;
- release blockers, Git-синхронизацию и минимальный безопасный следующий patch;
- где можно уменьшить объём плана без потери качества, а где сокращать нельзя.

## Что намеренно включено

- живой Git-статус и хеши ключевых файлов;
- roadmap с 95 work packages и machine-readable исходный YAML;
- итоговые M03.2 validation/code-review reports;
- свежий контрольный лог и исторический release-blocking report;
- карта кодовой базы, риск-реестр, QA-циклы и избранные исходные excerpts;
- manifest с SHA-256 каждого файла пакета.

## Что намеренно исключено

- полный исходный tree, assets, PNG, APK/AAB, build/cache/temp output;
- 190 MB raw Android screenshots/logcat и другие тяжёлые QA-артефакты;
- пользовательские неотслеживаемые папки, локальные absolute paths, credentials и секреты;
- любая инструкция на auto-push, merge, release deployment или удаление данных.

Отсутствие raw-артефактов не означает отсутствие QA: точные сводки, хеши и команды включены. Если внешний аудитор запросит raw proof, её следует предоставить отдельным, минимальным, privacy-reviewed пакетом.

## Требования к выводу внешнего аудитора

Верните отчёт на русском языке в следующем виде:

1. `Вердикт`: working / partially_working / blocked, с одним абзацем причин.
2. `Проверенные факты` и `гипотезы` — строго раздельно.
3. `Критические риски` (не более 10), с указанием конкретного файла или roadmap ID.
4. `Оценка дорожной карты`: оставить / переставить / декомпозировать / отменить — с обоснованием.
5. `Следующие 3 безопасных пакета`: граница, входы, выходы, тесты и rollback.
6. `Release readiness`: что технически подтверждено, что не подтверждено, какие user/external decisions нужны.
7. Не предлагайте переписывать весь `GameRoot`, не выдавайте debug x86_64 APK за release и не называйте старую QA доказательством текущего runtime без повторного прогона.

## Уровни достоверности

| Метка | Значение |
| --- | --- |
| `LIVE-2026-08-09` | Проверено в filesystem/Git в день создания пакета. |
| `VERIFIED-2026-07-23` | Подтверждено machine-readable evidence на последнем implementation checkpoint. |
| `HISTORICAL` | Правдиво для указанного commit/date, но требует повторной проверки перед новым patch или release. |
| `BLOCKED` | Нужны решение пользователя, external system или отдельное разрешение. |

## Состав

- `01_CURRENT_STATUS_AND_LOG.md` — текущий статус и timeline.
- `02_ROADMAP_STATUS_AND_FORECAST.md` — остаток, зависимости и сроки.
- `03_CODEBASE_AND_ARCHITECTURE_MAP.md` — карта Cocos-кода и seam-ы.
- `04_QA_CYCLES_AND_EVIDENCE.md` — QA, команды, границы доказательств.
- `05_RISKS_BLOCKERS_AND_AUDIT_QUESTIONS.md` — риски, блокеры, вопросы.
- `06_KEY_SOURCE_EXCERPTS.md` — малый проверяемый source subset.
- `07_EXTERNAL_AUDIT_PROMPT_RU.md` — готовый prompt для browser GPT.
- `EXTERNAL_AUDIT_MANIFEST.json` — проверка целостности.
- `source_documents/` в ZIP — выбранные первичные project documents.
