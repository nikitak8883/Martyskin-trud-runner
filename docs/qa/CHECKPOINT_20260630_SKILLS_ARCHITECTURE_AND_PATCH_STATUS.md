# Checkpoint — skills / architecture audit + current patch status

Generated: 2026-06-30 13:17:35 +03:00  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Evidence root: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\docs\qa\evidence\20260630_next_big_patch`

## Current status

Status: `partially_working`

The current Web patch line is validated through browser QA, but the full task is not complete yet because Android emulator QA, Android release APK, final GitHub Pages sync, final release packaging, phone install, and push have intentionally not been continued after the user requested stop/checkpoint.

## Architecture / skill audit result

- `local_worker` retrieval: working.
- Lemonade embedding health: working, dimension `2560`, expected `2560`.
- `orchestra_plan`: working, resource gate passed.
- Hermes context doctor: working.
  - Integrity: `ok`.
  - Checkpoints: `528`.
  - FTS rows: `528`.
  - Compaction limit: `258000`.
  - Threshold ratio: `0.95`, meaning checkpoint/compact safety at 5% remaining context.
- Hermes hooks:
  - `Stop`: checkpoint at threshold ratio `0.95`.
  - `PreCompact`: forced checkpoint before manual/automatic compact at threshold ratio `0.95`.
- Hermes status audit: `19/19` checks true.
- Hermes workspace index refreshed:
  - files: `299`
  - added: `64`
  - updated: `4`
  - unchanged: `227`
  - oversized: `3`
  - unreadable: `0`
- Hermes entrypoint profiles:
  - Android: ready.
  - Web: ready.
  - Windows: ready.
  - Linux: not ready because `wsl` is missing and `docker` is missing. This is not a blocker for the current Android/Web work, but future Linux tasks must alert/stop until profile is made ready.
- Antigravity CLI doctor:
  - version: `1.0.14`
  - status: `working`
  - mode: advisory only
  - model: `Gemini 3.1 Pro (High)`
  - tool permission: `request-review`
  - non-workspace access: disabled
  - telemetry: disabled

## Skill audit result

Skill audit output:

- `docs\qa\evidence\20260630_next_big_patch\architecture_skill_audit_20260630.json`

Summary:

- parser: `pyyaml`
- scanned skills: `136`
- duplicate skill names: `3`
  - `gh-address-comments`
  - `gh-fix-ci`
  - `supabase-postgres-best-practices`
- issue candidates: `51`

Notes:

- The duplicate names are expected mirror/plugin overlaps, not immediate blockers.
- The issue candidates are mostly skills that have usable descriptions but no explicit `Procedure` section. This is maintenance debt, not a blocker for the current game patch.
- Core skills used in this work have valid frontmatter and usable descriptions.

## Patch work completed before this checkpoint

### GameRoot

File: `assets\scripts\GameRoot.ts`

Completed:

- Added custom primate name input through Cocos `EditBox`.
- Replaced prompt-style name entry with in-game styled input flow.
- Added name sanitization and save/load sync.
- Added CSS guard for web EditBox DOM layer to avoid duplicate visible text.
- Fixed QA autostart level selection so `mtr_level=N` starts the requested level before forced bonus spawning.
- Added dev-only forced skin/variant/pose QA query support:
  - `mtr_skin` / `mtr_qa_skin`
  - `mtr_variant` / `mtr_qa_variant`
  - `mtr_pose` / `mtr_qa_pose`
- Removed always-on rainbow trail rectangles under the player.
- Connected new proper PNG bonus assets for jump, dash, and extra life.
- Changed bonus drawing to prefer PNG assets before runtime fallback icons.
- Cleaned objective category contract so bonus PNGs no longer duplicate under `equipment`.

### New / updated PNG bonus assets

Files:

- `assets\resources\objectives\bonuses\bonus_jump_spring_01.png`
- `assets\resources\objectives\bonuses\bonus_jump_spring_01.png.meta`
- `assets\resources\objectives\bonuses\bonus_dash_bolt_01.png`
- `assets\resources\objectives\bonuses\bonus_dash_bolt_01.png.meta`
- `assets\resources\objectives\bonuses\bonus_extra_life_01.png`
- `assets\resources\objectives\bonuses\bonus_extra_life_01.png.meta`

### Build wrapper

File: `tools\Run-MtrCocosBuild.ps1`

Completed:

- Added web postprocess after successful web build:
  - copies `assets\favicon.png` to `build\web-mobile\favicon.png`
  - injects `<link rel="icon" type="image/png" href="favicon.png"/>` into `build\web-mobile\index.html`
- Purpose: remove false browser `404` console noise during web QA.

### Config validator

File: `tools\validate-mtr-config.ps1`

Completed earlier in this patch line:

- Updated validator expectations to match current runtime anchor / equipment logging names instead of stale marker strings.

## QA completed before stop

### Static / config

- `tools\validate-mtr-config.ps1`: passed.
- PowerShell parse check for `tools\Run-MtrCocosBuild.ps1`: passed.

### Web build

- `patch4_category_cleanup_web_build_20260630.log`: successful web build after equipment category cleanup.
- `patch5_favicon_postprocess_web_build_20260630.log`: successful web build after favicon postprocess.
- Last build had `webPostProcess.ok = true`.

### Web runtime QA

All-level web QA after category cleanup:

- file: `patch4_all_levels_web_smoke_20260630.json`
- levels: `15/15`
- state mismatches: `0`
- missing/fallback logs: `0`
- bonus duplicated as equipment: `0`
- flagged before favicon fix: `1` benign browser `404`

Production-like web QA:

- file: `patch4_production_like_web_smoke_20260630.json`
- levels checked: `1`, `8`, `15`
- debug banner logs: `0`
- missing/fallback logs: `0`
- only benign browser `404` before favicon fix.

Favicon postprocess smoke:

- file: `patch5_favicon_postprocess_web_smoke_20260630.json`
- flagged: `0`
- pageErrors: `0`

Visual contact sheets:

- `patch4_all_levels_contact_sheet.png`
- `patch4_production_like_contact_sheet.png`
- `patch3_forced_skin_matrix_contact_sheet.png`
- `bonus_equipment_contact_sheet_after_new_20260630.png`

### Skin / bonus matrix QA

- `patch3_forced_skin_variant_matrix_20260630.json`
- forced cases: `42`
- missing cases: `0`
- visually inspected contact sheet: no obvious white matte blocks / huge wrong overlays / fallback body artifacts in tested problematic combinations.

## Infrastructure cleanup done before stop

- The temporary web QA server on port `8123` was stopped.
- Stopped process: `pid=9020`.
- Cocos build processes were not left running from the last successful build.
- Android/Java/ADB processes were not killed because they may belong to emulator/SDK state and were not part of the web QA server.

## Known non-blocking issues / risks

1. `npx tsc -p tsconfig.json --noEmit` cannot be used as-is because the project does not have TypeScript installed locally; `npx` resolves to the placeholder package message. This is not a game runtime failure, but a tooling gap.
2. Linux global profile is not ready: `wsl` missing, `docker` missing. Future Linux tasks must alert and stop until profile readiness is fixed.
3. Full Android emulator QA and final release APK were not run after this stop request.
4. GitHub Pages sync / push was not performed after this stop request.
5. Full hygiene/post-cleanup is still pending after Android/Web release validation.

## Exact next safe action

When resuming:

1. Read this checkpoint first.
2. Run `tools\validate-mtr-config.ps1`.
3. Run a short web smoke against `build\web-mobile` only if the build artifacts are suspected stale.
4. Continue with Android build path:
   - Android emulator build.
   - Android emulator QA cycles.
   - release/device-valid APK build.
   - verify ABI contents, especially `arm64-v8a`.
5. Sync web build to `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`.
6. Commit and push to `https://github.com/nikitak8883/Martyskin-trud-runner.git`.
7. If physical install is still explicitly authorized, install only with `adb -s R5CY933XP7P install --user 0 -r "<apk>"`.
8. Run final hygiene gate and write final release log/checkpoint.

## Key evidence files

- `docs\qa\evidence\20260630_next_big_patch\architecture_skill_audit_20260630.json`
- `docs\qa\evidence\20260630_next_big_patch\hermes_entrypoint_doctor_20260630.json`
- `docs\qa\evidence\20260630_next_big_patch\hermes_workspace_index_refresh_20260630.json`
- `docs\qa\evidence\20260630_next_big_patch\patch5_favicon_postprocess_web_build_20260630.log`
- `docs\qa\evidence\20260630_next_big_patch\patch5_favicon_postprocess_web_smoke_20260630.json`
- `docs\qa\evidence\20260630_next_big_patch\patch4_all_levels_web_smoke_20260630.json`
- `docs\qa\evidence\20260630_next_big_patch\patch4_all_levels_contact_sheet.png`
- `docs\qa\evidence\20260630_next_big_patch\patch4_production_like_contact_sheet.png`

