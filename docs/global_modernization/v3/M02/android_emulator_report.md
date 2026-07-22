# M02.4 Android emulator build and runtime report

Date: 2026-07-22  
Status: `PASS FOR M02.4 / RELEASE STILL BLOCKED`

## Accepted boundary

- Target: Cocos Creator `android-emulator`, debug, ABI `x86_64`.
- Runtime target: AVD `MTR_Pixel_8_Pro_API_35`, serial `emulator-5554`, product/model `sdk_gphone64_x86_64`.
- Emulator-only guard: `ro.kernel.qemu=1`; boot marker `sys.boot_completed=1`.
- Physical devices observed and ignored: `0`.
- Shared logical content identity: `mtr-v3-source-a5c4bdbb2fca`.
- Identity baseline: `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2`.
- Identity file SHA-256: `F8362EC17295FD646E335C501B40A24871E3B40C1CBA22B6A4C0F36AD9313395`.
- M02.4 changed build/runtime evidence and documentation only; packaged source remains the accepted M02.2 identity.

## Toolchain and build evidence

The strict toolchain probe used `-EnsureEmulator -FailOnNotReady -FullJsonOutput` and returned `qaReady=true`, zero blockers, policy `emulator-only-default`. Native status:

- `logs/android-toolchain-status-20260722-103627.json`;
- size `19,670` bytes;
- SHA-256 `F5AD59C04A5369C98BF215B50A98808CBB2228FD5C0913EA203541943660A1F0`.

Fresh Cocos command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 `
  -ConfigPath build-android-emulator.json `
  -LogDest creator-android-emulator-m02_4-20260722.log `
  -TimeoutSeconds 1800
```

Results:

- wrapper exit `0`; Cocos raw exit `36` accepted only because the log contains the terminal `build Task (android-emulator) Finished` marker;
- Cocos task duration `54 s`; output state `BUILT`;
- clean Gradle `assembleDebug`: `BUILD SUCCESSFUL in 2m 27s`, 96 actionable tasks;
- Cocos log SHA-256 `756726D2A8CD564E10B0FA7E898855FB7AD34F6D7543CF8ED1845DF4652F328B`;
- Gradle stdout SHA-256 `429BE54DD79333CC542F8F24EA97AD60680C6D1F371FDD50DED1050008781281`;
- payload guard: current menu route, native QA bridge, styled name flow, new bonus PNG pack and the developer unlock contract present; the unlock value is redacted from evidence; obsolete main-menu layer and browser `prompt(...)` absent.

## APK and install evidence

Artifact:

`build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`

| Field | Accepted value |
| --- | --- |
| Size | `142,882,685` bytes |
| SHA-256 | `EA6A79D4DB30FFAD240AF58CA7D8890EDD197A20DFA8FE23921FC6530E78835D` |
| Package | `com.martyskin.trudrunner` |
| Version | `versionCode=1`, `versionName=1.0` |
| SDK | `minSdk=21`, `targetSdk=35`, `compileSdk=36` |
| Installed ABI | `primaryCpuAbi=x86_64`, no secondary ABI |
| Activity | `com.martyskin.trudrunner/com.cocos.game.AppActivity` |
| Signature | v1/v2 verified; Android Debug certificate SHA-256 `139926D41F6BA30D3B442CC3D3EE1DB53A23E20677BD53D3F79C041D216E7D7C` |

Before install the serial was revalidated with `ro.kernel.qemu=1`. `adb -s emulator-5554 install -r ...` returned `Success`; no physical serial was addressed. The debug certificate is acceptable only for this emulator evidence and does not satisfy production signing.

## Full emulator QA

Matrix command executed all 13 canonical UI states and all 15 levels:

- status `pass`;
- cases `28/28 PASS`, failures `0`;
- native query, expected marker, menu gate, background and asset-summary gates passed for every case;
- fatal, deprecation and product-warning counts `0`; unexpected Cocos errors/warnings `0`;
- raw summary `docs/qa/20260722_m02_4_android/matrix/android_matrix_cycle1_summary.json`;
- raw summary size `33,257` bytes; SHA-256 `555629203E44570AB8801C0E68598A84E8CABEF6AA900E331C6EE5A3E5A489EA`.

Interaction/restart/soak command results:

- jump, dash, pause and resume touch flow: `PASS`, marker latency `357–383 ms`;
- editable primate name: typed `QAPrimateC1`, saved and restored after cold restart exactly;
- restart/retry loop: `10/10 PASS`, latency `438–475 ms`;
- soak: requested `300 s`, actual `300.623 s`, 328 input bursts, 17 state actions, zero process losses;
- observed states: `playing`, `paused`, `clear`;
- memory PSS: first `219,264 KiB`, peak `255,892 KiB`, final `206,628 KiB`; this bounded run has no monotonic leak signal, but performance ownership remains M10;
- all interaction/soak fatal, deprecation, product-warning and unexpected Cocos diagnostic counts are zero;
- raw summary `docs/qa/20260722_m02_4_android/interaction/android_interaction_cycle1_summary.json`;
- raw summary size `9,944` bytes; SHA-256 `7BCE5F9B71AC64B3718B7C52AD461CF76A58D7069778969D21DD57A77FFFFF1B`.

The ignored raw evidence set contains 81 files / 189,629,869 bytes, including 43 PNG screenshots and 32 logcat captures. Manual visual review sampled the main menu, name editor, level selector, levels 1/8/15, pause, persisted name and final soak frame. No white matte fragments, missing platforms, invalid menu background, stale under-text or broken compositing were observed.

## Review and limitations

- Preliminary development static gate `qg.20260722080310.cb31e1f5e6da`: `8/8 PASS`, zero findings, source stable; dirty-source authorization was explicit for this pre-commit evidence pass. Report SHA-256 `F7390695D2D196F9490AEC52750613F93D13B41FF7978C78A4DD3FE3FFE7F8E1`.
- Accepted clean-source static gate on `233e1cb03c0be213752c469eee74625d49de2bd1`: `qg.20260722080624.cb31e1f5e6da`, `8/8 PASS`, zero findings, source clean/stable and dirty authorization disabled. Report SHA-256 `F41F737C294C87E3ECBD58E9000D42362F74F9148EC969C6DD40EB52A28E0A95`.
- Build config, package metadata, signature, installed package state, all raw summaries and representative frames were inspected independently of the QA scripts' top-level PASS.
- The live emulator process keeps its empty startup stdout/stderr handles open; those two process-owned files are not canonical evidence and were not falsely hash-claimed.
- Cocos emitted known engine-cache/module fallback warnings; Gradle emitted existing deprecation notices. Neither produced a product warning in matrix/interaction diagnostics.
- No gameplay source, scene, runtime asset, signing material or physical-device state changed in M02.4.
- No production-signing, device-arm64, AAB, Pages or release-ready claim is made.

Next safe package: M02.5, a fresh ABI-valid arm64-v8a APK inspected for package/version/ABI/signature/content identity without claiming physical-device validation.

Rollback: delete the ignored emulator build/raw evidence and revert this report, summary and M02.4 index updates. No runtime rollback is required.
