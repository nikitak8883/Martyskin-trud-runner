# Android native lifecycle: retained Intent and bootstrap diagnostics

Status: retained-Intent repair verified on emulator; broader acceptance partial.
Parent: `ANDROID-NATIVE-BOOTSTRAP-001` / `M04-C-FAMILY-THEME-LOGISTICS` / `M12.7`.
No new roadmap unit/acceptance credit; `20/73`,53 mandatory +7 conditional remain.

## Bounded diagnosis before modification

Original failed cold launch remains immutable: APK
`7CBCDCADA60E0A4B6B1D7F4869FC61C20E0B47D6A9FBB363B6E0DB709F4BCFA4`.
All new laboratory receipts are under root `temp/native-bootstrap-20261001`.
Immediate cold baseline A reaches menu in10169ms. Stable density recreation
480->500->480 succeeds in the same PID3323, rebuilding native game threads and
preserving the original menu query. Early density timings250ms and1100ms reach
menu; the1100ms case includes actual destruction/recreation during native startup.
These controls do **not** reproduce/close the original pre-window boot failure.

Additional negative control `new-intent-baseline-a`: launch menu, deliver levels
Intent without force-stop, change density. After Activity recreation the game
returns **menu**, not **levels**; expected levels marker times out at35099ms.
Original queryLength14 reappears, with menu/screen/UI-gate markers. The failed
control and density restoration are preserved. This is a confirmed separate
retained-Intent defect, not proof of the cause of the original blank screen.

## Intended narrow change

- Project `AppActivity.onNewIntent()` retains the new Intent before the existing
  query bridge/super/SDK forwarding. No hot-runtime navigation is introduced:
  the test deliberately checks the next genuine Activity recreation.
- Debuggable APKs log numeric lifecycle instance/uptime/configuration evidence,
  before and after Cocos/SDK callbacks; non-debuggable builds return before trace
  work. No Intent/URI/query/name/credentials are logged. No manifest/SDK/Gradle,
  engine library, art or shared gameplay/config changes.
- New emulator-only QA checks exact installed/local APK SHA, user0, silence,
  existing-process new Intent, actual saved-state recreation, original density
  restoration and fresh-process default menu. Fixed35s, zero retries, immutable
  output directory; restoration in finally. Static contracts are expressly not
  Java execution or runtime acceptance.
- Silent-launch inventory recognizes compact and spaced argument arrays; the
  new eighth runtime launcher must not be skipped by whitespace differences.
- Canonical static gate grows35->36 mandatory steps; roadmap denominator does
  not change. Atlas revision4/tool pins/thresholds/schedules remain unchanged.

## Required acceptance

First new-APK focused run is retained as FAIL4/5 under project
`temp/native-bootstrap-20261001/lifecycle-cycle1-postinstall/report.json`.
The actual retained-Intent/recreated/restored levels cases pass in PID2900;
normal fresh menu also renders, but the first harness incorrectly required QA
query/screen markers for a launch with no QA Intent. Source `GameRoot` explicitly
emits those only when query parameters exist. Harness successor therefore checks
their **absence** for the default case plus the unchanged genuine menu UI gate;
all queried cases retain both strict markers. No product code or timeouts changed
for this harness correction. Instance identity now proves both real recreations.

Fresh Android/Web builds were produced from clean root commit
`1e3e347a125b471cab7d647d306575251d792d35`. Gradle clean/assembleDebug succeeded:
96 tasks,85 executed. Current debug APK SHA256 is
`7A771D566B9BFA1A10E26919DFF04289A2F16E923714EA706FF4F8767A302147`.
It is x86_64/emulator-only, NOT a release/device-valid artifact. Successor
`6b4198038dced235d6f7ebf7700f428b03ce0c3c` changes only the harness/contracts/docs;
native/shared/art/build inputs match the actual build source. Original installed
APK was extracted before replacement and retains its exact baseline SHA.

Four separate focused lifecycle cycles pass5/5 each. Two full startup/UI Android
matrices pass28/28 each:13 interface states plus all15 level startups. These do
NOT constitute full campaign gameplay, all skin/bonus combinations or Release
acceptance. All cases use emulator-5554/API35/x86_64,user0,host `-no-audio` and
verified media stream3=0. No physical device was selected. Both density changes
prove new Activity instance/same process; fresh default launch proves new process
and absence of stale QA query markers. Fixed35s timeout/zero retries unchanged.

Project-relative receipts under `temp/native-bootstrap-20261001`:

| Receipt | Result | SHA256 |
| --- | --- | --- |
| lifecycle-cycle1-successor/report.json | 5/5 | 6D09824A1EAFA0BF416E6A68E9ED1BE35E262325384DD9BD47DCC3371B14E64F |
| lifecycle-cycle2-qualified-cold/report.json | 5/5 | C4310F50AE62AFF792E2F737EB1066929FA7EFA1B5A7A5D6C1ACE0B916F64B5D |
| lifecycle-cycle3-stable/report.json | 5/5 | E85330C1DA5CE6B075B71F9F251FC61089D9DB7F7C45B297BEE505693F5BC93C |
| lifecycle-cycle4-cold-settled/report.json | 5/5 | F5069A35786C5384D01F2A8CE3985F70BFB46ECC7C6EBD781A397852EC4D3B35 |
| android-matrix1/android_matrix_cycle1_summary.json | 28/28 | AFB2DB94961E2C0C8E295A01CFAEEBB27C3FF36391C8558DE6377963E61FE7E7 |
| android-matrix2/android_matrix_cycle2_summary.json | 28/28 | 7484651EB10E8EB80E519BE5A5B1496CE72DA0D4B76217EC7237291FF36E5650 |
| static-native-precloseout/report.json | 36/36 | E84724445BB2917BE469F97305CA6D260F3D0826AB92A966FF3C33665F11290D |

The static receipt proves clean/stable exact source6b419803. Its72 stdout/stderr
artifacts were copied to `static-native-precloseout/artifacts-preserved` and
verified against every report SHA before another gate run. Full matrix fatal,
deprecation, product-warning and unexpected-Cocos error/warning counts are0;
known SDK transport noise remains recorded rather than suppressed. Sampled visual
review: initial menu, recreated level menu,level02 andlevel15 screenshots.
Scoped Codex review checked Intent ordering, debug-only numeric diagnostics,
callback forwarding, installed APK/user/audio identity, real recreation proof,
finally restoration, default-launch distinction and report fail-closed behavior.
No additional product patch was needed. Static source contracts are not a Java
execution substitute. External CodeRabbit/local-model review: NOT_RUN this slice.

Web build is valid but Web runtime regressions are **NOT_RUN**: the localhost
server-start command was rejected by execution policy before execution. No
server/QA was launched; no alternate shell/tool/encoding/elevation workaround
was attempted. Existing `--mute-audio` contracts remain passing. Source-only
publication/hosted receipts are separate post-commit evidence, never inferred
from the predecessor CI or this local gate. Keep first-launch blank-screen issue
open unless the original failure boundary is proven resolved.
No atlas input admission/samples, physical-device install, signing/main/Pages or
Release claim is authorized by this diagnostic slice.

## Preserved orchestration controls and hygiene

The first new focused run remains FAIL4/5 (harness expectation, not repaired
product regression). A premature cold re-admission remains FAIL0/5 at the audio
guard, before any game case. Launcher admission failures and the caller's unset
`$LASTEXITCODE` mistake are retained separately. Corrected caller waits all
emulator/qemu residents to exit naturally, invokes the launcher via native pwsh,
and independently requires `qaReady` AND `coldBootConfirmed` before any runtime.
No protocol-pinned tool/boot/audio file was changed. Final owned AVD was stopped
after identity verification; zero emulator/qemu residents verified on closeout.

Failed controls, build logs, screenshots and the old APK are intentional audit/
rollback evidence. Prior cleanup policy rejection is preserved; no deletion
workaround, unrelated user changes, global hooks/model/power/config changes or
atlas input mutation. The intermediate handoff is historical, not current state;
use the final control handoff/checkpoint for continuation.

## Sources and rollback

Android states that a delivered new Intent does not automatically replace
`getIntent()`: [Activity reference](https://developer.android.com/reference/android/app/Activity#onNewIntent(android.content.Intent)).
Pinned Cocos3.8.8 creates the native application on INIT_WINDOW and tears down
its loop on destruction: [AndroidPlatform source](https://github.com/cocos/cocos-engine/blob/v3.8.8/native/cocos/platform/android/AndroidPlatform.cpp).
Installed SDK source was read; it was not modified. These facts guide diagnostics,
not a claim that either SDK is the proven source of the failed boot.

Rollback source-only: revert the bounded lifecycle commit; rebuild from that
clean predecessor. Do not overwrite failed receipts, alter SDK/global settings,
reset unrelated root changes or relabel old APK evidence as the new build.
