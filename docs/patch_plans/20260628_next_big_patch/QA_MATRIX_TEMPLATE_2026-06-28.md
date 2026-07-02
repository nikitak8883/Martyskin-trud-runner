# QA matrix template — next big patch

Status: template only. Fill during the future audit/implementation pass.

## UI states

| Area | Web local | Android emulator | Evidence | Defects | Pass/Fail |
| --- | --- | --- | --- | --- | --- |
| Main menu |  |  |  |  |  |
| Start/name submenu |  |  |  |  |  |
| Custom name input: focus/keyboard |  |  |  |  |  |
| Custom name input: save/reload |  |  |  |  |  |
| Custom name input: records/achievements linkage |  |  |  |  |  |
| Skin select |  |  |  |  |  |
| Level select |  |  |  |  |  |
| Records |  |  |  |  |  |
| Achievements |  |  |  |  |  |
| Sound settings |  |  |  |  |  |
| Pause |  |  |  |  |  |
| Death/game over |  |  |  |  |  |
| Level clear |  |  |  |  |  |
| Developer gate/panel |  |  |  |  |  |

## Level pass

| Level | Theme | Web screenshots | Android screenshots | Platform status | Skin/bonus status | Log issues | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Стройплощадка примата |  |  |  |  |  |  |
| 2 | Банановая логистика |  |  |  |  |  |  |
| 3 | Отдел бессмысленных заявлений |  |  |  |  |  |  |
| 4 | Джунгли примата |  |  |  |  |  |  |
| 5 | Ферма сверхплана |  |  |  |  |  |  |
| 6 | Павлин-инспектор |  |  |  |  |  |  |
| 7 | Фабрика вечного труда |  |  |  |  |  |  |
| 8 | Архив важности |  |  |  |  |  |  |
| 9 | Банановый реактор |  |  |  |  |  |  |
| 10 | Коридор проверок |  |  |  |  |  |  |
| 11 | Ночная смена |  |  |  |  |  |  |
| 12 | Учебный отдел плана |  |  |  |  |  |  |
| 13 | Башня согласований |  |  |  |  |  |  |
| 14 | Министерство фабричного труда |  |  |  |  |  |  |
| 15 | Сердце Мартышкиного труда |  |  |  |  |  |  |

## Required evidence per level

- first playable screen
- early platform segment
- mid-level segment
- late-level segment
- obstacle cluster
- bonus/skin state when practical
- logcat/browser console scan for fallback/missing asset/crash markers

## Mandatory log markers to scan

- `MTR_PLAYER_SKIN_SAFE_FALLBACK`
- `MTR_PLAYER_SKIN_SAFE_FALLBACK_MISSING`
- `MTR_LEGACY_PLAYER_EQUIPMENT_OVERLAY_SUPPRESSED`
- `themed_platform_missing`
- `latest_themed_platform_asset_pending`
- `asset missing`
- `FATAL EXCEPTION`
- `ANR`
- `WebGL context lost`

