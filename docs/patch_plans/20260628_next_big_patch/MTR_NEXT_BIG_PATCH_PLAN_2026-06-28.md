# MTR next big patch plan — name input, skin alpha cleanup, platform repair

Date: 2026-06-28  
Project: Martyskin Trud Runner / Cocos Creator Android + Web  
Status: planning-only. Do not start runtime/code/asset implementation until the user explicitly approves the patch start.

## 0. Mission

Prepare the next large corrective patch for three confirmed user-facing problems:

1. The “имя персонажа / имя примата” menu must allow the user to enter a custom name directly in-game, not only rotate presets or rely on browser `prompt()`.
2. Many player skin sprites have bad cutouts: white matte chunks/fringes remain around the primate/equipment after skin-pack adaptation.
3. Some level platforms are missing, damaged, or replaced by incorrect textures with white chunks.

The next implementation pass must start with full code-review and QA of the whole game, every relevant menu state, and every level from 1 to 15. Fixes must be evidence-driven, reproducible, and validated on both Web and Android.

## 1. Hard project rules

- Read `AGENTS.md` and the four mandatory docs before implementation:
  - `docs/MARTYSKIN_WORLD.md`
  - `docs/CODEX_ANDROID_UPDATE_MASTER_TASK.md`
  - `docs/CODEX_MARTYSKIN_VIDEO_REVIEW_PROMPT.md`
  - `docs/CODEX_MARTYSKIN_POST_CLEANUP.md`
- Preserve the Russian UI and lore language.
- Android and Web must keep shared configs and level data.
- Do not replace backgrounds with gradients, grids, or unrelated abstract art.
- Bananas stay bananas, not lemons.
- Primate skins must keep readable limbs, helmet/accessories, face, and tail.
- Runtime Android QA defaults to emulator-only unless the user explicitly authorizes physical-device testing.
- If physical-device install is explicitly authorized, use `adb -s R5CY933XP7P install --user 0 -r "<apk>"`.
- Final Android release must be device-valid, normally with `arm64-v8a`, and emulator APKs must remain separate QA artifacts.
- After implementation, run at least 4 QA cycles and a hygiene gate before handoff.

## 2. Current technical anchors

Observed read-only anchors:

- Main runtime: `assets/scripts/GameRoot.ts`
- Current name state: `State` includes `name`; current `askName()` uses browser `prompt()` when available and cycles `NAME_POOL` otherwise.
- Player name persistence: `mtr_player_name` in localStorage.
- Records and achievements are keyed by normalized player name.
- Active player skin namespace: `assets/resources/characters/player_skins/`
- Active skin IDs: `brigadir`, `mudrec`, `cyber_makaka`, `red_prorab`, `depo_primate`, `orangutan_noir`, `lab_assistant_act`, `golden_brigadir`.
- Active skin variants: `base`, `helmet`, `vest`, `helmet_vest`, `boots`, `helmet_vest_boots`, `magnet`, `shield`, `blueprint`, `radio`, `banana_boost`, `key_pass`, `coffee`.
- Active skin poses: `idle`, `run_1`, `run_2`, `jump`, `jump_2`, `fall`, `crouch_dash`, `hit`, `victory`.
- Expected full skin visual coverage target: 8 skins × 13 variants × 9 poses = 936 runtime sprite entries, subject to manifest reality.
- Platform rendering currently selects keys through `themedPlatformKeysForLevel(levelIndex)` and `platformAssetKey(type, worldXSeed)`.
- If a platform asset cannot be used, `drawLatestPlatformLoadPlaceholder()` draws a fallback line placeholder; the next patch must prove these placeholders do not leak into normal gameplay.

## 3. Required work order

### Phase A — Baseline freeze and evidence setup

Technical task:

- Create a new evidence folder under `docs/qa/evidence/YYYYMMDD_next_big_patch/`.
- Record current commit/build state, latest Hermes checkpoint, build config paths, and active release artifacts.
- Do not delete or overwrite previous evidence.
- Produce a baseline inventory:
  - levels count and titles;
  - active skins / variants / poses;
  - platform asset keys per level;
  - all relevant UI states;
  - Android/Web build configs;
  - current known defects from user report.

Acceptance:

- A baseline log exists before any code or asset modification.
- The next engineer can reproduce the starting state.

### Phase B — Full code-review before fixing

Technical task:

Review these areas before implementation:

1. `GameRoot.ts` state machine:
   - `menu`, `name`, `skins`, `levels`, `playing`, `paused`, `clear`, `over`, `finished`, `devgate`, `devpanel`;
   - transition ownership and whether UI input nodes are activated/deactivated safely.
2. Name/profile flow:
   - `askName()`;
   - `normalizedPlayerName()`;
   - `saveSettings()` / `loadSettings()`;
   - records and achievements linkage;
   - localStorage failure handling;
   - Android soft keyboard behavior.
3. Skin runtime:
   - `PLAYER_SKIN_IDS`, variants, poses;
   - preloading;
   - fallback/redirect handling;
   - bonus-state switching;
   - logs such as `MTR_PLAYER_SKIN_SAFE_FALLBACK`.
4. Platform runtime:
   - platform generation density;
   - `themedPlatformKeysForLevel()`;
   - `platformAssetKey()`;
   - `canUseRuntimePlatformAsset()`;
   - fallback placeholder behavior;
   - collision/render size consistency.
5. Asset manifests/pipelines:
   - `assets/resources/config/last_iteration_asset_manifest.generated.json`;
   - `assets/resources/config/player_skin_equipment_matrix.json`;
   - `tools/mtr_last_iteration_asset_pipeline.py`;
   - any skin-pack import/cutout tools used previously.
6. Build/deploy:
   - `build-web-mobile.json`;
   - `build-android-emulator.json`;
   - `build-android.json`;
   - `tools/Run-MtrCocosBuild.ps1`;
   - GitHub Pages sync workflow.

Acceptance:

- Findings are written before fixes.
- Every finding has owner area, severity, reproduction/inspection evidence, and proposed correction.

### Phase C — Full QA discovery pass, all levels

Technical task:

- Run Web local build smoke and Android emulator smoke.
- Use developer mode only as a QA accelerator, not as a replacement for normal player flow.
- Capture screenshots and logs for all levels 1–15.
- For each level, capture at minimum:
  - first playable screen;
  - early platform segment;
  - mid-level segment;
  - late-level segment;
  - one obstacle cluster;
  - at least one bonus pickup state where practical.
- For UI, capture:
  - main menu;
  - start/name submenu;
  - custom name input flow;
  - skin select;
  - level select;
  - records;
  - achievements;
  - sound settings;
  - pause/death/clear states.

Acceptance:

- QA matrix has entries for all 15 levels and all listed UI states.
- Defects are marked as discovered before the implementation plan is locked.

### Phase D — Custom name input implementation

Technical task:

- Replace `prompt()`-based name entry with a real in-game input component.
- Preferred implementation:
  - create a `playerNameEditNode` with `EditBox`, similar to existing dev password input, but styled with the start-menu/profile PNG assets;
  - activate it only in `state === 'name'`;
  - hide/deactivate it in all other states;
  - scrub default labels/old helper text so no “label” ghost appears under PNG UI.
- Input policy:
  - max 24 visible characters;
  - trim leading/trailing whitespace;
  - allow Cyrillic, Latin, digits, spaces, hyphen, underscore;
  - reject/control invisible control characters;
  - empty value becomes `Безымянный примат`;
  - preserve existing saved names through migration.
- UI:
  - profile card shows current saved name;
  - button “СОХРАНИТЬ ИМЯ” or equivalent;
  - button “ВПЕРЁД, ПРИМАТЫ!” starts the selected level with the saved name;
  - optional quick preset/random button can remain, but must not be the only method.
- Persistence:
  - update `mtr_player_name`;
  - records and achievements use `normalizedPlayerName()`;
  - existing records remain readable.

Acceptance:

- Android emulator: soft keyboard opens, input saves, game starts, record uses the custom name.
- Web: keyboard input works without browser prompt dependency.
- UI style matches existing PNG menu style.
- No old background labels remain under the new input/button art.

### Phase E — Skin-pack alpha/cutout repair

Technical task:

- Inventory every active player skin PNG by skin, variant, and pose.
- Generate contact sheets for:
  - every base skin pose;
  - every bonus variant for at least idle/run/jump;
  - full all-bonus QA state.
- Detect defects:
  - white/near-white edge-connected matte pixels;
  - opaque white chunks inside transparent boundary areas;
  - inconsistent alpha premultiplication;
  - cropped limbs/tails/helmets;
  - wrong scale or anchor between poses.
- Do not blindly remove all white pixels. Intentional white elements such as eyes, text, highlights, lab coats, papers, and helmets must be preserved.
- Preferred repair order:
  1. regenerate from the best source with correct transparent background;
  2. if source is unavailable, use edge-connected matte detection/flood-fill to rebuild alpha;
  3. if alpha repair changes important content, repaint/regenerate the sprite;
  4. normalize canvas, anchor, scale, and pose baseline after repair.
- Update Cocos metadata/imports only through reproducible steps.

Acceptance:

- No white matte chunks visible at 1× gameplay scale or zoomed QA contact sheets.
- All active skin IDs and variants load without fallback in QA logs.
- Character silhouette remains readable and canon-compliant.

### Phase F — Platform texture repair

Technical task:

- Inventory all active platform keys per level.
- Verify every referenced platform texture exists, imports as transparent PNG/SpriteFrame, and matches level theme.
- Detect:
  - missing platform assets;
  - wrong category assets used as platforms;
  - white matte chunks;
  - bad transparency;
  - platform visuals that do not align with collision surface;
  - fallback placeholder rendering in normal gameplay.
- Repair platform packs holistically by level theme:
  - construction: scaffolds, beams, planks, concrete blocks;
  - logistics/storage: pallets, crates, conveyors;
  - bureaucracy/archive: shelves, cabinets, paper stacks as supports;
  - jungle/farm/inspection/factory/reactor/night/education/tower/ministry/final: theme-specific supports.
- Ensure collision line remains clear and not hidden by decorative art.

Acceptance:

- All 15 levels show valid themed platforms.
- No platform is invisible or replaced by a wrong “white chunk” texture.
- No `themed_platform_missing` or equivalent placeholder marker in normal QA logs.

### Phase G — Additional improvement research

Research candidates for the implementation patch:

1. Add a reusable visual QA gallery/dev panel:
   - cycle skin × variant × pose;
   - cycle platform asset packs per level;
   - screenshot-friendly static layout.
2. Add an automated PNG alpha audit tool:
   - edge-connected white matte detection;
   - alpha histogram;
   - suspicious asset report;
   - contact sheet output.
3. Add level screenshot automation:
   - deterministic seed;
   - jump to level;
   - jump to distance checkpoints;
   - capture Web and Android emulator screenshots.
4. Tighten asset loading telemetry:
   - missing platform/skin/bonus keys;
   - fallback counts;
   - per-level preload status.
5. Improve Web load:
   - lazy/priority loading for late-level assets;
   - atlas packing review;
   - asset compression budget;
   - no blocking preload of unrelated skin variants on first menu paint.
6. Add explicit build artifact separation:
   - `android-emulator` QA APK;
   - device-valid release APK;
   - web-mobile Pages build.

Acceptance:

- Research output becomes a prioritized “do now / defer” list before coding.

### Phase H — Implementation cycles

After approval to start implementation, run this sequence:

1. Fix name input first because it touches UI/state/persistence but not art.
2. Add/read-only asset audit tools and produce defect inventory.
3. Repair skin alpha/cutouts.
4. Repair platform packs and manifests.
5. Rebuild Web and Android emulator.
6. Run QA cycle 1: menu/name input + skin gallery.
7. Run QA cycle 2: all levels 1–15 platform pass.
8. Run QA cycle 3: all skins/bonus states.
9. Run QA cycle 4: full smoke, performance/log review, Web + Android parity.
10. Build device-valid Android release APK.
11. Sync Web build to GitHub Pages worktree.
12. Run hygiene gate.
13. Commit/push only after validation is clean.
14. Install on phone only after explicit authorization, using `R5CY933XP7P` and `--user 0`.

## 4. Final acceptance for the future patch

- Custom name entry works on Web and Android emulator.
- Records and achievements persist under the entered name.
- All 15 levels are visually inspected and logged.
- Every level has visible, themed, non-broken platforms.
- All active player skins and bonus variants are free from obvious white matte/cutout defects.
- No unintended fallback placeholders are visible in gameplay.
- Web and Android use the same configs/level data.
- Web build is pushed to GitHub Pages repo.
- Android release APK is device-valid and ABI-verified.
- Final QA logs, screenshots, and Hermes checkpoint exist.
- Post-cleanup/hygiene gate is complete.

## 5. Non-goals for the planning-only stage

- No runtime code changes.
- No PNG regeneration.
- No asset deletion.
- No build/push/release.
- No physical device QA.

