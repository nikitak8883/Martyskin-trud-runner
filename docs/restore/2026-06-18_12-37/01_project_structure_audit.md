# Project structure audit

## Root status

- Transfer directory found: yes.
- The transfer directory was initially an artifact container, not a Cocos project root.
- ZIP extraction created the actual project root:
  `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`
- Recommendation: keep the transfer artifacts and project in separate directories as they are now. Do not silently flatten or move the project.

## Transfer integrity

- Archive SHA-256: `5F29546EDA97D6C716D95DB707E58F085A05D16359326C2B8F70EC7A21BCA873`
- Archive contains 7,143 files and 1,129,177,994 uncompressed bytes.
- Full checksum verification: 7,144 checked including the ZIP, 0 missing, 0 mismatches.
- All seven top-level transfer artifacts match `TRANSFER_ARTIFACTS_SHA256SUMS.txt`.
- The Git bundle transfer hash also matches.

Conclusion: the portable transfer is intact.

## Cocos project identification

This is a valid Cocos Creator 3.x project:

- `package.json` declares Cocos Creator `3.8.8`.
- Project UUID: `c1388105-2ed5-4a8e-859c-72fccfc177e8`.
- `assets\`, `settings\`, `.creator\`, `native\`, `tsconfig.json` and build configs are present.
- Main scene: `assets\scenes\main.scene`.
- Start scene UUID in both build configs: `9b5fe441-884f-49d0-b7e7-1037af1377d8`.

The missing root `project.json` is not evidence of damage for this Creator 3.8 project. Project identity is stored in `package.json`; `settings\v2\packages\project.json` contains project settings.

## Key paths

- `package.json`: found
- `tsconfig.json`: found
- `assets\`: found
- `assets.meta`: found
- `settings\`: found
- `native\`: found
- `docs\`: found
- `.gitignore`: found
- `README_RU.md`: found
- `build-android.json`: found
- `build-web-mobile.json`: found
- `project.json` at root: absent, acceptable for this project format
- `src\`: absent; game TypeScript is under `assets\scripts`
- `scripts\`: absent; project tools are under `tools\`
- `build-templates\`: absent
- `.git\`: absent

## Package manager

- `package-lock.json`: absent
- `pnpm-lock.yaml`: absent
- `yarn.lock`: absent
- `package.json` has no scripts, dependencies or devDependencies.
- Selected package manager if one becomes necessary: npm.
- No Node dependency restoration is currently required.

## Asset metadata

- Asset content files: 1,318
- Asset `.meta` files: 1,501
- Asset directories: 184
- Content files missing `.meta`: 0
- Directories missing `.meta`: 0
- Scenes: 1
- Prefabs: 0

Conclusion: there is no sign of mass `.meta` loss.

## Duplicate/cache/build audit

- No `library`, `temp`, `build`, `node_modules`, `.gradle`, backup or nested copy directory was found in the extracted root.
- `releases\` is intentionally included and contains the canonical Web release and APK.
- The only nested `project.json` is the normal Cocos settings file at `settings\v2\packages\project.json`.
- No suspicious nested project copy was found.

## Existing release artifacts

- APK: `releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk`
- APK size: 130,638,198 bytes
- APK SHA-256: `56C9496A31BEA98D4BE362B2BD212665845C598E7004228A02EA957313B2C1E8`
- Web entry point: `releases\web\index.html`
- Release checksum verification: 3,860 files checked, 0 missing, 0 mismatches.

`README_RU.md` mentions a June 11 APK name, but the canonical manifest, QA report, checksum file and actual artifact consistently identify the June 12 release.

## Project validation

`tools\validate-mtr-config.ps1` completed successfully:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present.
```

## Structure conclusion

The extracted project is complete and internally consistent. The transfer itself is healthy; current blockers are environment/tooling blockers, not missing project data.

