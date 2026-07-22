# Control log / checkpoint — M01.7 and M02.2 complete

Date: 2026-07-22  
Project: Martyshkin Trud Runner  
Branch: `codex/mtr-source-freeze-v3`  
Release status: `BLOCKED`

## Completed scope

### M01.7

- Published a durable fail-closed release summary and final M01 code-review report.
- Evaluated the canonical `M2_PLUS` profile on a clean stable source.
- Correct result: `BLOCKED` with 8 `MANDATORY_EVIDENCE_MISSING` findings across two complete static/Web/Android-emulator/review cycles.
- Four focused-recovery slots are explicitly `NOT_APPLICABLE` because M01.7 changed no runtime seam.
- M01 quality/evidence framework is complete; this is not a release pass.

### M02.2

- Added Cocos asset `assets/resources/config/content_identity.json` plus valid unique `.meta`.
- Logical identity: `mtr-v3-source-a5c4bdbb2fca`.
- Immutable public pre-metadata baseline: `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2` on `mtr-source-v3`.
- Preserved M00 freeze provenance and aggregate SHA-256 `E3C72CE3D41BAA9EA54D9941A6A91312DFD38A94112C99ADC02D935915A8EDFD`.
- Extended `tools/Run-MtrCocosBuild.ps1` with fail-closed no-build identity preflight and shared `contentIdentity` output.
- Kept `platformArtifactManifest` separate for Web, x86_64 emulator Android and arm Android.
- Added `tools/validate-content-identity.py`, five focused tests and the eighth mandatory static-gate step.
- No Cocos build, browser runtime, emulator, physical device, signing or Pages action was performed.

## Accepted validation

- Final clean local gate: `qg.20260722063921.cb31e1f5e6da`, 8/8 PASS, 0 findings, source clean/stable, report SHA-256 `6B338FB66FA336E645836B7DE9356BE22A0A943DE324B4C64D3185835AE53118`.
- M02.2 implementation hosted gate: [run 29897120642](https://github.com/nikitak8883/Martyskin-trud-runner/actions/runs/29897120642), Windows and Ubuntu PASS, 8/8 and 0 findings on source `707ab97ad30bbfe7014c421c96c52ecfec5feaf7`.
- Acceptance-documentation hosted regression: [run 29897468090](https://github.com/nikitak8883/Martyskin-trud-runner/actions/runs/29897468090), Windows and Ubuntu PASS on source `ccf594be578980550fd02a639c12cb9b020d462f`.
- Both hosted M02.2 reports used identity SHA-256 `F8362EC17295FD646E335C501B40A24871E3B40C1CBA22B6A4C0F36AD9313395` and metadata SHA-256 `135824A44562019CB1C2A1FA7783552303813A3C0882EF1A8BA90CD755E43C3C` with 3/3 preflights.
- Hosted quality suites: 52 tests, 2 expected platform skips, 0 failures on each OS.

## Fail-closed correction log

Hosted run `29896755871` initially failed on both OS. The validator could not resolve the baseline commit because Actions checked out only the branch tip with `fetch-depth: 1`.

The validator was not weakened. The workflow now fetches full source history (`fetch-depth: 0`) so Git ancestry is directly provable. The same gate then passed on both OS in run `29897120642`.

## Git publication

- Sole remote: `https://github.com/nikitak8883/Martyskin-trud-runner.git`
- Source branch: `mtr-source-v3`
- M01.7 published baseline: `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2`
- M02.2 implementation/fix source: `707ab97ad30bbfe7014c421c96c52ecfec5feaf7`
- Acceptance documentation source: `ccf594be578980550fd02a639c12cb9b020d462f`
- No force push, history rewrite, `main`, Pages deployment or historical `codex` branch mutation occurred.

## Hygiene

- Tracked tree is clean.
- No TODO/FIXME/HACK/debug output remains in the touched source scope.
- The obsolete clean diagnostic worktree `C:\Projects\MTR-source-v3-ci-smoke` was removed through `git worktree remove` and metadata was pruned.
- User-owned untracked paths `Stiker pack/SG-1/`, `Tasks/4/_unpacked_20260702_145527/`, `Tasks/5/` and `project-library/corpora/` were not modified or staged.
- Current ignored M02.2 reports and downloaded hosted artifacts are retained as bounded local audit evidence for the next retention cycle; they do not enter Git or release artifacts.
- No old runtime path, superseded asset, generated build or release binary was introduced by this scope.

## Remaining release blockers

- no fresh accepted M02.3 Web build/runtime/matrix/restart/soak evidence;
- no fresh accepted M02.4 Android-emulator build/install/runtime evidence;
- no current M02.5 arm64 device-valid artifact from the accepted source;
- Web/Pages artifact parity is not restored;
- production signing/distribution ownership remains unresolved;
- M2_PLUS and RC2 release profiles remain blocked.

## Resume point

Start `M02.3` only: build Web from the accepted shared identity, generate a separate immutable Web artifact manifest, then run targeted runtime, matrix, restart and soak evidence. Do not start Android, signing, device installation or Pages deployment in the same patch.
