# MTR repository inventory — 2026-07-19

Статус: `read_only_revalidation_complete`  
Рабочая область: `C:\Projects\Monkey Work`  
Канонический проект: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

## Границы аудита

Инвентаризация выполнена без сборки, запуска Cocos, эмулятора, публикации, commit, push, перемещения ассетов и очистки. Созданы только отчёты и неисполняемая проектная библиотека планирования v3.

Внешний пакет проверен до использования:

- ZIP SHA-256: `85639CC7C93D4C1A2541D47DE5057B62BC6E555053827D72D74CC8F41AA04AA2` — совпадает с приложенным checksum;
- 93 файла, 198 928 распакованных байт;
- опасные пути, case-insensitive дубликаты и выход за корень: `0`;
- внутренний `MANIFEST.json`: 91/91 файлов совпадают по размеру и SHA-256;
- `MANIFEST_SHA256.txt`: 92/92 записей совпадают, включая `MANIFEST.json`.

## Git-топология

| Роль | Корень | Ветка / HEAD | Remote | Состояние |
| --- | --- | --- | --- | --- |
| Основной workspace/source | `C:\Projects\Monkey Work` | `main` / `76bac6c2e9f5e112489aa8a922dce48c3fd9970b` | отсутствует | dirty |
| Pages deployment | `C:\Projects\Monkey Work\_github\Martyskin-trud-runner` | `main` / `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f` | `origin` → `nikitak8883/Martyskin-trud-runner` | clean |

В родительском репозитории путь Pages записан как gitlink mode `160000`, но `.gitmodules` отсутствует. `git submodule status` завершается ошибкой. Это невалидное промежуточное состояние: путь нельзя считать ни корректным submodule, ни обычной папкой.

Полный машинный снимок, включая project-scoped status, находится в `live_git_state.json`.

## Живой source/runtime

- Cocos Creator: проект декларирует `3.8.8`; найден точный executable `C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe`.
- Runtime entry point: `assets/scripts/GameRoot.ts`, 5 428 строк, SHA-256 `22941AA58AF4A27DF103C5339D77D6E1D82028EE932740484CF7002B0EF507A2`.
- Общие данные Android/Web находятся в `assets/resources/config`; проектное правило требует сохранять единую конфигурацию платформ.
- Build profiles: `build-web-mobile.json`, `build-android-emulator.json`, `build-android.json`.
- Android package: `com.martyskin.trudrunner`.
- Android QA profile: x86_64/debug/debug keystore.
- Android device profile: arm64-v8a + armeabi-v7a, `debug: false`, но `useDebugKeystore: true`; фактическая сборка подписана сертификатом CocosCreator.
- `package.json` не содержит npm scripts/dependencies/lockfile. Пример CI из внешнего пакета с `npm ci` и `npx tsc` несовместим без адаптера.

## Уже существующая программа v2

Нельзя обнулять или повторно объявлять незавершёнными уже принятые результаты Tasks/4:

- graphics: reference validator и отчёты присутствуют;
- UI: 14 UI IR документов и выбранная runtime-интеграция присутствуют;
- skins/bonuses: статическая матрица 576/576, contact sheets и выбранный emulator QA присутствуют;
- двухцикловый Web/Android-emulator аудит 14 июля принят;
- модули release, gameplay decomposition, levels ownership, audio/VFX, save/telemetry, PCG остаются незавершёнными.

v3 интегрируется как слой source truth, release recovery, quality gates и уточнённой декомпозиции поверх v2, а не как новая программа с нуля.

## Текущие артефакты

- Web build: 4 814 файлов, 120 420 561 байт.
- Pages source: 4 818 файлов, 120 535 777 байт.
- Паритет Web/Pages: `FAIL` — 1 файл только в build, 5 только в Pages, 5 изменены.
- Emulator APK от 2026-07-14: x86_64, Android Debug signer, SHA-256 `D2DB02FA9ED21D8628D7B3DE2D8A98E69954F8854156D3CFA6A81CE3D872655F`.
- Arm APK от 2026-07-01: arm64-v8a + armeabi-v7a, CocosCreator signer, SHA-256 `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`.
- AAB: отсутствует.
- Ни один текущий артефакт не связан с immutable source commit и embedded content version.

Полный индекс находится в `live_build_artifact_index.json`.

## QA evidence

- 801 файл;
- 1 051 135 677 байт;
- каждый файл проиндексирован по относительному пути, размеру, времени и SHA-256;
- retention policy ещё не применена.

Полный индекс находится в `live_evidence_index.json`. Большой evidence не должен включаться целиком в будущий source commit: коммиту нужны индексы, итоговые отчёты и защищённые release-якоря.

## Классификация будущего checkpoint

### Предложено включить после отдельного review

- runtime source и обязательные `.meta`;
- canonical config/manifests;
- Android native source, относящийся к принятому runtime;
- проверенные validators и QA harnesses;
- канонические lore/AGENTS/docs;
- компактные current-state, module, QA и evidence indexes;
- project-local v2/v3 contracts после plan review.

### Предложено исключить

- `build/`, `library/`, `temp/`, `output/`, `.local_ai_index/`;
- loose root logs;
- APK/AAB/ZIP и другие generated artifacts вне утверждённого release index;
- raw evidence corpus целиком;
- `Tasks/4`, `Tasks/5` и распакованные внешние пакеты;
- secrets, keystores, passwords, `local.properties`;
- содержимое независимого Pages repo из parent staging.

### Требует ручного решения

- Git-топология Pages: корректный submodule, независимый sibling repo либо artifact deployment из будущего source remote;
- конкретный набор protected evidence;
- direct APK versus Google Play/AAB target;
- signing identity и сохранение upgrade compatibility установленного приложения;
- назначение remote для основного source repo.

## Результат

Живое дерево соответствует ключевым фактам отчёта от 14 июля, но source freeze не выполнен. До review состава checkpoint запрещено начинать архитектурную миграцию, release rebuild, Pages sync или cleanup.
