# M04-A code, contract and QA review

Date: `2026-08-21`  
Verdict: `PASS FOR CONTRACT-ONLY ASSET GOVERNANCE / RELEASE REMAINS BLOCKED`

## Review boundary

- Revalidate the accepted runtime assets and metadata.
- Establish canonical owner/provenance/atlas/bundle policy without moving, repacking, trimming or recompressing runtime art.
- Keep Android QA emulator-only on `emulator-5554`.
- Preserve unrelated root AGENTS, agent monitor, Tasks, sticker and project-library changes.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Initial M04 schema was placed in the closed shared quality-schema namespace | Fixed: moved to `M04/schemas`; the canonical M01 namespace gate then passed. |
| Broad `objectives/themed` ownership assigned themed UI to the level pipeline | Fixed: split eleven level families and themed UI into separate scopes; added `ATLAS_OWNER_MISMATCH` enforcement and fixture. |
| Source-root-relative selectors and project-root-relative provenance were implicit | Fixed: mandatory `path_conventions` added to manifest/schema with a negative fixture. |
| Local advisory suspected two governance `.meta` files were orphaned | Rejected with direct evidence: targets exist, canonical meta graph reports orphan `0`; a new unit test proves the valid pair and detects a real orphan. |
| Direct helper tests did not isolate canonical byte, containment, meta and Git ancestry semantics | Fixed: test suite expanded to eight direct tests plus eleven negative fixtures. |
| Added content identity reachability ref might not exist | Rejected: local branch exists at `58d057c`; validation skips absent optional refs and requires reachability from at least one canonical ref. |
| First Android touch after a cold emulator boot was delivered during an Activity input-sink transition | Fixed in the emulator-only harness: four stable input-channel samples plus bounded, marker-verified retries; the original failure receipt remains preserved. |
| Advisory review suspected a process-tree race and misleading redirect-drain timeout | Rejected after three consecutive entrypoint self-tests: inherited-handle descendants were cleaned in `3/3`, stream draining stayed bounded, and every logical exit remained fail-closed. |
| Advisory review suspected path/symlink escape, malformed-schema fail-open and weak byte hashing | Rejected by direct code reconciliation; tests now prove `..` and NTFS-junction escape rejection plus malformed Draft 2020-12 schema failure. Canonical byte normalization/hash behavior remains directly covered. |

Accepted/fixed findings: `5`. Rejected false positives: `8`. Open findings: `0`.

## Review and QA evidence

- Manifest/schema re-review: final verdict `accept`; path recommendations independently proved by canonical validator.
- Validator/tests review: orphan suspicion rejected and missing direct tests added.
- M04 validator: `PASS`, findings `0`, source `1,635`, scopes `24`, image groups `11`.
- Unit tests: `8/8 PASS`; negative fixtures: `11/11` fail with expected codes.
- Entrypoint inherited-handle regression: `3/3 PASS`; local coder lifecycle cleanup verified.
- Static pre-report and final post-reconciliation gates: `23/23 PASS` each, findings `0`.
- Web: fresh build plus A/B and final recovery `34/34`; interactions and restart loops pass.
- Android emulator: fresh APK install; A/B plus final recovery `28/28`; final touch/name/cold persistence, `10/10` restart and `30.719 s` soak pass; process losses `0`.
- Visual sample: menu/name/levels/level 15 pass; no white fragments, ghost layers or missing background.

## Hygiene and residual limits

- No runtime PNG/JPG/WAV/MP3 or Cocos import setting was changed.
- Generated build, screenshots, logs and temp reports remain ignored and are not committed.
- The one cold-boot touch failure and its corrected cycle are both retained as local evidence; no failure evidence was overwritten.
- QA Web server was stopped; no project QA port remains open.
- The APK is x86_64 debug emulator evidence, not a production arm64 release.
- Web evidence is local; Pages deployment was not authorized.
- Bundle lifecycle, measured atlas migration, production signing/deployment and final owner-approved cleanup remain later units/blockers.

M04-A is complete. The next dependency-safe unit is `M04-B` (`M04.3 + M04.4`).
