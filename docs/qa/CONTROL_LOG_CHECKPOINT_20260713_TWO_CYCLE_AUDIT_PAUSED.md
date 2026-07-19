# Контрольный лог и точка возобновления — два цикла аудита/QA

- Время фиксации: `2026-07-13T13:48:31+03:00`
- Проект: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`
- Git: ветка `main`, базовый HEAD `76bac6c`, рабочее дерево уже было и остаётся незакоммиченным
- Статус: `PAUSED_BY_USER_AFTER_CYCLE1_WEB_VISUAL_FIX`
- Важно: запрос на **два полных цикла** ещё не завершён. Нельзя считать этот чекпоинт финальным QA-разрешением.

## Точная точка остановки

Завершена статическая и визуальная Web-часть первого цикла. Проверены 14 UI-контрактов, 13 детерминированных UI-маршрутов, шесть соотношений сторон и все 15 уровней. Последним действием исправлена белая внутренняя подложка двух платформ уровня 14 и выполнена узкая повторная Web-проверка.

Запущенные для QA браузеры и Web-сервер остановлены. Android-эмулятор не запускался, физические устройства не использовались.

## Исправления первого цикла

1. Добавлены детерминированные QA-маршруты и UI IR для `clear`, `over`, `finished`; минимальная высота шести финальных кнопок доведена до `64 px`.
2. Холодный старт меню сделал UI-gate зависимым от конкретного экрана, чтобы `name`, `clear` и `finished` не считались готовыми только по ресурсам главного меню.
3. Ложные предупреждения о пропавшем скине теперь выдаются только после доказанной ошибки загрузки, а не во время ожидающей асинхронной загрузки.
4. Добавлены симметричные Web/Android QA query-параметры `mtr_qa_obstacles` и `mtr_spawn_obstacles`; валидатор проверяет полный набор native/runtime entrypoints.
5. Web-разрешение стало адаптивным: для окон уже `16:9` применяется `SHOW_ALL`, для широких Web-окон и native Android сохраняется `FIXED_HEIGHT`. Resize обрабатывается без рекурсивного события.
6. Из `GameRoot.ts` удалены три доказанно неиспользуемых helper-фрагмента старого тематического UI.
7. Исправлены внутренние белые matte-области в:
   - `mtr_last_logistics_extended_platforms_001.png`: удалено `2` компонента / `2 206` пикселей;
   - `mtr_last_logistics_extended_platforms_003.png`: удалено `15` компонентов / `7 221` пиксель.
8. В `scan_and_fix_white_matte_edges.py` добавлен безопасный opt-in детектор внутренних нейтрально-белых matte-компонентов. Он не правит весь арт автоматически и требует явного списка файлов, чтобы не удалить бумагу, вывески и блики.

## Пройденные проверки

### Статика

- Assets: `1528 PNG`, `0 decode errors`, `0 missing meta`, `0 oversize`, `0 white-matte edge suspects`, `0 blockers`.
- UI IR: `14/14` экранов, `209` узлов, `75` кнопок, `29` runtime literal buttons, `0 problems`, `0 warnings`.
- Конфигурация: `15` уровней, `15` bitmap-фонов, полная Web/Android QA query parity.
- `git diff --check`: `PASS` для затронутого кода и контрактов.
- Финальная Web-сборка: `PASS`, success marker найден, favicon post-process `PASS`.

### Web runtime

- UI-маршруты: `menu`, `name`, `levels`, `skins`, `sound`, `records`, `achievements`, `devgate`, `devpanel`, `paused`, `clear`, `over`, `finished`.
- Матрица: `1920x1080`, `1280x720`, `844x422`, `915x422`, `1024x768`, `390x844`.
- Портрет: полный кадр с letterbox; реальное касание кнопки `НАЧАТЬ ИГРУ` успешно открыло экран ввода имени.
- Уровни: отдельные свежие маршруты `1..15` с `mtr_qa_obstacles=1` и `mtr_qa_bonuses=1`; визуально просмотрен каждый снимок.
- Агрегированные Playwright-сессии: `0 errors`, `0 warnings`.
- После matte-патча уровень 14 пересобран и проверен повторно; отверстия паллеты и верёвочной сетки показывают фон, белых заливок нет.

## Ключевые доказательства

- `docs/qa/evidence/20260713_two_cycle_audit/cycle1_assets_after_enclosed_matte_fix.json`
- `docs/qa/evidence/20260713_two_cycle_audit/cycle1_ui_ir_stop_checkpoint.json`
- `docs/qa/evidence/20260713_two_cycle_audit/cycle1_enclosed_white_matte_before_fix.json`
- `docs/qa/evidence/20260713_two_cycle_audit/cycle1_enclosed_white_matte_fix.json`
- `docs/qa/evidence/20260713_two_cycle_audit/cycle1_enclosed_white_matte_postcheck.json`
- `logs/creator-two-cycle-audit-cycle1-web-enclosed-matte-final-20260713.log`
- `output/playwright/cycle1/cycle1_level_01.png` … `cycle1_level_15.png`
- `output/playwright/cycle1/cycle1_level_14_after_enclosed_matte_fix.png`
- `output/playwright/cycle1/cycle1_responsive_after_fix_portrait_390x844.png`
- `output/playwright/cycle1/cycle1_responsive_portrait_touch_after_start.png`

Итоговые SHA-256 исправленных PNG:

- pallet: `8CD1C6E8C9A710511ED577733CA0A728D51B6DA132628C0F6ED81730BFD27A75`
- rope net: `8F3E7766D686F12DF71024E1CF66CEEB31CE9C6BADED79EB0CB95F5AA74ED389`

## Что остаётся выполнить

1. Завершить первый цикл Web gameplay QA: jump/dash/pause input, повторные рестарты и длительный soak/performance run.
2. Собрать `build-android-emulator.json` и выполнить **только на виртуальном эмуляторе** полный Android-прогон:
   - все 13 UI-маршрутов;
   - все 15 уровней;
   - препятствия/бонусы, управление, рестарты и soak;
   - screenshots + logcat + проверка `FATAL EXCEPTION`, `ANR`, JS errors и обязательных `MTR_*` markers.
3. Выполнить второй независимый цикл: повтор всех статических gates, новая Web/Android сборка, все маршруты и 15 уровней, повторный визуальный/code-review.
4. После второго цикла провести окончательный hygiene gate, обновить сводные отчёты и только затем выставлять итоговый статус.

## Команды возобновления

Рабочая папка:

```powershell
Set-Location "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator"
```

Старт Web-сервера на выделенном QA-порту:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Start-MtrWebServer.ps1 `
  -Root (Resolve-Path build\web-mobile).Path `
  -Port 9490 `
  -StdoutPath docs\qa\evidence\20260713_two_cycle_audit\resume_web_server.out.log `
  -StderrPath docs\qa\evidence\20260713_two_cycle_audit\resume_web_server.err.log `
  -StatusPath docs\qa\evidence\20260713_two_cycle_audit\resume_web_server_status.json
```

Android emulator build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Run-MtrCocosBuild.ps1 `
  -ConfigPath .\build-android-emulator.json `
  -LogDest .\logs\creator-two-cycle-audit-cycle1-android-emulator-20260713.log
```

Перед продолжением сначала перечитать этот файл и проверить live tree; не восстанавливать состояние по множеству старых чекпоинтов.

## Состояние процессов при остановке

- Playwright sessions: `none`
- TCP `127.0.0.1:9490`: `not listening`
- ADB devices/emulators: `none`
- `tools/__pycache__`: удалён
- Git commit/push: не выполнялись
- Hermes context checkpoint: `id=653`, trigger `manual_user_pause_after_cycle1_web_fix`
- Hermes project memory pointer: `id=8`, stable id `2c6023e969699d775dafaba4`
- Hermes project latest: `C:\Users\nikit\.hermes-proagents\checkpoints\by-project\MTRCocosCreator-d20b07d42eaf7ab3\LATEST.md`
- Hermes doctor после записи: `integrity=ok`, `FTS 628/628`, threshold `95%` (`245100 / 258000` tokens)
- Hermes memory doctor: `integrity=ok`, `FTS 8/8`
