# Control log / checkpoint — 2026-07-02

status: partially_working

## Summary

The latest Martyskin Trud Runner implementation state was resumed from the previous Android release / web build checkpoint, smoke-tested, synchronized to the GitHub Pages worktree, committed, and pushed.

The Android release APK remains device-valid and signed, but physical-device installation could not be completed in this run because `adb devices -l` currently reports no connected devices.

## Files changed / published

- GitHub Pages worktree: `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`
  - Branch: `main`
  - Commit: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
  - Message: `Update Martyskin web release build`
  - Remote: `https://github.com/nikitak8883/Martyskin-trud-runner.git`
- Source web build synced from:
  - `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\build\web-mobile`
- Android release APK:
  - `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260701-next-big-patch-release.apk`

## Commands run

- `tools\validate-mtr-config.ps1`
- Local static HTTP smoke for `build\web-mobile` on `127.0.0.1:8124`
- Browser plugin attempt via bundled Browser runtime
- Fallback Chromium/CDP runtime smoke for `build\web-mobile`
- `robocopy build\web-mobile -> _github\Martyskin-trud-runner /MIR`
- Local static HTTP smoke for GitHub Pages worktree on `127.0.0.1:8125`
- Fallback Chromium/CDP runtime smoke for GitHub Pages worktree
- `git add -A`
- `git commit -m "Update Martyskin web release build"`
- `git push origin main`
- `adb start-server`
- `adb devices -l`
- `apksigner verify --verbose`
- APK ABI inspection through ZIP entries
- Cleanup of temporary local HTTP servers on ports `8124` and `8125`

## Tests passed

- MTR config validation:
  - result: passed
  - summary: `MTR config OK: 15 levels`
- Source web build HTTP smoke:
  - result: passed
  - evidence: `docs\qa\evidence\20260630_next_big_patch\web_http_smoke_20260702.json`
  - checked routes/assets: `/`, `/index.html`, `/application.js`, `/index.js`, `/assets/main/index.js`, `/assets/resources/index.js`, `/favicon.png`
- Source web runtime smoke:
  - result: passed on retry with browser log outside a path containing spaces
  - evidence:
    - `docs\qa\evidence\20260630_next_big_patch\web_runtime_smoke_20260702_retry.out.json`
    - `docs\qa\evidence\20260630_next_big_patch\web_runtime_smoke_probe_20260702_retry.json`
    - `docs\qa\evidence\20260630_next_big_patch\web_runtime_smoke_level15_20260702_retry.png`
  - result markers: `runtimeReady=true`, `canvasCount=1`, title `Cocos Creator | Martyshkin Trud Runner`
- GitHub Pages worktree HTTP smoke:
  - result: passed
  - evidence: `docs\qa\evidence\20260630_next_big_patch\web_pages_http_smoke_20260702.json`
- GitHub Pages worktree runtime smoke:
  - result: passed
  - evidence:
    - `docs\qa\evidence\20260630_next_big_patch\web_pages_runtime_smoke_20260702.out.json`
    - `docs\qa\evidence\20260630_next_big_patch\web_pages_runtime_smoke_probe_20260702.json`
    - `docs\qa\evidence\20260630_next_big_patch\web_pages_runtime_smoke_level15_20260702.png`
  - result markers: `runtimeReady=true`, `canvasCount=1`, title `Cocos Creator | Martyshkin Trud Runner`
- Git publish:
  - result: passed
  - pushed commit: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
  - remote branch: `origin/main`
- Android APK verification:
  - result: passed
  - SHA256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`
  - size: `137968594` bytes
  - signature: verifies with v1 and v2 schemes
  - ABIs: `arm64-v8a`, `armeabi-v7a`
  - release-validity note: no emulator-only `x86_64` ABI is present
- Temporary server cleanup:
  - result: passed after retry
  - ports cleared: `8124`, `8125`

## Tests failed / blocked

- Physical-device installation:
  - status: blocked
  - reason: `adb devices -l` reports no devices attached after `adb start-server`
  - no install attempt was made against an ambiguous or missing target
  - required target when available: `R5CY933XP7P`, main profile `--user 0`

## Metrics

- GitHub Pages commit: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
- APK SHA256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`
- APK size: `137968594` bytes
- Web runtime canvas: `1264x625`
- Published web URL target: `https://nikitak8883.github.io/Martyskin-trud-runner/`

## Risks / notes

- GitHub CLI is not authenticated in this Codex session, but regular `git push` worked through the existing Git credential setup.
- Bundled Browser plugin path was unavailable in this environment:
  - missing module: `browser-client.mjs`
  - fallback: local Chromium/CDP smoke scripts
- The first local-server cleanup command used `$pid`, which conflicts with PowerShell's read-only `$PID` variable. The cleanup was rerun with `$ownerProcessId` and succeeded.
- `apksigner` reported non-blocking warnings for unprotected Gradle metadata entries under `META-INF`; the APK still verifies and remains installable.

## Next exact continuation point

1. Reconnect or reauthorize the approved phone so `adb devices -l` shows `R5CY933XP7P`.
2. Install the already verified release APK:

```powershell
adb -s R5CY933XP7P install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260701-next-big-patch-release.apk"
```

3. If installation succeeds, launch and run a short real-device sanity check.
4. If installation fails, log the exact installer error and fix only the blocking installer issue before further feature work.

## Stop condition

Work is intentionally stopped after this checkpoint. Continue only after the user confirms the next step or reconnects the physical device for installation.
