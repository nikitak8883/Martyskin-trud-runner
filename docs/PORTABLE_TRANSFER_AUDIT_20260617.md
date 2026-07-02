# Portable Transfer Audit 20260617

Project root: `C:\Test\MTRCocosCreator`

## Source size before transfer packaging
- Files: 38192
- Bytes: 5364570726
- GB: 4.996

## Top-level directory sizes
- `build`: 3677.84 MB
- `.git`: 724.97 MB
- `Martyshkin world pictures`: 375.31 MB
- `nessesary`: 343.35 MB
- `releases`: 232.95 MB
- `library`: 221.52 MB
- `assets`: 110.68 MB
- `qa`: 72.35 MB
- `texture`: 68.8 MB
- `temp`: 11.96 MB
- `native`: 0.21 MB
- `tools`: 0.16 MB
- `docs`: 0.12 MB
- `.idea`: 0.09 MB
- `assets_seed`: 0.09 MB
- `settings`: 0.01 MB
- `profiles`: 0.0 MB
- `.creator`: 0.0 MB

## Large files over 50 MB
- `build/android/proj/build/RelWithDebInfo/156x1w1d/arm64-v8a/libcocos_engine.a`: 550.53 MB
- `build/android/proj/build/RelWithDebInfo/156x1w1d/armeabi-v7a/libcocos_engine.a`: 409.22 MB
- `build/android/proj/build/CocosGame/intermediates/cxx/RelWithDebInfo/156x1w1d/obj/arm64-v8a/libcocos.so`: 230.82 MB
- `build/android/proj/build/CocosGame/intermediates/merged_native_libs/release/mergeReleaseNativeLibs/out/lib/arm64-v8a/libcocos.so`: 230.82 MB
- `build/android/proj/build/CocosGame/intermediates/cxx/RelWithDebInfo/156x1w1d/obj/armeabi-v7a/libcocos.so`: 197.78 MB
- `build/android/proj/build/CocosGame/intermediates/merged_native_libs/release/mergeReleaseNativeLibs/out/lib/armeabi-v7a/libcocos.so`: 197.78 MB
- `build/android/proj/build/CocosGame/outputs/apk/release/CocosGame-release.apk`: 124.59 MB
- `releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk`: 124.59 MB
- `nessesary/9.zip`: 54.87 MB

## Transfer policy
Included in portable archive:
- Cocos source assets: `assets/`, `assets.meta`
- Project settings: `settings/`, `.creator/` metadata when explicitly allowed by Cocos source files
- Native/project support: `native/`, root build configs, `package.json`, `tsconfig.json`
- Source/reference assets: `nessesary/`, `Martyshkin world pictures/`, `texture/`, `assets_seed/`
- Documentation and tools: `docs/`, `tools/`, `AGENTS.md`, `README_RU.md`
- Final user-facing outputs: `releases/android/`, `releases/web/`, `releases/checksums/`

Excluded from portable archive:
- Cocos and Gradle generated folders: `build/`, `library/`, `temp/`
- IDE/user folders: `.idea/`, `profiles/`
- QA scratch evidence: `qa/`
- Transient logs and duplicate archives: `*.log`, `*.tmp`, `*.zip`, except extracted source folders
- Non-final Android outputs outside `releases/android/`

No files were deleted by this transfer preparation.

Generated transfer output directory:
`C:\Test\MTRCocosCreator_portable_transfer_20260617`
