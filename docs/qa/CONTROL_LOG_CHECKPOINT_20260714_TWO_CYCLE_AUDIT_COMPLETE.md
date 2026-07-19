# MTR — два полных цикла аудита и QA завершены

Дата завершения: 2026-07-14T18:31:58+03:00  
Проект: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Режим: audit + fix + rebuild + Web/Android runtime QA  
Android-цель: только виртуальный эмулятор `emulator-5554` (`ro.kernel.qemu=1`, x86_64)  
Физические устройства: не использовались и не затрагивались

## Итог

Оба независимых цикла приняты. После исправлений и финального повторного шлюза открытых блокеров, предупреждений продукта или визуальных дефектов не осталось.

| Шлюз | Цикл 1 | Цикл 2 / финал |
|---|---:|---:|
| Строгий project-only TypeScript | PASS | PASS |
| UI IR | PASS | PASS — 14/14 экранов, 209 узлов, 75 кнопок, 0 проблем/предупреждений |
| Скины и бонусы | PASS | PASS — 576/576 кадров, 0 блокеров/предупреждений |
| PNG и метаданные | PASS | PASS — 1 528 PNG, 0 decode errors, 0 missing meta, 0 white-matte suspects |
| Конфигурация и Web/Android contract | PASS | PASS — 15 уровней, 15 фонов, симметричные startup-query keys |
| Web runtime | PASS | PASS — 34/34 матричных кейса, 10/10 рестартов, 300.407 s soak |
| Android runtime | PASS | PASS — 28/28 матричных кейсов, 10/10 рестартов, 300.590 s soak |
| Визуальная инспекция | PASS | PASS — все UI-состояния, уровни, интеракции, рестарты и soak-кадры |
| Code review / hygiene | PASS | PASS — незакрытых замечаний нет |

## Цикл 1

Принятый подробный чекпоинт: `docs/qa/CONTROL_LOG_CHECKPOINT_20260714_TWO_CYCLE_AUDIT_CYCLE1_COMPLETE.md`.

- Web soak: 300.446 s, 39 серий ввода, 3 перехода `clear -> playing`, 0 console errors/warnings.
- Android matrix: 28/28 — 13 UI-состояний и 15 уровней.
- Android touch/FSM: jump, dash, pause, resume — PASS.
- Имя: `QAPrimateC1` сохранено и восстановлено после холодного запуска.
- Android restart: 10/10, 436–479 ms, среднее 449.5 ms.
- Android soak: 300.724 s, 319 серий ввода, 17 state actions, 0 потерь процесса.

## Цикл 2 — Web

Свежая Cocos Web-сборка `build/web-mobile` завершена по success marker и выходному артефакту. Маршрутизатор автоматически исправил форму Windows command line; post-process favicon завершён успешно.

Матричная проверка:

- evidence: `docs/qa/evidence/20260714_two_cycle_resume/cycle2_web/web_matrix_cycle2_summary.json`;
- 34/34 PASS: 13 UI-маршрутов, 6 viewport-профилей, portrait touch/name flow и все 15 уровней;
- jump, dash, pause, resume — PASS;
- restart loop: 10/10;
- console errors/warnings, page errors, product failures и request failures: 0.

Soak:

- evidence: `docs/qa/evidence/20260714_two_cycle_resume/cycle2_web/web_soak_cycle2_summary.json`;
- 300.407 s, финальное состояние `playing`;
- 39 input bursts, 3 clear clicks;
- FPS min/avg/max: 52.84 / 60.19 / 61.43;
- 10 heap-сэмплов по 33 100 000 bytes, признака роста нет;
- console errors/warnings: 0.

## Цикл 2 — Android emulator

Сборка и установка:

- APK: `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`;
- размер: 142 881 559 bytes;
- SHA-256: `D2DB02FA9ED21D8628D7B3DE2D8A98E69954F8854156D3CFA6A81CE3D872655F`;
- clean uninstall/install на `emulator-5554`, user 0: PASS;
- install manifest: `docs/qa/evidence/20260714_two_cycle_resume/cycle2_android/install_manifest.json`.

Матрица:

- evidence: `docs/qa/evidence/20260714_two_cycle_resume/cycle2_android_matrix/android_matrix_cycle2_summary.json`;
- 28/28 PASS: 13 UI-состояний и все 15 уровней;
- ожидаемые native-query, menu-gate, gameplay, full-background и asset-usage markers получены;
- fatal/ANR, app deprecations, product warnings, unexpected Cocos errors/warnings: 0.

Интеракции, имя, рестарты и soak:

- evidence: `docs/qa/evidence/20260714_two_cycle_resume/cycle2_android_interaction_soak/android_interaction_cycle2_summary.json`;
- jump/dash/pause/resume: 362 / 362 / 364 / 370 ms;
- `QAPrimateC2` точно сохранено и восстановлено после process-stopped cold restart;
- restart loop: 10/10, 410–445 ms;
- soak: 300.590 s, 339 input bursts, 16 state actions, 0 потерь процесса;
- PSS start/peak/end: 229 734 / 242 329 / 208 609 KiB; монотонной утечки нет;
- fatal/deprecation/product-warning/unexpected-Cocos: 0.

Важно: это x86_64 debug APK для QA в эмуляторе. Он не является финальным arm64 release APK для физического телефона.

## Визуальная инспекция

Web и Android проверены вручную по сохранённым кадрам:

- 13 UI-состояний;
- 6 Web viewport-профилей и portrait name flow;
- 15/15 уровней в каждой среде;
- jump, dash, pause, resume;
- ввод/сохранение/холодное восстановление имени;
- первый и десятый рестарты;
- все периодические и финальные soak-кадры.

Не обнаружено: белых фрагментов вырезки, matte-прямоугольников, пропавших платформ или фонов, старых подфоновых надписей, дублированных onion-слоёв, обрезанного UI или отсутствующих поздних тематических ассетов. На уровне 14 отверстия верёвочной сетки прозрачны.

## Исправления, подтверждённые обоими циклами

- `screen.windowSize` вместо deprecated `view.getFrameSize()`;
- supported outline-поля `Label` вместо deprecated `LabelOutline` component API;
- удалены invalid/no-op свойства `EditBox`;
- исправлена TypeScript control-flow проверка после `startLevel()`;
- UI preload/gate стал screen-aware для menu/name/levels/skins/achievements;
- Web и Android получили симметричные QA startup-query keys;
- end-state, records, obstacle и bonus QA routes стали детерминированными;
- устранён старый тематический UI chrome, создававший лишние слои;
- расширены touch targets без изменения визуального PNG-размера;
- fallback-логирование скинов сообщает ошибку только после фактического load failure;
- white-matte scanner получил opt-in обработку крупных замкнутых нейтрально-белых компонентов.

## Финальный code review и защитные исправления

Просмотрены tracked diff и новые QA/validator scripts. `git diff --check` проходит; сообщения Git относятся только к будущей LF/CRLF нормализации и не являются whitespace errors.

Найден и исправлен один дефект QA-инфраструктуры:

- Android matrix принимал произвольный serial, а interaction harness проверял QEMU после первого обращения к serial;
- теперь оба скрипта отклоняют всё, что не соответствует `^emulator-\d+$`, до первого ADB-вызова;
- после этого отдельно требуют `get-state=device` и `ro.kernel.qemu=1`;
- PowerShell syntax PASS, pre-ADB rejection PASS, живой emulator probe PASS.

Поиск `TODO/FIXME/HACK/XXX/debugger/TEMPORARY` не выявил оставленных хвостов. `console.log` в `GameRoot.ts` проверены вручную: это стабильные `MTR_*` диагностические контракты, используемые QA-матрицами.

Финальный повторный статический шлюз после guard-патча:

- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/ui_ir.json`;
- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/skin_bonus_matrix.json`;
- `docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/assets.json`;
- строгий TypeScript и `tools/validate-mtr-config.ps1`: PASS.

## Журнал сбоев QA-обвязки и предотвращение повторения

Это не продуктовые дефекты:

1. Playwright CLI упёрся в Windows command-line length. Матрица и soak перенесены в файловый runner: `tools/codex/run_web_playwright_function.js`.
2. Headless Chromium выдавал известный `ReadPixels` GPU-driver warning. Он изолирован как известный шум; остальные warnings по-прежнему блокируют PASS.
3. Повторный portrait route не дублировал общий ready-marker, но выдавал screen-specific menu gate. Harness теперь проверяет стабильный screen gate.
4. Headless input не имел canvas focus. Harness теперь явно активирует страницу/canvas и использует реальные key down/up.
5. Одноразовые PowerShell collectors дважды использовали недопустимое прямое `foreach |` и один раз неверно трактовали пустой `pidof`. Финальный шаблон использует `$rows = foreach (...)` и null-safe `(@(...) -join '').Trim()`; reusable Android harness использует `appProcessId`, а не `$pid`.

Неуспешные harness-attempt evidence сохранены только там, где они объясняют коррекцию; superseded калибровочные каталоги удалены.

## Hygiene gate

Безопасно удалены пять однозначно временных/заменённых каталогов:

- `.playwright-cli`;
- `output/qa_harness_cycle2`;
- `output/qa_harness_selftest_android`;
- `docs/qa/evidence/20260714_two_cycle_resume/cycle1_android_interaction_calibration`;
- `docs/qa/evidence/20260714_two_cycle_resume/cycle1_android_name_entry`.

Принятые matrix/interaction/soak evidence и объясняющие failure logs сохранены. Web listener 9491 закрыт; приложение `com.martyskin.trudrunner` остановлено на эмуляторе; сам ранее запущенный эмулятор сохранён. Физические устройства не использовались.

## Hermes recovery state

- автоматический порог: `95%` от лимита `258 000`, то есть checkpoint/compaction при `245 100` токенах и 5% остатка;
- latest context checkpoint: `id 662`, trigger `task-complete:two-cycle-audit-qa-final-log`;
- project `LATEST.md`: `C:\Users\nikit\.hermes-proagents\checkpoints\by-project\MTRCocosCreator-d20b07d42eaf7ab3\LATEST.md`;
- project memory: `id 9`, title `Two-cycle Web and Android emulator QA complete`, содержит точный путь к этому логу;
- context doctor после финального checkpoint и retention: `integrity=ok`, `632` checkpoint rows, `632` FTS rows, FTS consistent;
- memory doctor: `integrity=ok`, `9` memory rows, `9` FTS rows, FTS consistent;
- retention dry-run проверен, затем удалены ровно пять старых безопасных checkpoint pair: ids `603`, `602`, `601`, `597`, `596`;
- последние 12, latest-scope и release/milestone checkpoints защищены; аудит очистки: `C:\Users\nikit\.hermes-proagents\context-prune-audit.jsonl`.

## Git и точка остановки

Рабочее дерево остаётся намеренно dirty и содержит накопленные пользовательские изменения и evidence. Ничего не staged, не committed и не pushed. Чужие/несвязанные изменения не откатывались.

Работа по двум полным циклам аудита и QA завершена. Следующее действие должно начинаться с этого файла и живого `git status`; повторять уже принятые циклы без нового изменения продукта не требуется.
