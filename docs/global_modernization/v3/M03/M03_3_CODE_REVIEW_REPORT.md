# M03.3C code and runtime review

Date: 2026-08-10  
Verdict: `PASS FOR BOUNDED DEV-EVENT RUNTIME / RELEASE REMAINS BLOCKED`

## Review boundary

- Runtime change is limited to one observational adapter around the existing `GameRoot` transition/reset writer.
- `GameRoot.state` remains the only mutable session-state source and `transitionTo` remains its only writer.
- Release Web binds event storage and console output to the Cocos `DEBUG` compile-time macro and emitted zero development events.
- Input ownership, collision order, power-up ownership, save format, assets, UI and scenes remain outside M03.3C.
- Android runtime validation used only QEMU serial `emulator-5554`; no physical device was addressed.
- Unrelated workspace, agent-monitor, Tasks, sticker-pack and project-library changes were excluded from review and staging.

## Code findings and dispositions

| Risk | Result |
| --- | --- |
| Second gameplay-state owner | Rejected: adapter observes typed results and never writes `GameRoot.state`. |
| Duplicate transition event | Rejected: the three mutually exclusive accepted/idempotent/rejected branches each append once. |
| Reset/epoch mismatch | Rejected: every reset advances one epoch and emits changed/begin/end in deterministic order; nested or stale close fails closed. |
| Stale scheduled QA callback | Rejected for the four touched session callbacks: each captures the current lifecycle epoch and is suppressed after reset/destroy. |
| Release telemetry spam | Rejected by compile-time `DEBUG`; release Web runtime produced zero event and QA markers. |
| Unbounded/private payload | Rejected: capacity `128`, export bound `32768` bytes and small allowlisted scalar payloads only; no player name, storage value or Cocos object is passed. |
| Ambiguous reset-loop input | Accepted and fixed: the query now accepts only canonical decimal strings `1` through `10`, then retains numeric bounds checking. |
| Cocos nonzero exit false failure | Accepted and fixed: exit `36` is caller-allowlisted only for Cocos and becomes logical success only with bytes appended after launch that match a terminal build marker. All other nonzero exits remain fail-closed. |
| Incomplete Web output accepted | Rejected after fix: four required non-empty artifacts and favicon post-processing are mandatory before `buildFinished=true`. |

## Advisory review

- Bounded local `review_diff` analyzed only the project diff plus six new files. It reported two GameRoot concerns.
- One concern was rejected after source reconciliation because `GameRootResetReason` is already a closed four-value string union.
- One concern was accepted as input-contract hardening and fixed with canonical `1..10` decimal validation plus Node/Python structural assertions.
- A second heavy local review exceeded its 300-second tool deadline and returned no findings payload. It was not treated as evidence; the model later unloaded automatically and `lemonade_verify_model_unloaded` confirmed `loaded=false`.
- No local-model suggestion was auto-applied. Codex performed the final line review and acceptance.

## Validation evidence

- Adapter behavior: `10/10` Node groups PASS; TypeScript 5.8.2 / ES2015.
- Structural validator: PASS; one state writer, one adapter, four guarded callbacks, four typed reset reasons.
- Complete project TypeScript no-emit: PASS using the Cocos Creator 3.8.8 bundled compiler.
- Entrypoint-router self-test: stale marker rejected, current marker accepted, exit `7` rejected, allowlisted exit `36` accepted only with current marker, overflow rejected.
- Android toolchain regression: `35` PowerShell groups and Python validator PASS.
- Execution-plan validator: current plan PASS and `10/10` unit tests PASS; completed units retain closed-package provenance, while any non-complete unit referencing a closed package still fails with `COMPLETE_SOURCE_REPLANNED`.
- Canonical pre-commit quality gate: `15/15 PASS`, zero findings, source stable; run `qg.20260810123750.e72aea24a4c4`, report SHA-256 `9F4E3457B94DC2A2B3698BF4EDEBBD73EA01F303CE0D216076DE7A0EDB82C298`.
- Web release build: raw Cocos exit `36`, terminal marker current, required artifacts valid, wrapper exit `0`.
- Web event parity: DEBUG `33/33` unique and exact marker; release `0` events; diagnostics clean.
- Web full matrix: `34/34`, portrait PASS, interaction PASS, restart `10/10`.
- Android-emulator event parity: `33/33` unique and exact marker, zero failures/fatals.
- Android-emulator matrix: `28/28`; touch flow, custom name persistence and restart `10/10` PASS; 30.598-second targeted soak had zero process loss and no unexpected diagnostics.
- Fresh x86_64 QA APK: `142891427` bytes, SHA-256 `B2404E4A0DEAE5C8879576E87F39D34C692BBBA1E8BA191A991C4E998015C34C`.

## Hygiene and residual limits

- No TODO/FIXME/HACK/XXX/debugger residue and `git diff --check` is clean.
- Superseded transient evidence and the 123.9 MB temporary Web debug build were removed; final summaries and reproducible harnesses were retained.
- The event layer is local development diagnostics, not a semantic PII detector or production telemetry system.
- Guards cover only the four deferred callbacks touched by M03.3C; broader input/collision/power-up ownership remains M03.4-M03.6.
- Production signing and immutable Pages deployment are unresolved, so release remains blocked.

## Verdict

M03.3C closes source work package M03.3 and is safe to checkpoint. M03.4 may start from the accepted single-writer/session-epoch boundary.
