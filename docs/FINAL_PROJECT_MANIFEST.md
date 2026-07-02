# FINAL_PROJECT_MANIFEST

Generated: 2026-06-12 after texture10 background rebuild, main menu background 10.1 integration, old-value cleanup, Android release verification, Web verification, and post-cleanup.

## Canonical Source

- `assets/`
- `assets/scripts/GameRoot.ts`
- `assets/scripts/generated/ThemeAssetCatalog.generated.ts`
- `assets/resources/backgrounds/`
- `assets/resources/backgrounds_preview/`
- `assets/resources/ui/main_menu_background/`
- `assets/resources/objectives/themed/last_iteration/`
- `assets/resources/characters/player_skins/`
- `assets/resources/config/levels.json`
- `assets/resources/config/background_manifest_texture10.json`
- `assets/resources/config/last_iteration_asset_manifest.generated.json`
- `assets/scenes/main.scene`

## Canonical Config And Level Data

- `build-android.json`
- `build-web-mobile.json`
- Shared runtime logic and level registry in `assets/scripts/GameRoot.ts`
- Shared level data in `assets/resources/config/levels.json`
- Android and Web consume the same Cocos asset/config data.

## Canonical Tools

- `tools/asset_generation/build_martyshkin_texture10_backgrounds.py`
- `tools/asset_generation/build-martyshkin-backgrounds.ps1`
- `tools/asset_generation/build_martyshkin_main_menu_background.py`
- `tools/asset_generation/build-martyshkin-main-menu-background.ps1`
- `tools/mtr_last_iteration_asset_pipeline.py`
- `tools/validate-mtr-config.ps1`
- `tools/mtr_cleanup_audit.py`
- `tools/scan_and_fix_white_matte_edges.py`

## Canonical Source Assets

- `nessesary/10/Levels/` - source PNG folders for 15 level backgrounds.
- `nessesary/10.1/` - historical source PNG set for the retired layered main menu audit; runtime uses one cohesive generated `main_menu_bg_far.png`.
- `nessesary/10/mtr_level_canon_manifest.json` - canonical texture10 level map.
- `nessesary/9/` - transparent object/UI/level sprite source pool for gameplay assets.

## Final Android Release

- APK: `releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk`
- SHA256: `56C9496A31BEA98D4BE362B2BD212665845C598E7004228A02EA957313B2C1E8`
- Package: `com.martyskin.trudrunner`
- Version: `1.0`, versionCode `1`
- minSdk: `21`
- targetSdk: `35`
- compileSdk: `36`
- Native ABIs: `arm64-v8a`, `armeabi-v7a`

## Final Web Release

- `releases/web/index.html`
- `releases/web/application.js`
- `releases/web/assets/`
- `releases/web/cocos-js/`
- `releases/web/src/`
- File count: `3859`
- Total bytes: `113078927`

## GitHub Pages Deployment

- Repository: `https://github.com/nikitak8883/Martyskin-trud-runner`
- Branch: `main`
- Pushed commit: `67b49efd97ec92d45f741c46c81ccfb05b0c5c66`
- Commit message: `Deploy texture10 main menu background build`
- Public URL: `https://nikitak8883.github.io/Martyskin-trud-runner/`

## Checksums

- `releases/checksums/SHA256SUMS.txt`
- `docs/BACKEND_RUNTIME_DEPENDENCY_AUDIT.md`

## Build Outputs Kept

- `build/web-mobile/`
- `build/android/`
- `library/`
- `temp/`

These are reproducible outputs/caches kept because the final verification used them and the project root is not a Git repository.

## Google Drive Status

Raw APK upload is blocked by the current Google Drive tool exposure. The connector exposes Docs/Sheets/Slides imports and metadata/fetch actions, but not arbitrary binary `upload_file` for APK. The local APK above remains the canonical release artifact.
