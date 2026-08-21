# M04-C-PILOT code, contract and QA review

Date: `2026-08-21`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- The `objective_npc` Cocos Auto Atlas descriptor and metadata.
- Runtime pilot scheduling/metrics on Web and Android native.
- Baseline/candidate artifact comparator, visual-parity checker and manifest validator.
- Atlas schema, canonical manifest, regression tests and static-gate wiring.
- Project-only roadmap, rollback and checkpoint records; no production release or physical-device scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| The comparator accepted reports without proving baseline/candidate runtime identity, source UUID transition, APK identity or finite positive metric envelopes | Fixed fail-closed. The comparator now performs `63` checks and rejects a mutated atlas identity in a negative behavior test. |
| The manifest validator could throw on malformed evidence JSON and did not cross-check durable acceptance totals against the measurement contract | Fixed. It now emits structured findings; regression coverage includes malformed JSON and count drift. |
| Local advisory questioned `sys.isNative`, schedule retry reset, a native null-check and the PowerShell JSON access path | Rejected after direct source tracing, targeted tests and completed Web/Android runs; none reproduced. |
| Local advisory reported a missing brace in the comparator | Rejected by exact parse/execution and the `63/63` positive plus mutated-identity negative run. |

Accepted and fixed findings: `2`. Rejected non-reproducible findings: `4`. Open findings: `0`.

## Independent and direct evidence

- Three bounded local coding reviews ran sequentially; Codex reconciled every suggestion against source and runtime evidence.
- Local model lifecycle cleanup is verified (`cleanup_verified=true`); no coding/heavy model remains resident from review.
- Comparator: `63/63 PASS`; mutated atlas identity: rejected as expected.
- Manifest validator tests: `11/11 PASS`; metric instrumentation test: PASS.
- Post-review static gate: `26/26 PASS`, findings `0`.
- Fresh Web and Android-emulator builds passed two complete matrices each, interaction/restart paths and representative visual inspection.

## Residual limits

- Acceptance applies only to `objective_npc`; it does not close aggregate work package `M04.5` or authorize batch repacking.
- Web already collapsed the ten sources through Dynamic Atlas at baseline, so its accepted criterion is non-regression; Android supplies the material draw-call gain.
- The x86_64 debug APK is emulator QA evidence only, not a production arm64 release.
- Product release remains blocked by `M02.1`, `M02.7` and `M12.7`.
