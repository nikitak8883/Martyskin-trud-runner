# QA checkpoint: level select PNG icons and ghost-label shield

Дата: 2026-06-19.

## Scope

- Перевод меню выбора уровней на 15 отдельных PNG-иконок тематик.
- Удаление старой векторной runtime-логики `LEVEL_THEME_ICON_SPECS`.
- Runtime-защита кнопок от старых baked/подфоновых надписей через `buttonLabelPlate`.
- Фиксация UI asset contract и hygiene-gate для будущих патчей.

## Expected behavior

- Уровни 1-15 показывают собственные тематические PNG-иконки в единой стилистике.
- Уровни 9-15 больше не наследуют placeholder/повтор уровня 8.
- На графических кнопках видна только актуальная runtime-надпись.
- Если PNG-иконка ещё не загружена, показывается короткий безопасный fallback, после загрузки — полноценный PNG.

## Checks to run

- `python tools/ui/generate_level_select_theme_icons.py --verify-only`
- `powershell -ExecutionPolicy Bypass -File tools/validate-mtr-config.ps1`
- Targeted source search: `LevelThemeIconKind`, `LevelThemeIconSpec`, `LEVEL_THEME_ICON_SPECS`, `case 'crane'` must be absent from `assets/scripts/GameRoot.ts`.
- Runtime/web/android visual pass: открыть меню уровней, проверить 15 карточек и несколько экранов с кнопками на отсутствие ghost labels.

## Hygiene notes

- New deterministic generator is retained because it is the reproduction source for the PNG icon set.
- Legacy generated catalog entries for old six icons are intentionally retained until the generated catalog cleanup can be validated by a full build/emulation cycle.

## Entrypoint stability finding and mitigation

- Finding: Windows `Start-Process -ArgumentList @(...)` can split project/build paths containing spaces (`Monkey Work`) for Python/Cocos entrypoints, causing false launch failures before runtime QA.
- Mitigation: all local Cocos/web QA launches now go through `tools/codex/MtrEntrypoint.psm1`, which validates the executable and working directory, converts argument arrays into a safe Windows command-line string, logs compact JSONL evidence, and redacts sensitive argument values.
- Regression test: `powershell -ExecutionPolicy Bypass -File tools/Test-MtrEntrypoint.ps1` must pass before using wrapped launchers.
- Router self-test fix: first local run exposed an incompatible `SHA256.HashData` call on this PowerShell/.NET runtime; router was corrected to `SHA256.Create().ComputeHash()` before continuing QA.
- Router self-test hardening: second local run exposed unreliable `$args` handling via `PowerShell -EncodedCommand` and missing `ExitCode` after separate `Wait-Process`; router now uses direct `Process.WaitForExit()`, and the self-test uses `-File` with both script and payload paths containing spaces.
- Router self-test stabilization: diagnostic run confirmed the safe command-line path works with `pwsh`; self-test now prefers `pwsh` and falls back to the host PowerShell only when `pwsh` is unavailable.
- Router self-test finalization: packaged `WindowsApps\pwsh.exe` is not reliable as a child-process probe from legacy `powershell.exe`; the self-test now uses local Python, matching the web/static asset entrypoint family and validating a path-with-spaces payload argument directly.
- Router algorithm correction: legacy Windows PowerShell can report `HasExited=true` while leaving `Start-Process` `ExitCode` empty after manual waits. The router now uses direct `.NET ProcessStartInfo` for synchronous launches and keeps `Start-Process` only for detached/background launches.
- Current router self-test status: PASS via `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Test-MtrEntrypoint.ps1`; evidence is in `logs/entrypoint-router-20260619.jsonl`.
- Wrapped launchers:
  - `tools/Run-MtrCocosBuild.ps1`
  - `tools/Start-MtrWebServer.ps1`
