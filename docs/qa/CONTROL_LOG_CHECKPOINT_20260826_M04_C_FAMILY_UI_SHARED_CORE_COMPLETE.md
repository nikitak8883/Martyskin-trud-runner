# M04-C-FAMILY-UI-SHARED-CORE completion checkpoint

Date: `2026-08-26`  
Branch before unit commit: `codex/mtr-source-freeze-v3`  
Rollback anchor: `b2ec63f0caf593875e9004cb20cc408235c9cd9e`  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** `completed` for the isolated family child; aggregate `M04.5`, parent `M04-C-FAMILIES` and product release remain open.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-UI-SHARED-CORE` complete inside `M04-C-FAMILIES`.
- **Progress:** execution ledger `17/69` complete (`24.6377%`), `52` mandatory units remain plus `7` conditional. Source ledger remains `28/95`; `M04.5` stays pending.
- **Evidence:** comparison `63/63`; static `26/26 × 2` plus final documentation gate `26/26`; Web `34/34 × 2`; Android-emulator `28/28 × 2`; interaction/restart/soak PASS; M2_PLUS `8/8` applicable; open findings `0`.
- **Remaining:** `52` mandatory execution units and `7` conditional; `57` mandatory source packages plus `10` conditional; release blockers `M02.1`, `M02.7`, `M12.7`.
- **Next:** return to `M04-C-FAMILIES`, freeze exactly one remaining inventory-derived child contract, and do not batch unrelated atlas families.

## Accepted implementation

- Twenty-eight shared UI PNGs retain their paths, bytes and runtime resource keys.
- Four directory-local Cocos Auto Atlas descriptors plus one explicit standalone title banner reduce the runtime family topology to five textures on both platforms.
- Runtime dynamic repacking is disabled only for already statically packed `ui/shared` SpriteFrames.
- Manifest, schema, validator, comparator and thirteen direct regression tests now support mixed descriptors, per-descriptor rotation and intentional standalone sources fail-closed.
- Silent emulator QA is mandatory: AVD launch uses `-no-audio`; media stream `3` must be verified at volume `0` before every accepted matrix or interaction case.

## Acceptance evidence

- Comparison: `63/63 PASS`; preserved first pre-correction result `58/63`.
- Web: source textures `28→5`, draws `54→40`, load `991→564 ms`, texture memory `40.11→25.09 MiB`, FPS `45→49`.
- Android emulator: source/draw textures `28→5`, draws `62→40` (`-35.4839%`), load `1915→1255 ms`, texture memory `28.01→28.99 MiB`, FPS `8→8`.
- Visual parity: all 28 sources present; missing frames, white matte fragments and pivot/trim/rotation regressions `0`; exact repeat changed pixels `0` on both platforms.
- Web QA: fresh build, `34/34 × 2`, interaction PASS, restart `10/10 × 2`; port `8133` closed.
- Android emulator QA: fresh x86_64 build/install to `emulator-5554`, user `0`; silent `28/28 × 2`; touch and custom-name persistence PASS; restart `10/10`; soak `300.439 s`; process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four recovery slots `NOT_APPLICABLE`, findings `0`; profile SHA-256 `ECE555C6F5270B6049FA43E8930331E83BFDCA49F6CBAABB6A8EF1A2F9A32C36`.
- Final Codex review and hygiene: PASS; confirmed findings `6/6` corrected; open findings `0`.

## Sound policy and failure prevention

1. The emulator launcher now always supplies `-no-audio`; accepted QA cannot depend on host audio state.
2. Both Android matrix and interaction harnesses set media stream `3` to zero and verify it before each case. Failure to prove mute state aborts the run.
3. The earlier pre-policy matrix is retained only as diagnostic evidence and is excluded from acceptance.
4. No production audio preference or gameplay sound behavior was changed.

## Hash anchors

- Contract: `E837F99C519C1FAD7A00633708DEEA9AFF8BF7D7F707A7583245623B203D214D`.
- Durable acceptance: `654290DC38AFAFFF314D30A604FF888E9B060F928E947058A04B7BE0D78C52A9`.
- Comparison: `34A8A5710D77C1D7F11607E212873C74A19551A4496D2C0A1AEDBCE802F655BC`.
- Visual parity: `0BA25685E31DC54DC89510EBA4FC6FAE06328D5CAB339EBCD1D5E4B4D979D627`.
- Web cycles: `07EA370A511AD68CA21A40A415E52EB562614B20744A9FBDED5CA04DFE654A78`, `6D74AC527B4DC83A289C9E4CE9F16B8BB9D0873DC5BDD4DA6BA3F421645CF5E5`.
- Android matrices: `3ED84697FE909BCD3DEB6D28D310DD56976ABD504F17B063ED27D52C89CF7283`, `E2FF17D90F5A86CED83AF182386B40571861472172D9C04C1DBDF5290943ABB4`.
- Android interaction: `58C725492168A60B03AE9F59EC63A445ABA8DD56C83BA77F503224A751214942`.
- Emulator APK: `4C2FA55DE768F31026FA30628B6C84F066BBAC9D9519B3BEE79D2512CFD788DA` (`144556447` bytes; debug emulator evidence only).

## Hygiene and rollback

- QA port `8133` is closed and the AVD is stopped; no accepted test addressed the physical phone.
- Project-local Python bytecode caches are generated-only and removed at closeout; build, temp and log evidence remain ignored.
- Unrelated root AGENTS, agent-monitor, Tasks, sticker and project-library changes remain untouched.
- Rollback source: `docs/global_modernization/v3/M04/M04_C_FAMILY_UI_SHARED_CORE_ROLLBACK_MANIFEST.json`.

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run strict comparison, manifest and static gates if any shared-UI descriptor, source, runtime exclusion or contract drifts.
3. Re-enter `M04-C-FAMILIES` with one separately frozen child; preserve silent emulator-only QA by default.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
