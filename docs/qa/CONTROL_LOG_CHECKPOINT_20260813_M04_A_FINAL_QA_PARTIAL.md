# M04-A safe-stop checkpoint: final QA partial

Date: `2026-08-13`  
Reason: explicit user stop request after the nearest safe action boundary.

## Progress checkpoint

- **Status:** `partial` — M04-A implementation and fresh artifacts are complete; final acceptance, hygiene, commit and publication are not complete.
- **Roadmap position:** M04 / M04-A (`M04.1 + M04.2`), final artifact acceptance boundary before M04-B.
- **Progress:** closeout plan `2/5 completed`, `1/5 in progress`, `2/5 pending`; current execution ledger remains `11/65` complete with `54` mandatory units remaining and `7` conditional units.
- **Evidence:** final Web build and recovery matrix passed; final Android emulator build/install and `28/28` matrix passed; router inherited-handle regression self-test passed.
- **Remaining:** Android touch/name/persistence/restart/soak recovery; post-router-patch review; final static/contract/hygiene gates; report reconciliation; commit; source subtree push.
- **Next:** run only the Android interaction recovery command below, then close validation and publish M04-A if every gate passes.

## Accepted state at stop

- Git root HEAD: `58d057c65098935e4b8c1b6c40f4965b45238dd5`.
- Local branch: `codex/mtr-source-freeze-v3`.
- Remote source branch before this pending patch: `mtr-source-v3` at `4492deee4209ef8b09dce9a7ab35db7f5831d623`.
- No M04-A commit or push was performed in this stop cycle.
- Android QA target: `emulator-5554`, `ro.kernel.qemu=1`, ABI `x86_64`, install user `0`.
- No physical Android device was used.
- App process was stopped at checkpoint; QA port `18785` is closed; no project Cocos Creator process remains.
- Unrelated dirty files outside this Cocos project remain intentionally untouched.

## Completed in this continuation

### Entrypoint lifecycle correction

The real final Web build reproduced a router lifecycle defect: Cocos' main process exited after writing the terminal success marker while renderer/crash descendants retained redirected stdout/stderr handles. The wrapper then waited indefinitely for EOF.

`tools/codex/MtrEntrypoint.psm1` now:

- always cleans the recorded descendant tree after accepted terminal success, including when the main process already exited;
- bounds redirected stream draining and fails closed instead of hanging indefinitely;
- includes a regression case that starts a descendant holding inherited redirects and proves that it is cleaned.

Self-test: `PASS`, including `inheritedRedirectHandleDescendantCleaned=true`.

### Final Web artifact and QA

- Fresh Cocos Web build: `PASS`; wrapper returned in `36.349 s` after the router correction.
- Packaged atlas manifest contains `mtr.atlas_manifest`, `contract_only_no_runtime_repack`, and `source_root_relative_posix` path conventions.
- Full recovery matrix: `34/34 PASS`.
- Interaction: `PASS`.
- Restart loop: `10/10 PASS`.
- QA server port `18785`: closed.

### Final Android emulator artifact and matrix

- Fresh x86_64 debug emulator APK: `PASS`.
- APK installation: `adb -s emulator-5554 install --user 0 -r ...` → `Success`.
- APK contains exactly one atlas manifest payload at `assets/assets/resources/import/8d/8d3862d0-8179-4c23-ab4d-9c5e6b9759f0.json` with the final path conventions.
- Full emulator matrix: `28/28 PASS`, failures `0`.
- Fatal, deprecation, product-warning and unexpected Cocos diagnostics: `0` in all accepted cases.

## Immutable local evidence

| Evidence | SHA-256 |
| --- | --- |
| `temp/m04-a-final-build/entrypoint-selftest.json` | `77F579D1C7D3D9F8F230265C4EE6B23D09772C6FA8E0B2D7CA3549125D148299` |
| `temp/m04-a-final-build-rerun/web-build-report.json` | `EBE2F67AC0C9F9F22BF143F3BDB039E988C36EEDC6327E8A2D1793806ED3E312` |
| `temp/m04-a-final-web/matrix-recovery.json` | `4EB25592EDAA83C027787B8EF1081EEFD69A66F69ACE3B3926F50AE1EE372311` |
| `temp/m04-a-final-android/android-build-report.json` | `C10A2D5F12B0DF393C924A232D6480125FDB6607041A8A52613AE2B73F991218` |
| `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk` | `1E399112CC8E3892B3A78403BA043D48EA0CA0DD027DA46F7B0C284A2580517E` |
| `temp/m04-a-final-android/apk-atlas-payload.json` | `662CE2FCD6CEC949581AB45BBE416493391A0AAFD900B4E5F3CA887D0894A0DF` |
| `temp/m04-a-final-android/matrix-recovery/android_matrix_cycle3_summary.json` | `12256E3E9A224EB277C74DC55DD902DE586A1F9379D5F8F8BFB909D5B80FA0C0` |

The build, APK, screenshots, logcat and temp reports are ignored local evidence and are not intended for the source commit.

## Exact resume order

1. Verify `git status --short -- .`, `adb devices -l`, `adb -s emulator-5554 shell getprop ro.kernel.qemu`, and the evidence hashes above.
2. Run the pending Android interaction recovery only:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File tools/codex/Run-MtrAndroidEmulatorInteractionQa.ps1 -Serial emulator-5554 -Cycle 3 -OutputDir temp/m04-a-final-android/interaction-recovery -RestartIterations 10 -SoakSeconds 30 -MarkerTimeoutSeconds 35
   ```

3. Review the new `MtrEntrypoint.psm1` diff independently; do not auto-apply advisory findings.
4. Reconcile `M04_A_CODE_REVIEW_REPORT.md` and `M04_A_VALIDATION_SUMMARY.json` with the final build/recovery hashes and set hygiene status only after gates pass.
5. Run the six direct M04-A tests, eleven negative fixtures, canonical asset/content/roadmap validators, final `23/23` static gate, rollback-blob checks, `git diff --check`, stale/debug/conflict-marker search, port/process checks and intended-scope status review.
6. Commit only the Cocos project M04-A files. Preserve all unrelated root changes.
7. Publish through the canonical subtree mechanism:

   ```powershell
   git subtree split --prefix=MTRCocosCreator_portable_transfer_20260617/MTRCocosCreator HEAD
   git fetch origin mtr-source-v3
   git merge-base --is-ancestor origin/mtr-source-v3 <subtree-commit>
   git push origin <subtree-commit>:refs/heads/mtr-source-v3
   ```

8. Verify the remote ref and rerun the M04-A Git-ancestry validator. Do not push the parent governance branch and do not start M04-B in the same closeout.

## Rollback and residual risks

- Source rollback remains governed by `docs/global_modernization/v3/M04/M04_A_ROLLBACK_MANIFEST.json`; validate every referenced pre-change Git blob before commit.
- The final APK is an x86_64 debug emulator artifact, not an arm64 production release.
- Release remains blocked by `M02.1`, `M02.7`, and `M12.7`.
- M04-B must not start until this pending closeout is committed, published and post-push validated.
