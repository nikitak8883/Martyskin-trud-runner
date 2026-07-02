# Control log / checkpoint — 2026-07-02 — web live QA harness fixed

status: partially_working

## Summary

Continued from Hermes checkpoint `565`.

The web release published to GitHub Pages is live and functional. The apparent black-screen regression was traced to the QA harness launching Chrome as a hidden/background window without disabling background/occlusion throttling. The runtime itself was not the root cause.

The smoke harness was fixed to:

- disable Chrome background timer throttling;
- disable renderer/background occlusion throttling;
- optionally wait for a specific runtime log marker after `MTR_RUNTIME_CORE_READY`.

The final live web check now waits for `MTR_GAMEPLAY_START_GATE_READY level=15`, proving that the published page can load into level 15 rather than merely rendering the boot menu.

Android physical-device installation remains blocked because ADB still reports no attached devices.

## Files changed

- `tools/web-chrome-runtime-smoke.ps1`
  - added Chrome flags:
    - `--disable-background-timer-throttling`
    - `--disable-renderer-backgrounding`
    - `--disable-backgrounding-occluded-windows`
    - `--disable-features=CalculateNativeWinOcclusion,Translate`
  - added optional parameters:
    - `-WaitForLogPattern`
    - `-WaitForLogPatternTimeoutSeconds`
  - added result fields:
    - `waitForLogPattern`
    - `waitForLogPatternReady`
- QA log:
  - `docs\qa\CONTROL_LOG_CHECKPOINT_20260702_WEB_LIVE_QA_HARNESS_FIXED_PHONE_BLOCKED.md`

## Evidence kept

- HTTP smoke:
  - `docs\qa\evidence\20260630_next_big_patch\web_http_smoke_20260702.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_pages_http_smoke_20260702.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_live_pages_http_smoke_20260702.json`
- Source build runtime smoke after harness fix:
  - `docs\qa\evidence\20260630_next_big_patch\web_source_runtime_resmoke_fixed_harness_20260702.out.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_source_runtime_resmoke_fixed_harness_probe_20260702.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_source_runtime_resmoke_fixed_harness_level15_20260702.png`
- Local GitHub Pages worktree runtime smoke after harness fix:
  - `docs\qa\evidence\20260630_next_big_patch\web_local_pages_8125_runtime_resmoke_fixed_harness_20260702.out.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_local_pages_8125_runtime_resmoke_fixed_harness_probe_20260702.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_local_pages_8125_runtime_resmoke_fixed_harness_level15_20260702.png`
- Live GitHub Pages runtime smoke with explicit level 15 gameplay gate:
  - `docs\qa\evidence\20260630_next_big_patch\web_live_pages_runtime_level15_gate_fixed_harness_20260702.out.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_live_pages_runtime_level15_gate_fixed_harness_probe_20260702.json`
  - `docs\qa\evidence\20260630_next_big_patch\web_live_pages_runtime_level15_gate_fixed_harness_20260702.png`

## Evidence cleaned

Intermediate failed/experimental screenshots, CDP diagnostic outputs, and temporary browser logs from the investigation were removed after the root cause was identified and final evidence was captured.

## Commands run

- Restored latest Hermes checkpoint and checked ADB.
- Ran Skill Compass via local_worker.
- Checked live GitHub Pages HTTP assets.
- Ran Chrome runtime smoke on:
  - source `build\web-mobile`;
  - local GitHub Pages worktree;
  - live GitHub Pages URL.
- Diagnosed hidden Chrome throttling by comparing request timing and browser logs.
- Patched `tools\web-chrome-runtime-smoke.ps1`.
- Re-ran source/local/live web smoke after harness fix.
- Cleaned intermediate QA evidence.
- Stopped temporary local HTTP servers on ports `8124`, `8125`, and `8126`.
- Rechecked ADB.
- Created Hermes checkpoint:
  - id: `566`
  - trigger: `20260702-web-live-qa-harness-fixed-phone-blocked`
- Ran Hermes checkpoint retention:
  - `keep-last 12`
  - `delete-count 5`
  - deleted old checkpoint artifacts: `5`
  - `hermes_context.py doctor`: `integrity=ok`, `fts_consistent=true`

## Tests passed

- Source web runtime smoke:
  - `runtimeReady=true`
  - screenshot shows level 15 gameplay.
- Local GitHub Pages worktree runtime smoke:
  - `runtimeReady=true`
- Live GitHub Pages HTTP smoke:
  - all checked assets returned `200`
  - `assets/main/index.js` contains the expected runtime markers and no `prompt(`.
- Live GitHub Pages level 15 gate smoke:
  - `runtimeReady=true`
  - `waitForLogPattern=MTR_GAMEPLAY_START_GATE_READY level=15`
  - `waitForLogPatternReady=true`
  - screenshot shows level 15 scene loaded from the published GitHub Pages URL.
- Temporary server cleanup:
  - `8124` clear
  - `8125` clear
  - `8126` clear

## Tests failed / blocked

- Android physical-device install:
  - status: blocked
  - reason: `adb devices -l` reports no attached devices
  - required target remains `R5CY933XP7P` with `--user 0`

## Metrics

- Published GitHub Pages commit remains:
  - `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
- Live URL checked:
  - `https://nikitak8883.github.io/Martyskin-trud-runner/`
- Live level gate:
  - `MTR_GAMEPLAY_START_GATE_READY level=15`
- Final Android APK remains:
  - `releases\android\mtr-20260701-next-big-patch-release.apk`
  - SHA256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`

## Risks / notes

- Source git root is `C:\Projects\Monkey Work`; no remote is configured for that root.
- The nested GitHub Pages repo is clean and already pushed.
- The root git status still reports the nested `_github\Martyskin-trud-runner` worktree as modified from the root repository perspective; this is intentionally not staged here.
- Chrome GCM auth warnings in browser logs are unrelated to the game runtime.
- Hermes context threshold is still `0.95` of `258000`, i.e. checkpointing happens near the last 5% of the current configured context budget.

## Next exact continuation point

1. If the phone is connected, verify:

```powershell
adb devices -l
```

2. If `R5CY933XP7P` appears, install to the main profile:

```powershell
adb -s R5CY933XP7P install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260701-next-big-patch-release.apk"
```

3. Run a short real-device sanity check only after the install succeeds.

4. For future web QA that must assert a specific level state, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\web-chrome-runtime-smoke.ps1 `
  -Url "https://nikitak8883.github.io/Martyskin-trud-runner/?mtr_dev=1&mtr_autostart=1&mtr_level=15&mtr_qa_bonuses=1" `
  -BrowserPath "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  -WaitForLogPattern "MTR_GAMEPLAY_START_GATE_READY level=15" `
  -WaitForLogPatternTimeoutSeconds 75
```
