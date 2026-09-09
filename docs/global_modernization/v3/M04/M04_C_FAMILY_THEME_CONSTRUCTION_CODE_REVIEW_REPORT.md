# M04-C-FAMILY-THEME-CONSTRUCTION code review

Date: `2026-09-09`  
Rollback anchor: `8e0a758d53c7e3c266ab15e926fb429431d87e6d`  
Scope: one recursive construction-theme static atlas, DEBUG-only measurement routing, manifest/test/roadmap integration and Web/Android-emulator evidence.

## Decision

`PASS` for this isolated child. Confirmed findings: `5`; corrected: `5`; open: `0`. The parent `M04-C-FAMILIES`, source package `M04.5` and product release remain open.

## Confirmed findings and corrections

| Finding | Correction and evidence |
|---|---|
| The first Web baseline placed bottom-row labels at the viewport edge. | Rejected that baseline, changed only the DEBUG grid `yStep` from `150` to `140`, and recaptured both platform baselines before creating the descriptor. All 24 sources and labels are visible. |
| Creating the descriptor made exact source/meta fingerprints, `.pac` counts and construction ownership totals stale. | Updated the manifest to the validator-computed canonical values: source `1,647`, metadata `1,894`, descriptors `12`, construction ownership `25` files / `2,394,702` bytes. Validator reports zero findings. |
| The general `level_theme_families` selector still owned all 24 construction PNGs after the measured child was registered. | Removed only the construction selector from the general family and corrected its observed remainder to `227` PNG / `19,200,041` bytes. Repeated validation reports zero gaps and zero overlaps. |
| The canonical contact-sheet index became stale after the new descriptor metadata. | Regenerated with the canonical default output root. Deterministic check passes for `1,558` assets, `29` sheets, zero unclassified and zero duplicate classifications; index SHA-256 `AB039C5B32EDFEA3C6C08729D55504370BFD69E382D36FEE58FFCC228A2B83F6`. |
| The prepared rollback record used a non-canonical temporary shape and omitted the contact-sheet predecessor blob. | Replaced it with `mtr.m04_c_family_rollback_manifest`, added the exact `ca933989259ac50cedda83e5b6d4c395a9c54360` contact-sheet blob, retained every other pre-change blob and listed all new completion artifacts. |

## Accepted implementation review

- `GameRoot.ts` exposes construction assets only through the existing DEBUG atlas measurement route; production scene selection, gameplay, save state and sound settings are unchanged.
- One parent descriptor covers the existing `hazards/` and `platforms/` directories recursively. No PNG, PNG metadata, resource key or path changed; `allowRotation=false` preserves orientation-sensitive geometry.
- Frozen comparison is `63/63 PASS`: Web draw textures `10 → 1`, Android-emulator draw textures `24 → 1`, Web draws `41 → 31`, Android draws `54 → 31` (`-42.5926%`). Candidate-repeat screenshots are pixel-identical and material new-white pixels are zero.
- Every Android QA entrypoint independently verifies emulator identity, host `-no-audio` and STREAM_MUSIC `3` volume `0`; the fresh APK was installed only to emulator user `0`. Physical device use is `NO`.
- Web matrix `34/34 × 2`, Android matrix `28/28 × 2`, interaction/name persistence/restart/soak, static `27/27 × 2` and M2_PLUS `8/8` applicable gates pass.
- Execution arithmetic is consistent: adding one inventory-derived completed child changes `19/71` to `20/72` (`27.7778%`), while mandatory remaining stays `52`; source ledger remains `28/95` because aggregate `M04.5` is not closed.

## Advisory and fail-closed events

- System Python lacked `jsonschema`; no global package was installed. Validation used the existing isolated `uv`/quality-gate environment.
- M2_PLUS template preparation rejected a case-insensitive duplicate PowerShell key before writing; a list-of-pairs mechanical rewrite was then verified for zero stale farm references.
- The first local NPU batch rejected an over-budget prompt without truncation. A bounded retry received no retrieved chunk and emitted one search-regression suggestion; Codex classified it as a false positive because deterministic retrieval and project validators were already healthy.
- The accepted Web candidate was repeated after stopping QEMU to match baseline host load. No best-of selection or threshold weakening was used.
- Sixty-six Android near-white threshold crossings remain recorded as subthreshold diagnostics; all are below the frozen material channel delta and are not hidden.

## Release boundary

This review accepts only `M04-C-FAMILY-THEME-CONSTRUCTION`. It does not authorize physical-device QA, signing, release APK/AAB publication, Pages deployment, merge/rebase of the Pages line or closure of blockers `M02.1`, `M02.7`, `M12.7`.
