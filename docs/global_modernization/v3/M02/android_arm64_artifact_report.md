# M02.5 current ARM Android artifact report

Date: 2026-07-22  
Status: `PASS FOR M02.5 / ABI-VALID DEBUG-SIGNED APK / RELEASE STILL BLOCKED`

## Accepted boundary

- Build config: `build-android.json`, Cocos Creator `3.8.8`, `debug=false`.
- Requested ABIs: `arm64-v8a` and `armeabi-v7a`.
- Shared logical content identity: `mtr-v3-source-a5c4bdbb2fca`.
- Identity baseline: `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2`.
- Identity file SHA-256: `F8362EC17295FD646E335C501B40A24871E3B40C1CBA22B6A4C0F36AD9313395`.
- Physical installation: deliberately not performed. `adb devices -l` contained only `emulator-5554` before the build.

## Controlled build

Accepted command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 `
  -ConfigPath build-android.json `
  -LogDest creator-android-arm64-m02_5-20260722-retry1.log `
  -TimeoutSeconds 1800
```

Results:

- wrapper exit `0`; Cocos raw exit `36` accepted only with `build Task (android) Finished`;
- Cocos task duration `1 min 37 s`; platform artifact state `BUILT`;
- clean post-package Gradle `assembleDebug`: `BUILD SUCCESSFUL in 6m 26s`, 98 actionable tasks;
- Cocos log SHA-256 `DFE7BBB2DED03B795D80077DDF2ECE8BAAD03D9066C2908E968F6A3512854968`;
- Gradle stdout SHA-256 `34B76D94251CC063B260E8C57C613EAEBB6F2112FC903B2C8E29F1F7117A3064`;
- payload guard: current runtime menu, native QA route, styled name flow, bonus PNG pack and the developer unlock contract present; the unlock value is redacted from evidence; obsolete menu layer and `prompt(...)` absent.

The first launch was interrupted at 14 seconds by an incorrectly short outer shell timeout while the owned Cocos child continued. Its exact process tree was verified and terminated before retry. The accepted retry used the intended 1800-second shell timeout and a new log name. The partial attempt is not evidence and no concurrent Cocos/Gradle process was permitted.

## Artifact inspection

Artifact:

`build/android/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`

| Field | Accepted value |
| --- | --- |
| Size | `157,054,042` bytes |
| SHA-256 | `761FE83F4DE11AD5502A8FE18E3ED4123C2A86118EC2A8DC1AD259C0D5B69279` |
| Package | `com.martyskin.trudrunner` |
| Label | `Martyshkin Trud Runner` |
| Version | `versionCode=1`, `versionName=1.0` |
| SDK | `minSdk=21`, `targetSdk=35`, `compileSdk=36` |
| Native ABIs | `arm64-v8a`, `armeabi-v7a` |
| Signature | v1/v2 verified; Android Debug certificate SHA-256 `139926D41F6BA30D3B442CC3D3EE1DB53A23E20677BD53D3F79C041D216E7D7C` |

Native payload was checked independently of names:

- `lib/arm64-v8a/libcocos.so`: `72,434,000` bytes, ELF class 2, little-endian, machine `0x00B7` (`AArch64`) — PASS;
- `lib/armeabi-v7a/libcocos.so`: `47,873,636` bytes, ELF class 1, little-endian, machine `0x0028` (`ARM`) — PASS.

The artifact is therefore ABI-valid for arm64 and also contains a 32-bit ARM fallback. This is static compatibility evidence only: no physical-device install or launch was performed. It is debug-signed because the project config has `useDebugKeystore=true` and the project wrapper intentionally performs `assembleDebug` to prevent stale packaged assets. This satisfies M02.5 artifact/ABI integrity only; it is not a production release APK.

## Limitations and next gate

- Development static gate `qg.20260722082348.cb31e1f5e6da`: `8/8 PASS`, zero findings, source stable; report SHA-256 `65055CC4B661CDD97D7DC0181A7F7BC5B0CC828216D753FB6B246774D241B3D0`.
- No physical device was installed to or launched.
- No upgrade compatibility with a production signing key is claimed.
- No production APK/AAB, Play target or Pages deployment is claimed.
- M02.2–M02.5 technical entry gate for M03 is now satisfied; signing/distribution and Pages remain independent release blockers.

Next safe package: M03.1 read-only GameRoot responsibility/call/event/timer/listener/scene-binding inventory.

Rollback: delete ignored `build/android` and build logs, then revert this report/summary/index update. No device rollback is required.
