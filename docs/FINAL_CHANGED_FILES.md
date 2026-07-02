# Final Changed Files - Texture10/Main Menu Clean

Date: 2026-06-12

## Runtime And Asset Pipeline

- `assets/scripts/GameRoot.ts`
- `assets/resources/backgrounds/`
- `assets/resources/backgrounds_preview/`
- `assets/resources/backgrounds/background_sources.json`
- `assets/resources/config/background_manifest_texture10.json`
- `assets/resources/config/levels.json`
- `assets/resources/config/theme_asset_integration_plan_20260603.json`
- `assets/resources/config/strings_ru.json`
- `assets/resources/config/bonus_visual_states.json`
- `assets/resources/ui/main_menu_background/`
- `tools/asset_generation/build_martyshkin_main_menu_background.py`
- `tools/asset_generation/build-martyshkin-main-menu-background.ps1`
- `tools/asset_generation/build_martyshkin_texture10_backgrounds.py`
- `tools/asset_generation/build-martyshkin-backgrounds.ps1`
- `tools/scan_and_fix_white_matte_edges.py`
- `native/engine/android/build.gradle`
- `build/android/proj/build.gradle`

## Removed Runtime Surfaces

- retired pre-v2 player skin resource folder
- old background v2/v3 folders and manifests
- old release APKs superseded by the texture10 clean APK
- retired background seed prompts and seed backup images
- retired skin variant generator tied to the removed skin source namespace

## Release Artifacts

- `releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk`
- `releases/web/`
- `releases/checksums/SHA256SUMS.txt`

## QA Evidence

- `qa/texture10-background-evidence/reports/`
- `qa/texture10-background-evidence/screenshots/android-clean/`
- `qa/texture10-background-evidence/contact_sheets/`
- `qa/texture10-background-evidence/build-web-clean-stdout.log`
- `qa/texture10-background-evidence/build-android-clean-stdout.log`
- `qa/texture10-background-evidence/reports/backend_runtime_dependency_audit_20260612.json`
- `qa/texture10-background-evidence/reports/release_apk_texture10_clean_20260612.json`
- `qa/main-menu-background-10-1/main_menu_background_10_1_report.json`
- `qa/main-menu-background-10-1/screenshots/`
- `qa/texture10-background-evidence/reports/post_cleanup_old_marker_scan.json`

## Final Documentation

- `docs/FINAL_PROJECT_MANIFEST.md`
- `docs/FINAL_QA_REPORT.md`
- `docs/FINAL_INSTALL_RUN_GIT_GUIDE_RU.md`
- `docs/CLEANUP_INVENTORY.md`
- `docs/CLEANUP_REPORT.md`
- `docs/WEB_DEPLOY_GITHUB_PAGES.md`
- `docs/BACKEND_RUNTIME_DEPENDENCY_AUDIT.md`
- `docs/CODEX_ANDROID_UPDATE_MASTER_TASK.md`
- `docs/CLEANUP_PLAN.md`
- `README_RU.md`
