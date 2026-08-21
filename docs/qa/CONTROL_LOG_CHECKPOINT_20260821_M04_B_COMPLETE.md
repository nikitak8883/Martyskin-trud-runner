# M04-B completion checkpoint

Date: `2026-08-21`  
Execution unit: `M04-B` (`M04.3 + M04.4`)  
Status: `completed`; overall product release remains blocked.

## Roadmap checkpoint

- **Roadmap position:** M04 / M04-B complete; next dependency-safe unit is `M04-C-PILOT` (`M04.5`, one family only).
- **Progress:** execution ledger `12/65` complete, `53` mandatory units remain, plus `7` conditional units; source ledger `28/95` complete, `57` mandatory packages remain plus `10` conditional.
- **Runtime effect:** none; no gameplay source, PNG/JPG/JPEG or Cocos import metadata changed.
- **Release status:** blocked by `M02.1`, `M02.7` and `M12.7`; the APK below is emulator-only debug evidence.

## Acceptance result

- Pre-import validator: `1,558` images, blocker count `0`, trim `585 auto + 973 none`, pivots `1,558/1,558` at `0.5,0.5`.
- Contact sheets: seven categories, `1,558/1,558` exact coverage, `29` pages, unclassified/duplicates `0/0`.
- Direct tests: `14/14 PASS`; final static gate: `25/25 PASS`, findings `0`.
- Web: fresh build; cycle 1 and 2 each `34/34`, interaction PASS, restart `10/10`.
- Android emulator: fresh build/install to `emulator-5554`, user `0`; cycle 1 and 2 each `28/28`.
- Android interaction: touch/FSM PASS, name persisted across cold restart, restart `10/10`, soak `300.104 s`, process losses `0`.
- Visual review: representative Web/Android menu, name, level 15 and soak frames are coherent; no white fragments, ghost layer, missing background or broken platform observed.

## Evidence hashes

| Evidence | SHA-256 |
| --- | --- |
| `temp/m04-b-development/asset-validation-hardening.json` | `C109ED6C30589307246C5C104C80DC795575872BC417197ABCAD08B32E03A4F5` |
| `docs/global_modernization/v3/M04/contact_sheet_index.json` | `CBD9D7F2DBD4E2200681068F1A31E6CB99B321824E20DB3E9448A18EFE61BF7C` |
| `temp/m04-b-static-gate-final/report.json` | `9F1134FFED3DFD5A429A25C7279B2C63F6D33C3E23F33B42B65994A4B5D292D5` |
| `temp/m04-b-final-web-build/web-build-report.json` | `BA584E431ED5F75C0A5C859B22EC0F3D308274F7420A26E3CE7F5EF3A9F9C49E` |
| `temp/m04-b-final-web/matrix-cycle1.json` | `41E0759C4178E9F0C720D0BF21AF6570DC7D59D433D8DFFCB033726BB339CE0A` |
| `temp/m04-b-final-web/matrix-cycle2.json` | `0A8479AF101D794CC6F662961644D2BD6EA91AC237C23789E22B850D4940E2F1` |
| `temp/m04-b-final-android-build/android-build-report.json` | `43B8FBD75ADA91DE61F8059CEA4B8801ABFB2EC9EA81E4400C97BA5A0E3F6213` |
| `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk` | `1E399112CC8E3892B3A78403BA043D48EA0CA0DD027DA46F7B0C284A2580517E` |
| `temp/m04-b-final-android/matrix-cycle1/android_matrix_cycle1_summary.json` | `6EAE9DCF497B21FD50D1B1C091CC7A53578BA0F4A5E7705D7E4E5C96BCBBE57F` |
| `temp/m04-b-final-android/matrix-cycle2/android_matrix_cycle2_summary.json` | `E1CD5CC23AFF6A40B5C6CE4FF20F09BC7F1968244FD34C295BE993E35591F408` |
| `temp/m04-b-final-android/interaction-cycle1/android_interaction_cycle1_summary.json` | `46209D480FFD455D89F907E5AF4D1700757F8B5A046160571837646660A49D45` |

## Failure receipt and prevention

The first post-review static gate preserved a single `WinError 5` from the pre-existing atomic JSON writer self-test. The isolated test passed immediately and a full clean rerun passed all `25/25`; no product or M04-B defect reproduced. Confirmed containment and stale-artifact risks found during review were fixed and covered by regression tests.

## Hygiene and rollback

- Local QA server on port `9492` is stopped; generated builds/screenshots/logs/temp reports remain ignored.
- Stale contact-sheet pages are removed only by exact generator ownership under the selected temp output root.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- Physical Android device used: `NO`.
- Rollback source: `docs/global_modernization/v3/M04/M04_B_ROLLBACK_MANIFEST.json`.

## Publication note

The source commit cannot embed its own hash. Exact parent commit, subtree split, remote ref and final post-commit gate are recorded in the Hermes milestone checkpoint after publication.

## Resume order

1. Verify the post-push Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run the M04-B strict asset/contact-sheet checks if source or canonical manifests drift.
3. Start `M04-C-PILOT` with one measured low-risk atlas family only; do not batch the remaining families.
