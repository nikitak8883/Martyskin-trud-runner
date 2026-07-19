# Tasks/4 audit and implementation plan

Generated: 2026-07-02 15:00 +03:00  
Workspace: `C:\Projects\Monkey Work`  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`  
Input task folder: `C:\Projects\Monkey Work\Tasks\4`  
Mode: audit-only / no runtime implementation in this pass

## Status

`ready_for_user_confirmation`

The Tasks/4 archive was unpacked, hash-verified, structurally inspected, compared against the current Android/Web project state, and converted into a staged implementation plan with QA cycles and conflict controls.

No game runtime code was changed in this pass. The only project-side artifact created intentionally is this planning/audit report. The read-only asset audit produced evidence under `docs\qa\evidence\20260702_tasks4_audit`.

## Inputs inspected

### Tasks/4 package

- `README_START_HERE.md`
- `00_REPORT_REVIEW_AND_RESEARCH_DELTA.md`
- `01_GLOBAL_MODERNIZATION_MASTER_PLAN.yaml`
- `SOURCE_BIBLIOGRAPHY.md`
- `MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2.zip`
- `MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2.zip.sha256.txt`
- unpacked root:
  - `C:\Projects\Monkey Work\Tasks\4\_unpacked_20260702_145527\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2`

### Unpacked library contents

- 10 module specs:
  - `01_graphics_rendering_asset_pipeline.md`
  - `02_ui_ux_design_system.md`
  - `03_character_skin_bonus_animation_pipeline.md`
  - `04_gameplay_core_mechanics.md`
  - `05_levels_backgrounds_content_pipeline.md`
  - `06_procedural_validation_difficulty.md`
  - `07_audio_vfx_feedback.md`
  - `08_save_achievements_telemetry.md`
  - `09_android_web_release_performance.md`
  - `10_agent_tooling_ci_qa.md`
- schemas:
  - `ui_ir.schema.yaml`
  - `skin_manifest.schema.json`
  - `atlas_manifest.schema.json`
  - `qa_result.schema.json`
- checklists:
  - `QA_MATRIX.md`
  - `CODE_REVIEW_CHECKLIST.md`
  - `RELEASE_GATE_CHECKLIST.md`
- prompts/templates:
  - `CODEX_GLOBAL_UPDATE_PROMPT.md`
  - `CODEX_MODULE_PROMPT_TEMPLATE.md`
  - module/code-review/QA report templates

### Current project state inspected

- `package.json`
- `build-web-mobile.json`
- `build-android.json`
- `build-android-emulator.json`
- `tsconfig.json`
- `AGENTS.md`
- `UI_ALLOWED_ASSETS.md`
- `assets\scripts\GameRoot.ts`
- `assets\resources\config\ui_skin_manifest.json`
- `docs\skins_integration\manifests\player_skins_manifest.json`
- `assets\resources\characters\player_skins\_shared\manifests\source_inventory.json`
- `tools\validate-mtr-config.ps1`
- `tools\Run-MtrCocosBuild.ps1`
- `tools\web-chrome-runtime-smoke.ps1`
- `tools\scan_and_fix_white_matte_edges.py`
- latest control logs:
  - `docs\qa\CHECKPOINT_20260630_SKILLS_ARCHITECTURE_AND_PATCH_STATUS.md`
  - `docs\qa\CONTROL_LOG_CHECKPOINT_20260701_STOP_AFTER_ANDROID_RELEASE_WEB_BUILD.md`
  - `docs\qa\CONTROL_LOG_CHECKPOINT_20260702_WEB_LIVE_QA_HARNESS_FIXED_PHONE_BLOCKED.md`

## Commands and evidence

### Archive integrity

- ZIP SHA-256 expected:
  - `bbda184566303926ea9607cec0b74793445733186d4915f80432dada9ca466f8`
- ZIP SHA-256 actual:
  - `bbda184566303926ea9607cec0b74793445733186d4915f80432dada9ca466f8`
- Result: `pass`

### Internal manifest

- `MANIFEST_SHA256.txt`: 28 entries
- Manifest verification: `pass`
- JSON parse check:
  - `MANIFEST.json`: pass
  - all `schemas\*.json`: pass
- YAML parse check:
  - `01_GLOBAL_MODERNIZATION_MASTER_PLAN.yaml`: pass
  - `schemas\ui_ir.schema.yaml`: pass

### Project validator

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-mtr-config.ps1
```

Result:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present.
```

### Runtime PNG white-matte scan

Command:

```powershell
python .\tools\scan_and_fix_white_matte_edges.py `
  --root assets/resources `
  --report docs/qa/evidence/20260702_tasks4_audit/white_matte_scan_20260702.json `
  --contact-sheet docs/qa/evidence/20260702_tasks4_audit/white_matte_scan_20260702_contact_sheet.png
```

Result:

```json
{"checkedCount": 978, "suspectCount": 0, "fixedCount": 0}
```

Important limitation: this scan detects edge-connected opaque white matte artifacts in runtime PNGs. It does not prove correct skin pivots, bonus placement, animation consistency, platform geometry, or visual readability. Those remain covered by the planned QA matrix.

## Findings

### F0 — Tasks/4 archive is valid and internally consistent

Severity: info  
Status: confirmed

The package is not corrupted. Top-level companion docs match their unpacked copies by SHA-256, and archive manifest verification passed.

### F1 — Tasks/4 is a global modernization library, not a narrow patch

Severity: high planning risk  
Status: accepted into plan

The package covers graphics, UI, skins, gameplay state, levels, PCG, audio/VFX, saves/achievements, release/performance, and agent tooling. Applying it as one giant patch would violate the package's own safe-patch policy and would likely destabilize the current Android/Web release line.

Resolution: split into module-by-module implementation cycles with checkpoints, code review, QA evidence, and stop conditions.

### F2 — Current project already contains partial implementations of several requested concepts

Severity: medium duplication risk  
Status: accepted into plan

Existing pieces:

- Cocos Creator profile: `3.8.8`
- Android/Web build configs exist.
- 15-level config validator exists and passes.
- `ui_skin_manifest.json` already encodes no-legacy and runtime-label policy.
- Skin integration tools and manifests exist.
- Current canonical skins: 8.
- Existing skin manifest reports 600 generated runtime skin PNGs.
- Current web QA harness supports explicit runtime log gates.
- Android native QA startup-query bridge exists.
- Latest release APK is device-valid by ABI:
  - `arm64-v8a`
  - `armeabi-v7a`

Resolution: do not recreate these systems blindly. First normalize them into the new manifest/report/checklist structure, then refactor only where evidence shows drift or fragility.

### F3 — `docs/global_modernization` was absent before this audit

Severity: medium process gap  
Status: partially resolved by this report

Tasks/4 requires module reports under `docs/global_modernization/`, but the directory did not exist. This report establishes the directory and first audit artifact. Future implementation must add module-specific reports there instead of scattering state across ad hoc logs.

### F4 — `docs/codex/CURRENT_STATE.md` is missing

Severity: medium context-recovery gap  
Status: queued

Tasks/4 expects short context checkpoints such as `CURRENT_STATE.md`. The current project has useful QA checkpoints, but no canonical compact current-state file under `docs/codex/`.

Resolution: Module 10 should create/update `docs/codex/CURRENT_STATE.md` and keep it compact, machine-readable, and human-readable.

### F5 — `GameRoot.ts` is a monolith

Severity: high architecture risk  
Status: accepted into phased plan

`assets\scripts\GameRoot.ts` is approximately 5350 lines and currently hosts UI, state, skins, bonuses, audio, achievements, render layers, input, and QA gates. This is not an immediate blocker because the runtime is working, but it is the main risk for future modernization.

Resolution: avoid a rewrite. First add external contracts/validators and route wrappers. Then extract registries/routers one subsystem at a time:

1. skin/bonus visual registry;
2. UI IR and screen inventory;
3. gameplay state/event router;
4. audio/VFX event maps;
5. save/achievement schema.

### F6 — Android/Web contract is currently mostly aligned, but not formally versioned

Skill verdict:

```json
{
  "skill": "android-web-contract-check",
  "verdict": "needs_patch",
  "summary": "Android and Web share current configs and runtime markers, but Tasks/4 requires explicit content manifest versioning and release gates.",
  "risk": "medium",
  "requires_worktree": false,
  "requires_model": "none"
}
```

Evidence:

- `tools\validate-mtr-config.ps1`: pass.
- Latest web live QA reached `MTR_GAMEPLAY_START_GATE_READY level=15`.
- Android emulator QA logs observed native startup query and runtime transitions.
- Release APK SHA-256 exists.
- Missing formal content manifest version shared across Android/Web release notes.

Resolution: Module 09 must introduce a release/content manifest version check before future release claims.

### F7 — QA target rule conflict: package allows emulator or real device, user default requires emulator-only

Severity: high operational conflict  
Status: resolved in plan

Tasks/4 says Android can be tested on emulator or real device. User-level project defaults require emulator-only unless physical device testing is explicitly authorized. Physical install, when authorized, must use serial `R5CY933XP7P` and `--user 0`.

Resolution:

- Default QA cycles use Android emulator only.
- Physical phone install is a separate explicit release action, not a default QA path.
- Final release APK/AAB must remain valid for real device installation even when QA is emulator-only.

### F8 — Release vs Play-production scope must stay separate

Severity: medium release-policy risk  
Status: accepted into plan

The current release APK is install-valid and signed, but the build config uses `useDebugKeystore: true`. This is acceptable for local install/release-candidate testing but not a Play production signing process.

Resolution:

- Keep current local release APK path for install-valid local artifacts.
- Add AAB/Play signing/PAD planning only after base APK/Web release pipeline remains stable.
- Do not introduce Play Asset Delivery until the AAB path is stable and asset size justifies it.

### F9 — Tooling gap: TypeScript check is not currently reliable

Severity: medium QA gap  
Status: accepted into plan

Prior checkpoint notes that `npx tsc -p tsconfig.json --noEmit` cannot be used as-is because TypeScript is not installed locally in this project. This limits strict static validation.

Resolution: Module 10 should add a deliberate local tooling decision:

- either vendor/project-install TypeScript and Cocos typings correctly;
- or document why Cocos build is the authoritative TypeScript compilation path.

### F10 — Cleanup tails exist and need controlled removal

Severity: low now / medium before release  
Status: queued

Observed tails:

- `tools\skins\__pycache__\inspect_skin_pngs.cpython-313.pyc`
- many historical creator logs at project root
- new untracked unpack folder under `Tasks/4`
- root git reports nested `_github\Martyskin-trud-runner` as modified from the parent repository perspective

Resolution: cleanup must be dry-run-first, path-guarded, and must preserve QA evidence needed for the release line. Do not delete the Tasks/4 unpacked source until the implementation plan is accepted and copied/normalized into project docs.

## Implementation decomposition

### Operating rules for every module

Each module must use this loop:

```text
retrieve bounded context
inspect live files
write module mini-plan
checkpoint
patch minimal slice
run module validators
run Android/Web parity checks where relevant
fix failures
retest
write module report
code review
hygiene dry-run
checkpoint
stop or request next approval
```

Hard rules:

- No Cocos version upgrade without explicit approval.
- No destructive cleanup without dry-run report and approval.
- No old/new UI systems active on the same screen.
- No runtime AI dependency for UI or sprite generation.
- No release claim without Web + Android smoke evidence.
- No physical phone QA/install unless explicitly authorized.
- Any final Android artifact must be device-valid, not emulator-only.
- Web and Android must share the same content manifest version.

## Module plan

### Module 0 — Repository inventory and safety scaffold

Priority: P0  
Patch type: docs/tooling only  
Expected files:

- `docs/codex/CURRENT_STATE.md`
- `docs/global_modernization/repository_inventory.md`
- `docs/global_modernization/module_execution_index.md`
- optional copied schemas/checklists under `docs/global_modernization/library/`

Tasks:

1. Record current build configs, release artifacts, pages repo commit, APK hashes, and known QA state.
2. Normalize Tasks/4 checklists into project docs without changing runtime.
3. Add content-manifest-version placeholder policy.
4. Add cleanup dry-run list; do not delete yet.

QA:

- `tools\validate-mtr-config.ps1`
- manifest parse checks
- git status review

Stop condition:

- If docs disagree with live build/release evidence, fix docs before runtime work.

### Module 1 — Graphics, rendering, atlas, asset pipeline

Priority: P0  
Patch type: validators first, asset movement later

Tasks:

1. Inventory all runtime PNG/SpriteFrame/Atlas assets.
2. Create project-specific `atlas_manifest.json`.
3. Extend current white-matte scan into stricter alpha/checkerboard/trim/pivot validation.
4. Produce contact sheets by runtime co-visibility group:
   - hud
   - menu
   - runner_core
   - player_skins
   - bonus_items
   - obstacles
   - backgrounds
   - VFX
5. Define static atlas policy; dynamic atlas only for documented small ephemeral UI fragments.

Conflicts to avoid:

- Do not move runtime assets before manifests and references are verified.
- Do not compress UI text or alpha-sensitive sprites without visual QA.

QA:

- alpha/checkerboard validator
- missing resource scan
- Web smoke to menu and level 1
- Android emulator smoke for representative gameplay
- draw-call/memory baseline if Cocos profiler data is accessible

Required report:

- `docs/global_modernization/graphics_inventory.md`
- `docs/global_modernization/atlas_policy_report.md`
- `docs/global_modernization/art_validation_report.md`

### Module 2 — UI/UX design system and responsive layout

Priority: P0  
Patch type: one screen at a time

Tasks:

1. Inventory screens:
   - main menu
   - start submenu
   - name entry
   - level select
   - primate select
   - settings
   - achievements
   - records
   - dev gate/panel
   - pause
   - death/fail screen
2. Convert `ui_skin_manifest.json` rules into `ui_ir.schema.yaml`-compatible project policy.
3. Define shared theme tokens and button/panel families.
4. Replace absolute layouts with Layout/SafeArea wrappers incrementally.
5. Keep interactive text strategy consistent:
   - blank/base PNG + runtime Cocos label by default;
   - canonical baked-text exceptions only if documented and atomic.

Conflicts to avoid:

- No double labels.
- No ghost legacy layers.
- No old transparent panels under new panels.
- No direct scene surgery without report.

QA:

- visual snapshots for 16:9, 18:9, 19.5:9, tablet, web wide
- click/tap all UI paths
- Cyrillic glyph fit
- dev password flow, including `primatal`
- web EditBox DOM layer duplicate-label check

Required report:

- `docs/global_modernization/ui_inventory.md`
- `docs/global_modernization/ui_ir_migration_report.md`
- `docs/global_modernization/ui_snapshot_report.md`

### Module 3 — Character skin, bonus, animation pipeline

Priority: P0  
Patch type: validate existing pack first, refactor registry second

Tasks:

1. Validate current `player_skins_manifest.json` against Tasks/4 schema concepts.
2. Run full skin x animation x bonus matrix.
3. Check pivots/baselines and frame jitter, not only alpha.
4. Introduce/normalize `SkinRegistry` and `BonusVisualResolver` boundaries.
5. Prefer baked variants for physical clothing/equipment:
   - helmet
   - vest
   - boots
   - magnet
   - shield
   - blueprint
   - radio
   - banana_boost
   - key_pass
   - coffee
6. Allow runtime VFX only for aura/glow/particles, not clothing placement.

Conflicts to avoid:

- Do not silently fallback to Brigadir in QA.
- Do not create floating runtime clothing sprites without anchors.
- Do not regenerate all assets unless validation proves source defects.

QA:

- full skin/variant/pose matrix, Web and Android emulator
- contact sheet visual review
- level transition / death / retry with selected skins
- bonus collect/expire visual cleanup check

Required report:

- `docs/skins_integration/source_inventory.md`
- `docs/skins_integration/frame_mapping_report.md`
- `docs/skins_integration/skin_bonus_qa_report.md`
- `docs/global_modernization/skin_bonus_contract_report.md`

### Module 4 — Gameplay core, mechanics, state machines

Priority: P0  
Patch type: wrapper/router before refactor

Tasks:

1. Define `player_state_machine.yaml`.
2. Define `GameSessionState` explicitly:
   - menu
   - loading
   - countdown
   - playing
   - paused
   - failed
   - completed
3. Centralize input actions:
   - jump
   - glide
   - dash
   - pause
4. Centralize collision routing:
   - pickup
   - obstacle
   - platform
   - trigger
   - finish
5. Define power-up lifecycle:
   - spawn
   - collect
   - activate
   - tick
   - expire
   - cleanup

Conflicts to avoid:

- Do not change game feel while extracting contracts.
- Do not let UI mutate player physics directly.
- Do not place bonus mechanics inside the visual skin controller.

QA:

- 10 pause/resume loops
- 10 restart loops
- level transitions
- every power-up collect/expire path
- console/logcat fatal scan

Required report:

- `docs/global_modernization/gameplay_state_report.md`
- `docs/global_modernization/powerup_lifecycle_report.md`

### Module 5 — Levels, backgrounds, platforms, content pipeline

Priority: P1  
Patch type: manifest first, level batches second

Tasks:

1. Create `level_content_manifest.json` for all 15 levels.
2. Bind per-level:
   - `bg_far`
   - `bg_mid`
   - `bg_near`
   - platform variants
   - obstacle pools
   - collectable density
   - progression markers
3. Validate platform silhouettes and background readability.
4. Ensure no old fragments appear behind new art.

Conflicts to avoid:

- Do not use one global background for all levels.
- Do not add signage/text that looks like UI/hazards in the active lane.
- Do not overload foreground layers with alpha-heavy clutter.

QA:

- 60-second representative level recordings/screenshots
- levels 1, 8, 15 mandatory
- player readability
- collectible readability
- old-asset fragment scan

Required report:

- `docs/global_modernization/level_manifest_report.md`
- `docs/global_modernization/visual_readability_report.md`

### Module 6 — Procedural validation and difficulty

Priority: P1  
Patch type: offline validator only at first

Tasks:

1. Define segment schema.
2. Implement offline segment validator.
3. Apply validators to existing handcrafted segments.
4. Add seed logging for generated/test segments.
5. Keep heuristic DDA behind feature flag.

Conflicts to avoid:

- No runtime random obstacle placement without reachability validation.
- No ML/DDA before telemetry.
- No synchronous heavy validation inside frame update.

QA:

- validator on all existing segments
- 1000 seed fuzz when generator exists
- five-minute run with telemetry
- feature flag off by default

Required report:

- `docs/global_modernization/pcg_validation_report.md`
- `docs/global_modernization/difficulty_telemetry_report.md`

### Module 7 — Audio, VFX, feedback

Priority: P1  
Patch type: event-map introduction before routing changes

Tasks:

1. Inventory current audio/VFX.
2. Define `audio_event_map.json`.
3. Define `vfx_event_map.json`.
4. Add bus model:
   - UI
   - SFX
   - MonkeyVoice
   - Ambience
   - Music
5. Add cooldowns and priority rules.
6. Ensure Web audio unlock has no console spam.

Conflicts to avoid:

- No direct `AudioSource.play` scattering after router adoption.
- No uncapped particles.
- No full-screen haze that hides gameplay.

QA:

- Web first-tap audio unlock
- settings persistence
- collect chain
- hit/death/fail
- pause/resume audio state

Required report:

- `docs/global_modernization/audio_vfx_inventory.md`
- `docs/global_modernization/feedback_qa_report.md`

### Module 8 — Save data, achievements, records, telemetry

Priority: P1  
Patch type: schema/migration first

Tasks:

1. Define `save_schema_version`.
2. Define `profile_id` / nickname scoping.
3. Define achievement/record manifests.
4. Add migration path for old saves.
5. Add local-only QA telemetry export.

Conflicts to avoid:

- No unversioned global achievements object.
- No network telemetry without explicit policy.
- No blocking save writes in hot loops.

QA:

- create profile
- custom name entry
- unlock achievement
- restart app
- switch profile
- corrupt-save recovery

Required report:

- `docs/global_modernization/save_migration_report.md`
- `docs/global_modernization/achievements_records_report.md`

### Module 9 — Android/Web release and performance

Priority: P0  
Patch type: pipeline/reporting before new release claims

Tasks:

1. Define build matrix:
   - Web Mobile
   - Android emulator debug APK
   - Android release APK
   - Android AAB optional/future
2. Add content manifest version to release notes.
3. Keep Web runtime smoke with explicit log gate.
4. Keep Android emulator install/launch/logcat smoke.
5. Add release APK verifier into the wrapper or dedicated release script.
6. Add Android vitals monitoring plan.
7. Add AAB/PAD plan only after APK/Web remains stable.

Conflicts to avoid:

- No Android success claim from Gradle build only.
- No web success claim from HTTP 200 only.
- No emulator-only ABI artifact as final release.
- No physical phone install unless explicitly authorized.

QA:

- Web HTTP smoke
- Web runtime smoke to gameplay gate
- Android emulator launch screenshot
- logcat fatal scan
- 10 restart loop
- 5-minute performance run
- APK/AAB size/hash
- final release SHA-256

Required report:

- `docs/global_modernization/release_build_report.md`
- `docs/global_modernization/android_device_qa_report.md`
- `docs/global_modernization/performance_baseline.md`

### Module 10 — Agent tooling, CI, QA, code review

Priority: P0  
Patch type: process scaffolding and validation scripts

Tasks:

1. Create compact `docs/codex/CURRENT_STATE.md`.
2. Add module report index.
3. Normalize Tasks/4 checklists into project docs.
4. Add/extend validators:
   - asset validation
   - UI IR validation
   - skin validation
   - release validation
5. Enforce retrieval-first, one-heavy-model-at-a-time policy for local helpers.
6. Add cleanup dry-run protocol.

Conflicts to avoid:

- No hooks enabled without explicit approval.
- No unbounded agent autonomy.
- No markdown-only false success.
- No destructive cleanup before dry-run.

QA:

- validator scripts parse and run
- sample module report generated
- code review checklist applied to the module diff
- cleanup dry-run reviewed

Required report:

- `docs/global_modernization/agent_execution_report.md`
- `docs/global_modernization/code_review_report.md`
- `docs/global_modernization/final_qa_report.md`

## Mandatory QA cycles for implementation

### Cycle 1 — Build and smoke

Minimum:

- `tools\validate-mtr-config.ps1`
- Web build if runtime assets/scripts changed:
  - `tools\Run-MtrCocosBuild.ps1 -ConfigPath build-web-mobile.json`
- Android emulator build if runtime assets/scripts/native Android changed:
  - `tools\Run-MtrCocosBuild.ps1 -ConfigPath build-android-emulator.json`
- Web smoke to menu and level 1.
- Android emulator install/launch/logcat smoke.

Stop condition:

- Any fatal console/logcat error blocks continuation.

### Cycle 2 — Visual and UI

Minimum:

- main menu
- start submenu
- name entry
- level select
- primate select
- settings
- achievements
- records
- dev gate/panel
- pause
- death/fail

Target aspects:

- 16:9
- 18:9
- 19.5:9
- tablet
- web wide

Stop condition:

- ghost layer, double text, overlap, unreadable Cyrillic, or broken touch target blocks continuation.

### Cycle 3 — Gameplay and physics

Minimum:

- jump
- glide
- dash
- pause
- 10 restart loop
- all collision categories
- completion and fail paths

Stop condition:

- state leak, broken pause, collision regression, or debug collider in production blocks continuation.

### Cycle 4 — Skins and bonuses

Minimum:

- 8 skins
- all base poses
- all bonus visuals:
  - helmet
  - vest
  - magnet
  - blueprint
  - radio
  - shield
  - banana_boost
  - boots
  - key_pass
  - coffee
- expiry cleanup

Stop condition:

- missing frame, visual fallback hidden as success, wrong equipment placement, or leftover bonus artifact blocks continuation.

### Cycle 5 — Audio and VFX

Minimum:

- audio buses
- Web unlock
- settings persistence
- collect/hit/fail/achievement feedback
- VFX readability

Stop condition:

- audio spam, blocked Web audio spam, or VFX hiding controls/player blocks continuation.

### Cycle 6 — Performance and device

Default target:

- Android emulator only unless physical device is explicitly authorized.

Minimum:

- 5-minute gameplay run
- memory/PSS where available
- FPS/frame pacing if available
- APK/Web size
- load times
- bundle load failures

Stop condition:

- black screen, startup timeout, crash/ANR, fatal logcat, severe frame pacing drop, or unbounded memory growth blocks release.

### Cycle 7 — Release regression and cleanup

Minimum:

- re-run critical smoke after optimization
- generate release artifacts
- generate SHA-256
- cleanup dry-run
- confirm no runtime assets accidentally removed
- final release report

Stop condition:

- release artifact missing required payload, Web/Android content version mismatch, or cleanup would delete required QA/runtime files.

## Plan audit

### Conflict audit result

| Conflict | Decision |
| --- | --- |
| Tasks/4 global scope vs current request | Treat as planning and future modular implementation, not immediate all-in-one patch. |
| Package permits emulator or real device | Use emulator-only by default; physical `R5CY933XP7P --user 0` only with explicit authorization. |
| Existing systems vs new schemas | Reuse and normalize existing manifests/tools; do not recreate blindly. |
| Monolithic `GameRoot.ts` vs modernization desire | Add contracts/validators first, then extract routers one by one. |
| Dynamic atlas temptation | Static curated atlases for runtime-critical assets; dynamic atlas only documented and measured. |
| AAB/PAD ambition | Keep as later release-engineering phase after APK/Web pipeline is stable. |
| Cleanup desire vs data loss risk | Dry-run and path-guard cleanup; no destructive delete in planning pass. |
| Git root lacks remote / nested pages repo | Do not stage/push in this audit pass; preserve nested Pages repo state. |

### Plan corrections made during audit

1. Added Module 0 before the Tasks/4 module list because the live project needs a safety/current-state scaffold first.
2. Moved Module 10 near the beginning operationally, even though it is module `10`, because report/checkpoint tooling must exist before large runtime changes.
3. Split skin validation into alpha/matte and geometry/pivot/bonus placement; the current matte scan passed but does not cover all skin risks.
4. Added explicit Android/Web content manifest versioning as a release gate.
5. Preserved the latest web QA harness fix as mandatory web runtime smoke infrastructure.
6. Preserved emulator-only default and device-valid release requirement.
7. Added cleanup-tail tracking without immediate deletion.

## Recommended execution order

1. Module 0 + Module 10 minimal scaffold:
   - current state
   - report index
   - normalized checklists
   - cleanup dry-run list
2. Module 1 validators only:
   - asset inventory
   - atlas policy
   - stricter alpha/checkerboard validation
3. Module 3 validation layer:
   - skin/bonus matrix
   - manifest-schema alignment
   - contact sheets
4. Module 2 UI inventory and one-screen UI IR pilot:
   - name entry or main menu shell recommended first
5. Module 9 release pipeline hardening:
   - content manifest version
   - release verifier
   - Web/Android parity report
6. Module 4 gameplay router wrapper:
   - state machine and event log before refactor
7. Module 5 level content manifest:
   - levels 1, 8, 15 pilot, then batches
8. Module 7 audio/VFX event map
9. Module 8 save/profile/achievement schema
10. Module 6 PCG/DDA validators, offline only

## Next safe action

Wait for user confirmation before implementation.

Recommended first implementation slice:

```text
Create Module 0/10 scaffold:
- docs/codex/CURRENT_STATE.md
- docs/global_modernization/module_execution_index.md
- normalized Tasks/4 checklists under docs/global_modernization/library/
- cleanup dry-run report
- no runtime code changes
- run validate-mtr-config.ps1
- create Hermes checkpoint
```

This gives the next heavy patch a stable runway without changing gameplay yet.
