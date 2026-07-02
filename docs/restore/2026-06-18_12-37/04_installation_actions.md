# Installation actions

## Actions performed after user approval

- Located and verified the existing Cocos Creator `3.8.8` installation.
- Installed Temurin JDK `17.0.19` alongside existing Java versions.
- Installed official Android SDK command-line tools.
- Installed Android platforms 35 and 36.
- Installed Android Build Tools 35.0.0 and 36.0.0.
- Installed NDK `23.2.8568313` (r23c).
- Installed CMake `3.22.1`.
- Installed Android 15 and Android 16 Google APIs x86_64 system images.
- Created and tuned three AVD profiles, including the final Android 16 S25 Ultra-oriented profile.

## Project-local configuration

- Updated `build-android.json` to current SDK, NDK and JDK 17 paths while preserving ARM release ABIs.
- Added `build-android-emulator.json` with x86_64 debug ABI.
- Generated the Gradle wrapper through Creator 3.8.8.

## Environment-variable policy

No permanent global Android environment variables were required. Build commands set `JAVA_HOME`, `ANDROID_HOME` and `ANDROID_SDK_ROOT` for the current process, while Cocos build profiles contain explicit local paths.

## Intentionally not installed or changed

- No system Gradle; the generated wrapper is authoritative.
- No pnpm or yarn; the project does not require them.
- No newer Cocos Creator version.
- Existing JDK versions were not removed.
