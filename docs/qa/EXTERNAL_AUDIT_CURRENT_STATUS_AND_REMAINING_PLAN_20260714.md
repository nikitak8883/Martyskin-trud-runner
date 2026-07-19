# MTR — текущий статус и незавершённый план для внешнего аудита

Сформировано: `2026-07-14T19:17:51+03:00`  
Проект: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Исходное ТЗ модернизации: `C:\Projects\Monkey Work\Tasks\4`  
Режим этой проверки: read-only аудит живого дерева и доказательств; единственное изменение — данный отчёт

## 1. Итоговый вердикт

```yaml
product_runtime: working
current_web_build: working_and_qa_passed
current_android_emulator_build: working_and_qa_passed
release_delivery: partially_working
global_modernization_program: partially_implemented
source_control_state: dirty_uncommitted
external_release_readiness: blocked
audit_confidence: high_for_local_tree_and_recorded_qa
```

Игровая линия в текущем локальном дереве прошла два независимых полных QA-цикла на Web и Android-эмуляторе. Открытых продуктовых блокеров в принятом QA от 14 июля нет.

При этом текущую линию нельзя считать готовым внешним релизом:

- исходники и QA-инфраструктура не закоммичены;
- актуальная Web-сборка не полностью синхронизирована с GitHub Pages;
- свежий Android-артефакт — только `x86_64` debug APK для эмулятора;
- последний arm64 APK собран 1 июля и не содержит последующие изменения 4–14 июля;
- AAB отсутствует;
- используется Cocos/debug signing configuration, а не зафиксированный production signing pipeline;
- архитектурная программа Tasks/4 реализована только частично.

## 2. Правило приоритета источников

При расхождении данных внешний аудитор должен использовать следующий порядок:

1. живое файловое и Git-состояние на момент этого отчёта;
2. `docs/qa/CONTROL_LOG_CHECKPOINT_20260714_TWO_CYCLE_AUDIT_COMPLETE.md` и его evidence;
3. исходные спецификации Tasks/4;
4. более ранние отчёты `docs/codex/CURRENT_STATE.md`, `module_execution_index.md`, `ui_ir_migration_report.md` и `code_review_report.md` только как историю.

Последняя группа обновлялась 6 июля и устарела относительно живого состояния: там указано 11 UI IR экранов и следующая работа `over`, тогда как в дереве уже есть `over`, `clear`, `finished`, а финальный шлюз подтверждает 14/14 экранов.

## 3. Подтверждённое состояние продукта

### 3.1 Финальный QA-шлюз

Основной контрольный лог:

- `docs/qa/CONTROL_LOG_CHECKPOINT_20260714_TWO_CYCLE_AUDIT_COMPLETE.md`

| Проверка | Подтверждённый результат |
| --- | --- |
| TypeScript | PASS |
| UI IR | 14/14 экранов, 209 узлов, 75 кнопок, 0 проблем, 0 предупреждений |
| Скины/бонусы | 8 скинов × 9 поз × 8 вариантов = 576/576 кадров, 0 блокеров |
| Ассеты | 1 528 PNG, 0 decode errors, 0 missing meta, 0 white-matte suspects |
| Конфигурация | 15 уровней, 15 фонов, Android/Web startup-query parity |
| Web matrix | 34/34 PASS |
| Web restart | 10/10 PASS |
| Web soak | 300.407 s, 0 console errors/warnings, FPS 52.84/60.19/61.43 min/avg/max |
| Android emulator matrix | 28/28 PASS |
| Android restart | 10/10 PASS |
| Android soak | 300.590 s, 0 process losses, PSS 229734/242329/208609 KiB start/peak/end |
| Визуальная инспекция | все UI-состояния, все 15 уровней, интеракции, рестарты и soak-кадры — PASS |
| Code review / hygiene | PASS, незакрытых замечаний принятого цикла нет |

Контрольные JSON:

- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/ui_ir.json`
  - SHA-256: `0FEEDF915BAF3667D3FE780819A212C9D7CB059CF7D4E568061B0BF3F930D238`;
- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/skin_bonus_matrix.json`
  - SHA-256: `A80522DD2FBAF35EA8277F53DAC9C8DB95A4982D5DBA964B3EE805E1966C1CF8`;
- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/assets.json`
  - SHA-256: `9958C36DC37FC7A3862C7CA043AB993777CD0E3FF0DE16D07075F5DD14A2CBE6`.

### 3.2 Текущая Web-сборка

Локальная сборка:

- путь: `build/web-mobile`;
- файлов: `4814`;
- размер: `120420561` bytes;
- последнее обновление: `2026-07-14T15:38:17+03:00`;
- эта сборка прошла принятый Web matrix/restart/soak QA.

GitHub Pages зона:

- путь: `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`;
- branch: `main`;
- local HEAD: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`;
- remote `origin/main`: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`;
- remote: `https://github.com/nikitak8883/Martyskin-trud-runner.git`;
- вложенное Pages-дерево само по себе clean.

Полное сравнение `build/web-mobile` с Pages-деревом:

```json
{
  "sourceFiles": 4814,
  "pagesFiles": 4818,
  "missingInPages": 1,
  "extraInPages": 5,
  "changed": 5
}
```

Среди различающихся файлов присутствуют `assets/main/index.js`, runtime config и PNG. Следовательно, опубликованная версия не подтверждена как эквивалент актуальной локальной сборке.

### 3.3 Android-артефакты

Свежий принятый QA APK:

- `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`;
- `142881559` bytes;
- SHA-256: `D2DB02FA9ED21D8628D7B3DE2D8A98E69954F8854156D3CFA6A81CE3D872655F`;
- ABI: `x86_64`;
- назначение: только эмуляторный QA, не установка на физический телефон и не релиз.

Последний device-valid APK:

- `releases/android/mtr-20260701-next-big-patch-release.apk`;
- `137968594` bytes;
- SHA-256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`;
- ABI: `arm64-v8a`, `armeabi-v7a`;
- apksigner v1/v2: PASS;
- дата: `2026-07-01`;
- статус: технически устанавливаемый, но устаревший относительно текущего исходного дерева.

Дополнительные ограничения:

- `build-android.json` содержит `useDebugKeystore: true`;
- сертификат APK — `CN=CocosCreator, ...`;
- production signing pipeline не оформлен;
- `build/android/.../outputs/bundle/release` отсутствует, AAB не создан;
- физическое устройство в последнем QA-цикле не использовалось, что соответствует emulator-only политике по умолчанию.

## 4. Git и воспроизводимость

Основной Git root:

- `C:\Projects\Monkey Work`;
- branch: `main`;
- HEAD: `76bac6c2e9f5e112489aa8a922dce48c3fd9970b`;
- remote для основного root отсутствует;
- staged changes отсутствуют;
- commit/push текущей линии не выполнялись.

Tracked runtime/tool changes включают:

- `assets/scripts/GameRoot.ts`;
- `native/engine/android/app/src/com/cocos/game/AppActivity.java`;
- `assets/resources/config/ui_skin_manifest.json`;
- два platform PNG уровня logistics;
- удаление устаревшего `mtr_start_menu_button_enter_name_01.png` и `.meta`;
- `tools/scan_and_fix_white_matte_edges.py`;
- `tools/validate-mtr-config.ps1`;
- `tools/web-chrome-runtime-smoke.ps1`.

Кроме этого, не tracked целиком или частично:

- `docs/codex/`;
- `docs/global_modernization/`;
- новые QA-логи/evidence;
- новые validator/harness scripts;
- часть `output/`;
- распакованный Tasks/4 пакет и project-library corpus на уровне общего root.

`git diff --check` проходит. LF/CRLF сообщения являются предупреждениями о будущей нормализации, не whitespace errors.

Git-топология имеет отдельный риск: `_github/Martyskin-trud-runner` — вложенный Git-репозиторий, но не валидно описанный submodule. `git submodule status` в родительском root завершается ошибкой `no submodule mapping found in .gitmodules`. Синхронизацию Pages следует выполнять только из вложенного репозитория, не смешивая её со staging основного root.

## 5. Фактическое состояние программы Tasks/4

Обозначения:

- `complete` — критерии данного этапа подтверждены;
- `partial` — рабочая функциональность или подготовительный слой есть, но исходный модуль не завершён;
- `not_started` — требуемый контракт/архитектура и отчёты отсутствуют;
- `blocked_release` — отсутствие пункта блокирует текущий внешний релиз.

| Порядок | Модуль | Состояние | Подтверждённая часть | Что осталось |
| ---: | --- | --- | --- | --- |
| 0 | Repository inventory / safety scaffold | `partial` | CURRENT_STATE, индекс, checklists и cleanup dry-run созданы | обновить устаревшие статусы; создать отсутствующий `repository_inventory.md`; формализовать актуальный baseline |
| 10 | Agent tooling / CI / QA / review | `partial` | retrieval-first, Hermes, QA matrix/checklists, validators и два QA-цикла применены | единый runner, CI/release blocking, module prompt template, итоговый named report, контроль Git/evidence retention |
| 1 | Graphics / atlas / asset pipeline | `partial` | inventory, alpha/meta/reference validators, draft atlas policy, skin contact sheets | final atlas manifest, Cocos atlas/bundle integration, import/quarantine rules, contact sheets всех групп, draw-call/load/memory baseline |
| 3 | Skins / bonuses / animation | `partial` | 576/576 static matrix, 8 contact sheets, selected emulator QA, текущие визуальные дефекты закрыты | отдельные SkinRegistry/BonusVisualResolver, полный runtime matrix, bundle lifecycle, удаление старого visual stack после миграции |
| 2 | UI/UX design system | `partial` | 14/14 UI IR экранов и полный Web/Android visual QA | shared theme components/tokens, 9-slice policy в runtime, SafeArea/Layout migration, prefab/declarative rebuild, уменьшение screen-specific logic |
| 9 | Android/Web release/performance | `partial`, `blocked_release` | Web/Android QA harness, matrix, restart, soak, hashes, старый device-valid APK | content version gate, свежий arm64 release, production signing, AAB plan/build, актуальный Pages sync/push, release reports/vitals plan |
| 4 | Gameplay core/state machines | `partial` | в GameRoot есть State/FsmMode, RunnerGameState, transition logging и прошедшие input/restart тесты | отдельные state/input/collision/power-up routers, формальная transition schema, lifecycle reports, разгрузка монолита |
| 5 | Levels/backgrounds/content | `partial` | 15 уровней/фонов и визуальный QA проходят | `level_content_manifest.json`, data ownership уровней, layer/platform/obstacle/density/progression contracts, content reports и streaming policy |
| 7 | Audio/VFX/feedback | `partial` | audio manifest, playback/settings/unlock logic существуют и smoke не выявил ошибок | event maps, пять buses, cooldown/priority, VFX router/budget/pooling, module reports |
| 8 | Save/achievements/records/telemetry | `partial` | имя, достижения и рекорды существуют; name cold-start persistence подтверждён | versioned save schema, profile scope, manifests, migrations/corrupt recovery, privacy-safe telemetry/export/rotation, reports |
| 6 | PCG/difficulty validation | `not_started` | имеются текущие difficulty/random helpers, но не модульный validator pipeline | segment schema, offline/runtime validators, seed logging, invalid-segment gate, feature-flagged DDA после telemetry, fuzz/reporting |

## 6. Полный реестр ещё не реализованных пунктов

### P0-A — закрытие релизной линии (Module 9)

- [ ] Ввести единый `content_manifest_version` для Web и Android.
- [ ] Блокировать release при несовпадении версии/контента.
- [ ] Создать воспроизводимый build matrix: Web, Android emulator debug, Android arm release, AAB при выбранной store-цели.
- [ ] Проверять количество файлов, обязательные config aliases и runtime payload автоматически.
- [ ] Пересобрать device-valid arm64 APK из текущего дерева после freeze/commit.
- [ ] Настроить отдельный production keystore/signing policy; не выдавать Cocos/debug signed APK за store production.
- [ ] Создать AAB plan и, если Play является целью, валидный AAB.
- [ ] Выполнить финальный emulator release regression; физическое устройство использовать только по отдельному разрешению пользователя.
- [ ] Синхронизировать актуальный `build/web-mobile` во вложенный Pages repo, повторить smoke, commit и push.
- [ ] Создать `release_build_report.md`, `android_device_qa_report.md`, `performance_baseline.md` и Android vitals plan.
- [ ] Зафиксировать SHA-256, ABI, signing identity, versionCode/versionName и content version в release summary.

Критерий закрытия: текущие Web и Android release-артефакты строятся из одного зафиксированного commit/content version, проходят обязательные gates и воспроизводятся штатной командой.

### P0-B — Git, документация и автоматический gate (Modules 0/10)

- [ ] Создать/актуализировать `repository_inventory.md`.
- [ ] Обновить `CURRENT_STATE.md`, `module_execution_index.md`, UI reports и code review report до состояния 14 июля.
- [ ] Разделить основной source commit и отдельный Pages commit; не staging вложенного repo из родительского root.
- [ ] Решить Git-топологию `_github`: документированный независимый repo либо корректный submodule, но не текущее промежуточное состояние.
- [ ] Добавить project-local module prompt template/START_FROM_HERE для Tasks/4.
- [ ] Объединить validators и QA gates в один воспроизводимый runner с машинным итогом.
- [ ] Добавить CI workflow либо эквивалентный обязательный локальный release gate.
- [ ] Блокировать релиз при неполных QA/code-review/hygiene результатах.
- [ ] Создать требуемый `docs/global_modernization/final_qa_report.md` как индекс принятого evidence, без копирования тяжёлых логов.
- [ ] Ввести retention policy для `output/`, устаревших сборок и superseded evidence с dry-run/path guards.

Критерий закрытия: любой внешний аудитор восстанавливает exact source/build/evidence state из commit и одного current-state индекса без ручного поиска по истории.

### P0-C — графический и atlas pipeline (Module 1)

- [ ] Перевести `atlas_manifest.draft.json` в валидируемый final `atlas_manifest.json`.
- [ ] Добавить обязательные поля owner, usage scope, bundle, compression, padding и fallback policy.
- [ ] Расширить import validator на trim margins, naming, bundle placement, provenance и quarantine.
- [ ] Создать contact sheets для HUD, menu, runner core, bonuses, obstacles, backgrounds и VFX; сейчас полноценно закрыты только player skins.
- [ ] Реально настроить статические co-visibility atlas groups в Cocos и мигрировать по одной группе.
- [ ] Ограничить dynamic atlas измеряемыми малыми UI-фрагментами.
- [ ] Измерить draw calls, atlas waste, bundle load time и memory до/после.
- [ ] Проверять новый pack до попадания в runtime resources и создавать art integration report.

Критерий закрытия: каждый runtime asset принадлежит утверждённому manifest/atlas/bundle контракту, ссылки не теряются, а экономия подтверждена Web/Android метриками.

### P0-D — UI architecture completion (Module 2)

- [ ] Вынести общие theme tokens: colors, fonts, button/panel/icon families.
- [ ] Перевести масштабируемые panels/buttons/cards на 9-slice там, где это не искажает стиль.
- [ ] Ввести SafeArea roots для HUD и меню.
- [ ] Заменить ручные card-grid координаты на Layout containers.
- [ ] Создать reusable components/prefabs или декларативный renderer, который реально потребляет UI IR.
- [ ] Убрать дублированную screen-specific style/layout логику после поэкранного QA.
- [ ] Сохранить 14/14 visual matrix как обязательный regression gate.

Критерий закрытия: все экраны используют общий responsive contract и не зависят от ручной разметки внутри 5428-строчного `GameRoot.ts`.

### P0-E — skin/bonus runtime architecture (Module 3)

- [ ] Вынести `SkinRegistry` и `BonusVisualResolver` из монолита.
- [ ] Провести через resolver все base/bonus/equipment paths; запретить обходные visual nodes вне разрешённого VFX.
- [ ] Сделать полный runtime skin × pose × bonus matrix, а не только 576 static checks и выбранные runtime cases.
- [ ] Проверить switch/expire/death/retry/level-transition cleanup для каждого варианта.
- [ ] Загружать выбранный skin/bundle, а не весь optional pack; безопасно освобождать неиспользуемые bundle.
- [ ] Удалить старый visual stack только после полного parity gate и cleanup dry-run.

Критерий закрытия: один manifest-driven resolver управляет всеми 576 комбинациями, а fallback не скрывает отсутствующий asset.

### P0-F — gameplay core decomposition (Module 4)

- [ ] Определить `player_state_machine.yaml` и допустимые переходы.
- [ ] Формализовать GameSessionState: menu/loading/countdown/playing/paused/failed/completed.
- [ ] Вынести jump/glide/dash/pause в единый input action router.
- [ ] Вынести pickup/obstacle/platform/trigger/finish в collision router.
- [ ] Вынести spawn/collect/activate/tick/expire/cleanup в power-up lifecycle.
- [ ] Сделать детерминированный bounded dev event log.
- [ ] Убрать UI/skin coupling с физикой и гарантировать очистку timers/state при reset/transition.
- [ ] Создать `gameplay_state_report.md` и `powerup_lifecycle_report.md`.

Критерий закрытия: gameplay transitions и effects проходят через явные routers/contracts, а `GameRoot.ts` больше не является владельцем всех подсистем.

### P1-A — level content pipeline (Module 5)

- [ ] Создать `level_content_manifest.json` для всех 15 уровней.
- [ ] Привязать bg_far/bg_mid/bg_near/track/fog/start-mid-end props.
- [ ] Привязать platform variants, obstacle pools, color grade и collectible density.
- [ ] Добавить progression markers и readability budget активной полосы.
- [ ] Мигрировать сначала уровни 1/8/15, затем 2–5, 6–10 и 11–15.
- [ ] Ввести current/next preload и release previous bundle policy.
- [ ] Измерить overdraw, background size и Web/APK impact.
- [ ] Создать `level_manifest_report.md` и `visual_readability_report.md`.

Критерий закрытия: вся визуальная идентичность уровня принадлежит одному manifest, а в gameplay нет hardcoded level-art paths.

### P1-B — audio/VFX/feedback routing (Module 7)

- [ ] Создать `audio_event_map.json` и `vfx_event_map.json`.
- [ ] Ввести buses: UI, SFX, MonkeyVoice, Ambience, Music.
- [ ] Добавить cooldown, priority и simultaneous-voice limits.
- [ ] Перевести VFX/audio вызовы на event router.
- [ ] Ввести visual feedback budget для magnet/shield/hit/dash/collect.
- [ ] Добавить pooling и bounded particle lifecycle.
- [ ] Проверить persistence всех bus settings и Web first-tap unlock.
- [ ] Создать `audio_vfx_inventory.md` и `feedback_qa_report.md`.

Критерий закрытия: нет прямых разрозненных playback/VFX вызовов, спама или неконтролируемых эффектов; настройки управляют всеми buses.

### P1-C — save/achievements/records/telemetry (Module 8)

- [ ] Ввести `save_schema_version`.
- [ ] Ввести стабильный `profile_id` и nickname scoping.
- [ ] Создать `achievement_manifest.json` и `record_manifest.json`.
- [ ] Создать миграцию прежнего save с dev backup и отчётом.
- [ ] Добавить corrupt-save recovery tests.
- [ ] Разделить persistence/data logic и UI rendering.
- [ ] Собирать bounded local QA telemetry: level/skin/bonus/deaths/completions/collectibles/performance.
- [ ] Добавить anonymized local export, rotation и явную privacy policy; никакой отправки без отдельного решения.
- [ ] Создать `save_migration_report.md` и `achievements_records_report.md`.

Критерий закрытия: данные версионированы, мигрируют, изолированы по профилю и восстанавливаются после повреждения без скрытой сетевой телеметрии.

### P1-D — PCG/difficulty validation (Module 6, выполнять последним)

- [ ] Определить segment schema: lane, obstacles, pickups, gaps, timing windows.
- [ ] Реализовать offline reachability/fairness validator.
- [ ] Прогнать его на существующих handcrafted segments.
- [ ] Для будущей генерации логировать seed и параметры, блокировать invalid segments.
- [ ] Добавить ahead-of-player runtime validator только после измерения стоимости.
- [ ] Оставить heuristic DDA выключенным feature flag до появления telemetry и `experiment_id`.
- [ ] Выполнить 1000-seed fuzz и пятиминутный telemetry run.
- [ ] Создать `pcg_validation_report.md` и `difficulty_telemetry_report.md`.

Критерий закрытия: каждый generated segment воспроизводим и валиден; DDA ограничен, логируется и не меняет core rules скрытно.

## 7. Рекомендуемый порядок следующей реализации

1. Зафиксировать source/evidence baseline и обновить устаревшие current-state документы.
2. Закрыть Module 9: content version, актуальные Web/arm64 release artifacts, signing, Pages sync и release reports.
3. Закрыть Module 10: единый runner, release gate, Git topology и CI/локальный обязательный эквивалент.
4. Выполнить Module 4 router wrapper без переписывания gameplay целиком.
5. Завершить Module 1 и Module 3 manifest/registry/bundle pipeline.
6. Завершить Module 2 declarative/responsive extraction малыми экранами.
7. Выполнить Module 5, затем Module 7, затем Module 8.
8. Module 6 запускать последним, только после telemetry contracts.

Каждый пункт должен выполняться отдельным safe-patch циклом: bounded retrieval → mini-plan → минимальный patch → static gates → Web QA → Android emulator QA → code review → hygiene → отчёт/checkpoint. Повторять два полных дорогих цикла без изменения продукта не требуется.

## 8. Основные риски внешнего аудита

1. **Нет воспроизводимого source anchor.** Рабочая линия подтверждена QA, но не зафиксирована commit.
2. **Релизные артефакты расходятся с исходниками.** Актуален только emulator APK; device APK старее текущих правок.
3. **Web publish drift.** Pages HEAD clean, но его runtime дерево отличается от текущего Web build.
4. **Документационный drift.** Индекс модулей и CURRENT_STATE отстают от live tree.
5. **Монолит.** `assets/scripts/GameRoot.ts` содержит 5428 строк и остаётся владельцем UI, gameplay, persistence, audio, assets и QA routes.
6. **Git topology.** Вложенный Pages repo не оформлен как submodule, основной root не имеет remote.
7. **Release signing.** Технически валидная подпись не равна production signing policy.
8. **Evidence volume.** Полезные доказательства необходимо индексировать и ротировать, не удаляя release/audit anchors.

## 9. Что было проверено в этом статус-аудите

- retrieval-first поиск по проектной локальной индексации;
- Skill Compass как advisory router; нерелевантная низкоуверенная рекомендация не применялась;
- Hermes latest checkpoint и project memory;
- Tasks/4 master plan и 10 module specs;
- живые `CURRENT_STATE`, module reports, manifests и required-report presence;
- `GameRoot.ts` line/architecture inventory;
- основной `git status`, `git diff --stat`, `git diff --check`;
- вложенный Pages repo branch/HEAD/status/remote и `git ls-remote`;
- полное хеш-сравнение текущего Web build с Pages tree;
- SHA-256 Android/Web QA artifacts и parse финальных evidence JSON;
- наличие APK/AAB output и release reports.

Новые runtime/build тесты в этой read-only проверке не запускались: после принятого двухциклового QA продуктовые файлы не менялись. Доказательства QA проверены на наличие, JSON parse и SHA-256; единственное новое изменение — этот отчёт.

## 10. Точка остановки

Следующее безопасное действие после внешнего аудита:

```text
P0 release/source freeze:
1. review this report and the 20260714 two-cycle control log;
2. reconcile stale current-state documents;
3. review and commit the intended source/tool/evidence set;
4. add content manifest versioning;
5. build and validate current Web + device-valid arm64 release from that exact commit;
6. sync and push Pages from the nested repo only;
7. write release reports and checkpoint.
```

До выполнения этих пунктов корректная формулировка статуса: **локальная продуктовая линия работает и прошла QA; внешний релиз и полная Tasks/4 модернизация не завершены**.
