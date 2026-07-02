# MTR release resume checkpoint

Date: 2026-06-19
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

This is the compact local resume record for the Martyshkin Trud Runner skin/background/web/Android release pass.

## Current state

- Web deploy is pushed to `https://github.com/nikitak8883/Martyskin-trud-runner`.
- Latest pushed commit: `fd0c2ab7cac45550599e7470a28c5f1b3f8c7c92`.
- Live URL: `https://nikitak8883.github.io/Martyskin-trud-runner/`.
- Android release APK exists at `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260619-skins-bg-release.apk`.
- APK SHA-256: `0c09f701e0ffbafa24bb862acfa86f49431c4b9e161aab08f1812af05a9ef9a8`.
- Final QA/release report: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\docs\qa\FINAL_RELEASE_SKINS_BG_WEB_ANDROID_20260619.md`.

## Implemented

- Integrated the monkey skin pack from `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\Tasks\1\Skin-paks`.
- Verified skin prompt SHA-256: `a76f9e3d23dffe3c1b7dd6ba7221b8a40d8f1b790345b6a7f06d90e2d7262262`.
- Generated 8 canonical runtime skins and 600 runtime skin PNGs under `assets/resources/characters/player_skins`.
- Preserved `player_skins_v2` only as compatibility fallback.
- Replaced the main-menu background with one coherent PNG at `assets/resources/ui/main_menu_background/main_menu_bg_far.png`.
- Preserved background Cocos UUID `53c450ff-6297-4ffc-91e4-82243e894da8`.
- Hardened the background generator against legacy onion-layer output.
- Hardened white-matte scanner to avoid false positives from stylized highlights/dust/motion streaks.
- Stale clean-scan contact-sheet cleanup is automatic.

## QA status

- Web local HTTP smoke passed before push.
- Android release Gradle build passed.
- Android QA was emulator-only on `emulator-5554`.
- Physical devices were not used for QA.
- Release APK installed to emulator owner profile with `--user 0`.
- Main menu, skin selection, level select, level icons after level 8, and gameplay smoke were checked.
- App-PID strict error scan found 0 fatal/ANR/crash/JS error matches.
- Final white-matte scan: `checkedCount=618`, `suspectCount=0`, `fixedCount=0`.
- Deploy clone status after push: `## main...origin/main`.

## Owner-profile install command

```powershell
adb devices
adb shell pm list users
adb install --user 0 -r "C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\releases\android\mtr-20260619-skins-bg-release.apk"
```

Do not replace `--user 0` with work-profile user IDs unless physical work-profile testing is explicitly requested.

## If resuming

1. Read `docs\qa\FINAL_RELEASE_SKINS_BG_WEB_ANDROID_20260619.md`.
2. Verify the APK SHA-256 before distributing.
3. Use emulator-only QA unless the user explicitly asks for a physical device.
4. Keep source evidence, useful audit logs, release artifacts, skin manifests, and final checkpoints.
5. Clean stale/generated debugging tails before handoff.
