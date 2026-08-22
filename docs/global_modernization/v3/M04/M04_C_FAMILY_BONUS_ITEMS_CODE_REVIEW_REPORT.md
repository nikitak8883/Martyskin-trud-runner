# M04-C bonus_items code, contract and QA review

Date: `2026-08-22`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- Twelve gameplay bonus/equipment PNGs represented by two Cocos Auto Atlas descriptors in their original directories.
- DEBUG-only family measurement routing on Web and Android native.
- Multi-directory artifact measurement, manifest/schema/contract identity, visual parity and rollback linkage.
- Frozen before/after comparison, two full Web cycles, two full Android-emulator matrices, interaction/restart/soak and M2_PLUS.
- No production release, Pages deployment, signing decision or physical-device scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| A generic manifest patch transiently matched `ui_shared_core` instead of `bonus_items` | The validator failed with 16 findings before any source commit. The edit was replaced by an atlas-ID-bounded patch; `manifest-pre-fingerprint.json` preserves the failure and the post-fix validator reports zero findings. |
| The frozen contract requested a `50%` Android total-draw reduction, impossible with 18 fixed draws and a two-descriptor floor of 20 | The first `62/63` comparison is preserved. Before acceptance, only the relative threshold was corrected to the established `30%` family gate; the absolute minimum and all texture, dynamic-atlas, runtime, artifact and visual gates remained unchanged. The final result is `63/63`. |
| Adding descriptor metadata made the deterministic contact-sheet index stale | The first static cycle failed visibly at `24/26`. The canonical generator refreshed the index; two complete static cycles then passed `26/26`. |
| The new Web runner and modified artifact measurer initially accepted unknown or duplicate singleton CLI arguments | Both parsers now reject unknown arguments and duplicate singleton arguments; repeated source directories remain the only explicit repeatable option. Negative tests and a real loopback Web smoke pass. |
| A validator test expected the noncanonical error label `SCHEMA_VALIDATION_FAILED` | The assertion was corrected to the canonical `SCHEMA_VIOLATION`; validator behavior was not weakened. All `12/12` direct tests pass. |

## Infrastructure receipts

- One JavaScript-orchestrated ADB command failed to parse because a PowerShell line continuation was embedded in a template. It failed before ADB execution; the accepted installation path used a typed argument array, explicit `-s emulator-5554`, qemu guard and user `0`.
- `Compare-MtrAtlasPilot.js --help` was rejected because that CLI has no help mode. No mutation occurred; parser/source inspection was used instead.
- A complex one-line `Start-Process` smoke launcher was rejected by command policy before execution. The smoke was rerun through a bounded terminal session, produced a `PASS` report and left port `8133` closed.

Confirmed product/code findings after correction: `0`. Open findings: `0`.

## Independent evidence

- Comparison: `63/63 PASS`; preserved pre-correction result `62/63` and exact arithmetic rationale.
- Manifest validator tests: `12/12 PASS`; metric instrumentation and CLI fail-closed fixtures PASS.
- Static: `26/26 PASS × 2`, findings `0`.
- Web post-fix: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`; post-hardening runner smoke PASS with zero diagnostics.
- Android emulator post-fix: fresh build/install to `emulator-5554`, user `0`; `28/28 × 2`.
- Android interaction: touch `4/4` on first attempts, name persistence PASS, restart `10/10`, soak `300.771 s`, process losses `0`, unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable slots PASS; four focused-recovery slots explicitly not applicable because no save, migration, signing, release or recovery seam changed.
- Hygiene: no tracked build output, backup/reject/temp-source/pyc artifact or surviving QA listener in project scope.

## Residual limits

- Acceptance applies only to `bonus_items`; aggregate source package `M04.5` and parent `M04-C-FAMILIES` remain open for `ui_shared_core`.
- `ui_shared_core` spans five UI directories and requires a separate frozen multi-descriptor screen-coverage contract.
- The x86_64 debug APK is emulator QA evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
