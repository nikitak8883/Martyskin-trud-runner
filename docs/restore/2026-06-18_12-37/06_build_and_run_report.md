# Build and run report

## Project validation

The project validator passed:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present.
```

## Fresh Web build

- Builder: Cocos Creator 3.8.8
- Output: `build\web-mobile`
- Files: 3,859
- Browser smoke test: passed over local HTTP
- Canvas: 1280×720 CSS / 2560×1440 internal
- Browser console errors: 0
- Browser console warnings: 0
- Note: Creator completed the build but its Electron CLI process remained alive; only that build process was stopped.

Because Creator 3.8.8 truncates an absolute `--project` value at the space in `C:\Projects\Monkey Work`, the successful safe invocation used the project directory as the working directory and `--project .`.

## Fresh Android emulator build

- Output profile: `build-android-emulator.json`
- Package: `com.martyskin.trudrunner`
- App label: `Martyshkin Trud Runner Emulator`
- ABI: x86_64 only
- Debuggable: yes
- compileSdk: 36
- targetSdk: 35
- minSdk: 21
- Gradle: 8.11.1
- Android Gradle Plugin: 8.10.1
- JDK: Temurin 17.0.19
- NDK: 23.2.8568313
- CMake: 3.22.1
- Full native build: passed, including 700 C/C++ steps
- Incremental verification: `BUILD SUCCESSFUL` in 17 seconds, 70 tasks, 2 executed and 68 up-to-date

APK:

```text
build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
```

- Size: 135,641,341 bytes
- SHA-256: `1A01EF50382E07EE8C357270E1F07ABB1D0E7E7EA646F72CCFEC5E938DC3C65D`

## Android 16 runtime

- AVD: `MTR_Galaxy_S25_Ultra_Android_16`
- API: 36
- Display: 1440×3120 at 500 dpi
- Runtime orientation: landscape, 3120×1440
- RAM: 12 GB
- CPU: 8 x86_64 vCPU
- GPU: Android Emulator OpenGL ES Translator on AMD Radeon 890M
- GLES: 3.1
- Physical display mode: 120 Hz-capable
- Install: passed
- Cold launch: 1,556 ms
- Hot resume after Home: 143 ms
- Process survived background/resume with the same PID
- Foreground activity: `com.cocos.game.AppActivity`
- PSS after startup: approximately 222 MB
- Crash buffer: empty
- ANR/fatal signal: none

Runtime markers confirmed:

- `Cocos Creator v3.8.8`
- `MTR_RUNTIME_CORE_READY`
- `Success to load scene: db://assets/scenes/main.scene`
- `MTR_MENU_UI_GATE_READY`
- Main-menu backgrounds and themed UI sprites loaded successfully.

## Visual result

The main menu renders correctly with Russian labels and expected assets. The game preserves its 16:9 design inside the S25 Ultra's 19.5:9 landscape screen, producing intentional side mattes rather than Android compatibility letterboxing.

Evidence is stored in `android-emulator-qa\`; see `09_android_emulator_qa.md`.

## Existing release integrity

- Existing ARM release APK and Web release checksums remain fully valid.
- The ARM release profile remains separate and unchanged in ABI intent.
- Real-device ARM/One UI runtime validation is the next external test, not a blocker for local restoration.
