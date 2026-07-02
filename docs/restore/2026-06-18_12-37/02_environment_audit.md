# Environment audit

## Machine

- OS: Microsoft Windows 11 Pro `10.0.26200`, AMD64
- PowerShell: `7.6.2`
- User: `OWL2\nikit`
- Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

## Core tools

- Git: `2.54.0.windows.1`
- Node.js: `v24.16.0`
- npm: `11.13.0`
- Python: `3.13.14`
- Project npm dependencies: none

## Java

- Default shell Java: Temurin `21.0.11`
- Project build Java: Temurin `17.0.19`
- Project JDK path: `C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot`
- Gradle confirmed Launcher JVM and Daemon JVM `17.0.19`.
- Other installed JDKs were preserved.

## Android Studio and SDK

- Android Studio: `2026.1`
- SDK: `C:\Users\nikit\AppData\Local\Android\Sdk`
- ADB: `1.0.41`, platform-tools `37.0.0-14910828`
- Emulator: `36.6.11.0`
- Command-line tools / sdkmanager: installed, version `20.0`
- Platforms: Android 35, Android 36 and Android 36.1
- Build Tools: `35.0.0`, `36.0.0`, `36.1.0`, `37.0.0`
- NDK: `23.2.8568313` (r23c)
- CMake: `3.22.1`
- Emulator hypervisor: active through WHPX

`ANDROID_HOME` and `ANDROID_SDK_ROOT` remain unset globally. Builds are reproducible because the Cocos build profiles and Gradle session use explicit local paths.

## Cocos Creator

- Required version: `3.8.8`
- Installed version: `3.8.8`
- Executable: `C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe`
- File and product version: `3.8.8`
- No project upgrade was performed.

## Generated Android toolchain

- Gradle wrapper: `8.11.1`
- Android Gradle Plugin: `8.10.1`
- compileSdk: 36
- targetSdk: 35
- minSdk: 21
- Emulator ABI: x86_64
- Release ABIs retained separately: arm64-v8a and armeabi-v7a

## Emulator profiles

- `MTR_Pixel_8_Pro_API_35`
- `MTR_Galaxy_S25_Ultra_API_35`
- `MTR_Galaxy_S25_Ultra_Android_16`

The final QA target is Android 16/API 36, 1440×3120, 500 dpi, 12 GB RAM, 8 vCPU, 120 Hz-capable, Google APIs x86_64.

## Non-blocking warnings

- CMake/AGP reports an SDK XML version warning because the intentionally retained CMake 3.22.1 toolchain reads metadata produced by newer Android Studio packages. Both full and incremental builds succeed.
- The debug runtime cannot enumerate network interfaces under current Android SELinux policy; this only affects automatic V8 debugger address discovery.
