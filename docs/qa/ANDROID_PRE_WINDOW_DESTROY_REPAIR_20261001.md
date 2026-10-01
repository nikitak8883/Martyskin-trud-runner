# Android pre-window destroy — controlled mechanism repaired and runtime-verified

Parent: ANDROID-NATIVE-BOOTSTRAP-001 / M04-C-FAMILY-THEME-LOGISTICS / M12.7.
No roadmap credit added:20/73,53 mandatory +7 conditional remain.

## Evidence and reproducible boundary

Original cold failure showed APP_CMD_DESTROY before INIT_WINDOW and no game
initialization. Zero-delay density control on current7A771D56 APK reaches menu
in7166ms but sets density before Activity create; it does not test recreation.

Debug-only,one-shot fault injection hides the initial Surface then requests
Activity recreation. Opt-in boolean extra is consumed before recreation; both
debuggable APK and null saved state required. It is not added to JS query keys,
not enabled in release or normal launches,not a host wait/retry workaround.
Fresh diagnostic APK3F3831B38AE62F5AD57ABE9164D89F0C74471947B6D004426E6971C840CE6133
was built from clean root2bcb613013251d7e14029d36589158aaf60df0b9.
Normal control passes10419ms. Two separately preserved injected runs fail:
36133ms/PID3286 and36336ms/PID3709. Both prove exactly one request,DESTROY before
any INIT_WINDOW,one old instance,no menu,no return from Cocos onDestroy,no fatal.
These are controlled failures,not claimed as a reproduction of the original
system overlay trigger. Root-relative receipts:
`temp/native-pre-window-20261001/pre-window-negative-a` and `-b`.
SIGQUIT reacted/wrote a tombstoned trace; native debuggerd refused root. No root
escalation/bypass was attempted; full backtrace is NOT_AVAILABLE in this slice.

Installed Cocos3.8.8 native glue does not set destroyRequested on DESTROY and
waits for app-thread completion. AndroidPlatform emits CLOSE,then its loop waits
for destroyRequested. The usual close listener exists only after cocos_main
creates an application/Engine. Thus pre-window destruction lacks that exit
path. Source and two failing controls support the diagnosis. The four paired
fixed controls below verify this mechanism, not the original system overlay trigger.

## Narrow project-local repair

Android-only MtrPreWindowLifecycle.cpp binds a native WindowEvent listener at
library load. For CLOSE **only when current application is empty**,request the
existing platform exit on the same native app thread. Started-app close returns
unchanged,retaining normal JS/game cleanup. Listener lifetime spans Activity
recreations; no polling,thread,force-kill,global SDK edit or configChanges mask.
Local Android CMake registers this source; common/Web/native-other targets are
unchanged. Optional debug trace contains only a fixed event marker.

Dedicated silent emulator-only QA requires exact installed APK,user0,one-shot
pre-window destroy,actual new instance/saved-state create,guard callback marker,
complete native destroy and final menu;35s/zero retries,immutable outputs.
Normal control must have no injected request. Failed runs remain failures.

## Verified build and runtime acceptance

Fresh repair build belongs to clean root
`b3b82b1364a85bab59381be89ab98969a26129c6`, not its documentation successor.
Cocos export passed; Gradle clean/assembleDebug passed in2m51s with96 tasks
(85 executed). Repair compilation is explicit in
`logs/gradle-android-postpack-20261001-162619.out.log` line1274:
`MtrPreWindowLifecycle.cpp.o`. Debug/x86_64 APK SHA-256:
`D323FA64E4536634D8CCAAFA70FDDD2085EA1E994313F9C948E8DA1BE610392B`.
Every focused run verifies installed APK equality and user0. This is an
emulator artifact, not a signed/device-valid Release APK.

AVD MTR_Pixel_8_Pro_API_35/API35/x86_64/SwiftShader/emulator-5554/user0;
host -no-audio plus fail-closed verified media stream3=0. No build/model/static
work overlapped runtime. The owned AVD was stopped; zero emulator/qemu residents
verified after the final cycle. Product audio/preferences remain unchanged.

App-relative receipt base: `temp/native-pre-window-20261001`.

| Cycle | Injected | Normal | Injected / normal marker wait ms |
| --- | --- | --- | --- |
| repair-pair1 | PASS | PASS | 10092 / 9223 |
| repair-pair2 | PASS | PASS | 9677 / 9155 |
| repair-pair3 | PASS | PASS | 10123 / 9253 |
| repair-pair4 | PASS | PASS | 9448 / 9293 |

All injected receipts prove one request, DESTROY before first INIT_WINDOW,
guard exit marker, completed Cocos destruction, actual new instance/saved-state
create, final focused menu and no fatal. Normal controls have no injected request
or early guard callback. This is8/8 acceptance without retry/timeout inflation.
The two negative receipts remain FAIL; they are never overwritten/relabelled.

- `lifecycle-repair-cycle1` through `cycle4`:5/5 each; retained-Intent/newIntent,
  actual density recreation/restoration and no stale query on a default start.
- `android-repair-matrix1/android_matrix_cycle1_summary.json`:28/28;
  SHA `EDE39EE8A5A064EBFEDD6BD8DA87C544E7E8C8E4817B7B6258885CD1BA6B89A1`.
- `android-repair-matrix2/android_matrix_cycle2_summary.json`:28/28;
  SHA `9333024A8A084525BED0D2550A6CC5515C01F6EA4A6A5A1B4E165CF21C661E91`.
- Each matrix covers13 UI starts + all15 level starts. Fatal/deprecation/product
  warning/unexpected Cocos error/warning counts are zero. Existing allowlisted
  engine diagnostics remain84 errors/28 warnings per matrix; not hidden as zero.
- Scoped Codex review and three actual screenshots (recreated menu, level02,
  level15) found no new confirmed defect. This is sampled visual QA, not full
  campaign/all-skin acceptance. External CodeRabbit/local-model review NOT_RUN.
- Native static contracts14/14 passed four times; audio inventory covers9
  Android QA launchers. Full clean36-step gate and exact source-only hosted CI
  must be read from their post-documentation receipts; older hosted run36864040175
  validates predecessor7f081308, not this repair.

## Remaining acceptance boundary

Original cold system-overlay trigger has NOT been replayed. The controlled
pre-window mechanism is fixed. A subsequent preregistered AB/BA/AB/BA cold-boot
cohort passes8/8 (four immediate, four separately30s-settled arms) on this exact
APK, then another28/28 Android UI/all15-level startup matrix. All silent/user0;
no artificial immediate wait/retry, installed hashes verified, zero residents.
Eight broad resource candidates are game DEV_OVERLAY markers, not system events;
original trigger remains NOT_OBSERVED. This completes only that bounded cold
cohort, not wider system-overlay qualification. Actual repair source9c0a9992
hosted36875609617 passed Windows/Linux36/36 with all artifact hashes verified.
See `ANDROID_COLD_BOOT_COHORT_20261001.md` for immutable failures/timings/SHAs.
Web/shared/art/build inputs are unchanged, but Web runtime
remains NOT_RUN due prior server-start policy rejection; never bypass that
rejection. No full campaign/all-skin/atlas attempt02, phone, signed/device-valid
release, main/Pages or Release claim by this repair. Attempt02 must lock fresh
inputs and symmetric native repair semantics before timed sample admission.

Raw diagnostics,source-pinned build and baseline APK backups retained privately.
Hygiene: preserve unrelated user changes,failed controls and permitted evidence;
no new global hooks/models/power/config changes. Rollback by reverting only this
project-local repair/instrumentation slice and rebuilding the exact predecessor.

## References

[Android Native App Glue contract](https://developer.android.com/reference/games/game-activity/group/android-native-app-glue)
requires completing the app thread on destruction. Installed SDK source was read
without modification; [Cocos AndroidPlatform3.8.8](https://github.com/cocos/cocos-engine/blob/v3.8.8/native/cocos/platform/android/AndroidPlatform.cpp)
and [Engine3.8.8](https://github.com/cocos/cocos-engine/blob/v3.8.8/native/cocos/engine/Engine.cpp)
provide the lifecycle context. The packaged glue source,not a guessed upstream
URL,is authoritative for this host;the guessed raw external source URL returned404.
