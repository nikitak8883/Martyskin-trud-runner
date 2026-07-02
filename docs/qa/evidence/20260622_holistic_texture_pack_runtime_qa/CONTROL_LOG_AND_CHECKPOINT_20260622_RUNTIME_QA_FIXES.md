# MTR runtime QA fixes checkpoint — 2026-06-22

Status: stopped after build + emulator QA, per user instruction.

Project cwd:

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

Evidence directory:

`docs/qa/evidence/20260622_holistic_texture_pack_runtime_qa`

## What was fixed in this cycle

Source file:

`assets/scripts/GameRoot.ts`

1. Developer password gate:
   - Kept the valid password semantics for `Primatal`, but made runtime checking robust by normalizing ASCII input to lowercase and stripping non-letters.
   - Accepts the intended password even if the native EditBox appends it after an internal default text fragment.
   - Does not log password content; denial log records only input/normalized lengths.

2. Dev password field visual cleanup:
   - Removed the Cocos EditBox internal default `label` tail by scrubbing only Label components whose string is exactly `label`.
   - Added a custom styled placeholder text drawn by the game UI.

3. QA “Все бонусы” full-equipment route:
   - Replaced the single-variant preload gate with a holistic gate over all `PLAYER_SKIN_VARIANTS`.
   - The route now waits until all selected-skin baked variant poses are loaded before entering gameplay.
   - Extended QA bonus duration to 24 seconds so visual audit does not expire mid-check.
   - Added bounded logs: `MTR_QA_BONUS_PRELOAD_WAIT variants=13 missing=...`.

## Builds

Web build:

- Command wrapper: `tools/Run-MtrCocosBuild.ps1`
- Config: `build-web-mobile.json`
- Log: `docs/qa/evidence/20260622_holistic_texture_pack_runtime_qa/creator-20260622-runtime-qa-fixes3-web.log`
- Result: OK.
- Built JS checked at `build/web-mobile/assets/main/index.js`.

Android emulator build:

- Command wrapper: `tools/Run-MtrCocosBuild.ps1`
- Config: `build-android-emulator.json`
- Log: `docs/qa/evidence/20260622_holistic_texture_pack_runtime_qa/creator-20260622-runtime-qa-fixes3-android-emulator.log`
- Gradle post-package: OK, `gradle-clean-assembleDebug`.
- APK:
  `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`
- APK timestamp observed after final rebuild: `2026-06-22 03:18:58`.
- APK size observed after final rebuild: `142823921` bytes.

Note: this is an emulator QA artifact. A final real-device-valid release APK/AAB was not produced in this stop-point cycle.

## Emulator QA

ADB target:

- `emulator-5554`
- Physical devices were not used.

Fresh APK install:

- Installed with explicit serial and array-safe path passing.
- Package: `com.martyskin.trudrunner`
- App data cleared before regression cycle.

Key evidence:

- `cycle4_devgate_no_label.png` — dev password screen after EditBox label cleanup.
- `cycle4_devpanel_password_ok2.png` + `cycle4_devpanel_password_ok2_logcat.txt` — password route opens dev panel; log contains `MTR_DEV_MODE_OPENED`.
- `cycle5_devpanel_password_ok.png` + `cycle5_devpanel_password_ok_logcat.txt` — password route rechecked on final APK.
- `cycle5_all_bonuses_wait.png` — QA route waits in dev panel while all variants preload.
- `cycle5_all_bonuses_gameplay.png` + `cycle5_all_bonuses_gameplay_logcat.txt` — all-bonus gameplay after holistic preload.
- `cycle6_start_submenu.png` — normal start submenu regression.
- `cycle6_direct_gameplay.png` + `cycle6_direct_gameplay_logcat.txt` — normal user flow to gameplay.

Important log observations:

- `cycle5_all_bonuses_gameplay_logcat.txt` shows preload decreasing:
  - `MTR_QA_BONUS_PRELOAD_WAIT variants=13 missing=85`
  - then `77`, `65`, `54`, `41`, `26`, `10`
  - then `MTR_FSM:DEV_MODE->RUNNING`
- `cycle5_all_bonuses_gameplay_logcat.txt` shows:
  - `MTR_SKIN_VARIANT_ACTIVE skin=brigadir variant=helmet_vest_boots ...`
  - later `MTR_SKIN_VARIANT_ACTIVE skin=brigadir variant=helmet_vest ...`
- `cycle5_all_bonuses_gameplay_logcat.txt` search for `MTR_PLAYER_SKIN_SAFE_FALLBACK` returned no hits in the final all-bonus cycle.
- `cycle6_direct_gameplay_logcat.txt` search for `MTR_PLAYER_SKIN_SAFE_FALLBACK` returned no hits in the normal user flow.

Visual observations:

- Main menu background remains a real image, not a blob.
- Dev password `label` artifact is gone.
- Start submenu uses PNG-styled buttons and profile box consistently.
- Normal gameplay and all-bonus QA screenshots do not show the previous obvious yellow-object/cube-under-feet issue.

## Web parity smoke

Static server test:

- Port: `8922`
- Evidence: `web_static_smoke_20260622.json`
- Result:
  - `indexStatus: 200`
  - `mainStatus: 200`
  - `containsQaGate: true`
  - `containsVariantGate: true`
  - `containsDevPassword: true`

Server startup note:

- Two failed attempts were logged because `Start-Process -ArgumentList` split a path with spaces when using `--directory`.
- Final working approach used `WorkingDirectory = build/web-mobile` and no `--directory` argument.

## Hygiene / cleanup

- CocosCreator stale build processes were stopped after they remained as build tails.
- Local Python web smoke server was stopped after the test.
- One misplaced early screenshot was moved into this evidence directory:
  `cycle2_dev_password_primatal_before_fix.png`.
- Searched `GameRoot.ts` for conflict markers, TODO/FIXME/debugger leftovers: no hits.
- Searched project for common temp patch leftovers (`*.tmp`, `*.bak`, `*.orig`, `*.rej`): no hits.

Remaining intentional evidence/build artifacts are preserved.

## Git / repo status

Active portable project directory is not itself a git worktree:

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

Git worktree found separately:

`C:\Projects\Monkey Work\_github\Martyskin-trud-runner`

Observed git status there at checkpoint time:

- `M assets/main/index.js`
- `M assets/resources/import/b7/b746e25c-2c41-4f04-9f35-7c2a189ad527.json`

No commit or push was performed in this stop-point cycle because the user requested: build, final log/checkpoint, then stop.

## Recommended next continuation

1. Decide whether to sync the source changes from the portable Cocos project into the `_github/Martyskin-trud-runner` worktree before pushing.
2. If continuing toward release:
   - run a release Android build, not emulator-only;
   - verify arm64/device-valid ABI coverage;
   - produce a real-device-valid APK/AAB;
   - only then push/tag/release as requested.
3. If continuing QA:
   - add a browser-runtime screenshot/playtest if Browser/Playwright tooling is available;
   - run level-selection and skin-selection cycles for at least one non-Brigadir skin;
   - test all-bonus route after selecting another skin to ensure variant gate works for every skin index.
