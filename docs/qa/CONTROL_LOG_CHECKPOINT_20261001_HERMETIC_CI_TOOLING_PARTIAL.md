# Hermetic CI repair — four bounded prerequisites

- Status: `completed` for local implementation/targeted validation; `partial`
  for final hosted CI, parent atlas/native/Release acceptance.
- Roadmap position: existing `M01.6`/`M12.7` prerequisites before
  `P2 / M04-C-FAMILY-THEME-LOGISTICS`; no new execution unit or acceptance credit.
- Progress: `20/73` mandatory (`27.3973%`), source `28/95`, unchanged.
- Evidence: four compiler cycles `10/10`; four stable-input proof/asset cycles
  `19/19 +18/18 +14/14`; compiler guard four further `19/19` after resolved-path
  cleanup hardening. Cocos/npm compiler main bytes match, exact dependency lock.
  Original/source rollback whole trees and all10 old blobs match. Final canonical
  gate has34 steps; source-pinned local/hosted receipts follow the unit commit.
- Remaining: `53` mandatory +7 conditional execution units; original source
  ledger `57` mandatory +10 conditional packages. PNG/contact-sheet portability,
  native bootstrap, attempt02 inputs/timed samples and Release gates stay open.
- Next: hosted verification, then diagnose remaining PNG/index portability with
  raw source/provenance checks preserved, then native bootstrap/paired experiment.

## Cause and bounded corrections

The previous source already failed hosted Windows/Linux CI (runs `36832697272`
and `36843587679`); failed ID sets were equal. Three silent-QA additions passed
both platforms. This patch fixes four prerequisite clusters, not gameplay:

1. Nine Node tests depended implicitly on a local Windows Creator path. Shared
   loader now uses private tool-only TypeScript5.8.2, exact npm lock/integrity and
   main compiler SHA. Explicit legacy override must match version/hash; no code
   executes before checks. Strict diagnostics and behavior assertions unchanged.
2. Linux symlink cleanup used directory `rmdir`. Now unlink a symlink or remove
   a Windows junction only after verifying its test-owned parent/type. Outside
   sentinel survives; containment negative control is retained.
3. Windows checkout added36 bytes to12 `.pac` JSON descriptors. The LF Git
   attribute and both autocrlf roundtrips preserve descriptor and binary bytes.
   No descriptor contents/source inventory/acceptance thresholds were refreshed.
4. Hosted source-only history lacks monorepo M03.7A commit. A separate mapping
   binds the unchanged original cleanup manifest to existing published source
   commit `ba6b3676e7e40626c0df546bb34ceb9dc4d6330c`. Tree equality is
   `d5cae55f7ce145da6927f81544614c3f44085396`, plus all10 original blobs. The
   fallback is source-only, ancestry-checked and fail closed for missing/wrong
   trees/blobs. Monorepo still requires its original anchor; no weak substitution.

## Review / tests / rollback

Codex scoped review: four fixes are coherent; negative fixtures verify no fallback
on invalid compiler/provenance or unsafe test paths. Local package install is
explicit, scripts/audit/funding disabled; tests themselves do not download.
No external CodeRabbit/model patch review, global configuration, signing, deploy,
physical-device access or runtime asset change is authorized by this qualification.

Initial13-test asset smoke preceded the final14-test checkout fixture; only the
four final stable14-test cycles are used for final asset qualification. Failed
hosted predecessors and native bootstrap evidence remain preserved.

Local receipts: `temp/ci-portability-20261001/compiler-cycle1..4` and
`proof-asset-cycle1..4`. Source parent before this slice:
`84be2701877b4bf2481e7b685d7b6de0516275d8`; sole source remote is
`nikitak8883/Martyskin-trud-runner`, branch `mtr-source-v3`. Post-push Hermes
checkpoint records exact commit/projection/remote/current CI; don't invent hashes
inside their own source commit. Historical cleanup/atlas/provenance files unchanged.

Rollback only this project-scoped commit. Installed nested `node_modules` is an
ignored reproducible tool cache, not a runtime backup or copied global skill root.
Source fixture trees are cleaned with ownership guards; reports intentionally kept
as audit evidence. No APK build/game runtime QA in this tooling slice. All future
runtime QA remains host-silent and emulator-only unless separately authorized.
