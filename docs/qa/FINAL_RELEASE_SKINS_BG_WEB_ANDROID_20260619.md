# Martyshkin Trud Runner — final release QA log

Date: 2026-06-19  
Scope: skin-pack integration, main-menu background rebuild, web deploy, Android release APK, emulator-only QA, hygiene cleanup.

## Release artifacts

- Android release APK: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260619-skins-bg-release.apk`
- APK SHA-256: `0c09f701e0ffbafa24bb862acfa86f49431c4b9e161aab08f1812af05a9ef9a8`
- APK size: `104493757` bytes
- GitHub Pages repository: `https://github.com/nikitak8883/Martyskin-trud-runner`
- Pushed commit: `fd0c2ab7cac45550599e7470a28c5f1b3f8c7c92`
- Live URL: `https://nikitak8883.github.io/Martyskin-trud-runner/`

## Skin-pack integration

- Prompt SHA-256 verified: `a76f9e3d23dffe3c1b7dd6ba7221b8a40d8f1b790345b6a7f06d90e2d7262262`
- Source groups detected: `7`
- Runtime skins generated: `8`
- Runtime skin PNGs generated: `600`
- Canonical runtime root: `assets/resources/characters/player_skins`
- Compatibility fallback: `player_skins_v2` is retained only as a runtime fallback, not as the primary generation or QA root.
- Manifest: `docs/skins_integration/manifests/player_skins_manifest.json`
- Contact sheet: `docs/skins_integration/qa/player_skins_runtime_contact_sheet.png`

Canonical skins:

- `brigadir`
- `mudrec`
- `cyber_makaka`
- `red_prorab`
- `depo_primate`
- `orangutan_noir`
- `lab_assistant_act`
- `golden_brigadir`

## Main-menu background

- Active policy: one coherent PNG backdrop, no regenerated onion-layer stack.
- Active runtime asset: `assets/resources/ui/main_menu_background/main_menu_bg_far.png`
- Source PNG SHA-256: `043a9820926ed64e56b5a2e905aa2d09cfdb7613262300b5ed3c0cef003a4bb0`
- Cocos asset UUID: `53c450ff-6297-4ffc-91e4-82243e894da8`
- APK payload contains the same background PNG at `assets/assets/resources/native/53/53c450ff-6297-4ffc-91e4-82243e894da8.png`.
- Background generator was hardened to preserve existing Cocos `.meta` UUIDs on repeat runs.
- Legacy layer names are listed only in `skippedLegacyAssets` for audit traceability.

## Web validation and deploy

Local HTTP smoke passed before push:

- `/` -> `200`
- `/index.html` -> `200`
- `/application.js` -> `200`
- `/index.js` -> `200`
- `/assets/main/index.js` -> `200`
- `/assets/resources/index.js` -> `200`

Git state after push:

- `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`
- `## main...origin/main`

## Android release build and emulator QA

- Release build command: `gradlew.bat :CocosGame:assembleRelease`
- Build result: `BUILD SUCCESSFUL`
- QA target policy: emulator-only. Physical devices are excluded unless separately requested.
- QA emulator: `emulator-5554`
- Android user scope used in QA: `UserInfo{0:Owner:4c13} running`
- Installed release APK to emulator owner profile with `--user 0`.
- Package: `com.martyskin.trudrunner`
- Activity: `com.cocos.game.AppActivity`
- `targetSdkVersion`: `35`
- QA log directory: `logs/android-qa-release-skins-bg-20260619`

Verified flows:

- Main menu renders the generated scenic background as a single coherent picture.
- No visible old under-text behind the new PNG buttons in the checked menu state.
- Skin-selection screen displays the integrated skin set.
- Skin selection and confirm flow work for `lab_assistant_act`.
- Level-select screen shows thematic icons after level 8, including levels 9-15.
- Gameplay smoke starts with the selected skin resources loaded.

Strict app-PID error scan:

- Fatal/ANR/Crash/JS error matches: `0`
- Non-fatal warnings observed: emulator CPU variant warning, HWUI/EGL fallback, Cocos shading-scale warning, deprecated `LabelOutline`.

Key runtime markers:

- `MTR_BG_SCENIC_SYNC_OK owner=GameRootBackgroundController layers=BG_FAR mode=scenic-fit repeat=none proceduralFallback=0 correctionRectangles=0`
- `MTR_MENU_UI_GATE_READY surface=main_menu`
- `MTR_PLAYER_SKIN_CRITICAL_PRELOAD_REQUESTED reason=skin-confirm skin=lab_assistant_act count=9`
- `MTR_PLAYER_SKIN_VARIANTS_DEFERRED_PRELOAD_REQUESTED reason=skin-confirm skin=lab_assistant_act count=72 policy=chunked-idle`
- `MTR_SKIN_VARIANT_ACTIVE skin=lab_assistant_act variant=base model=selected_skin pose=run_1 key=characters/player_skins/lab_assistant_act/base/run_1`
- `MTR_THEMED_OBJECT_SPRITE_LOAD_OK ... mtr_level_select_theme_icon_09` through `15`

## Owner-profile phone install command

For a real phone, install only into the main owner profile:

```powershell
adb devices
adb shell pm list users
adb install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260619-skins-bg-release.apk"
```

Fallback if direct install is blocked by the device:

```powershell
adb push "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260619-skins-bg-release.apk" /data/local/tmp/mtr-release.apk
adb shell cmd package install -r --user 0 /data/local/tmp/mtr-release.apk
adb shell rm /data/local/tmp/mtr-release.apk
```

Do not replace `--user 0` with work-profile user IDs unless physical work-profile testing is explicitly requested.

## Hygiene gate

Cleanup and stabilization completed:

- `tools/scan_and_fix_white_matte_edges.py`
  - Default scan root changed from stale `player_skins_v2` to canonical `characters/player_skins`.
  - The white-matte heuristic was corrected so stylized highlights, dust, and motion streaks are not misreported as defects.
  - Final dry scan: `checkedCount=618`, `suspectCount=0`, `fixedCount=0`.
  - Report: `qa/hygiene_white_matte_scan_20260619.json`
  - Stale suspect contact-sheet cleanup is automatic when the scan result is clean.
- `tools/asset_generation/build_martyshkin_main_menu_background.py`
  - Active generator path is single-PNG only.
  - Legacy onion-layer generation is blocked from active output.
  - Existing Cocos image UUID is preserved across repeat runs.
  - Generation report: `qa/main-menu-background-10-1/main_menu_background_10_1_report.json`

Preserved intentionally:

- source evidence and QA logs,
- generated production assets,
- final release APK,
- skin integration manifest and contact sheets,
- audit reports needed for reproduction.

## Hermes resume checkpoint

- A clean MTR-specific resume log was written to `docs/qa/MTR_RELEASE_RESUME_20260619.md`.
- Machine-readable resume transcript: `logs/hermes/mtr_release_resume_20260619.jsonl`
- Hermes clean checkpoint: `id=154`, trigger `mtr-final-release-resume-clean-v2`.
- Hermes latest for this project was verified to point to the MTR release resume, not to a neighbouring thread summary.
