# Дорожная карта: остаток и прогноз

## Current position

Source: `docs/global_modernization/v3/WORK_PACKAGE_INDEX.yaml`, live read on 2026-08-09.

| Metric | Value |
| --- | ---: |
| Full catalogue work packages | 95 |
| Completed | 19 / 95 (20.0%) |
| Mandatory catalogue (non-conditional) | 85 |
| Completed mandatory | 19 / 85 (22.4%) |
| Mandatory remaining | 66 |
| Conditional remaining | 10 |
| Explicitly blocked packages | 3 |
| Next safe package | `M03.3` |

`Conditional` does not mean complete. It means work may be omitted only if its condition never becomes true: Google Play AAB (`M02.6`), physical-device performance (`M10.3`) and the entire non-release-blocking PCG/DDA track (`M11.1–M11.8`).

## Module progress

| Module | Scope | Complete / total | Mandatory remaining | Conditional | Status |
| --- | --- | ---: | ---: | ---: | --- |
| M00 | source freeze and Git topology | 6 / 6 | 0 | 0 | complete |
| M01 | quality gate, CI, review, evidence | 7 / 7 | 0 | 0 | complete, release gate active |
| M02 | Web/Android delivery and signing | 4 / 8 | 3 | 1 | technically partial; release blocked |
| M03 | GameRoot seams | 2 / 7 | 5 | 0 | in progress |
| M04 | graphics/atlas/bundles | 0 / 8 | 8 | 0 | pending after M03 |
| M05 | UI/UX responsive runtime | 0 / 7 | 7 | 0 | pending; depends on M03/M04/M06 |
| M06 | skins, bonuses, animation | 0 / 7 | 7 | 0 | pending after M03/M04 |
| M07 | levels/background/content | 0 / 7 | 7 | 0 | pending |
| M08 | audio/VFX/feedback | 0 / 7 | 7 | 0 | pending |
| M09 | saves/achievements/records | 0 / 8 | 8 | 0 | pending |
| M10 | performance/loading | 0 / 7 | 6 | 1 | stale baseline; depends on M04–M09 |
| M11 | PCG/difficulty | 0 / 8 | 0 | 8 | optional, non-release-blocking |
| M12 | RC/release/cleanup | 0 / 8 | 8 | 0 | pending after M02/M10 |

## Mandatory work still ahead

1. **M02** — choose signing/distribution, deploy the approved Web topology, then bind RC evidence.
2. **M03.3–M03.7** — bounded dev log, one input adapter, typed collision events, power-up lifecycle and UI/physics decoupling.
3. **M04–M06** — controlled asset/atlas/bundle governance, UI system and skins/bonus runtime pipeline.
4. **M07–M09** — level/content ownership, audio/VFX routing, persistence and local telemetry.
5. **M10** — budgets, baselines, measured optimizations and independent regression.
6. **M12** — RC freeze, two independent RC cycles, final Web/arm64 build, release evidence and approved cleanup.

The full work-package definition is included in the ZIP as `source_documents/WORK_PACKAGE_INDEX.yaml`; do not infer omitted requirements from this overview alone.

## Dependency-critical blockers

| ID | Blocker | Owner needed |
| --- | --- | --- |
| M02.1 | Direct APK vs Google Play, signing identity, upgrade and secret-backup policy | User/product owner |
| M02.7 | Approved immutable Web/Pages deployment topology | User/repository owner |
| M12.7 | Explicit approval to apply cleanup after accepted final build | User/product owner |
| Git integration | `codex/mtr-source-freeze-v3` and `origin/main` have no common merge-base | User decision after topology audit |

## Time forecast

This is an engineering range, not a release promise. The roadmap deliberately requires bounded patches, rollback mapping, Android/Web parity and repeated independent QA; collapsing them would contradict the accepted quality model.

| Scenario | Scope | Estimated effort | Calendar with one primary delivery lane |
| --- | --- | --- | --- |
| Next safe slice | M03.3 only | 2–5 engineering days | 1–2 weeks including QA/review/checkpoint |
| Mandatory technical roadmap | M02, M03–M10, M12; M11 deferred; external decisions already made | 38–58 engineering weeks | about 9–14 months |
| Full roadmap | mandatory scope plus optional M11 PCG/DDA | 48–72 engineering weeks | about 11–17 months |
| Parallelized delivery | two carefully separated lanes after M03 seam stabilizes | same effort | about 5–9 months for mandatory scope; QA/RC stays serial |

The forecast assumes each runtime package receives at least targeted static tests, CodeRabbit advisory review where appropriate, Android emulator and Web checks for behaviour changes, and a checkpoint. Rework from findings, new asset defects or inaccessible signing/deployment credentials extends it. No forecast can include waiting time for blocked user/external decisions.

## Recommended next three packages

1. `M03.3` — bounded deterministic development event log with clear reset ownership and zero release spam.
2. `M03.4` — InputActionRouter for keyboard, touch, HUD buttons and pause zone; preserve the 220 ms pause debounce.
3. `M03.5` — typed collision event wrapper, preserving the current update order before extracting side effects.

Do not combine them: their parity failures would be difficult to attribute and would invalidate the strangler approach.
