# M04-C-FAMILY-RUNNER-COLLECTIBLES completion checkpoint

Timestamp: `2026-08-22T14:17:22+03:00`  
Branch: `codex/mtr-source-freeze-v3`  
Pre-completion HEAD: `8fb9ee12d4bb690f0457dafb2c6eb09e1c7f5435`  
Scope: one measured `runner_collectibles` static Auto Atlas child under `M04-C-FAMILIES`.  
Physical device used: `NO`.

## Roadmap checkpoint

- **Status:** complete child / parent and source package remain open / release blocked.
- **Roadmap position:** Phase P2, `M04-C-FAMILY-RUNNER-COLLECTIBLES` complete inside `M04-C-FAMILIES`.
- **Progress:** execution denominator expanded for the inventory-derived child: `15/67` complete (`22.3881%`), `52` mandatory remain plus `7` conditional. Source remains `28/95`; `M04.5` stays pending.
- **Authorization boundary:** no other atlas family, dynamic-atlas policy, bundle policy, Pages deployment, signing or physical-device QA is authorized.

## Accepted implementation

- Added `runner_collectibles.pac` for exactly 14 governed PNG sources; UUID `f2b9f0ac-e094-4354-b291-94f7b6777c7c`.
- Preserved all source PNG bytes, pivots, trim policy, paths and runtime keys.
- Extended the strict DEBUG-only measurement allowlist by one exact family; release behavior remains closed to QA query routing.
- Updated canonical manifest/contact-sheet linkage for three measured static atlases and corrected the accepted family compression state to measured lossless Auto Atlas on Web and Android.

## Acceptance evidence

- Strict comparison: `63/63 PASS`.
- Android emulator draw median: `34 → 21` (`-13`, `-38.2353%`); load `698 → 658 ms`.
- Web draw median: `21 → 21`; texture memory `29.57 → 14.24 MiB`; load `254 → 249 ms`.
- Automated and manual visual parity: all 14 sprites visible; white matte, missing frames and pivot/trim regressions `0`.
- Static: `26/26 PASS × 2`, post-fix `26/26`, findings `0`.
- Web post-fix: fresh build, `34/34 × 2`, interaction PASS, restart `10/10 × 2`.
- Android emulator post-fix: fresh x86_64 build/install to `emulator-5554`, user `0`; `28/28 × 2`.
- Android interaction: custom name persistence PASS, restart `10/10`, soak `300.301 s`, `319` input bursts, process losses and unexpected diagnostics `0`.
- M2_PLUS: `8/8` applicable PASS, four focused-recovery slots explicitly `NOT_APPLICABLE`, findings `0`.
- Final Codex review and hygiene: PASS, open findings `0`.

## Corrected failures and prevention

1. The first static gate correctly failed `25/26` because exact inventory assertions still represented two measured atlases. Counts and ordered IDs were updated; all complete reruns pass.
2. The first targeted unittest invocation placed interpreter option `-B` after `unittest`; it was corrected and the suite passed `11/11`.
3. Early boot polling met a transient offline/null ADB response. Accepted actions begin only after a ready emulator, with explicit `-s emulator-5554`, qemu verification and user `0`.
4. Review found the accepted family still labeled `pending_measurement` in compression metadata. It was corrected, the contact-sheet index regenerated, and both platforms rebuilt and fully rerun.
5. A context-insufficient manifest patch transiently matched `ui_shared_core`; it was reverted before validation. Atlas-ID-scoped patches and a full group table are now the accepted edit path.
6. One read-only hash-collection PowerShell command had an empty pipeline element, and one tool-orchestration retry omitted its local JavaScript variable. Neither mutated project state; both were corrected with explicit intermediate arrays and self-contained calls.
7. The first post-commit gate declaration used a short Git SHA and was rejected before tests with `SOURCE_DECLARATION_MISMATCH`. The accepted rerun uses `source-commit=auto` and the exact full HEAD.

## Hash anchors

- Contract: `9E85FD6B0C45457F4CF2C8DE4E3BB0D5575B887D03BB5ECC0A04C786333D8D9F`.
- Durable acceptance: `DCD031D9488AF104160ABEEF4750D8B004B4DDC52DC41B29D0AA9236139C50F0`.
- Comparator: `27536887D36529E96E04A6E59CEB70115438232F6F3E925B93C7E5EE778937BE`.
- Visual parity: `79018FB0794B3ADFA6554446DCD88817AB5DB08679E7E0228D5BA900FFBB7F48`.
- Post-fix Web: `C9BC35587CD58C102427788EBD2AE0471A2FFE1B9BC85DBF35DD1298FC3D564D`, `E5B182562CAE564195CE50A353D4F39ECF729A9E442211E05212D9832F22FB39`.
- Post-fix Android matrices: `0A9D874F0EEF623305DF363BFBBBC02F30A321DF78E441CC70DC44423EFA1B0C`, `DDC65B3CF252322E9825EEB645C8996712B4A5E83504558E6BA9A90DA5C07B29`; interaction `288517789CAB412EDA3053C6E6A86B280B3436542209909536673987B3342587`.
- M2_PLUS: `9E36DF7D9B28DFC7738F810ABFF95AF80C7DD3A4FA9C9DD4BB460A9318BAFE96`.
- Emulator APK: `2E4BCBC3481651F9FF05CF1DBA47A523208E9CE0F2013C2FA26CBD6E3417A519` (`144031734` bytes; emulator debug only).

## Resume order

1. Verify this checkpoint, the Hermes milestone and `origin/mtr-source-v3` ancestry.
2. Re-run strict M04 comparator/manifest/static checks if the descriptor, manifest, contract or durable evidence drifts.
3. Re-enter `M04-C-FAMILIES` by selecting exactly one new candidate before mutation; do not batch families. `bonus_items` requires a separately approved split/relocation decision.
4. Keep release blocked by `M02.1`, `M02.7` and `M12.7`.
