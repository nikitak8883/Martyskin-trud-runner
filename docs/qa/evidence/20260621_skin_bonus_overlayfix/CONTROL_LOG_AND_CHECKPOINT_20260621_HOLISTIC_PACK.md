# Control log — holistic skin bonus texture pack

Date: 2026-06-21 22:25 Asia/Jerusalem

Status: stopped after successful web + Android emulator builds, per user instruction.

Hermes checkpoint:

- ID: 513
- Trigger: `post-build-holistic-skin-pack-stop`
- Markdown: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260621T192153Z-post-build-holistic-skin-pack-stop.md`
- JSON: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260621T192153Z-post-build-holistic-skin-pack-stop.json`
- Project latest: `C:\Users\nikit\.hermes-proagents\checkpoints\by-project\MTRCocosCreator-d20b07d42eaf7ab3\LATEST.md`

## What changed in this cycle

- Replaced the previous point-fix approach with a holistic texture-pack generation pass.
- Treated old baked bonus frames as invalid source material because they contained baked artifacts:
  - yellow slab near hardhat;
  - rectangular blocks under feet;
  - box/envelope-like baked fragments on torso;
  - polluted `depo_primate/base` frames.
- Generated fresh item texture packs from normalized base frames.
- Rebuilt `depo_primate/base` from a clean brigadir-derived base with depot palette accents.
- Added separate baked PNG variants for all required item families:
  - `helmet`
  - `vest`
  - `boots`
  - `helmet_vest`
  - `helmet_vest_boots`
  - `magnet`
  - `shield`
  - `blueprint`
  - `radio`
  - `banana_boost`
  - `key_pass`
  - `coffee`
- Updated skin variant routing in `assets/scripts/GameRoot.ts`.
- Updated `assets/resources/config/player_skin_equipment_matrix.json`.

## Generated asset evidence

- Manifest: `docs/qa/evidence/20260621_skin_bonus_overlayfix/finalpng/holistic_texture_pack_manifest_20260621.json`
- Backup before holistic regeneration: `docs/qa/evidence/20260621_skin_bonus_overlayfix/finalpng/player_skins_backup_pre_holistic_texture_pack_20260621.zip`
- Records generated/changed: 873
- New Cocos `.meta` files created for new resource entries: 360
- New item resource count for each newly added item family:
  - `blueprint`: 72 PNG
  - `radio`: 72 PNG
  - `banana_boost`: 72 PNG
  - `key_pass`: 72 PNG
  - `coffee`: 72 PNG

## Visual pre-QA evidence

Main contact sheets:

- `docs/qa/evidence/20260621_skin_bonus_overlayfix/finalpng/holistic_run2_all_skins_variants_contact.png`
- `docs/qa/evidence/20260621_skin_bonus_overlayfix/finalpng/base_all_poses_contact_holistic.png`
- `docs/qa/evidence/20260621_skin_bonus_overlayfix/finalpng/bonus_helmet_vest_boots_all_poses_contact_holistic.png`

Visual check result before build:

- No yellow slab near hardhat visible on inspected `run_2` overview.
- No rectangular blocks under feet visible on inspected `run_2` overview.
- No torso envelope/box artifact visible on inspected `run_2` overview.
- All-skins/all-poses full-safety sheet was visually checked after regeneration.

## Build results

Web build:

- Command wrapper: `tools/Run-MtrCocosBuild.ps1`
- Config: `build-web-mobile.json`
- Log: `creator-20260621-holistic-texture-pack-web.log`
- Result: success, exitCode 0
- Log size: 37,492 bytes
- Last write: 2026-06-21T22:14:14.5177837+03:00

Android emulator build:

- Command wrapper: `tools/Run-MtrCocosBuild.ps1`
- Config: `build-android-emulator.json`
- Log: `creator-20260621-holistic-texture-pack-android-emulator.log`
- Result: success, exitCode 0
- Android post-package: `gradle-clean-assembleDebug`
- Post-package verification: ok
- APK: `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk`
- APK size: 142,823,089 bytes
- APK last write: 2026-06-21T22:18:49.5930704+03:00

Important: this APK is an emulator QA artifact. It is not the final real-device release artifact.

## Work intentionally not continued

Stopped here by user instruction:

- no emulator install;
- no runtime QA cycle;
- no GitHub Pages web sync;
- no git commit;
- no push.

## Next required step

Resume from here with:

1. Install the newly built APK to the Android emulator only.
2. Run full emulator QA:
   - main menu;
   - start submenu;
   - name flow;
   - hidden developer taps;
   - all-bonuses flow;
   - per-item visual checks for all baked variants;
   - logcat capture.
3. Run web parity smoke test.
4. Run code-review/hygiene gate.
5. Sync web build to `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`.
6. Commit and push to `nikitak8883/Martyskin-trud-runner` only after QA passes.

## Current caution

The generated texture-pack is visually cleaner in contact sheets, but runtime validation has not yet been run after this build. Do not mark the patch as complete until emulator QA confirms the new resources are actually selected and rendered in-game.
