# Control log checkpoint — M01.4 typed quality profiles

Дата: 2026-07-21  
Статус: `PASS FOR M01.4 / RELEASE BLOCKED`

## Completed

- Added canonical typed D4, P4, M2_PLUS, QA7 and RC2 profile catalog.
- Added config, invocation-scope and aggregate-report schemas.
- Added fail-closed profile resolver and aggregate evaluator over fresh M01.3 reports.
- Added explicit mandatory, conditional and `NOT_APPLICABLE` semantics.
- Bound child evidence to source commit, content version, freshness, config/artifact hashes and independent run identity.
- Preserved emulator-only Android default; physical-device evidence requires a conditional scope decision and an explicit CLI switch.
- Added profile bootstrap routing and PowerShell wrapper.
- Hardened same-byte JSON snapshots and active-venv bootstrap handling after independent review.

## Validation snapshot

- Isolated unit/integration suite: `46` discovered / `44` PASS / `0` FAIL / `2` expected platform skips.
- PowerShell AST: PASS.
- Wrapper forwarding and exit code: PASS.
- M01.2 direct regression: PASS.
- M01.2 through M01.3 runner: PASS.
- Post-commit clean-source suite and M01.2 runner: PASS with no dirty override.
- `git diff --check`: required again at final hygiene gate.

## Deliberately not executed

- Cocos/game runtime changes;
- Web build or runtime;
- Android build or emulator;
- physical device;
- Pages deployment, signing or release.

These are not required for the documentation/tooling-only M01.4 slice and no runtime or release claim is made.

## Restart point

Next safe action: `M01.5` — classify evidence as protected, retained_recent or rotatable, then implement an index-first retention dry-run with resolved-path guards. Do not begin M02 release recovery or M03+ runtime modernization before the M01 dependency gate permits it.
