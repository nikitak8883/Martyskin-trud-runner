# Cleanup Report

Generated: 2026-06-12.

## Result

Post-cleanup status: passed.

## Removed

- Retired background runtime families, old manifests, and old rebuild script folders.
- Retired pre-v2 player skin runtime fallback after verifying `player_skins_v2` completeness.
- Old release APKs superseded by `Martyshkin-Trud-texture10-clean-20260612-release.apk`.
- Old main-menu background path was superseded by the dedicated `ui/main_menu_background` layered set.
- Stale Web release contents before copying the clean `build/web-mobile`.
- Retired level names and old menu/object tokens from active source/config/docs.
- Retired background seed prompts and backup seed images.
- Retired skin generator script tied to the removed source namespace.
- Deprecated Gradle repository comments.

## Kept

- `assets/`
- `build/`
- `docs/`
- `library/`
- `native/`
- `nessesary/9/`
- `nessesary/10/Levels/`
- `qa/texture10-background-evidence/`
- `releases/`
- `tools/`

## Current Cleanup Audit

- `qa/texture10-background-evidence/reports/qa_cycle_1_full_runtime_audit_after_cleanup.json`
- `qa/texture10-background-evidence/reports/qa_cycle_2_web_clean_build_audit.json`
- `qa/texture10-background-evidence/reports/qa_cycle_3_apk_static_audit_clean.json`
- `qa/texture10-background-evidence/reports/qa_cycle_4_android_visual_runtime_audit.json`
- `qa/texture10-background-evidence/reports/backend_runtime_dependency_audit_20260612.json`
- `qa/texture10-background-evidence/reports/release_apk_texture10_clean_20260612.json`
- `qa/main-menu-background-10-1/main_menu_background_10_1_report.json`
- `qa/main-menu-background-10-1/screenshots/`
- `qa/texture10-background-evidence/reports/post_cleanup_old_marker_scan.json`
- `docs/BACKEND_RUNTIME_DEPENDENCY_AUDIT.md`

## Final Release

- APK: `releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk`
- APK SHA256: `56C9496A31BEA98D4BE362B2BD212665845C598E7004228A02EA957313B2C1E8`
- Web: `releases/web/`
- Checksums: `releases/checksums/SHA256SUMS.txt`
