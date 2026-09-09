# M04-C level_theme_farm code, contract and QA review

Date: `2026-09-09`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- Twelve existing farm hazard/platform PNGs represented by one recursive parent Cocos Auto Atlas descriptor; no source relocation, PNG rewrite, PNG metadata rewrite or resource-key change.
- DEBUG-only atlas measurement exposure in `GameRoot.ts`; production gameplay and production sound settings are unchanged.
- Atlas manifest, contact-sheet provenance, frozen comparison, visual parity, rollback and roadmap linkage.
- Two full Web cycles, two full Android-emulator matrices, interaction/name/restart/soak, two static cycles and M2_PLUS.
- Mandatory silent Android QA: AVD `-no-audio` plus verified STREAM_MUSIC stream `3` at volume `0`.

## Confirmed findings and dispositions

| Finding | Disposition |
| --- | --- |
| Finalizing the farm descriptor changed the canonical source/metadata digests while the manifest retained the pre-finalization hashes | Recomputed with the governance validator and updated only the two exact SHA-256 values; counts and bytes remained unchanged, and the validator then reported zero findings. |
| Governance tests still expected ten atlas descriptors and omitted `level_theme_farm` | Updated exact source/atlas counts and the complete ordered measured-atlas list. Direct tests pass `13/13`; no threshold was relaxed. |
| The contact-sheet index became stale, and the first regeneration accidentally persisted the unit-local output directory | Regenerated with the canonical generator entrypoint and default `temp/m04-b-contact-sheets` root; schema, source hash, `1,558`-asset coverage and deterministic check pass. |
| Screenshot-directory comparison case-folded paths on every OS | Restricted case-folding to Windows; Linux/macOS now use case-sensitive normalized paths. Containment, same-directory and screenshot-existence checks remain mandatory. |
| The rollback manifest omitted the modified governance-test file | Added its exact blob from anchor `d295cd3f0dce664d56e673ea0d9c5ba0ae00477d`, completing the tracked pre-change mapping. |

Confirmed findings corrected: `5/5`. Open findings: `0`.

## Advisory reconciliation

- The bounded local NPU reviewer reported no runtime or visual-comparator defects and correctly highlighted the cross-platform path-comparison risk.
- Its remaining warnings about stale counters and missing negative coverage were either already corrected or non-applicable: the suite includes negative fixtures, live Web/Android execution, exact descriptor/artifact checks and deterministic repeat evidence.
- Oversized advisory inputs failed closed twice and were split explicitly; no prompt was silently truncated and no local helper applied changes.
- Codex performed the final source, contract, evidence and rollback review.

## QA and silent-audio review

- Both Android matrices and the interaction/soak run recorded `MTR_Pixel_8_Pro_API_35`, `emulator-5554`, host `-no-audio` and STREAM_MUSIC `0/15`.
- Matrix coverage is `28/28 × 2`; interaction, custom-name cold persistence, restart `10/10` and soak `300.539 s` all pass with zero process loss or unexpected diagnostics.
- No physical serial was selected or addressed. The emulator and Web QA server were stopped after runtime evidence capture.

## Independent evidence

- Frozen comparison: `63/63 PASS`; Web draws `25 → 19`, Android draws `30 → 19` (`-36.6667%`).
- Visual parity: all 12 sources visible; zero material new-white pixels; Web and Android repeat screenshots are pixel-identical.
- Web: fresh build, `34/34 × 2`, interaction PASS and restart `10/10 × 2`.
- Android emulator: fresh x86_64 build/install, silent `28/28 × 2`, interaction/name/restart/soak PASS.
- Static: `27/27 PASS × 2`; M2_PLUS `8/8` applicable PASS with four recovery slots explicitly `NOT_APPLICABLE`.

## Hygiene and residual limits

- Build, temp, logs and `.local_ai_index` remain ignored; no cache, bytecode or duplicate backup is tracked.
- Acceptance applies only to `level_theme_farm`; aggregate `M04.5` and parent `M04-C-FAMILIES` remain open.
- The x86_64 debug APK is emulator evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
