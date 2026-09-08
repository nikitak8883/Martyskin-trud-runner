# M04-C level_theme_archive code, contract and QA review

Date: `2026-09-08`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- Seventeen existing archive hazard/platform PNGs represented by one empirically verified recursive parent Cocos Auto Atlas descriptor; no source relocation, PNG rewrite, metadata rewrite or resource-key change.
- DEBUG-only atlas measurement exposure in `GameRoot.ts`; production gameplay and production sound settings are unchanged.
- Atlas manifest, contact-sheet provenance, frozen comparison, visual parity, rollback and roadmap linkage.
- Two full Web cycles, two full Android-emulator matrices, interaction/name/restart/soak, two static cycles and M2_PLUS.
- Global project rule that Android runtime QA is emulator-only and host-silent: AVD `-no-audio` plus verified STREAM_MUSIC volume zero.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| The initial two-descriptor candidate increased Web median draws from `24` to `26`, exceeding the frozen maximum `25` | The failed `62/63` candidate is preserved under ignored evidence. No threshold was weakened. It was replaced by one recursive parent descriptor, then rebuilt and remeasured on both platforms; the corrected candidate is `63/63` with Web draws `24 → 24` and Android draws `40 → 24`. |
| Manifest/count/contact-sheet fixtures still described the previous nine-atlas topology after the archive descriptor was added | Canonical inventory, metadata hash, ownership pointers and direct test expectations were regenerated from the accepted manifest. Manifest validation has zero gaps, overlaps or metadata findings; direct validator tests pass `13/13`. |
| The first rollback manifest review omitted the pre-change blob for `tools/codex/tests/test_validate_m04_a_asset_contract.py` | The exact HEAD blob `4c38d8ba5ea8212054852f1c807fd05f30c67c70` was added. The atlas contract test now checks this rollback anchor and every new high-value removal target, preventing recurrence. |

Confirmed findings corrected: `3/3`. Open findings: `0`.

## Advisory reconciliation

- The local coding adviser flagged an allegedly empty `spriteFrames` array. This was rejected as a non-applicable interpretation: a Cocos Creator Auto Atlas source descriptor intentionally contains only `{"__type__":"cc.SpriteAtlas"}`, while imported packing membership is derived from the descriptor directory and `.meta` importer settings. The accepted existing descriptors use the same shape, and fresh Web/Android build artifacts prove all 17 sources are packed with zero retained source-UUID artifacts.
- Two over-budget advisory attempts failed closed before loading a specialist and did not truncate input or alter files. The eventual bounded call completed, and the normal unpinned `quick_helper` plus `embedding` NPU pair was verified restored.

## QA and silent-audio review

- All seven Android runtime QA launch scripts import the shared `MtrAndroidQaAudioGuard.ps1` and abort if the target is not `emulator-*`, `ro.kernel.qemu != 1`, the matching host AVD lacks `-no-audio`, or media stream `3` cannot be set and read back as `0`.
- The sole repository AVD launcher includes `-no-audio`; the static policy validator is a mandatory quality-gate step.
- Both accepted Android matrices and the interaction/soak cycle record `MTR_Pixel_8_Pro_API_35`, `emulator-5554`, `-no-audio`, and STREAM_MUSIC `0/15`.
- No physical serial was selected or addressed.

## Independent evidence

- Comparison: `63/63 PASS`; visual repeat is pixel-identical on Web and Android and introduces zero near-white pixels.
- Static: `27/27 PASS × 2`; final documentation gate `27/27 PASS`.
- Web: fresh build, `34/34 × 2`, interaction PASS and restart `10/10 × 2`.
- Android emulator: fresh x86_64 build/install, silent `28/28 × 2`.
- Android interaction: touch and custom-name persistence PASS, restart `10/10`, soak `300.345 s`, process losses `0`, unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS; four focused-recovery slots explicitly `NOT_APPLICABLE`; findings `0`.

## Hygiene and residual limits

- Port `8133` is closed and `emulator-5554` is stopped after evidence capture.
- Build, temp, logs and local indexes remain ignored; no generated cache or duplicate backup is tracked.
- Acceptance applies only to `level_theme_archive`; aggregate `M04.5` and parent `M04-C-FAMILIES` remain open.
- The x86_64 debug APK is emulator evidence only, not a production-valid arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
