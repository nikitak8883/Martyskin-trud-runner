# M01.4 typed quality profile composition

Дата: 2026-07-21  
Итог: `PASS FOR BOUNDED M01.4 / RELEASE BLOCKED`

## Accepted profile catalog

| Profile | Ordered cycles | Slots | Mandatory | Conditional | Intended boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| D4 | 1 | 4 | 4 | 0 | documentation, schema, compatibility and independent review; no runtime claim |
| P4 | 1 | 4 | 4 | 0 | static, targeted Web, targeted Android emulator, regression/review |
| M2_PLUS | 3 | 12 | 8 | 4 | independent P4 pass A and B, plus focused recovery only when high risk is declared |
| QA7 | 1 | 7 | 7 | 0 | seven-domain product QA matrix |
| RC2 | 3 | 20 | 18 | 2 | two independent QA7 cycles plus source/artifact/deployment parity |

Canonical catalog: `quality_gate.config.json`  
Catalog ID: `mtr.v3.quality-profiles`  
Catalog SHA-256: `B82025891085FEC4F0E207EAD89C3F6DD479C77730307AF26820D0297DB40EB3`

## Composition semantics

- Every applicable mandatory slot requires a fresh, schema-valid M01.3 child report bound to the exact profile source commit and content version.
- Missing, skipped, stale, copied, source-drifted or unknown-schema mandatory evidence produces `BLOCKED`, never `PASS`.
- A conditional slot must have one explicit condition decision. `false` becomes structured `NOT_APPLICABLE` with a reason code and cannot carry an evidence binding; `true` becomes mandatory.
- Optional slots are supported by the engine and may be visible as non-blocking `SKIPPED`, but the canonical five profiles intentionally contain no optional slots.
- Child run IDs, report hashes and artifact paths cannot be reused across independent slots/cycles.
- Profile config, scope, schemas, evaluator code, child reports, child configs and child artifacts are protected by source/path/hash checks. JSON identity and parsing use the same byte snapshot.
- Aggregate output cannot overwrite any canonical input, child report, child config or child artifact.
- Android defaults to `android-emulator`. The sole `android-device` RC2 slot is conditional and requires both a true scope decision and explicit CLI authorization.
- RC2 rejects the development dirty-source override.

## Architecture decision

M01.4 does not add a second arbitrary command runner. It composes fresh reports from the accepted M01.3 runner. M01.3 remains responsible for bounded process execution and native evidence adaptation; M01.4 owns profile topology, applicability, independence, freshness and aggregate acceptance.

## Scope boundary

This work package changed schemas, profile policy, evaluator/bootstrap code, tests and documentation only. It did not change game runtime, assets, Web output, Android output, Pages, signing or release artifacts. Therefore no Web runtime, Android emulator or physical-device session is claimed for M01.4 itself.

Next safe action: M01.5 evidence classification and index-first retention dry-run.
