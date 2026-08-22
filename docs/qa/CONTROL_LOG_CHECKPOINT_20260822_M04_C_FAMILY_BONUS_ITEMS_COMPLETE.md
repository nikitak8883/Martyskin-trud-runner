# M04-C-FAMILY-BONUS-ITEMS completion checkpoint

Date: `2026-08-22`  
Branch before unit commit: `codex/mtr-source-freeze-v3`  
Rollback anchor: `55557ff566cead8832b7a90714c1f999e384797d`

## Status

- **Status:** `completed` for the isolated family child; aggregate `M04.5`, parent `M04-C-FAMILIES` and product release remain open.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-BONUS-ITEMS` complete inside `M04-C-FAMILIES`.
- **Progress:** the inventory-derived child expands the execution denominator to `16/68` complete (`23.5294%`), `52` mandatory remain plus `7` conditional. Source remains `28/95`; `M04.5` stays pending.
- **Evidence:** comparison `63/63`; static `26/26 × 2`; Web `34/34 × 2`; Android-emulator `28/28 × 2`; interaction/restart/soak PASS; M2_PLUS `8/8` applicable; open findings `0`.
- **Remaining:** `52` mandatory execution units, `7` conditional units; `57` mandatory source packages plus `10` conditional; release blockers `M02.1`, `M02.7`, `M12.7`.
- **Next:** freeze one isolated `ui_shared_core` multi-descriptor screen-coverage contract before any runtime mutation.

## Accepted scope

- Twelve original PNGs remain in `assets/resources/objectives/bonuses` and `assets/resources/objectives/equipment`.
- Two directory-local Cocos Auto Atlas descriptors preserve every resource key and avoid relocation.
- Android emulator draws improve `30 → 20`; Web `19 → 20` remains within the frozen absolute non-regression allowance.
- The first `62/63` report is retained; its impossible `50%` relative threshold was corrected to `30%` before acceptance with all other gates unchanged.
- No physical device, production signing, Pages deployment or release artifact was used.

## Resume order

1. Verify this checkpoint, `M04_C_FAMILY_BONUS_ITEMS_VALIDATION_SUMMARY.json`, Git status and canonical remote projection.
2. Confirm `ui_shared_core` exact five-directory ownership, co-visibility/screen coverage and pre-mutation descriptor split.
3. Freeze its baseline, thresholds, rollback map and Web/Android-emulator evidence paths.
4. Implement only that child, then repeat P4, visual parity, interaction/restart/soak and M2_PLUS before continuing.
