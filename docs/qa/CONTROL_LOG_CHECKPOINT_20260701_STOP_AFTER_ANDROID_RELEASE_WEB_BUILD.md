# Control log / checkpoint — stop after Android release + web build

Generated: 2026-07-01 11:55 +03:00  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Evidence root: `docs\qa\evidence\20260630_next_big_patch`

## Status

`partially_working`

The current implementation slice is built and Android-emulator validated, and a device-valid Android release APK was created and verified. The full delivery task is not complete yet because the latest web build has not yet been smoke-tested after this final runtime change, GitHub Pages sync/push has not been performed, final phone install has not been performed in this stop cycle, and final hygiene cleanup is still pending.

## What changed in this stop cycle

### Android native QA route

Files:

- `native\engine\android\app\src\com\cocos\game\AppActivity.java`
- `assets\scripts\GameRoot.ts`

Changes:

- Added a narrow Android startup-query bridge for QA/dev parameters from `Intent` data/extras.
- Added `AppActivity.getStartupQuery()` for Cocos JSB reflection.
- Added TypeScript startup query parsing for native + web using the same query contract.
- Added fallback from `native.reflection` to `jsb.reflection`.
- Added stable Android QA parameters:
  - `mtr_dev`
  - `mtr_autostart`
  - `mtr_level`
  - `mtr_qa_bonuses`
  - `mtr_qa_skin`
  - `mtr_qa_variant`
  - `mtr_qa_pose`
  - `mtr_pause`
  - `mtr_show_touch_zones`
- Added `MTR_NATIVE_STARTUP_QUERY_READY` and `MTR_QA_STARTUP_PAUSE_APPLIED` logging.

Reason:

- ADB touchscreen taps stopped changing Cocos UI state despite AppActivity focus being correct. The new route makes emulator QA deterministic and repeatable without relying on fragile coordinates.

### Build wrapper verifier

File:

- `tools\Run-MtrCocosBuild.ps1`

Changes:

- Updated APK payload verification away from stale old-menu markers.
- Current verifier now checks ASCII runtime anchors:
  - no old main-menu layer draw marker;
  - current runtime menu marker;
  - native QA startup route marker;
  - styled name-flow marker;
  - new bonus PNG pack markers;
  - `primatal`;
  - no `prompt(` call.
- Removed non-ASCII regex markers after they broke PowerShell parsing under the current file encoding.

## Builds and QA performed

### Static / config

- `powershell -File .\tools\validate-mtr-config.ps1`: passed.
- `tools\Run-MtrCocosBuild.ps1` PowerShell parser check after verifier fix: passed.

### Android emulator build

Latest successful emulator build:

- `docs\qa\evidence\20260630_next_big_patch\android_emulator_build_20260701_native_pause_qa.log`
- Cocos log: `creator-android-emulator-20260701-native-pause-qa.log`
- APK: `build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk`

### Android emulator QA

Evidence directory:

- `docs\qa\evidence\20260630_next_big_patch\android_emulator_qa_20260701`

Cycles:

1. Level 1 autostart with QA bonuses:
   - screenshot: `cycle2_level1_intent_autostart_retry.png`
   - logcat: `cycle2_level1_intent_autostart_retry_logcat.txt`
2. Level 15 autostart with forced skin/variant and QA bonuses:
   - screenshot: `cycle3_level15_intent_autostart_bonuses.png`
   - logcat: `cycle3_level15_intent_autostart_bonuses_logcat.txt`
3. Level 8 autostart into pause overlay:
   - screenshot: `cycle4_level8_pause_intent.png`
   - logcat: `cycle4_level8_pause_intent_logcat.txt`

Summary:

- file: `android_emulator_qa_summary_20260701.json`
- fatal crashes: `0` in all three cycles.
- native startup route observed: `1/1` in each cycle.
- RUNNING transition observed: `1/1` in each cycle.
- PAUSED transition observed in pause cycle.
- Bonus PNG usage logs observed in gameplay/bonus cycles.

Known non-fatal Android runtime noise:

- `Failed to accquire interfaces, error: Permission denied`
- `failed to get addresses Permission denied`
- `Failed to set shading scale, pipelineSceneData is invalid`
- deprecated `LabelOutline.color` / `LabelOutline.width`

No `FATAL EXCEPTION` / `AndroidRuntime` crash was detected in the tested cycles.

### Android release APK

Release APK:

- `releases\android\mtr-20260701-next-big-patch-release.apk`

Verification:

- evidence: `docs\qa\evidence\20260630_next_big_patch\android_release_apk_verification_20260701.json`
- size: `137968594` bytes
- SHA-256: `5BA586CAA604AF01C8BAA1B75FB616C0D0CD2BA8FEA06AF7116785569F97E3E9`
- ABI:
  - `arm64-v8a`
  - `armeabi-v7a`
- `x86_64`: absent
- `apksigner verify --verbose --print-certs`: OK
- runtime markers:
  - `primatal`: present
  - native startup query route: present
  - pause QA route: present
  - `bonus_jump_spring_01`: present
  - `bonus_dash_bolt_01`: present
  - `bonus_extra_life_01`: present
  - `prompt(`: absent

### Web build

Latest web build:

- `docs\qa\evidence\20260630_next_big_patch\web_build_20260701_native_qa_sync.log`
- Cocos log: `creator-web-20260701-native-qa-sync.log`
- output: `build\web-mobile`

Result:

- build finished: true
- favicon postprocess: OK
- `favicon.png` copied into web build
- `index.html` patched with favicon link

Important: this latest web build has not yet been smoke-tested locally after the final runtime changes.

## Git / deploy status

- Portable project path is not a git repository.
- GitHub Pages worktree is separate:
  - `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`
  - current status at stop: `## main...origin/main`
- Latest `build\web-mobile` has not yet been synced into the GitHub Pages worktree.
- No commit/push was performed in this stop cycle.

## Files changed in this cycle

- `assets\scripts\GameRoot.ts`
- `native\engine\android\app\src\com\cocos\game\AppActivity.java`
- `tools\Run-MtrCocosBuild.ps1`
- `docs\qa\CONTROL_LOG_CHECKPOINT_20260701_STOP_AFTER_ANDROID_RELEASE_WEB_BUILD.md`

Generated evidence/artifacts include:

- `docs\qa\evidence\20260630_next_big_patch\android_emulator_build_20260701_native_qa.log`
- `docs\qa\evidence\20260630_next_big_patch\android_emulator_build_20260701_native_query_fallback.log`
- `docs\qa\evidence\20260630_next_big_patch\android_emulator_build_20260701_native_pause_qa.log`
- `docs\qa\evidence\20260630_next_big_patch\android_emulator_qa_20260701\*.png`
- `docs\qa\evidence\20260630_next_big_patch\android_emulator_qa_20260701\*.txt`
- `docs\qa\evidence\20260630_next_big_patch\android_emulator_qa_20260701\android_emulator_qa_summary_20260701.json`
- `docs\qa\evidence\20260630_next_big_patch\gradle_android_assembleRelease_20260701.log`
- `docs\qa\evidence\20260630_next_big_patch\android_release_apk_verification_20260701.json`
- `docs\qa\evidence\20260630_next_big_patch\apksigner-release-verify-20260701.out.log`
- `docs\qa\evidence\20260630_next_big_patch\apksigner-release-verify-20260701.err.log`
- `docs\qa\evidence\20260630_next_big_patch\web_build_20260701_native_qa_sync.log`
- `releases\android\mtr-20260701-next-big-patch-release.apk`

## Known risks / pending work

1. Run local web smoke against the latest `build\web-mobile`.
2. Sync `build\web-mobile` into `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`.
3. Review GitHub Pages diff, commit, and push to `origin/main`.
4. If physical phone install is still authorized, install the release APK only to the main profile:
   - `adb -s R5CY933XP7P install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260701-next-big-patch-release.apk"`
5. Run final hygiene gate:
   - remove or justify stale generated logs/temp artifacts;
   - do not delete QA evidence needed for this release;
   - keep release APK and core proof logs.
6. Optional but recommended: update Android wrapper to run release verification directly, not only debug postpackage.

## Exact resume point

Resume from here:

1. Read this file.
2. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1`.
3. Run a local web smoke against `build\web-mobile`.
4. Sync latest web build to the GitHub Pages worktree.
5. Commit and push.
6. Install release APK to phone only if still in scope.
7. Create final release log and checkpoint.

