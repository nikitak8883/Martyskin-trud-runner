# Restore session log

- Session: `2026-06-18_12-37`
- Initial diagnostic completion: `2026-06-18 12:43 +03:00`
- Build/runtime continuation completion: `2026-06-18 14:10 +03:00`
- Transfer directory: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617`
- Project root: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`
- Final mode: authorized environment completion, build and runtime QA

## Main actions

1. Verified all transfer artifacts, extracted files and existing releases by SHA-256.
2. Confirmed Cocos Creator `3.8.8` at `C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe`.
3. Installed and verified Temurin JDK `17.0.19` alongside the user's existing JDKs.
4. Installed Android command-line tools, API 35/36, Build Tools 35/36, NDK r23c and CMake 3.22.1.
5. Created Android 15 development AVDs and the final Android 16 S25 Ultra-oriented AVD.
6. Generated and browser-smoke-tested a fresh Web build.
7. Generated an x86_64 Android project and completed the native Gradle/CMake/NDK build.
8. Installed and launched the APK on the Android 16 emulator.
9. Captured UI tree, screenshots, logcat, memory, ABI, display, GPU and lifecycle evidence.
10. Re-ran `:CocosGame:assembleDebug` with explicit JDK 17 and SDK paths; the build was reproducibly successful.

## Integrity and build results

- Transfer artifacts: 7/7 SHA-256 matches.
- Full transfer manifest: 7,144 checked, 0 missing, 0 mismatches.
- Existing release checksums: 3,860 checked, 0 missing, 0 mismatches.
- Project validator: passed.
- Fresh Web build: passed; 3,859 files; browser console had no errors or warnings.
- Fresh Android x86_64 native build: passed.
- Incremental Gradle verification: `BUILD SUCCESSFUL` in 17 seconds.
- APK SHA-256: `1A01EF50382E07EE8C357270E1F07ABB1D0E7E7EA646F72CCFEC5E938DC3C65D`.
- Android cold launch: passed in 1,556 ms.
- Crash/ANR buffer: empty.

## Safety

- No important project data was deleted.
- No Cocos version upgrade or project migration was performed.
- JDK 26/21 installations were not removed; JDK 17 is selected only for the project build.
- Release ARM ABI configuration remains separate from the x86_64 emulator configuration.
- Git metadata was not restored in place because that remains a deliberate, separate operation.
