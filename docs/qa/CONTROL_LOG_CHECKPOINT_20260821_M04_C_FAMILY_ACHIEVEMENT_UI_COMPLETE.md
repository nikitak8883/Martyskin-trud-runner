# M04-C-FAMILY-ACHIEVEMENT-UI completion checkpoint

Timestamp: `2026-08-21T15:39:46+03:00`  
Branch: `codex/mtr-source-freeze-v3`  
Pre-completion HEAD: `5716a6eed3ee3e2290f08a20ce01bd90ce123a89`  
Scope: one measured `achievement_ui` static Auto Atlas child under `M04-C-FAMILIES`.  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** complete child / parent and source package remain open / release blocked.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-ACHIEVEMENT-UI` complete inside `M04-C-FAMILIES`.
- **Progress:** execution denominator expanded for the inventory-derived child: `14/66` complete (`21.2121%`), `52` mandatory remain plus `7` conditional. Source remains `28/95`; `M04.5` stays pending.
- **Authorization boundary:** no other atlas family, dynamic-atlas policy, bundle policy, Pages deployment, signing or physical-device QA is authorized.

## Accepted implementation

- Added `achievement_ui.pac` for exactly nine governed PNG sources; UUID `35f049fd-ff92-47ec-bbe0-7ab05469eab2`.
- Preserved all source PNG bytes, pivots, trim policy, paths and runtime keys.
- Generalized the DEBUG-only measurement route from one pilot ID to an exact two-ID allowlist; release behavior remains closed to QA query routing.
- Made artifact source directory and screenshot filename contract-driven and contained.
- Updated canonical manifest/schema/contact-sheet linkage for two measured static atlases.

## Acceptance evidence

- Strict comparison: `63/63 PASS`.
- Android emulator draw median: `24 → 16` (`-8`, `-33.3333%`); load `475 → 425 ms`.
- Web draw median: `16 → 16`; texture memory `30.68 → 15.13 MiB`; load `212 → 219 ms`.
- Automated visual parity and manual Web/Android review: all nine sprites visible; white matte, missing frames and pivot/trim regressions `0`.
- Static: `26/26 PASS × 2`, findings `0`.
- Web: fresh build, `34/34 × 2`, interaction PASS, restart `10/10 × 2`.
- Android emulator: fresh x86_64 build/install to `emulator-5554`, user `0`; `28/28 × 2`.
- Android interaction: custom name persistence PASS, restart `10/10`, soak `300.914 s`, `311` input bursts, process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four focused-recovery slots explicitly `NOT_APPLICABLE`, findings `0`.
- Final Codex review and hygiene: PASS, open findings `0`.

## Corrected failures and prevention

1. Two nested PowerShell attempts failed to bind the Boolean Web-server switch. Direct typed invocation is now the recorded accepted path; no server started in either failed attempt.
2. Android QA first exposed `$PSScriptRoot` use in a parameter default under Windows PowerShell 5.1. Project-root resolution moved after script entry and a child CLI regression passed.
3. Successful `adb pull` progress on stderr was misclassified as a NativeCommandError. Native exit code is now authoritative and remote screenshot cleanup remains mandatory.
4. The visual comparator expected the pilot filename. Screenshot basename now comes from the family contract and is validated before use.
5. The first post-acceptance static gate correctly failed `24/26` because the generator-owned contact-sheet hash was stale. The index was regenerated deterministically; both complete reruns pass `26/26`.
6. The first M2 review gate incorrectly used `node --check` on an anonymous function expression. It was replaced by executable CLI syntax validation; the runtime function was independently executed in both Web cycles and direct tests.
7. A local review call used the non-existent profile alias `coder`; the accepted `coding_efficiency` route was then used. No model remained loaded after review.
8. Three direct validator calls from ambient Python were rejected because the pinned `jsonschema` environment was absent. They were rerun through the canonical bootstrap; the complete final gate passed `26/26`. This preserves the isolation rule instead of installing into global Python.
9. An explicit coding-model unload returned `model not loaded` because the lifecycle wrapper had already unloaded it. The independent status probe confirmed only the embedding model remained.

## Hash anchors

- Contract: `13195F0F1AE525778A63F4E1BD5B70718C6BCBF55513903AA4F8328CF4AF7110`.
- Durable acceptance: `6A0219604856E049067B01D54862B13DF39197CF21AA39052E2E169BB808A530`.
- Comparator: `657B427BFC062B1D17E6E9AD8C95C3F5D888710D3695DBFAC441597653035E10`.
- Visual parity: `88A62D04997DDB54ED90C076A123DEC31693EDA35FC816FD8630BAC108C7FD14`.
- Static cycles: `98B6EC4A81E88DF207A090C05ED1C195C289DCFEE3DA47AE13938C7BB18A05DD`, `1D3084353D03FBE0FA8A4689DEE13372E4B8FDEDC04C06FB5A0761CA61D34693`; post-roadmap gate `7BFC666031A9B56C38CB8EEC77D78F9B03DE41874027F26B11EB9663376C8C59`.
- M2_PLUS: `046273FA51C9ADB760FB8E5BD7763BA71E0E022A83E8DBD5DD75392F2B2B380A`.
- Emulator APK: `171954C511F84F2A0E7D0EC79756BF02E46C38BA55A853D4A7240B7A919833E3` (`143697815` bytes; emulator debug only).

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run strict M04 comparator/manifest/static checks if the descriptor, manifest, contract or durable evidence drifts.
3. Re-enter `M04-C-FAMILIES` by selecting exactly one new candidate before mutation; do not batch families.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
