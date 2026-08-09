# QA-циклы и границы доказательств

## M03.2 acceptance evidence — VERIFIED-2026-07-23

| Check | Result |
| --- | --- |
| Executable state contract | PASS: 14 states, 58 accepted, 138 rejected, 14 idempotent, 1 writer |
| Structural Python validator | PASS: 14 session states, 8 player states, 44 player transitions |
| Strict Cocos TypeScript module check | PASS |
| Full Cocos TypeScript project check | PASS |
| `git diff --check` | PASS |
| Static gate | PASS: 9/9, zero findings |
| CodeRabbit final re-review | 0 issues across 16 staged M03.2 files |
| Android emulator matrix | PASS: 28/28 (13 UI routes, 15 levels) |
| Android restart loop | PASS: 10/10 |
| Android soak | PASS: 300.369 s, 323 input bursts, 17 state actions, 0 process losses |
| Web matrix | PASS: 34/34 |
| Web restart loop | PASS: 10/10 |
| Web soak | PASS: 300.525 s, 39 input bursts, 3 clear-route actions, 0 console errors/warnings |

Android QA used only `emulator-5554` (`MTR_Pixel_8_Pro_API_35`). No physical device was addressed. The installed x86_64 debug APK is explicitly emulator-only.

## Evidence topology

| Evidence | Path in project | Included in ZIP |
| --- | --- | --- |
| M03.2 machine summary | `docs/global_modernization/v3/M03/M03_2_VALIDATION_SUMMARY.json` | yes |
| M03.2 review report | `docs/global_modernization/v3/M03/M03_2_CODE_REVIEW_REPORT.md` | yes |
| M03.2 state report | `docs/global_modernization/v3/M03/gameplay_state_report.md` | yes |
| Sanitized current checkpoint log | `01_CURRENT_STATUS_AND_LOG.md` | yes; original excluded for local-path privacy |
| Android summary JSON | `docs/qa/20260723_m03_2_android/...summary.json` | no: summarized/hashes only |
| Android raw screenshots/logcat | 81 files, 190,028,450 bytes | no: heavy/raw evidence |
| Web summary JSON | `docs/qa/20260723_m03_2_web/*.json` | yes |
| Build APK/creator output | build/log directories | no |

## Why raw Android evidence is excluded

The external auditor needs conclusion-level evidence, test parameters, result counts and hashes first. The raw Android evidence is almost 190 MB, contains large screenshots and device logs, and is not required to assess roadmap/architecture. It may be shared later as a separate reviewed bundle if a specific visual or log claim is challenged.

## Historical fail-closed release result

The M01.7 report is included because it correctly reports release `BLOCKED`. It was generated before M02.2–M03.2 and therefore has historical scope: do not interpret its missing slots as a contradiction of the M03.2 QA. It demonstrates the release-gate policy, not the current final release state.

## Required fresh validation before next runtime patch

1. Reconfirm `git status`, branch/remote topology and current toolchain.
2. Re-run M03.2 contract tests before changing the seam.
3. Add targeted tests for the new M03.3 ring-buffer/reset behavior.
4. Run static gate on the bounded diff.
5. Run privacy-scoped CodeRabbit advisory review, resolve findings manually.
6. Run Android emulator and Web parity QA for runtime changes.
7. Create a new checkpoint; never overwrite M03.2 evidence.

## What QA has not proven

- production signed APK/AAB installation and upgrade compatibility;
- live Pages deployment parity;
- Android physical-device performance/thermal/background-resume behaviour;
- final RC2, cleanup and publication acceptance;
- any runtime behaviour after the 2026-07-23 source checkpoint.
