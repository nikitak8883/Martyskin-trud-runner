# Control log: release sync, push, APK

Date: 2026-06-22  
Project: Martyshkin Trud Runner  
Portable project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
GitHub Pages worktree: `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`

## Outcome

- Web build was synchronized from portable `build\web-mobile` into the GitHub Pages worktree.
- Git commit was created and pushed to `origin/main`.
- Device-valid Android release APK was built and copied into `releases\android`.
- Web smoke, release APK verification, and emulator runtime smoke were completed.
- Physical phone was not used; runtime QA remained emulator-only.

## Git sync / push

- Repository: `https://github.com/nikitak8883/Martyskin-trud-runner.git`
- Branch: `main`
- Commit: `5b3e1dbe858a58f377e7a316a3ace0211286e743`
- Commit message: `Update Martyskin web build and skin assets`
- Remote verification: `origin/main` points to the same commit.
- Worktree after push: clean.

## Web build validation

Evidence:

- `web_pages_smoke_20260622.json`
- `web-pages-server-8923.out.log`
- `web-pages-server-8923.err.log`

Result:

- `index.html`: HTTP 200
- `assets/main/index.js`: HTTP 200
- Runtime JS contains:
  - `MTR_QA_BONUS_PRELOAD_WAIT`
  - `Primatal` / `primatal`
  - `variants=`

## Android release build

Release APK:

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260622-runtime-qa-skins-release-arm64.apk`

Verification:

- Size: `137795501` bytes
- SHA-256: `D899514C20F1BF896270D22014EFF0FDF21CF2C680BEABD89931F7283093DFD3`
- ABI inside APK:
  - `arm64-v8a`
  - `armeabi-v7a`
- `x86_64`: absent, as expected for device-valid release APK
- JS payload entry: `assets/assets/main/index.js`
- `apksigner verify --verbose --print-certs`: OK

Evidence:

- `creator-android-device-build-20260622.log`
- `gradle-android-assembleRelease-20260622.out.log`
- `android_release_apk_verification_20260622.json`
- `apksigner-release-verify-20260622.out.log`
- `apksigner-release-verify-20260622.err.log`

Note: `tools\Run-MtrCocosBuild.ps1` returned a non-zero wrapper result because its custom legacy verification expected an old `hasNewMainMenuGrid` marker. The underlying Cocos build finished successfully, Gradle debug packaging was successful, and the final `assembleRelease` was executed and verified independently.

## Emulator QA smoke

AVD:

- `MTR_Pixel_8_Pro_API_35`

APK used for runtime smoke:

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk`

Result:

- Install: OK
- Launch: OK
- Screenshot captured
- Logcat scan: no `FATAL EXCEPTION`, no `ANR`, no `MTR_PLAYER_SKIN_SAFE_FALLBACK`, no QA timeout markers
- Emulator was stopped after smoke; no ADB devices remained attached.

Evidence:

- `emulator_smoke_20260622.json`
- `emulator_smoke_logcat_20260622.txt`
- `emulator_smoke_release_sync_20260622.png`

## Hygiene gate

Checked:

- Git worktree after push: clean
- Conflict markers: no hits
- `debugger;`: no hits
- Temporary local web server: stopped
- Emulator process: stopped
- ADB devices after QA: none

Justified retained guard:

- `MTR_PLAYER_SKIN_SAFE_FALLBACK` remains in `assets\scripts\GameRoot.ts` as a defensive runtime log/guard. Fresh emulator smoke did not emit it.

## Install command for main phone profile

When explicit physical-device install is requested, use an explicit serial and user `0`:

```powershell
adb devices
adb -s <PHONE_SERIAL> install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260622-runtime-qa-skins-release-arm64.apk"
```

Do not omit `-s <PHONE_SERIAL>` when more than one device/emulator is attached.

## Physical phone install

Explicit user approval was given after the release cycle to install on the connected physical phone.

- Serial: `R5CY933XP7P`
- Model: `SM_S938B`
- Target user/profile: `0`
- Command form: `adb -s R5CY933XP7P install --user 0 -r <release-apk>`
- Result: OK
- `pm path --user 0 com.martyskin.trudrunner`: package found

Evidence:

- `physical_phone_install_user0_20260622.json`
- `physical_phone_install_user0_dumpsys_20260622.txt`

## Cross-project Android device rule update

The current approved physical Android device was saved as a global cross-project note:

- Memory note: `C:\Users\nikit\.codex\memories\extensions\ad_hoc\notes\20260622T211129-android-primary-physical-device.md`
- ADB serial: `R5CY933XP7P`
- Model: `SM_S938B`
- Default install profile after explicit physical-device authorization: `--user 0`

## Resume note

Current task is complete: sync, push, release APK, verification, and checkpoint are expected to be the final state for this cycle.

## Hermes checkpoint

- Checkpoint ID: `518`
- Trigger: `release-sync-push-stop`
- Markdown: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260622T180802Z-release-sync-push-stop.md`
- JSON: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260622T180802Z-release-sync-push-stop.json`
- Hermes doctor:
  - integrity: `ok`
  - FTS consistent: `true`
  - compact limit: `258000`
  - threshold ratio: `0.95`
  - threshold tokens: `245100`
