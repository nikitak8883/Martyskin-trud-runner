# M01.1 — инвентарь quality gates и harnesses

Дата: 2026-07-19  
Статус: `PASS / M01.1 COMPLETE / M01.2 READY`  
Снимок инструментов: `e60ab6f489793f8b66de5f32601122723aba82aa`  
Frozen source anchor: `12670452ae4580ef5c685ff986476daf91522978`

## Результат

Все `32/32` tracked исполняемых файла под `tools/` перечислены и сопоставлены с их фактическими входами, побочными эффектами, timeout-политикой, outputs, exit semantics, evidence contract и сохраняемой командой. Полный машинный реестр находится в `quality_gate_inventory.json`.

M01.1 не изменял runtime, assets, native-код, build outputs или Pages. Cocos build, браузерный runtime, Android emulator и физическое устройство не запускались. Повторно исполнены только не-мутирующие статические проверки.

Текущая система качества фрагментирована: полезные валидаторы и QA-harnesses есть, но общего fail-closed runner, единого schema namespace, freshness-проверки и CI/local parity пока нет. Поэтому M01.1 завершает инвентаризацию, но не снимает release block.

## Сводка классификации

| Класс | Количество | Роль в будущем gate |
| --- | ---: | --- |
| Fail-closed validators | 7 | сохранить; вызывать typed runner'ом с обязательными strict flags |
| Conditional validator | 1 | сохранить; запретить нестрогий вызов в gate |
| Runtime QA harnesses | 5 | сохранить; добавить внешний timeout, source identity и schema validation |
| Build/process infrastructure | 3 | сохранить как инфраструктуру, не как самостоятельное доказательство качества |
| Diagnostics/evidence generators | 6 | не принимать как PASS без семантического wrapper'а |
| Producers/mutators | 10 | исключить из обязательного quality profile |
| **Всего** | **32** | покрытие `32/32` |

Дополнительные поверхности: `build-web-mobile.json`, `build-android.json`, `build-android-emulator.json`. В `package.json` отсутствуют scripts и dependencies; `.github/workflows` отсутствует; Playwright локально не закреплён lockfile'ом.

## Валидаторы

| Tool | Входы | Побочные эффекты | Timeout | Evidence / exit | Решение |
| --- | --- | --- | --- | --- | --- |
| `tools/validate-mtr-config.ps1` | project root, `GameRoot.ts`, config/assets, Android bridge | нет | отсутствует | stdout; exit 1 при накопленных ошибках | сохранить; позже дать JSON-adapter и timeout |
| `tools/validate-assets.py` | resources и пять manifest families, strict flags | только optional JSON report | отсутствует | `mtr.asset_validation.v1`; blockerCount управляет exit | сохранить; gate всегда использует `--fail-on-white-matte` |
| `tools/validate-skin-bonus-matrix.py` | skin manifest/resources/frame size | только optional JSON report | отсутствует | `mtr.skin_bonus_matrix_validation.v1`; warnings падают только с flag | сохранить; gate всегда использует `--fail-on-warnings` |
| `tools/validate-ui-ir.py` | 14 UI IR, UI skin manifest, resources | только optional JSON report | отсутствует | `mtr.ui_ir_validation.v1`; problemCount управляет exit | сохранить; runtime/visual QA остаётся отдельным gate |
| `tools/ui/generate_level_select_theme_icons.py --verify-only` | существующие icon PNG/meta | в verify-only нет | отсутствует | assertion/exit; проверяет 15 RGBA8 пар | сохранить только verify-only; generation mode исключить |
| `tools/Test-MtrEntrypoint.ps1` | project root, owned log path | test log и собственный temp с cleanup | bounded внутри router | `passed=true`; exit 1 при fail | сохранить как self-test process layer |
| `tools/codex/Test-MtrGitTopology.ps1` | parent root, canonical child path, URL | optional JSON report, Git subprocesses | отсутствует | schema v1; `pass=false` → exit 1 | сохранить; нормализовать path в M01.3 |
| `tools/codex/Test-MtrAndroidToolchain.ps1` | SDK/Gradle/AVD и policy flags | logs/status; optional emulator launch | boot default 300 s | status schema v2; fail закрыт только с `-FailOnNotReady` | conditional validator; strict flag обязателен |

### Проверенный path-contract Git topology

Эквивалентный Windows-вызов с `-ChildRelative "_github\Martyskin-trud-runner"` дал false failure из-за текстового сравнения с `.gitmodules`. Канонический и повторно прошедший вариант:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\codex\Test-MtrGitTopology.ps1 `
  -Root "C:\Projects\Monkey Work" `
  -ChildRelative "_github/Martyskin-trud-runner" `
  -ExpectedUrl "https://github.com/nikitak8883/Martyskin-trud-runner.git"
```

Это harness defect, а не дефект текущей topology: parent gitlink и clean Pages HEAD совпали на `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`.

## Runtime QA harnesses

| Tool | Побочные эффекты | Timeout | Evidence / exit | Решение |
| --- | --- | --- | --- | --- |
| `tools/codex/Run-MtrAndroidEmulatorMatrixQa.ps1` | 28 запусков приложения, logcat, screenshots | marker waits bounded; `adb` process unbounded | `mtr.android_emulator_matrix.v1`; любой case fail → exit 1 | сохранить; обернуть per-process timeout и freshness |
| `tools/codex/Run-MtrAndroidEmulatorInteractionQa.ps1` | taps/text, restart loop, soak, screenshots/XML/logs/metrics | marker/soak bounded; `adb` process unbounded | `mtr.android_emulator_interaction.v1`; overall fail throws | сохранить; обернуть per-process timeout и freshness |
| `tools/codex/run_web_playwright_function.js` | Chromium, output directories, summary JSON | navigation 30 s; outer function unbounded | распознаёт matrix/soak и выставляет exit 1 | сохранить, но сейчас blocked до pinned Playwright runtime |
| `tools/codex/web_matrix_playwright_function.js` | UI navigation/interactions/restarts/screenshots/localStorage | локальные waits bounded; global timeout отсутствует | возвращает `mtr.web_matrix_interaction.v1` | запускать только через строгий runner |
| `tools/codex/web_soak_playwright_function.js` | минимум 30/default 300 s input soak, screenshots, browser state | локальные waits bounded; global timeout отсутствует | возвращает `mtr.web_soak.v1` | запускать только через строгий runner |

Оба Android harness'а явно запрещают не-emulator serial. Это сохраняется как глобальный default. Физический телефон в M01.1 не использовался.

## Инфраструктурные harnesses

| Tool | Роль | Риск/ограничение | Решение |
| --- | --- | --- | --- |
| `tools/codex/MtrEntrypoint.psm1` | typed argument arrays, process-tree timeout, redacted JSONL, stdout/stderr | семантический PASS остаётся обязанностью caller | сохранить как основу M01.3 |
| `tools/Run-MtrCocosBuild.ps1` | Cocos build, Web postprocess, Android Gradle/payload verification | меняет `build/`; build success не равен full QA | сохранить, не включать в D4 и не принимать отдельно |
| `tools/Start-MtrWebServer.ps1` | локальный Python HTTP server | default `StopExisting=true` может убить чужой listener | сохранить; будущий runner использует reserved port + ownership token |

## Diagnostics и evidence generators

| Tool | Output | Почему не самостоятельный PASS |
| --- | --- | --- |
| `tools/codex/build_source_content_manifest.py` | deterministic source fingerprint v1 | требует независимого SHA/commit/gitlink check; Git calls не все bounded |
| `tools/mtr_cleanup_audit.py` | dry-run candidate JSON | всегда exit 0 независимо от candidates |
| `tools/render-skin-contact-sheets.py` | PNG/HTML/JSON visual evidence | evidence требует validator/runtime pair; source identity отсутствует |
| `tools/skins/inspect_skin_pngs.py` | alpha/quarantine/mapping/safety reports | risks и checksum mismatch не меняют exit 0 |
| `tools/web-cdp-smoke.ps1` | screenshot, console/events, probe stdout | `runtimeReady=false` может завершиться exit 0 |
| `tools/web-chrome-runtime-smoke.ps1` | probe JSON, screenshot, console/browser logs | `runtimeReady=false` или marker miss может завершиться exit 0 |

PowerShell Web probes сохраняются как низкоуровневые collectors. До появления strict adapter их отчёты нельзя использовать для green release claim.

## Producers и mutators, исключённые из gate

| Tool | Основные изменения | Критичное ограничение |
| --- | --- | --- |
| `tools/asset_generation/build-martyshkin-backgrounds.ps1` | делегирует runtime background generation | report warnings не обязательно дают non-zero |
| `tools/asset_generation/build-martyshkin-main-menu-background.ps1` | делегирует menu PNG/meta generation | legacy `C:\Test` default; нет явной проверки native exit |
| `tools/asset_generation/build_martyshkin_main_menu_background.py` | menu PNG/meta + QA report/contact sheet | нет dry-run/CLI root |
| `tools/asset_generation/build_martyshkin_texture10_backgrounds.py` | 15 backgrounds/previews/manifests/evidence | `report.passed=false` из-за warnings всё равно exit 0 |
| `tools/asset_generation/build_martyshkin_ui_system.py` | shared UI PNG family | нет manifest/report/dry-run |
| `tools/mtr_last_iteration_asset_pipeline.py` | сотни runtime sprites/meta/config/generated TS | `--clean` рекурсивно удаляет предыдущую generated family |
| `tools/prepare_portable_transfer.py` | ZIP/manifests/checksums/environment report | packaging producer, не source/release validator |
| `tools/repair-web-mobile-settings.ps1` | in-place rewrite build settings | legacy `C:\Test` default; non-atomic |
| `tools/scan_and_fix_white_matte_edges.py` | report/contact sheet; optional in-place PNG fixes | suspects не меняют exit; mutation flags запрещены в gate |
| `tools/skins/integrate_skin_pack.py` | 576 runtime frames/meta/manifests/reports | `ok=true` подтверждает генерацию, а не visual/runtime QA |

## Обязательные исправления следующих work packages

### M01.2 — schemas

1. Зафиксировать namespace/version для каждого принимаемого JSON.
2. Добавить adapters для текущих v1/v2 форматов без переписывания работающих validators.
3. Добавить positive и negative fixtures, включая false-green Web probe и Android toolchain без strict flag.
4. Включить `source_commit`, logical `content_version`, target identity, started/finished time и tool SHA.

### M01.3 — typed runner

1. Аргументы только массивами; никаких shell-composed commands.
2. Per-process timeout и process-tree cleanup для `adb`, Git, Node, Cocos и browser.
3. Path containment, reserved-port ownership и owned-profile cleanup.
4. Atomic report write (`temp + fsync/close + replace`) и schema validation до PASS.
5. Обязательные strict flags: asset white matte, skin warnings, Android toolchain readiness, icon verify-only.
6. Нормализация эквивалентных path forms до сравнения.

### M01.4+ — profile/evidence policy

- mandatory/optional/not-applicable semantics;
- stale, missing, skipped и unknown schema всегда блокируют обязательный profile;
- D4 не запускает producers/build/runtime;
- P4/QA7 явно привязывают build/runtime evidence к source/content anchor;
- retention начинает с index-first dry-run и не затрагивает protected anchors.

## Сохранённые команды

Статические команды, повторно прошедшие в M01.1:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1 -ProjectRoot .
node "C:\ProgramData\cocos\editors\Creator\3.8.8\resources\app.asar.unpacked\node_modules\typescript\lib\tsc.js" -p tsconfig.json --noEmit --skipLibCheck --lib es2020,dom --isolatedModules false
python .\tools\validate-assets.py --project-root . --fail-on-white-matte
python .\tools\validate-skin-bonus-matrix.py --project-root . --fail-on-warnings
python .\tools\validate-ui-ir.py --project-root .
python .\tools\ui\generate_level_select_theme_icons.py --verify-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Test-MtrEntrypoint.ps1 -ProjectRoot . -LogPath <owned-temp-log>
```

Сборочные и runtime-команды сохранены в `quality_gate_inventory.json` со статусом `preserved_historical_not_run` или `blocked_unpinned_dependency`; M01.1 не переименовывает их в «проверенные».

## M01.1 D4 evidence

| Проверка | Результат |
| --- | --- |
| Project config | PASS — 15 levels/backgrounds, required configs/assets and Android/Web query parity |
| Cocos-compatible TypeScript | PASS |
| Asset validator strict | PASS — 1528 PNG, 0 blockers, 0 white-matte suspects |
| Skin/bonus matrix strict | PASS — 576/576, 0 blockers, 0 warnings |
| UI IR | PASS — 14/14 screens, 0 problems, 0 warnings |
| Level-select icon verify-only | PASS — 15 PNG + 15 meta, 128×128 RGBA8 |
| Entrypoint quoting self-test | PASS |
| Git topology canonical path | PASS — parent gitlink equals clean Pages HEAD |

## Exit и следующий шаг

M01.1 выполнен: покрытие полное, работающие validators сохранены, опасные/false-green поверхности не замаскированы. Следующий bounded work package — `M01.2`: schema compatibility matrix, adapters и positive/negative fixtures. Runtime-код по-прежнему не разрешён этим переходом.
