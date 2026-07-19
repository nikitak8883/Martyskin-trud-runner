# MTR two-cycle audit checkpoint — cycle 1 complete

Date: 2026-07-14  
Workspace: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Scope: audit and QA cycle 1 for Web and Android  
Android target: emulator only (`emulator-5554`, API 35, x86_64)  
Physical-device actions: none

## Result

Cycle 1 is complete and accepted. All product gates are green after the fixes recorded below.

| Gate | Result | Evidence |
|---|---:|---|
| Project-only TypeScript compile | PASS | Cocos-compatible `tsc -p tsconfig.json --noEmit --skipLibCheck --lib es2020,dom --isolatedModules false` |
| UI IR validator | PASS | 14/14 screens, 209 nodes, 75 buttons, 0 problems/warnings |
| Skin/bonus validator | PASS | 576/576, 0 blockers/warnings |
| Asset validator | PASS | 1,528 PNG, 0 missing meta, 0 white-matte suspects |
| Config/Web-Android contract | PASS | 15 levels, 15 backgrounds, native/Web query parity |
| Web interaction/restart/soak | PASS | 300.446 s, 39 input bursts, 3 clear-to-playing transitions, 0 console errors/warnings |
| Android screen/level matrix | PASS | 28/28: 13 UI states plus all 15 levels |
| Android touch/FSM | PASS | jump, dash, pause and resume markers plus screenshots |
| Android name entry/persistence | PASS | `QAPrimateC1` typed and preserved after cold restart |
| Android restart loop | PASS | 10/10, latency 436–479 ms (average 449.5 ms) |
| Android gameplay soak | PASS | 300.724 s, 319 input bursts, 17 state actions, 0 process losses |

## Product corrections made during cycle 1

`assets/scripts/GameRoot.ts` was corrected before the accepted builds:

- deprecated `view.getFrameSize()` was replaced by `screen.windowSize`;
- deprecated `LabelOutline.color/width` use was replaced by supported `Label` outline fields;
- invalid/no-op `EditBox` properties were removed;
- the post-`startLevel()` state check was made explicit for TypeScript control-flow analysis.

Both Web and Android were rebuilt after these corrections. The clean Android smoke contained no frame-size or label-outline deprecation messages.

## Android matrix and visual inspection

Machine summary:

- `docs/qa/evidence/20260714_two_cycle_resume/cycle1_android_matrix/android_matrix_cycle1_summary.json`
- 28 pass, 0 fail;
- every UI case had the expected QA marker and menu gate;
- every level had the expected gameplay gate, full background application, and asset-usage summary;
- fatal/ANR, product warnings, app deprecations, and unexpected Cocos warnings/errors: 0.

All 28 screenshots were inspected. No missing background, white cutout fragment, missing platform, stale under-label, or duplicated/onion UI layer was found.

## Android interaction, persistence, restart and soak

Accepted machine summary:

- `docs/qa/evidence/20260714_two_cycle_resume/cycle1_android_interaction_soak/android_interaction_cycle1_summary.json`

Touch/FSM evidence:

- jump pose wait: 373 ms;
- dash (`crouch_dash`) pose wait: 370 ms;
- `playing -> paused`: 372 ms;
- `paused -> playing`: 377 ms;
- all four states have screenshots and a combined logcat record.

Name entry evidence:

- native `CocosEditBoxActivity` received `QAPrimateC1`;
- editor was closed back to `AppActivity` before tapping the in-game PNG save button;
- after a process-stopped cold restart, UI Automator returned the same exact value;
- no player name was written to product logs by the application.

Restart evidence:

- ten independent seeded `over -> playing` retries passed;
- process remained alive on every iteration;
- fatal/deprecation/product-warning/unexpected-Cocos counts remained zero.

Soak evidence:

- actual duration: 300.724 seconds;
- states observed: `playing`, `paused`, `clear`;
- input bursts: 319;
- state actions: 17;
- process losses: 0;
- PSS start/peak/end: 197,383 / 246,762 / 207,873 KiB;
- PSS was not monotonic and returned close to its initial plateau after the peak;
- fatal/deprecation/product-warning/unexpected-Cocos counts: 0;
- six periodic/final screenshots show coherent progression from levels 1 through 4.

## QA-harness defects found and corrected

These were test-infrastructure defects, not accepted product failures:

1. The first manual name attempt tapped the game while Gboard still covered it. The accepted route now confirms return to `AppActivity` before tapping the save button.
2. The initial cold-restart harness reused a stale logcat `screen=name` marker from the prior PID. The harness now clears logcat at the process boundary and retains combined pre/post-restart logs.
3. PowerShell `$pid` conflicted with the built-in read-only `$PID`. The variable is now `appProcessId`.
4. The restart matcher assumed an internal mode name `FAILED`; the actual contract is `GAME_OVER`. The accepted matcher now checks the stable state transition `state=over->playing reason=start_level`.

The corrected reusable harness passed its 30-second self-test before the accepted five-minute run:

- `tools/codex/Run-MtrAndroidEmulatorInteractionQa.ps1`

## Web evidence

- `docs/qa/evidence/20260714_two_cycle_resume/cycle1_web_interaction_restart_soak.json`
- `docs/qa/evidence/20260714_two_cycle_resume/CYCLE1_WEB_INTERACTION_RESTART_SOAK.md`
- accepted Web soak: `cycle1_soak_pass_20260714`;
- duration 300.446 seconds;
- FPS min/average/max 59.94 / 60.34 / 61.09;
- heap start/end 68,257,122 / 61,654,852 bytes;
- console errors/warnings: 0.

## Exact continuation point

Start cycle 2 independently from fresh validators and fresh Web/Android builds. Repeat the complete Web matrix/interactions/restart/300-second soak, then rebuild and reinstall the Android x86_64 emulator APK and repeat the 28-case matrix plus interaction/name/restart/300-second soak. Fix every new finding and rerun the affected gate before final code review, hygiene cleanup, final report, and Hermes checkpoint.

