# M04-A completion checkpoint

Date: `2026-08-21`  
Execution unit: `M04-A` (`M04.1 + M04.2`)  
Status: `completed` for asset-governance implementation and validation; overall product release remains blocked.

## Roadmap checkpoint

- **Roadmap position:** M04 / M04-A complete; next dependency-safe unit is `M04-B` (`M04.3 + M04.4`).
- **Progress:** current execution ledger `11/65` complete, `54` mandatory units remain, plus `7` conditional units.
- **Scope:** canonical asset inventory, ownership, atlas/bundle policy, schema, validator, fixtures, routing resilience and emulator-QA harness resilience.
- **Runtime effect:** none; no PNG/JPG/audio asset was moved, repacked, recompressed or deleted.
- **Release status:** blocked by `M02.1`, `M02.7` and `M12.7`; the x86_64 APK is emulator QA evidence, not a production arm64 release.

## Acceptance result

- Canonical M04-A contract: `PASS`, findings `0`, sources `1,635`, images `1,558`, ownership scopes `24`, atlas groups `11`.
- Direct contract tests: `8/8 PASS`; negative fixtures: `11/11` rejected with expected findings.
- Asset scan: `PASS`; decode errors, missing meta, oversize, white-matte suspects and reference blockers all `0`.
- Content identity and three build preflights: `PASS`.
- Typed static gate: pre-report, final and closure runs each `23/23 PASS`.
- Entrypoint inherited-handle regression: `3/3 PASS`; local coder model cleanup verified.
- Final Web build/recovery: build `PASS`, matrix `34/34`, interaction `PASS`, restart `10/10`, QA port closed.
- Final Android emulator build/recovery: build/install `PASS`, matrix `28/28`, unexpected diagnostics `0`.
- Final Android interaction: four touch actions `PASS` on first verified attempt, name `QAPrimateC4` persisted across cold restart, restart `10/10`, soak `30.719 s`, process losses `0`.
- Visual review: dash, pause, persisted-name and soak frames are coherent; no white fragments, ghost text, missing background or broken platform was observed.

## Failure receipt and correction

The first cold-boot recovery cycle failed at `touch_dash` while Android reported an `ActivityRecordInputSink` transition. The same APK and coordinate succeeded on controlled fresh starts, so the defect was isolated to emulator-input stabilization rather than gameplay. The harness now requires four stable focused input-channel samples and performs bounded marker-verified retries, recording every attempt. The original failure evidence was retained and the corrected full cycle passed.

## Evidence hashes

| Evidence | SHA-256 |
| --- | --- |
| `temp/m04-a-final-build/entrypoint-selftest.json` | `77F579D1C7D3D9F8F230265C4EE6B23D09772C6FA8E0B2D7CA3549125D148299` |
| `temp/m04-a-final-build-rerun/web-build-report.json` | `EBE2F67AC0C9F9F22BF143F3BDB039E988C36EEDC6327E8A2D1793806ED3E312` |
| `temp/m04-a-final-web/matrix-recovery.json` | `4EB25592EDAA83C027787B8EF1081EEFD69A66F69ACE3B3926F50AE1EE372311` |
| `temp/m04-a-final-android/android-build-report.json` | `C10A2D5F12B0DF393C924A232D6480125FDB6607041A8A52613AE2B73F991218` |
| `build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk` | `1E399112CC8E3892B3A78403BA043D48EA0CA0DD027DA46F7B0C284A2580517E` |
| `temp/m04-a-final-android/apk-atlas-payload.json` | `662CE2FCD6CEC949581AB45BBE416493391A0AAFD900B4E5F3CA887D0894A0DF` |
| `temp/m04-a-final-android/matrix-recovery/android_matrix_cycle3_summary.json` | `12256E3E9A224EB277C74DC55DD902DE586A1F9379D5F8F8BFB909D5B80FA0C0` |
| `temp/m04-a-final-android/interaction-recovery/failure_cycle3_touch_dash.json` | `53020FE74A513A91EA8F9199341777C08DA89FBC661F339708A920250D3176EE` |
| `temp/m04-a-final-android/interaction-recovery-cycle4/android_interaction_cycle4_summary.json` | `424D6E88E8018FBA4A8C9A78584D7FD0C11D6C25B721921996C200C2F6867619` |
| `temp/m04-a-final-review/m04-a-contract.json` | `30255EE8BA0CCA2C04D600BBE1F861DA66DA7535B17B5C8879F7DF71190D98CC` |
| `temp/m04-a-final-review/asset-scan.json` | `39BD5142BAB0200BBD74300BFF7EC2FD7F7EDA6E995CFE2E80A94EB54DA86EA2` |
| `temp/m04-a-final-review/static-gate-closure.json` | `12BCB6886D8638ECAE7D642A1E61685F2650B4883709FAC31C43D81E65B4106D` |

## Hygiene and rollback

- Rollback audit: `PASS`; `13` tracked pre-change blobs match anchor `58d057c65098935e4b8c1b6c40f4965b45238dd5`, and every present new file is declared.
- Hygiene scan: `PASS`; `25` changed/new files inspected, conflict markers `0`, stale code markers `0`, junk/backup files `0`, project helper processes `0`, port `18785` listeners `0`.
- Build, screenshots, logs, temp evidence and caches remain ignored and are not part of the source publication.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- No physical Android device was used; target was emulator-only `emulator-5554`, `ro.kernel.qemu=1`, user `0`.
- Rollback source: `docs/global_modernization/v3/M04/M04_A_ROLLBACK_MANIFEST.json`.

## Publication note

The source commit containing this checkpoint cannot embed its own hash without becoming self-referential. Exact parent commit, generated subtree commit and verified remote `mtr-source-v3` ref are therefore recorded in the post-push Hermes checkpoint and are reproducible from Git history.

## Resume order

1. Verify the post-push Hermes receipt and `origin/mtr-source-v3` ancestry.
2. Re-run the canonical M04-A Git-aware validator if the remote ref changes.
3. Start `M04-B` only from the published M04-A state.
