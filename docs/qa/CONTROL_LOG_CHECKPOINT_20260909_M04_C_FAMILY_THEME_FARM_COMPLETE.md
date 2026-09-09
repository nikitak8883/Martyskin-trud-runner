# M04-C-FAMILY-THEME-FARM completion checkpoint

Date: `2026-09-09`  
Branch before unit commit: `codex/mtr-source-freeze-v3`  
Rollback anchor: `d295cd3f0dce664d56e673ea0d9c5ba0ae00477d`  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** `completed` for the isolated family child; aggregate `M04.5`, parent `M04-C-FAMILIES` and product release remain open.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-THEME-FARM` complete inside `M04-C-FAMILIES`.
- **Progress:** execution ledger `19/71` complete (`26.7606%`), `52` mandatory units remain plus `7` conditional. Source ledger remains `28/95`; `M04.5` stays pending.
- **Evidence:** comparison `63/63`; static `27/27 × 2` plus final documentation gate; Web `34/34 × 2`; Android-emulator `28/28 × 2`; interaction/restart/soak PASS; M2_PLUS `8/8` applicable; open findings `0`.
- **Remaining:** `52` mandatory execution units and `7` conditional; `57` mandatory source packages plus `10` conditional; release blockers `M02.1`, `M02.7`, `M12.7`.
- **Next:** return to `M04-C-FAMILIES`, inventory and freeze exactly one remaining measured family, and do not batch unrelated atlas families.

## Accepted implementation

- Twelve farm hazard/platform PNGs for levels `5` and `10` retain their exact source bytes, metadata, paths and resource keys.
- One recursive parent Cocos Auto Atlas descriptor at `assets/resources/objectives/themed/last_iteration/farm/level_theme_farm.pac` owns both child directories without source relocation.
- `GameRoot.ts` exposes the family only through the DEBUG atlas measurement route; production gameplay and production sound settings are unchanged.
- The Web harness now requires its screenshot to exist inside the same requested output directory. Directory comparison is case-insensitive only on Windows and case-sensitive on Linux/macOS.
- Near-white threshold crossings remain visible in diagnostics, while only crossings above the already frozen channel-delta threshold count as material white-matte defects.
- Android QA is fail-closed: emulator-only, AVD `-no-audio`, STREAM_MUSIC `3` set and verified at volume `0` before runtime execution.

## Acceptance evidence

- Comparison: `63/63 PASS`; Web draws `25 → 19`; Android draws `30 → 19` (`-11`, `-36.6667%`).
- Web: source textures `12 → 1`, dynamic copies `8 → 0`, load `347 → 238 ms`, texture memory `29.41 → 13.69 MiB`.
- Android emulator: source/draw textures `12 → 1`, load `667 → 442 ms`, texture memory `15.27 → 15.55 MiB` within the frozen budget.
- Visual parity: all 12 sources visible; material new-white pixels, missing frames and pivot/trim regressions `0`; levels `5` and `10` reviewed on both platforms; exact-repeat changed pixels `0`.
- Web QA: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`; port `8133` closed.
- Android emulator QA: fresh x86_64 build/install to `emulator-5554`, user `0`; silent `28/28 × 2`; touch and custom-name persistence PASS; restart `10/10`; soak `300.539 s`; process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four recovery slots `NOT_APPLICABLE`, findings `0`.
- Final Codex review and hygiene: PASS; confirmed findings `5/5` corrected; open findings `0`.

## Fail-closed events corrected

1. The first static attempt rejected stale source/metadata fingerprints.
2. The next attempt rejected stale exact descriptor counts and the stale contact-sheet hash.
3. A non-canonical unit-local contact-sheet output root was rejected by schema and regenerated through the canonical entrypoint.
4. M2_PLUS preparation rejected an incorrect template-root depth and a replacement-order collision before generating trusted evidence.
5. M2_PLUS composition rejected dirty-source evidence until the explicit profile-level `--allow-dirty-source` authorization was supplied.
6. Two oversized local-review prompts were rejected without truncation and then split into bounded slices.

## Hash anchors

- Contract: `589E8D668E47C3976451A96708EF82090D17A53DB1C84E63C5091105960B959E`.
- Durable acceptance: `3091C71E2CA229D2516CA98EE8F46C763D473FC184BB5E165AD9C9BA23BFC57A`.
- Comparison: `E9CA499FAE4F5C27F88568B3A9D7EFC65413A639483263C53F524581FDA4532F`.
- Visual parity: `06BAC23D1E315A961AD98A8DBDE8674543B2AE169ADEF28F4CCAAB850926F1B5`.
- Web cycles: `665F6A9ED5F46EC7537FE77FBD647CB73E5E2D49682ED5AF95E2FEE32349F18A`, `166DE7A54FA5B872C812F7003209564028C7C1D5A48E3F1239A1FF54B7DF9967`.
- Android matrices: `0EF398CFB36539CE78BDD49E4A37B329E60D68D3C60EC5E8A33E0A5D43B7A2C4`, `D28AEB862CBA2D6B76E883BFC6F095AB889AC1871DD1A91EE4A65DE74969D4DA`.
- Android interaction: `7D4981E52B20F25419DEEFBCDF557E4741CB2C09D8D8C4BB26F8D6F04C94A381`.
- Emulator APK: `6BE5A0FCA60844B914D0C1367B81FD1C6FCA862A83C5C0DDB38183317464D207` (`145454639` bytes; debug emulator evidence only).
- Final M2_PLUS profile: `D3C80E3E0D05FF5A005189E9EBEDE13BA694A287D5D9D9B5112BCBC23C79908D`.

## Hygiene and rollback

- QA port `8133` is closed, the AVD is stopped and no accepted test addressed the physical phone.
- Build, temp, logs and local indexes remain ignored; no project Python bytecode cache or duplicate backup is tracked.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- Rollback source: `docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_FARM_ROLLBACK_MANIFEST.json`.

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run comparison, manifest and static gates if the farm descriptor, source set, runtime measurement route, screenshot routing or mute guard drifts.
3. Re-enter `M04-C-FAMILIES` with one separately frozen child and preserve silent emulator-only QA by default.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
