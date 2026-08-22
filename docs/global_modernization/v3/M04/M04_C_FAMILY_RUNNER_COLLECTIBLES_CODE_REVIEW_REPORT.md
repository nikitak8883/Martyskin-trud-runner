# M04-C runner_collectibles code, contract and QA review

Date: `2026-08-22`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- The 14-source `runner_collectibles` Cocos Auto Atlas descriptor and metadata.
- The DEBUG-only multi-family atlas measurement route on Web and Android native.
- Exact ownership, runtime-key, contract, artifact, screenshot and manifest linkage.
- Frozen before/after comparison, two full post-fix Web cycles, two full post-fix Android-emulator matrices, interaction/restart/soak, M2_PLUS and rollback records.
- No production release, Pages deployment, signing decision or physical-device scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| The accepted `runner_collectibles` manifest entry retained `platform_default_pending_measurement` compression text | Corrected to the measured Web/Android `auto_atlas_png_lossless` state; the contact-sheet index, both builds, both platform matrices and M2_PLUS were regenerated/rerun afterward. |
| Exact validator counts still described the two-atlas source state | The first static gate failed visibly at `25/26`; expected source/descriptor/measured-atlas counts and ordered family IDs were updated, then two full cycles and the post-fix gate passed `26/26`. |
| A context-insufficient manifest patch transiently matched `ui_shared_core` | Reverted before validation and replaced with atlas-ID-bounded edits; a complete group table and static validator confirmed `ui_shared_core` remains policy-only and `runner_collectibles` alone gained the measured state. |
| The first targeted unittest command placed `-B` after the unittest module | Reissued with interpreter flags in the valid position; `11/11` tests passed. |
| Early emulator boot polling attempted `.Trim()` on an offline/null ADB response | No product mutation occurred; all accepted device checks use a ready `emulator-5554`, explicit `-s`, qemu guard and user `0`. Future polling is null-safe. |

Confirmed product/code findings after correction: `0`. Open findings: `0`.

## Independent evidence

- Comparison: `63/63 PASS`; negative identity drift is rejected.
- Manifest validator tests: `11/11 PASS`; metric instrumentation PASS.
- Static: `26/26 PASS × 2` plus post-fix `26/26`, findings `0`.
- Web post-fix: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`.
- Android emulator post-fix: fresh build/install to `emulator-5554`, user `0`; `28/28 × 2`.
- Android interaction: touch/name persistence PASS, restart `10/10`, soak `300.301 s`, process losses `0`, unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable slots PASS; four focused-recovery slots explicitly not applicable because no save, migration, signing, release or recovery seam changed.
- Hygiene: no tracked build output, backup/reject/temp-source/pyc artifact or surviving QA listener in project scope.

## Residual limits

- Acceptance applies only to `runner_collectibles`; aggregate source package `M04.5` and parent `M04-C-FAMILIES` remain open.
- `bonus_items` remains deferred because its sources span two directories and one descriptor would require an unauthorized relocation or split contract.
- The x86_64 debug APK is emulator QA evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
