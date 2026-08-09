# V4 project-local preparation library

This directory contains only strengthened drafts that are not already owned by the canonical v3 library.

## Status classes

- `reference/`: compile-checked design drafts; not runtime code and never copied blindly.
- `schemas/`: machine contracts for v4 planning/toolchain and M03.3 preparation.
- `configs/`: non-active examples validated by schemas.

The DevEvent reference is bounded at append and export boundaries, rejects
invalid scalar identities, never evaluates plain-object accessors, and uses a
null-prototype output object. These are design requirements for M03.3A, not a
claim that runtime telemetry has already been integrated.

The canonical M01 quality runner, schemas, profiles, adapters and exact dependency lock remain under `docs/global_modernization/v3/library` and `tools/codex/quality-gate`. V4 must not fork them.

## Activation gate

Reference TypeScript may move into `assets/scripts/qa` only inside `M03.3A/B`, after live owner inspection, exact-file mini-plan, tests and a bounded checkpoint. Default logging is disabled; release enablement is forbidden.
