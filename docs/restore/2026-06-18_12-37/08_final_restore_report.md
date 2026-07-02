# Final restore report

## Project path

```text
C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator
```

## Restore status

- Project structure: passed
- Transfer integrity: passed
- Asset metadata integrity: passed
- Project validator: passed
- Existing release integrity: passed
- Dependencies: passed; no npm dependencies are declared
- Cocos Creator 3.8.8: found and verified
- JDK 17: installed and verified
- Android SDK/API/NDK/CMake: installed and verified
- Fresh Web build: passed
- Browser smoke test: passed
- Fresh Android x86_64 native build: passed
- Android 16 install and runtime: passed
- Crash/ANR check: passed
- Git bundle: intact; metadata restoration intentionally deferred

## What was installed or prepared

- Temurin JDK 17.0.19
- Android command-line tools
- Android API 35 and 36
- Build Tools 35.0.0 and 36.0.0
- NDK r23c / 23.2.8568313
- CMake 3.22.1
- Android 15 and Android 16 x86_64 system images
- Three AVD profiles
- Separate ARM release and x86_64 emulator Cocos build profiles

## Build outputs

Web:

```text
build\web-mobile
```

Android emulator APK:

```text
build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
```

APK SHA-256:

```text
1A01EF50382E07EE8C357270E1F07ABB1D0E7E7EA646F72CCFEC5E938DC3C65D
```

## Runtime result

The APK launches on `MTR_Galaxy_S25_Ultra_Android_16` in 1.556 seconds, loads the main scene and menu, survives background/resume, and produces no crash, ANR or fatal signal. The clean screenshot confirms the intended Russian UI and assets.

## Remaining manual decisions

1. Connect the real Galaxy S25 Ultra for ARM64 and One UI 8.5 validation.
2. Decide whether to restore Git history from the verified bundle into this directory.
3. Optionally add permanent Android SDK environment variables; they are not required for the current project profiles.

## Known non-blocking risks

- One UI, Snapdragon/Adreno and Samsung services cannot be reproduced by the Google Android Emulator.
- The required CMake 3.22.1 integration emits an SDK XML metadata warning with the newer Android Studio package set, but builds succeed.
- Debug runtime network-interface discovery is restricted by emulator SELinux; normal game networking and rendering are not shown to be broken.
- The app currently renders at a 60 Hz cadence while the emulated display advertises a 120 Hz physical mode. This is normal unless the game explicitly requests a higher frame rate.

## Overall result

Restore completed for this machine. The project is intact, rebuildable, browser-tested, Android-native-buildable and runnable in the Android 16 S25 Ultra-oriented emulator.
