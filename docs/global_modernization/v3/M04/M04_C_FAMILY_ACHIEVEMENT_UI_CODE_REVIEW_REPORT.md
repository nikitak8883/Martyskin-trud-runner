# M04-C achievement_ui code, contract and QA review

Date: `2026-08-21`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- The nine-source `achievement_ui` Cocos Auto Atlas descriptor and metadata.
- The DEBUG-only multi-family atlas measurement route on Web and Android native.
- Contract-driven artifact and screenshot selection, visual comparator and manifest validator.
- Two full Web cycles, two full Android-emulator matrices, one Android interaction/restart/soak cycle, M2_PLUS and roadmap/rollback records.
- No production release, Pages deployment, signing decision or physical-device scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Artifact measurement could silently retain the pilot source directory | Fixed fail-closed with explicit contained `--candidate-source-directory`; the report records the selected directory. |
| Windows PowerShell 5.1 evaluated `$PSScriptRoot` too early in a parameter default | Fixed by resolving the script path after entry; child CLI regression passed. |
| Successful `adb pull` progress on stderr became a false NativeCommandError | Fixed by treating the native exit code as authoritative while retaining stderr evidence. |
| Visual comparison was hard-wired to `atlas-pilot.png` | Fixed with contract-driven, basename-validated screenshot selection. |
| M2 review initially ran `node --check` on an intentionally anonymous function expression | Corrected to validate the executable CLI; the function itself executed in both Web cycles and metric tests. The failed run remains preserved as a tooling receipt. |
| Local advisory proposed five null dereferences in `GameRoot` | Rejected after direct source tracing: both asynchronous paths have explicit null guards and metric helpers use optional chaining with empty-array fallback. |
| Local advisory questioned case-sensitive PNG names and contract constants | Rejected as intentional fail-closed behavior: the contract owns one exact screenshot basename and regression values must drift visibly. |

Confirmed product/code findings after correction: `0`. Rejected non-reproducible or intentional-guard hypotheses: `7`. Open findings: `0`.

## Independent evidence

- Comparison: `63/63 PASS`; negative identity drift is rejected.
- Manifest validator tests: `11/11 PASS`; metric instrumentation PASS.
- Static gate: `26/26 PASS × 2`, findings `0`.
- Web: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`.
- Android emulator: fresh build/install to `emulator-5554`, user `0`; `28/28 × 2`.
- Android interaction: touch/name persistence PASS, restart `10/10`, soak `300.914 s`, process losses `0`, unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable slots PASS; four focused-recovery slots explicitly not applicable because no save, migration, signing, release or recovery seam changed.
- Hygiene: no backup/reject/temp-source/pyc artifacts in tracked scope; no QA listener or build process remained; local coding model verified unloaded.

## Residual limits

- Acceptance applies only to `achievement_ui`; aggregate source package `M04.5` and parent `M04-C-FAMILIES` remain open.
- The x86_64 debug APK is emulator QA evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
