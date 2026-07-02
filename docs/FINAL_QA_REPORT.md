# Final QA Report - Texture10/Main Menu Clean

Date: 2026-06-12

## Result

Final status: passed for texture10 background integration, texture9 object-pool compatibility, main menu background 10.1 layered integration, old-value cleanup, backend/runtime/dependency audit, Web build/deploy preparation, Android release build, APK static audit, and Android runtime smoke.

## Artifacts

- APK: `C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk`
- APK SHA256: `56C9496A31BEA98D4BE362B2BD212665845C598E7004228A02EA957313B2C1E8`
- Package: `com.martyskin.trudrunner`
- Web release: `C:\Test\MTRCocosCreator\releases\web`
- GitHub Pages commit: `67b49efd97ec92d45f741c46c81ccfb05b0c5c66`
- GitHub Pages URL: `https://nikitak8883.github.io/Martyskin-trud-runner/`
- Evidence: `C:\Test\MTRCocosCreator\qa\texture10-background-evidence`
- Main menu evidence: `C:\Test\MTRCocosCreator\qa\main-menu-background-10-1`
- Checksums: `C:\Test\MTRCocosCreator\releases\checksums\SHA256SUMS.txt`

## Four QA Cycles

1. Config/resource audit: passed. 15 levels match `nessesary/10/mtr_level_canon_manifest.json`; 15 backgrounds and previews have expected sizes; old tokens are absent.
2. Web clean build audit: passed. `build/web-mobile` and `releases/web` are current; HTTP smoke returned 200; old token scan passed.
3. APK static audit: passed. Release APK built and scanned; old background/player namespaces and retired level names are absent.
4. Android runtime audit: passed. Clean install launched, menu has the launch button, tapping it reaches gameplay, new layered main menu background renders, and logcat has no game FATAL/ANR.
5. Backend/runtime/dependency audit: passed. No separate server backend exists; Cocos runtime, shared configs, asset-loading algorithms, Android Gradle dependencies, and Web release packaging were checked.

## Runtime Evidence

- Android menu: `qa\texture10-background-evidence\screenshots\android-clean\01-menu.png`
- Android gameplay: `qa\texture10-background-evidence\screenshots\android-clean\02-gameplay-after-start.png`
- Reports: `qa\texture10-background-evidence\reports\qa_cycle_1_full_runtime_audit_after_cleanup.json` through `qa_cycle_4_android_visual_runtime_audit.json`
- Backend/runtime/dependency audit: `docs\BACKEND_RUNTIME_DEPENDENCY_AUDIT.md`
- Main menu Web menu screenshot: `qa\main-menu-background-10-1\screenshots\web-menu-1280x720-final-20260612.png`
- Main menu Web gameplay screenshot: `qa\main-menu-background-10-1\screenshots\web-after-start-1280x720-final-20260612.png`
- Main menu Android menu screenshot: `qa\main-menu-background-10-1\screenshots\android\09-menu-final-20260612.png`
- Main menu Android gameplay screenshot: `qa\main-menu-background-10-1\screenshots\android\10-after-start-final-20260612.png`
- Backend/runtime/dependency audit JSON: `qa\texture10-background-evidence\reports\backend_runtime_dependency_audit_20260612.json`

## Google Drive

Raw APK upload is blocked by the currently exposed Google Drive tools: no callable arbitrary `upload_file` tool is available for APK MIME. The APK is built, signed, checksumed, and ready for manual Drive upload or a Drive connector exposing raw binary upload.
