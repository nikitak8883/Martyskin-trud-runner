# Codex status — Hermes, Android/Web audit fixes, skin-pack route

Generated: 2026-06-19 13:28:30 +03:00  
Workspace: `C:\Projects\Monkey Work`  
Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`

## Recovery summary

Use this file as the compact local resume point if the Codex context window is compacted or interrupted.

Current stage:

1. Hermes checkpointing and entrypoint routing were verified.
2. The latest Android/Web audit was compared against previous MD reports.
3. The highest-confidence Android lint blocker was fixed and verified.
4. A new skin-pack integration route was added to the action plan, but the new PNG packs have not been integrated yet.

## Hermes / local context status

- Hermes context database: `C:\Users\nikit\.hermes-proagents\context.sqlite3`
- Hermes checkpoints root: `C:\Users\nikit\.hermes-proagents\checkpoints`
- Context integrity: `ok`
- Configured compaction/checkpoint threshold: 95% of context limit, equivalent to a 5% remaining-context safety threshold.
- Entrypoint router status:
  - Android: ready.
  - Web: ready.
  - Windows: ready.
  - Linux: not fully ready because WSL/Docker are not available in the current environment.
- Router autocorrection now resolves project-local wrappers and plugin surfaces, including the Android Gradle wrapper at:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\build\android-emulator\proj\gradlew.bat`

## Audit comparison result

Latest full audit source:

`C:\Users\nikit\.hermes-proagents\audit-spool\Monkey-Work\20260618T175118Z-android-web-audit-only\AUDIT_REPORT.md`

Compared against older restore/audit MD files in the project docs. No contradiction was found on basic build/runtime readiness. The latest audit adds the actionable issues below:

- `F-ANDROID-LINT-001` — Android lint failed in `:libcocos`.
- `F-UI-OVERLAP-001` — sound/settings UI text overlap on Android/Web.
- `F-WEB-LAYOUT-001` — Web kiosk 1280x720 shifted/cropped.
- `F-HERMES-ROUTER-001` — Canvas/game automation should be screenshot/OCR/template/image-driven.
- `F-ANDROID-RUNTIME-LOGS-001` — noisy Android runtime logs without crash.

## Applied project/runtime fix

Fixed the Android lint blocker in the Cocos Creator 3.8.8 runtime used by this project.

Files modified:

- `C:\ProgramData\cocos\editors\Creator\3.8.8\resources\resources\3d\engine\native\cocos\platform\android\libcocos2dx\AndroidManifest.xml`
  - Added `android.permission.VIBRATE`, required by `CocosHelper.java`.
- `C:\ProgramData\cocos\editors\Creator\3.8.8\resources\resources\3d\engine\native\cocos\platform\android\java\src\com\cocos\lib\CocosLocalStorage.java`
  - Replaced unsafe direct `getColumnIndex(...)` usage with checked column-index handling in `getItem`, `getKey`, and `getLength`.

Verification:

- `.\gradlew.bat :libcocos:lintDebug` — `BUILD SUCCESSFUL`.
- `.\gradlew.bat :CocosGame:assembleDebug` — `BUILD SUCCESSFUL`.
- Lint report no longer contains the previous `VIBRATE` or `getColumnIndex can be -1` errors.
- Merged manifests contain `android.permission.VIBRATE`.
- Debug APK produced at:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\build\android-emulator\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk`

## New skin-pack integration route added

User-provided task files:

- Prompt:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\Tasks\1\MTR_CODEX_SKIN_PACK_CUT_AND_INTEGRATION_PROMPT.md`
- Prompt SHA file:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\Tasks\1\MTR_CODEX_SKIN_PACK_CUT_AND_INTEGRATION_PROMPT.md.sha256.txt`
- New source skins:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\Tasks\1\Skin-paks`

Preflight result:

- Prompt file exists.
- Prompt SHA-256 verified:
  `A76F9E3D23DFFE3C1B7DD6BA7221B8A40D8F1B790345B6A7F06D90E2D7262262`
- `Skin-paks` exists.
- 14 PNG files found.

Important prompt constraints to preserve:

- Do not perform destructive cleanup before reports and explicit confirmation.
- Do not blindly rename source files.
- First create source mapping and extraction reports.
- Prefer baked bonus variants over fragile runtime clothing composition unless exact anchors exist.
- Do not delete existing `.meta` files.
- Do not integrate sheets with baked checkerboard/background artifacts; mark them as `needs_alpha_repair` or quarantine.

Skin-pack action plan:

1. Phase 0 — safety and local recovery
   - Read the full skin-pack prompt before implementation.
   - Read relevant project docs if present: `docs/agent/START_FROM_HERE_CODEX_FIRST.md`, `docs/codex/CURRENT_STATE.md`, `docs/tz/`, `docs/audit/`, `MARTYSKIN_WORLD.md`, and existing skin pipeline docs.
   - Create a Hermes checkpoint before any bulk asset operation.

2. Phase 1 — inventory and mapping
   - Enumerate all PNG files from `Tasks\1\Skin-paks`.
   - Infer `skin_id`, sheet type, confidence, and reason.
   - Create:
     `assets/resources/characters/player_skins/_shared/extraction_reports/source_file_mapping_report.md`
   - Stop for confirmation if confidence is low or ambiguous.

3. Phase 2 — PNG / alpha QA
   - Inspect image mode, dimensions, alpha distribution, transparent/sem transparent/opaque pixels.
   - Detect baked checkerboard or solid background pixels.
   - Create contact sheets and a machine-readable inspection report.
   - Quarantine or mark `needs_alpha_repair` when the source is not clean enough.

4. Phase 3 — extraction and normalization scripts
   - Implement scripts for alpha-based sprite detection, connected components, row grouping, cropping with padding, baseline normalization, and debug overlays.
   - Keep output staged and reversible.
   - Preserve proportions and VFX that are part of a frame.

5. Phase 4 — target asset structure and manifests
   - Stage assets under:
     `assets/resources/characters/player_skins/<skin_id>/`
   - Use subfolders: `source_sheets`, `base`, `bonus`, `preview`, `headshot`, `manifests`.
   - Create shared reports/debug outputs under:
     `assets/resources/characters/player_skins/_shared/`
   - Generate runtime manifests for frames, animations, previews, and baked bonus variants.

6. Phase 5 — runtime integration
   - Add/adjust TypeScript skin registry and runtime loading.
   - Wire skins into gameplay, character select, records/achievements where applicable.
   - Prefer data-driven manifests over hardcoded per-file assumptions.

7. Phase 6 — Android/Web QA
   - Verify Web load, character select, gameplay skin swap, bonus variants, records/achievements paths.
   - Verify Android emulator install/launch/render and relevant logs.
   - Compare visual output against debug contact sheets.

8. Phase 7 — cleanup proposal
   - List old conflicting references.
   - Mark deprecated references.
   - Provide a safe cleanup plan.
   - Wait for explicit user confirmation before mass removal.

## Remaining known work

1. Fix sound/settings text overlap on Android/Web.
2. Fix Web 1280x720 kiosk layout shift/crop.
3. Add screenshot/OCR/template-driven Canvas automation where it materially improves QA reliability.
4. Triage noisy Android runtime logs.
5. Begin skin-pack Phase 0/1 only after the next explicit go-ahead.

## Stop point

Stop after creating this log and a Hermes checkpoint. Next recommended work item is either:

- start skin-pack preflight/inventory/mapping, or
- continue remaining Android/Web UI/layout audit fixes.
