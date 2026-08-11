# M03.5 code and runtime review

Date: 2026-08-11  
Verdict: `PASS FOR BOUNDED COLLISION ROUTING / RELEASE REMAINS BLOCKED`

## Review boundary

- Runtime mutation is limited to wrapping eight existing collision outcomes in one synchronous typed router and consuming them in `GameRoot`.
- Collision detection, loop order, physics constants, score/balance values, storage schema, UI composition and content assets are unchanged.
- Native warmup deferral is included because the fresh M03.5 Android build exposed product slow-load warnings before the first level; current-level critical loading remains gated and non-critical utility/skin warmup starts with gameplay.
- QA infrastructure adds a guarded Web collision query, an emulator-only Android collision runner and deterministic failure evidence for the existing interaction harness.
- Physical devices, production signing, Pages deployment and destructive cleanup are outside this package.
- Unrelated workspace, agent-monitor, Tasks, sticker-pack and project-library changes are excluded from review and staging.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Event routing could reorder legacy effects | Rejected by structural validation and runtime markers: eight detection slots and eight consumer cases preserve the inventory order; Web and Android report the exact same sequence. |
| A router callback could become a second state owner | Rejected: the router only validates, stamps and synchronously emits immutable data; all gameplay mutation remains in `GameRoot.applyCollisionEvent`. |
| Payload or event data could be mutated after dispatch | Prevented: payload is cloned and frozen, then the complete event is frozen before callback invocation. |
| Callback recursion could interleave sequence/order | Prevented: reentrant routing throws and the `finally` path always releases the dispatch guard. |
| Callback failures could be hidden or retried | Prevented: errors propagate synchronously; the router does not retry, batch or queue. |
| QA collision execution could leak into release | Prevented: capture and execution require `DEBUG`, developer mode and explicit `mtr_qa_collisions=1`; release Web produced no QA event stream. |
| Native startup generated utility/skin slow-load warnings | Fixed by retaining critical current-level admission and deferring non-critical utility/selected-skin warmup until gameplay start; both fresh Android cycles then had zero product warnings. |
| First cold recovery lost evidence before the summary file existed | Fixed: every terminating harness error now persists JSON, logcat, input/window dumps and screenshot. The reproduced failure bundle was retained. |
| Implicit `adb input tap` intermittently targeted `ActivityRecordInputSink` after rotation | Fixed: touch injection declares source `touchscreen`, display `0` and current logical coordinates. Fresh cold recovery passed. |
| Local advisory review hypothesized changed side-effect order, reentrancy and mutable payloads | Rejected against source and tests: all three properties are explicitly guarded and runtime A/B/recovery evidence is green. |

## Validation evidence

- Pure collision router behavior: `10/10 groups PASS`.
- Structural integration: 8 kinds, 8 production routes, 8 QA routes, one router, one exhaustive consumer, exact legacy order.
- Canonical development static gate: `18/18 PASS`, zero findings; SHA-256 `4CF2C4FD31084C2B7587088501AA599CCBA6835DD963060F861E91608EF6DD27`.
- Web Pass A / Pass B / recovery: each `34/34 PASS`, interaction and restart `10/10` PASS.
- Android Pass A / Pass B: each matrix `28/28`; interaction, custom-name persistence, restart `10/10` and soak PASS.
- Android focused recovery after `pm clear`: explicit display-0 touchscreen injection, restart `10/10`, soak `30.378 s`, zero process losses and unexpected diagnostics.
- Fresh QA APK: `142896264` bytes, SHA-256 `5FD85C440C41BB0190126CBF90C506FF7F9C39108565C813E05A7A6CE9EBC6C1`.
- Canonical M2_PLUS: `12/12 PASS`, zero findings; profile SHA-256 `B47EF43DF95BFD0D7FA21727A973AAE0A8A449D538C67546BF654894D20408FA`.

## Hygiene and residual limits

- No new TODO/FIXME/HACK/XXX, conflict marker, debugger path, cache or generated build output is accepted in the tracked diff.
- Corrected failed Android evidence remains only under ignored `temp`; it is excluded from runtime/package artifacts.
- QA builds, screenshots and debug markers are not production artifacts.
- Power-up lifecycle remains explicitly owned by M03.6; M03.5 does not alter timers, duration values or balancing.
- Release remains blocked independently by signing/distribution, immutable Web deployment and final cleanup approval.

## Verdict

M03.5 is safe to checkpoint. M03.6 may begin from this typed collision boundary without carrying a second detector, asynchronous event queue or alternate side-effect owner.
