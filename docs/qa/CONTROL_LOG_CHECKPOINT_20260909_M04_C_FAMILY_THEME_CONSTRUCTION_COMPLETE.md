# M04-C-FAMILY-THEME-CONSTRUCTION completion checkpoint

Date: `2026-09-09`  
Branch before unit commit: `codex/mtr-source-freeze-v3`  
Rollback anchor: `8e0a758d53c7e3c266ab15e926fb429431d87e6d`  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** `completed` for the isolated family child; aggregate `M04.5`, parent `M04-C-FAMILIES` and product release remain open.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-THEME-CONSTRUCTION` complete inside `M04-C-FAMILIES`.
- **Progress:** execution ledger `20/72` complete (`27.7778%`), `52` mandatory units remain plus `7` conditional. Source ledger remains `28/95`; `M04.5` stays pending.
- **Evidence:** comparison `63/63`; static `27/27 × 2` plus final documentation gate; Web `34/34 × 2`; Android-emulator `28/28 × 2`; interaction/restart/soak PASS; M2_PLUS `8/8` applicable; open findings `0`.
- **Remaining:** `52` mandatory execution units and `7` conditional; `57` mandatory source packages plus `10` conditional; release blockers `M02.1`, `M02.7`, `M12.7`.
- **Next:** return to `M04-C-FAMILIES`, inventory and freeze exactly one remaining measured family, and do not batch unrelated atlas families.

## Accepted implementation

- Twenty-four construction hazard/platform PNGs for levels `1`, `2` and `10` retain their exact source bytes, metadata, paths and resource keys.
- One recursive parent Cocos Auto Atlas descriptor at `assets/resources/objectives/themed/last_iteration/construction/level_theme_construction.pac` owns both child directories without source relocation.
- `GameRoot.ts` exposes the family only through the DEBUG atlas measurement route; production gameplay and production sound settings are unchanged.
- Android QA is fail-closed and silent: emulator-only, AVD `-no-audio`, STREAM_MUSIC `3` set and verified at volume `0` before runtime execution.

## Acceptance evidence

- Comparison: `63/63 PASS`; Web draws `41 → 31`; Android draws `54 → 31` (`-23`, `-42.5926%`).
- Web: source/draw textures `24/10 → 1/1`, dynamic copies `15 → 0`, load `644 → 444 ms`, texture memory `33.7 → 18.12 MiB`.
- Android emulator: source/draw textures `24/24 → 1/1`, load `1572 → 736 ms`, texture memory `21.09 → 21.51 MiB` within the frozen budget.
- Visual parity: all 24 sources visible; material new-white pixels, missing frames and pivot/trim regressions `0`; exact-repeat changed pixels `0` on both platforms.
- Web QA: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`; port `8133` closed.
- Android emulator QA: fresh x86_64 build/install to `emulator-5554`, user `0`; silent `28/28 × 2`; touch and custom-name persistence PASS; restart `10/10`; soak `300.132 s`; process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four recovery slots `NOT_APPLICABLE`, findings `0`.
- Final Codex review: confirmed findings `5/5` corrected, open findings `0`; local advisory false positives `1`.

## Fail-closed events corrected

1. The first visual baseline rejected a clipped bottom-row label layout before candidate creation.
2. The first manifest validation rejected stale exact fingerprints, descriptor counts and ownership totals.
3. The next manifest validation rejected the still-overlapping general construction selector.
4. Contact-sheet check rejected the stale descriptor-derived hash and was regenerated canonically.
5. System Python rejected the validator due missing `jsonschema`; the isolated project quality environment was used without global installation.
6. M2_PLUS preparation rejected case-insensitive duplicate replacement keys before any rewrite.
7. Local NPU review rejected an over-budget prompt without truncation; its bounded empty-retrieval retry produced one false positive, rejected by Codex.

## Hash anchors

- Contract: `87B80EA569993BFD271CFB80883770F4CF4EA51CC7BEE41FB4D93D3F9373207B`.
- Durable acceptance: `05EEC95DA4B680B00F51EEEFB2C81FB4311CC9825BAD0E918EF5A5AEDF424CBE`.
- Comparison: `C6813A2AFF456755BE84CD6CC9935F6C46ECADC2F2EEE59F164A35319641FC12`.
- Visual parity: `BA190C0F943EEF4EC53D36EB017BFB2DF6020CD64ABD6F993D9EA6EAF1A6AFC1`.
- Web cycles: `0DA3D7DAB4FF634F33F6E5E5808310E34DFABA284025C91A1A82DF6AECE6B36E`, `4A2796ACA051413F73912C39D80B8D81592D80419D88E9B67864CB1795DC2DBF`.
- Android matrices: `0A37516D467AA2AB93EFCB4DE3DA7A2D3597CA191A28290ECB74F1CC3612CE1C`, `8380B27F133073D7696A598E663BD22AB7D29F42743100C8CCBAA7921773E952`.
- Android interaction: `A5B18B898BF54579507EF62631A56313AB8F55E5B2BAB570ADCF0F8E602D36B2`.
- Fresh emulator APK: `F8FAD54A57EB2930157A16864BD4AF4BBFA3B75171CA0501A58A2DCF841C83F9` (`146,280,317` bytes; debug emulator evidence only).
- Final M2_PLUS profile: `95347AB8C7EB9767CA86E90C37010917189580B7A3146D3232C88A82782D6D7A`.

## Hygiene and rollback

- QA port `8133` is closed, the AVD is stopped and no accepted test addressed the physical phone.
- Build, temp, logs and local indexes remain ignored; no project Python bytecode cache or duplicate backup is tracked.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- Rollback source: `docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_CONSTRUCTION_ROLLBACK_MANIFEST.json`.

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run comparison, manifest and static gates if the construction descriptor, source set, runtime measurement route or mute guard drifts.
3. Re-enter `M04-C-FAMILIES` with one separately frozen child and preserve silent emulator-only QA by default.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
