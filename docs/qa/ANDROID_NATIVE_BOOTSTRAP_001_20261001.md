# ANDROID-NATIVE-BOOTSTRAP-001

Status: **open**, technical follow-up under `M04-C-FAMILY-THEME-LOGISTICS`
qualification and final `M12.7` closure. No new roadmap unit or acceptance credit.
Not a signing/owner blocker; Codex can continue a bounded technical investigation.

## 2026-10-01 controlled pre-window mechanism supplement

Historical observations below are immutable failure evidence, not current
acceptance. A debug-only one-shot pre-window recreation subsequently reproduced
the native hang twice on diagnostic APK3F3831B3. The project-local Android native
guard at rootb3b82b13 repairs CLOSE before application creation by requesting the
existing app-thread exit; it leaves started-application cleanup unchanged.
Fresh APKD323FA64 passed four injected+normal pairs8/8, four retained-Intent
lifecycle cycles5/5 and two startup/UI/all15-level matrices28/28, all silently
on emulator/user0. See `ANDROID_PRE_WINDOW_DESTROY_REPAIR_20261001.md` for exact
identity and preserved negative controls. This confirms and repairs a controlled
mechanism; the original immediate-cold system-overlay trigger itself was NOT
replayed. Broader cold/overlay qualification and attempt02 input admission remain
open; no roadmap credit or Release acceptance follows from these controls.

## Observed failure

Current verified unpacked debug APK, SHA-256
`7CBCDCADA60E0A4B6B1D7F4869FC61C20E0B47D6A9FBB363B6E0DB709F4BCFA4`.
AVD `MTR_Pixel_8_Pro_API_35`, API35/x86_64, SwiftShader, emulator-5554/user0.
Host `-no-audio`; media stream3 verified zero. No builder or model task running.

On the first launch immediately after a confirmed no-snapshot cold boot,
`ui_menu` did not reach a native query or MTR screen marker within the unchanged
35s timeout. The process existed, but the captured screen was blank. Full matrix
result: `27/28`, not PASS. All later menu/level starts passed.

- Failed summary:
  `temp/qa-silent-boot-20261001/android-cycle2/android_matrix_cycle2_summary.json`
  SHA-256 `3DDCDBBE668A4D5254C89AE272FC23DBEBE809E43887EE5872597A2AAEA43496`.
- Log:
  `temp/qa-silent-boot-20261001/android-cycle2/ui_menu.logcat.txt`
  SHA-256 `29601319C95863EAE8E50F7E9B3D0ACA8434A1293474C46E304845C8D1D3E04C`.
- Screen:
  `temp/qa-silent-boot-20261001/android-cycle2/ui_menu.png`
  SHA-256 `6B2FFFA8466F9904677999ECF18E98383BCA060C8F0678BCE69DB423398A7AD6`.

## Trace facts and hypothesis

Log lines 470/1125 record process1680 and successful `libcocos.so` load.
Lines1243/1253 record APP_CMD_START/RESUME. Lines1318-1320 record changed
application resources/removed Android system overlay assets; lines1322-1348
record PAUSE, STOP, SAVE_STATE and DESTROY. No MTR initialization marker follows
in the captured first-case log. This supports an **unconfirmed hypothesis** of
early-boot resource/configuration recreation racing native initialization.
There is no proof yet of a particular Cocos/SDK implementation fault.

Separate controlled follow-up: a new cold boot followed by 30s settling passed
the complete unchanged matrix `28/28` (cycle3-settled). The original failed run
is preserved, not relabelled or replaced. This is evidence for a test-host
readiness condition, **not proof that native activity recreation is fixed**.
It does not establish the cause of atlas attempt01's load/FPS failure.

## Next bounded technical cycle

1. Recover these exact receipts and the AppActivity/AndroidManifest lifecycle
   source before changing anything. Freeze reproduction conditions and inspect
   the pinned Cocos3.8.8 native activity lifecycle; do not patch the whole SDK.
2. Distinguish boot readiness from a genuine recreation defect. Keep an
   immediate-after-boot negative/reproduction run plus a settled positive
   control; verify activity/process identity, query bridge and first frame.
3. Reproduce resource/configuration recreation after stable startup with logs
   and state/save assertions. If a product defect is confirmed, scope the
   smallest native fix, fresh Android build and Web parity checks.
4. Require the relevant lifecycle tests and full matrices after any fix.
   Never increase the marker timeout, hide diagnostics, insert a success retry
   or call a fixed prelaunch wait the product fix.
5. Resolve input-admission risk before attempt02 measurements. The preregistered
   protocol already defines symmetric 30s post-install settling, but this issue
   stays open until its runtime acceptance boundary is explicitly established.

Physical/device Release, signing, Pages publication and full campaign/skin-bonus
acceptance remain outside this tooling qualification.
