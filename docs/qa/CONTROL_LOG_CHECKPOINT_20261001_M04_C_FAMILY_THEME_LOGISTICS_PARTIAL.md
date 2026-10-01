# Logistics source fix and rejected-atlas rollback checkpoint

Date: `2026-10-01`  
Branch: `codex/mtr-source-freeze-v3`  
Anchor before slice: `d9175adcdbb5a6fe072063fd7ffd9275b364daf8`  
Physical device: **NO**. APK evidence: debug `x86_64`, emulator user `0` only.

## Roadmap checkpoint

- Status: `partial` for `M04-C-FAMILY-THEME-LOGISTICS`; retained alpha correction,
  regression prevention and rejected-atlas rollback are implemented and verified.
- Roadmap position: Phase `P2`, `M04.5` / `M04-C-FAMILIES` / logistics child.
- Progress: `20/73` mandatory execution units (`27.3973%`); no completion credit
  for the rejected atlas. The denominator gained one explicit inventory-derived
  child, so remaining grew from `52` to `53` without a completed increment.
- Evidence: final Web `34/34 x2`, Android `28/28 x2`, interaction/name/restart/soak,
  exact rollback visual match, source tests `13/13`, host-preflight tests `14/14`,
  M2_PLUS `8/8` applicable. Final full static gate `29/29 PASS`, findings `0`.
- Remaining: `53` mandatory units plus `7` conditional; source ledger `28/95`,
  `57` mandatory remaining plus `10` conditional. Release blockers: `M02.1`,
  `M02.7`, `M12.7`.
- Next: preregister a quiet paired performance/cache experiment for this same
  child before another atlas descriptor; no best-of repeat or threshold weakening.

## Retained implementation

- Lifebuoy `mtr_last_logistics_extended_hazards_002`: enclosed checkerboard removed
  using an imagegen-approved transparent cutout. Canvas `244x232`, UUID
  `05b16bb5-fa0d-4bea-9c3d-3d93b4b35e15`, pivot/import rectangle/resource key and
  original metadata bytes are preserved. Runtime PNG SHA-256:
  `0A430E298AF44E9615DB233AE1847FBDAFAAB73792AD30AE190D435D09504933`.
- Generated source, prompt, normalized source and metadata pins stay outside
  packaged `assets/`. Positive/negative tests reject matte recurrence, hash/UUID/
  provenance drift, traversal and invalid later records before target mutation.
- Legacy extraction preflights pins and restores this reviewed replacement.
  Full original-sheet regeneration is **NOT_RUN**; generic unreviewed UUID
  regeneration remains a separate follow-up, not silently certified by this fix.
- DEBUG gallery covers all 26 logistics hazard/platform sprites. Gameplay,
  collision, save schema and production audio settings are unchanged.
- Read-only host preflight blocks atlas measurements overlapping MTR build/QA
  and emits no raw command lines. It is a start-time snapshot, not a lock; it is
  wired to the two atlas entrypoints, not every functional matrix.

## Rejection preserved

Attempt01: `61/63`, **REJECTED**. Android load `4756 ms > 2953.75 ms` and median
FPS `4 < 5.1`. Web draws `42 -> 33`, Android `58 -> 33` and visual gates pass,
but cannot override the failures. Faster repeat load `1168 ms` is not selected
as acceptance. Cause remains **unconfirmed**.

Candidate full Android matrices `27/28` and `25/28` also remain failed; slow-load
warnings coincided with native build overlap. Candidate interaction/restarts/
`300.75 s` soak passed, but are not reused as final-unpacked APK evidence.

The rejected `.pac` and `.pac.meta` are removed, and accepted measured ownership
still contains only the eight previously accepted atlas families through construction.

## Fresh unpacked final QA

- Web and Android builds finish through the existing verified Cocos wrapper;
  raw Cocos exit `36` is not used alone as acceptance. Android Gradle finishes.
- Both platforms: source textures `26`, source UUID artifacts `78`; original
  unpacked resource bytes `122,070,847` restored. Web runtime `127,405,098` bytes;
  Android `127,591,483` bytes.
- Rollback content ROI images equal the corrected baseline: MAE `0`, changed
  pixels `0`, material new near-white pixels `0` on both platforms. This is
  rollback verification, not a new atlas acceptance or independent repeat claim.
- Web `34/34 x2`, interaction PASS and restart `10/10 x2`.
- Android `28/28 x2`: all 15 level-start gates and 13 screens; no unexpected
  product/engine warnings or fatal errors. Existing known-engine allowlists are
  unchanged; this does not claim a complete playthrough of every level/combination.
- Final-unpacked touch/FSM and typed-name cold persistence PASS; restart `10/10`;
  soak `300.642 s`, `318` input bursts, `17` state actions, process losses `0`.
  PSS start/peak/end: `206,466 / 262,938 / 200,682 KiB`.
- Every Android entrypoint confirms AVD `-no-audio` and media stream 3 volume
  `0/15`, fail-closed. No phone, physical-user profile or production mute setting
  was changed.
- Final QA APK: `146,279,961` bytes, SHA-256
  `7CBCDCADA60E0A4B6B1D7F4869FC61C20E0B47D6A9FBB363B6E0DB709F4BCFA4`.
  This is not a release APK and is not represented as device-valid release evidence.

## Review and orchestration corrections

- Codex review records nine corrected findings and two open follow-ups; see
  `../global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_CODE_REVIEW_REPORT.md`.
- First temporary M2_PLUS binding was `BLOCKED`: eight exact child gate-ID
  mismatches. First report is preserved (SHA-256
  `99AC958A09A783D13639BD43F29CE3C6F03950E3184C3234EFE0E3F0808B93DC`).
  Preparation now gets exact IDs from the authoritative catalog, not shortened
  domain names. All eight child gates and the profile were rerun without relaxing
  contracts: `8/8 PASS`, four recovery slots `NOT_APPLICABLE`, findings `0`.
  Final profile SHA-256:
  `7F28471FA6624CA21DD7A08DC7B977602498545785F4BDD2A9D014E07A85CD35`.
- Read-only orchestration probes caught a non-existent guessed schema/library
  path, an invalid top-level Hermes verb, Git warning-prefixed JSON and relative
  untracked-path assumptions before any affected artifact was written. CLI help,
  `rg --files`, JSON framing, `git ls-files --full-name` and prefix guards corrected
  the calls. No global router/permissions/hooks were modified.
- A non-canonical `core.autocrlf=false` diff probe surfaced the CRLF pin risk;
  the project's default whitespace check passes. Two exact metadata paths now
  have explicit CRLF checkout rules, and Git roundtrip tests under both settings
  prove unchanged pinned bytes. Four source-test cycles pass `13/13`; this is not
  a claim of full native Linux runtime acceptance.

## Hygiene, publication and resume

- The QA HTTP server and emulator are stopped. Builds, logs, screenshots and
  rejected-candidate evidence remain ignored local evidence, not tracked game data.
- Reviewed generated source is intentionally retained for restoration/provenance;
  it is not a packaged duplicate. No full-recut output or runtime backup was added.
- Root AGENTS, widget, Tasks, stickers and root project-library work stay untouched.
- Canonical repository remains `nikitak8883/Martyskin-trud-runner`; source projection
  is `mtr-source-v3`. Final commit/projection/remote verification belongs in the
  post-commit Hermes milestone. No Pages/main, signing or release publication.
- Resume from `CURRENT_STATE.md`, the contract, rejection and next-experiment doc.
  Preserve first failed results, unchanged gates, source pins and silence.
- Rollback instructions retain audit history and unrelated work; the atlas-only
  rollback is already verified. Do not revert the art fix merely to retry packaging.

Detailed report and SHA-bound local evidence:
`../global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_VALIDATION_SUMMARY.json`.

Final full static report SHA-256:
`03C1354D9FC0F0F3D699703CC2F189FC00BE35E27486AA12229C0DEFA3AED3AD`.
