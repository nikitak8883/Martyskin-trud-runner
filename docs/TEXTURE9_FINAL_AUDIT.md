# TEXTURE9_FINAL_AUDIT

Generated: 2026-06-06.

## Scope

- Source texture directory used: `nessesary/9/`
- Source PNG count: `30`
- Runtime manifest entries: `474`
- Later source material is excluded from this pass and absent from active runtime references.

## Asset Pipeline Result

- Manifest: `assets/resources/config/last_iteration_asset_manifest.generated.json`
- Generated catalog: `assets/scripts/generated/ThemeAssetCatalog.generated.ts`
- Pipeline warnings: `0`
- Pixel audit: passed, issue count `0`
- Level logic audit: passed, issue count `0`

Role totals:

| Role | Count |
| --- | ---: |
| Obstacle | 127 |
| UiIcon | 79 |
| UiCard | 50 |
| PlatformAlt | 49 |
| PlatformMain | 35 |
| InteractiveProp | 33 |
| UiButton | 33 |
| UiProp | 17 |
| Collectible | 15 |
| UiTitle | 15 |
| Signage | 13 |
| ForegroundProp | 8 |

Theme totals:

| Theme | Count |
| --- | ---: |
| ui | 194 |
| security | 30 |
| industrial | 30 |
| steampunk | 29 |
| inspection | 29 |
| office | 28 |
| shared | 28 |
| jungle | 27 |
| logistics | 26 |
| construction | 24 |
| archive | 17 |
| farm | 12 |

## Level Audit

Every level has themed platforms, alternative platforms, and hazards. No level is backed by a whole PNG sheet.

| Level | PlatformMain | PlatformAlt | Hazards | Main themes |
| --- | ---: | ---: | ---: | --- |
| lvl01 | 5 | 13 | 36 | construction, industrial |
| lvl02 | 4 | 9 | 24 | construction, industrial |
| lvl03 | 6 | 6 | 30 | office, inspection |
| lvl04 | 7 | 13 | 37 | logistics, security, industrial |
| lvl05 | 6 | 8 | 19 | jungle, farm |
| lvl06 | 4 | 7 | 48 | inspection, security |
| lvl07 | 8 | 2 | 19 | steampunk |
| lvl08 | 13 | 7 | 33 | archive, logistics, steampunk, industrial |
| lvl09 | 8 | 5 | 47 | office, inspection, archive |
| lvl10 | 5 | 7 | 24 | construction, farm |
| lvl11 | 9 | 10 | 36 | logistics, steampunk, industrial |
| lvl12 | 12 | 8 | 30 | steampunk, jungle |
| lvl13 | 8 | 5 | 47 | office, inspection, archive |
| lvl14 | 2 | 9 | 34 | security, logistics |
| lvl15 | 8 | 3 | 49 | office, inspection, archive, security |

Farm check: farm platforms from catalog `9` are present in the farm/jungle-farm pool.

## UI Audit

- Main menu: title, props, icons, and buttons exist; launch button is present.
- Pause: themed title/icons/buttons are present; the conflicting central text-card layer is suppressed so old-looking text no longer sits under the buttons.
- Death: card/title/button coverage exists; retry/menu buttons use themed textures.
- Secondary menu UI preload is staged after main menu readiness to prevent old UI flash.
- Retired pause/menu texture keys are absent from active runtime paths.

## Old Value Annihilation

Active scan returned no matches for removed menu keys, removed platform/hazard paths, retired UI-catalog names, retired visual-runtime hooks, or active references to the excluded texture directory.

Post-cleanup also removed obsolete local web copies, old iteration folders, root logs, old APKs, and temporary workspaces.

## Build And Runtime QA

Four-cycle verification was completed:

1. Structural audit: config validation, manifest checks, old marker scan.
2. Visual/asset audit: pixel audit, level asset-role audit, menu/death/pause screenshot review.
3. Runtime audit: Web smoke, Android emulator smoke, native log marker checks.
4. Final package/deploy audit: Android release build, APK signing/badging, static web HTTP check, GitHub push, post-cleanup dry-run.

Final build results:

- Android Gradle `assembleRelease`: passed after cleanup.
- APK signature verification: passed.
- Web static release check: HTTP `200`.
- GitHub Pages deploy was superseded by the texture10 clean web release; see `docs/WEB_DEPLOY_GITHUB_PAGES.md`.

## Known External Blocker

Google Drive raw APK upload is blocked in the current tool exposure. The Drive connector rejected `application/vnd.android.package-archive` and only exposed document/spreadsheet/presentation imports.
