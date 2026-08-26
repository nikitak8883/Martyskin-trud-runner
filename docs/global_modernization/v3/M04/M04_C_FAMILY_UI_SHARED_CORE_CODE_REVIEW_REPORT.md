# M04-C ui_shared_core code, contract and QA review

Date: `2026-08-26`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- Twenty-eight shared UI PNGs represented by four Cocos Auto Atlas descriptors plus one explicit standalone banner; no PNG relocation or rewrite.
- Runtime exclusion from redundant Cocos dynamic-atlas repacking after build-time static-atlas import.
- Mixed-topology manifest/schema/validator identity, artifact measurement, visual parity and rollback linkage.
- Two full Web cycles, two full Android-emulator matrices, interaction/name/restart/soak, static gates and M2_PLUS.
- QA-only silent-emulator enforcement; no production audio setting, production release, Pages deployment, signing decision or physical-device scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| The first five-descriptor design kept a one-source banner descriptor that did not pack and left five controls eligible for runtime dynamic repacking | The singleton descriptor was removed, the banner became an explicit standalone source, and `ui/shared` SpriteFrames are marked non-packable only after static-atlas import. Final Web/Android topology is five draw textures with zero dynamic copies. |
| The first four-descriptor packing exceeded the Android texture-memory absolute gate | Rotation was enabled only for large rectangular cards/panels. Candidate area fell from `4,058,178` to `3,733,352 px`; Android texture memory fell from `30.22` to `28.99 MiB`. |
| The inherited visual changed-pixel fraction was calibrated on smaller families | The family-specific `0.006` edge envelope was accepted only together with a zero-new-near-white-pixel gate, unchanged MAE threshold, manual 28-sprite review and exact Web/Android repeat stability. Alpha-fix and trim-none alternatives were measured and rejected. |
| The frozen `40%` Android total-draw ratio was mathematically impossible with 34 fixed draws and a five-texture floor | The first failed report was preserved. Before acceptance, the ratio was corrected to the established `30%` gate; the unchanged absolute gate still required 20 draws saved and the candidate saved 22. |
| The pre-existing atlas manifest could not express four descriptors plus one intentional standalone source or per-descriptor rotation | Schema, validator and 13 direct tests were extended fail-closed. Manifest validation covers 1,644 sources, nine atlas files, five measured groups and reports zero gaps, overlaps or metadata findings. |
| A best-effort stream-volume command was not durable while the first diagnostic matrix was still launching cases | That matrix is preserved only as pre-policy evidence. The AVD was restarted with `-no-audio`, media stream 3 was verified at zero, mute checks were embedded into both QA harnesses, and both accepted `28/28` matrices plus interaction/soak were rerun silently. |

## Infrastructure receipts

- The first post-restart ADB probe found no emulator and a legacy polling expression attempted `.Trim()` on null. No device mutation occurred; recovery used null-safe polling, explicit `emulator-5554`, QEMU/ABI/user checks and fresh installation.
- A detached Web server `Start-Process` form was rejected before execution. The accepted Web QA used a bounded managed process; both reports passed and port `8133` was closed.
- No physical serial was selected or addressed. Android evidence is x86_64 debug/emulator-only.

Confirmed product/code findings after correction: `0`. Open findings: `0`.

## Independent evidence

- Comparison: `63/63 PASS`; preserved first failed result `58/63` and exact correction receipts.
- Manifest validator: zero findings; direct tests `13/13 PASS`; metric and visual comparator contracts PASS.
- Static: `26/26 PASS × 2`; final documentation gate `26/26 PASS`, findings `0`.
- Web: fresh build; `34/34 × 2`, interaction PASS and restart `10/10 × 2`.
- Android emulator: fresh build/install to `emulator-5554`, user `0`; silent `28/28 × 2`.
- Android interaction: touch PASS, name persistence PASS, restart `10/10`, soak `300.439 s`, process losses `0`, unexpected diagnostics `0`.
- M2_PLUS: final source-bound `8/8` applicable PASS with four focused-recovery slots explicitly not applicable; findings `0`.

## Residual limits

- Acceptance applies only to `ui_shared_core`; aggregate source package `M04.5` and parent `M04-C-FAMILIES` remain open for other inventory-selected children.
- The x86_64 debug APK is emulator QA evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
