# Backend Runtime Dependency Audit

Date: 2026-06-12

## Scope

This project has no separate server backend. The audited backend/runtime surface is the Cocos Creator game runtime, shared config data, asset loading algorithms, Android Gradle packaging, Web release packaging, and local pipeline dependencies.

## Result

Status: passed.

## Runtime Algorithms

- `assets/scripts/GameRoot.ts` is the single runtime owner for level registry, menu flow, input handling, gameplay update, background drawing, and asset loading.
- Background loading uses a preview-first pipeline, then applies the full level bitmap when ready.
- Background frames are cached with `BACKGROUND_FRAME_CACHE_LIMIT`; dropped frames are released through Cocos `resources.release`.
- No old procedural background renderer is used for level visuals. Missing background state shows an explicit neutral loading/missing message instead of falling back to retired art.
- Main menu rendering waits for critical themed UI sprites and dedicated `ui/main_menu_background` layers before drawing the interactive menu, preventing old-menu flash before the new UI is ready.
- Quiet menu states no longer call the level bitmap background renderer; they draw the new layered menu background directly.
- The launch button is visible on the verified Android menu screen and starts gameplay.
- Object sprites are requested once per key and cached in `objectSpriteFrames`; repeated failed loads are de-duplicated by failure message.
- Input listeners registered in `onLoad` are removed in `onDestroy`.
- Active player visuals use `assets/resources/characters/player_skins`; `player_skins_v2` is retained only as a code-level compatibility redirect for stale saved keys.

## Shared Configs

- Android and Web use the same `assets/resources/config/levels.json`.
- Runtime levels match `nessesary/10/mtr_level_canon_manifest.json`.
- New backgrounds are attached through `assets/resources/config/background_manifest_texture10.json`.
- Main menu background layers are attached through `assets/resources/ui/main_menu_background/` and generated from `nessesary/10.1`.
- Object texture pools remain in `assets/resources/objectives/themed/last_iteration/` and are validated by `assets/resources/config/last_iteration_asset_manifest.generated.json`.

## Dependencies

- `package.json` declares Cocos Creator metadata only and has no npm runtime dependencies.
- TypeScript config extends the Cocos-generated `temp/tsconfig.cocos.json`; no app-specific external TS dependency was added.
- Android build uses Cocos Creator 3.8.8 native engine modules.
- Android Gradle Plugin: `com.android.tools.build:gradle:8.10.1`.
- Active Android repositories: `google()` and `mavenCentral()`.
- Release build has `minifyEnabled true` and `shrinkResources true`.
- Optional InputSDK dependency is gated by `PROP_ENABLE_INPUTSDK=false`, so it is inactive in the verified release.
- Release APK package: `com.martyskin.trudrunner`.
- Release ABIs: `arm64-v8a`, `armeabi-v7a`.

## Cleanup Confirmed

- Retired background seed prompts and old background backup seed images were removed.
- Retired skin generator script was removed after confirming the v2 skin namespace is complete.
- Deprecated repository comments in Gradle files were removed.
- Old-value scans pass for retired background manifests, retired skin namespace paths, retired APK names, retired level names, and retired menu/object tokens.
- The old single-screen/menu background path is absent from the active main-menu render path.

## Evidence

- Config validation: `tools/validate-mtr-config.ps1`
- QA cycle 1: `qa/texture10-background-evidence/reports/qa_cycle_1_full_runtime_audit_after_cleanup.json`
- QA cycle 2: `qa/texture10-background-evidence/reports/qa_cycle_2_web_clean_build_audit.json`
- QA cycle 3: `qa/texture10-background-evidence/reports/qa_cycle_3_apk_static_audit_clean.json`
- QA cycle 4: `qa/texture10-background-evidence/reports/qa_cycle_4_android_visual_runtime_audit.json`
- Android screenshots: `qa/texture10-background-evidence/screenshots/android-clean/`
- Main menu 10.1 audit: `docs/MAIN_MENU_BACKGROUND_10_1_AUDIT.md`
- Main menu 10.1 screenshots: `qa/main-menu-background-10-1/screenshots/`
