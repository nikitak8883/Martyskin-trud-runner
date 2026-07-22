# Release-blocking QA summary

Date: 2026-07-22  
Work package: `M01.7`  
Release verdict: `BLOCKED`

## Decision

The release is not eligible for publication, installation claims, or Web/Android parity claims. The canonical `M2_PLUS` profile was evaluated against the current clean source and rejected the release because eight applicable mandatory evidence slots have no fresh bound report.

This is the expected fail-closed result. Completing M01.7 means the release decision is now explicit and machine-enforced; it does not mean the release itself passed.

## Evaluated source and profile

- Parent source commit: `c0d79e197833ed46ac9758586f9b96756462876b`
- Content version used for this decision: `mtr-m01-7-release-gate-20260722`
- Profile: `M2_PLUS`
- Profile config SHA-256: `B82025891085FEC4F0E207EAD89C3F6DD479C77730307AF26820D0297DB40EB3`
- Scope SHA-256: `EE9589DC6EFA765B9D5BBA8F6D931939D29018968F3E19CE29B88235DE3FB44D`
- Profile report SHA-256: `F46A10E9F1477856B82F1C7BE9E667245FBBE0F2FE148B0BF88812921C33DF4A`
- Profile run: `profile.m01-7.release-blocking-summary`
- Source clean: `true`
- Source matched scope and remained stable: `true`
- Schema engine: isolated `jsonschema 4.26.0`, Draft 2020-12

The detailed report is intentionally generated in the ignored `temp/m01-7/report.json` workspace. Its command, input/output hashes, decision and slot-level results are preserved here and in `docs/global_modernization/v3/M01/M01_7_VALIDATION_SUMMARY.json`; it can be reproduced without committing rotating evidence.

## Blocking mandatory evidence

| Cycle | Domain | Result | Finding |
| --- | --- | --- | --- |
| `pass_a` | static contract | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_a` | targeted Web | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_a` | targeted Android emulator | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_a` | regression/review | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_b` | static contract | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_b` | targeted Web | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_b` | targeted Android emulator | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |
| `pass_b` | regression/review | `BLOCKED` | `MANDATORY_EVIDENCE_MISSING` |

All four `focused_recovery` slots are explicitly `NOT_APPLICABLE` under reason code `no_runtime_patch_in_scope`. M01.7 changes only the release-decision boundary; it does not change gameplay, save data, signing, deployment, GameRoot, Web runtime, Android runtime, or failure-recovery seams.

## Fail-closed acceptance matrix

| Invalid evidence state | Required profile result | Verification |
| --- | --- | --- |
| Missing mandatory binding | `BLOCKED` | Actual M01.7 profile run and `test_missing_mandatory_binding_blocks_with_valid_report` |
| Failed mandatory child gate | `FAIL` or blocking result | `test_nonzero_mandatory_step_fails` |
| Skipped mandatory child gate | `BLOCKED` | `test_skipped_mandatory_step_blocks_without_starting` |
| Stale unchanged native report | `BLOCKED` | `test_unchanged_native_report_is_stale_and_blocks` |
| Stale bound child report | `BLOCKED` | `test_stale_child_report_blocks` |
| Unknown child schema | `BLOCKED` | `test_unknown_child_schema_blocks_instead_of_false_green` |
| Changed/reused child artifact | `BLOCKED` | `test_changed_child_artifact_blocks` |

The accepted hosted M01.6 suites ran the complete quality-runner tests on both Windows and Ubuntu: 47 discovered, 45 passed, 2 expected platform skips, 0 failures. That static success cannot satisfy or bypass any missing runtime slot listed above.

## Explicitly unproven

- current Web build and runtime behavior;
- current Android emulator build, install, launch, logcat, restart or soak behavior;
- one shared Web/Android content identity;
- arm64 device-valid APK, signing identity or upgrade compatibility;
- immutable Pages deployment and live-site parity;
- RC2 release-candidate evidence.

No physical device was used. No release artifact, signing key, deployment tree, Pages branch, game runtime, or asset was changed by M01.7.

## Reproduction

From the project root, regenerate a scope with the current source commit, matching profile-config SHA-256 and explicit condition decisions, then run:

```text
python tools/codex/quality-gate/bootstrap.py --entrypoint profile -- --project-root . --config docs/global_modernization/v3/M01/quality_gate.config.json --scope temp/m01-7/scope.json --output temp/m01-7/report.json
```

Exit code `2` with schema-valid status `BLOCKED` is the accepted M01.7 outcome while the eight mandatory evidence bindings are absent. A zero exit code is permitted only after every applicable mandatory slot has fresh, source-bound, schema-valid passing evidence.

## Next safe sequence

1. Establish the shared logical Web/Android content identity in M02.2.
2. Produce fresh M02.3 Web and M02.4 Android-emulator evidence from that same identity.
3. Produce M02.5 device-valid arm64 artifact evidence without physical installation.
4. Resolve the independent M02.1 signing/distribution decision before any release claim.
5. Bind two complete accepted cycles and rerun `M2_PLUS`; proceed to RC2 only after it passes.
