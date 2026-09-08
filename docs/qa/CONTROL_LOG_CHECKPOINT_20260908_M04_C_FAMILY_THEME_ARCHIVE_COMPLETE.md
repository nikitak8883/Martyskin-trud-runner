# M04-C-FAMILY-THEME-ARCHIVE completion checkpoint

Date: `2026-09-08`  
Branch before unit commit: `codex/mtr-source-freeze-v3`  
Rollback anchor: `66a2aa52c5bb9baa5c1ab7261dc37a3c7abdb8b6`  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** `completed` for the isolated family child; aggregate `M04.5`, parent `M04-C-FAMILIES` and product release remain open.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-THEME-ARCHIVE` complete inside `M04-C-FAMILIES`.
- **Progress:** execution ledger `18/70` complete (`25.7143%`), `52` mandatory units remain plus `7` conditional. Source ledger remains `28/95`; `M04.5` stays pending.
- **Evidence:** comparison `63/63`; static `27/27 × 2` plus final documentation gate `27/27`; Web `34/34 × 2`; Android-emulator `28/28 × 2`; interaction/restart/soak PASS; M2_PLUS `8/8` applicable; open findings `0`.
- **Remaining:** `52` mandatory execution units and `7` conditional; `57` mandatory source packages plus `10` conditional; release blockers `M02.1`, `M02.7`, `M12.7`.
- **Next:** return to `M04-C-FAMILIES`, inventory and freeze exactly one remaining measured family, and do not batch unrelated atlas families.

## Accepted implementation

- Seventeen archive hazard/platform PNGs for levels `8`, `9`, `13` and `15` retain their exact source bytes, metadata, paths and resource keys.
- One recursive parent Cocos Auto Atlas descriptor at `assets/resources/objectives/themed/last_iteration/archive/level_theme_archive.pac` owns both child directories without source relocation.
- The initial two-descriptor candidate was rejected at `62/63` because Web draws regressed `24 → 26`; no threshold was weakened.
- `GameRoot.ts` exposes the family only through the DEBUG atlas measurement route; production gameplay is unchanged.
- The global Android QA rule is fail-closed: emulator-only, AVD `-no-audio`, STREAM_MUSIC `3` set and verified at volume `0` before runtime execution.

## Acceptance evidence

- Comparison: `63/63 PASS`; corrected Web draws `24 → 24`; Android draws `40 → 24` (`-16`, `-40%`).
- Web: source textures `17 → 1`, dynamic copies `17 → 0`, load `546 → 323 ms`, texture memory `29.61 → 13.84 MiB`.
- Android emulator: source/draw textures `17 → 1`, load `482 → 261 ms`, texture memory `16.10 → 16.34 MiB` within the frozen budget.
- Visual parity: all 17 sources visible; missing frames, white matte fragments and pivot/trim regressions `0`; levels `8`, `9`, `13`, `15` manually inspected on both platforms; exact-repeat changed pixels `0`.
- Web QA: fresh build; `34/34 × 2`, interaction PASS, restart `10/10 × 2`; port `8133` closed.
- Android emulator QA: fresh x86_64 build/install to `emulator-5554`, user `0`; silent `28/28 × 2`; touch and custom-name persistence PASS; restart `10/10`; soak `300.345 s`; process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four recovery slots `NOT_APPLICABLE`, findings `0`; profile SHA-256 `F7F69717E26FE479E1A47D704B60BA63EE275D14C6135565321D76A233CD2F45`.
- Final Codex review and hygiene: PASS; confirmed findings `3/3` corrected; open findings `0`.

## Sound policy and failure prevention

1. The sole AVD launcher supplies `-no-audio`.
2. Every discovered Android runtime QA harness imports one shared guard and refuses non-emulator serials.
3. The guard identifies the active AVD host process, verifies `-no-audio`, sets stream `3` to zero and reads it back; any missing proof aborts QA.
4. The static policy validator covers all seven launch harnesses and is mandatory in the canonical static gate.
5. Production sound settings were not changed.

## Hash anchors

- Contract: `5C49780CAA01795DE235B2D318E76112DD8996A0E2B5A551FD4DCD2C69039A95`.
- Durable acceptance: `8DEF88C1A50121C9493F26AB7C23B07928727594CE0BD5E409C2B2B613B26E01`.
- Comparison: `66DF0D11238F7F4DDEB51FC00D400F687EC3216B7708C10E1C6BD2B46BDB47C1`.
- Visual parity: `4C11E31839CCD4DE5EB7DC4A6BD5D335EB6AE2FBE7F8FAD3433012D91C91FEC0`.
- Web cycles: `7539DEF0347300A33E2A8133AD01E2A4DE0092643508F6081517B28B74D427AE`, `C729B32EF67629DCFD99D59375E68A139DFF0A2A09D2053FBF3B38D8AF2B1FC7`.
- Android matrices: `055E9F3079E26DAC4C8AA1C32E4BFCF050310C098D5C99402F9A47FC0B98368A`, `AD5D39252B46F05A0682D5A239991519A3AA9F5181B42C5AFEDEFDED822B489A`.
- Android interaction: `B3154292BD5D20F9DC53542E13ED42ACFAD35847E5C24B489CB7FC33EEF6AF71`.
- Emulator APK: `9A416427DFCC6DF84B1BEE62734C062D5334F83FBDACE14ABD8B6F394E421C2E` (`144984911` bytes; debug emulator evidence only).

## Hygiene and rollback

- QA port `8133` is closed and the AVD is stopped; no accepted test addressed the physical phone.
- Build, temp, logs and local indexes remain ignored; no project Python bytecode cache or duplicate backup is tracked.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- Rollback source: `docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_ARCHIVE_ROLLBACK_MANIFEST.json`.

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run comparison, manifest and static gates if the archive descriptor, source set, runtime measurement route or mute guard drifts.
3. Re-enter `M04-C-FAMILIES` with one separately frozen child and preserve silent emulator-only QA by default.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
