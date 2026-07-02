# MTR UI De-onion R9 QA — 2026-06-19

## Итог

PASS. Главный экран переделан из многослойного “лука” в единый матовый фон: в runtime оставлен только `main_menu_bg_far.png`, старые подложки/таблички/декор-слои вынесены из `assets/resources` в evidence-архив. Web и Android emulator прошли визуальную проверку.

## Что изменено

- Активный фон `assets/resources/ui/main_menu_background/main_menu_bg_far.png` очищен от baked-readable лозунгов/табличек.
- В `assets/scripts/GameRoot.ts` runtime-отрисовка main menu background сведена к одному far background + haze; старые слои больше не грузятся и не рисуются.
- Legacy-слои архивированы в `docs/qa/evidence/main_menu_legacy_layers_20260619_r9/`.
- Обновлены allowed-assets правила:
  - `docs/UI_ALLOWED_ASSETS.md`
  - `UI_ALLOWED_ASSETS.md`

## Evidence

- Before original with baked text: `docs/qa/evidence/main_menu_bg_far_before_deonion_20260619_r9.png`
- Web main menu: `docs/qa/web_main_menu_deonion_20260619_r9.png`
- Web level select: `docs/qa/web_level_select_deonion_20260619_r9.png`
- Android main menu: `docs/qa/android_main_menu_deonion_20260619_r9.png`
- Android level select: `docs/qa/android_level_select_deonion_20260619_r9.png`
- Web summary: `logs/web-qa-deonion-20260619-r9-summary.json`
- Android summary: `logs/android-qa-deonion-20260619-r9-summary.json`
- Final scan: `logs/qa-deonion-r9-final-scan.json`
- Asset rebuild log: `logs/main-menu-bg-deonion-r9.json`
- Legacy archive log: `logs/main-menu-legacy-layer-archive-r9.json`

## Проверки

- `tools/Test-MtrEntrypoint.ps1`: PASS.
- `tools/validate-mtr-config.ps1`: PASS — 15 levels, 15 bitmap backgrounds, story themes, objective sprites, achievements, Russian labels present.
- Web build: PASS, Cocos `buildFinished=true`.
- Android emulator build: PASS, APK `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`.
- Runtime/source scan: old layer keys have 0 hits in:
  - `assets`
  - `build/web-mobile`
  - `build/android-emulator`

## Визуальная QA

- Main menu: чистый тёмный матовый фон без старых читаемых надписей под PNG-кнопками.
- Level select: уровни 1–15 видны, тематические иконки после уровня 8 присутствуют.
- Старые legacy background layers не видны в web и Android emulator.

## QA-инцидент и предотвращение

Android emulator QA поймал coordinate mismatch между PNG screenshot space и `adb input tap`. Видимый центр кнопки `ВЫБОР УРОВНЯ` при наивных координатах попадал в экран выбора примата. Финальная проверка использовала emulator hit coordinate `1610,740`, после чего экран `ВЫБОР УРОВНЯ` был подтверждён визуально.

Для будущих Android проверок этот случай нужно трактовать как правило QA-маршрутизации: не доверять координате без последующей screenshot-валидации целевого экрана.

## Ограничения

- Физическое Android-устройство не использовалось. По глобальному правилу проекта Android QA выполняется только в эмуляторе, пока пользователь отдельно не попросит physical-device run.
