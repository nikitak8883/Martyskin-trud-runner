# M03.4 code and runtime review

Date: 2026-08-10  
Verdict: `PASS FOR BOUNDED INPUT ROUTING / RELEASE REMAINS BLOCKED`

## Review boundary

- Runtime mutation is limited to routing existing jump, glide, dash and pause entrypoints through one adapter.
- Physics methods, session transition writer, save format, assets, UI composition, collision order and power-up ownership are unchanged.
- New QA infrastructure is limited to a guarded local Web matrix CLI and corrected Android-emulator interaction sequencing.
- Physical devices, production signing, Pages deployment and cleanup approval are outside this package.
- Unrelated workspace, agent-monitor, Tasks, sticker-pack and project-library changes were excluded from review and staging.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Multiple pause surfaces could debounce independently | Prevented: all keyboard, global-touch, HUD, pause-zone and QA routes share the adapter's fixed `220 ms` clock. |
| Glide could retain state after reset or key/touch release | Prevented: all releases use `releaseGlide`, reset has a typed `session_reset` source and one callback owns the mutable value. |
| Adapter could become a second physics owner | Rejected: callbacks invoke the existing `GameRoot` physics methods; the adapter stores only debounce/glide routing state. |
| Listener count/order could drift | Rejected by structural validation: six global listener pairs and one pause-zone pair remain unchanged. |
| Web matrix remained callable only as anonymous code | Fixed: `Run-MtrWebMatrixQa.js` provides contained local paths, Playwright discovery, atomic report output and fail-closed cleanup. |
| Android recovery initially missed dash pose | Fixed in QA sequencing: dash is asserted directly after gameplay-ready, before collision can clear its short timer; fresh cold recovery passed. |
| Local review suggested the new timing could be flaky | Rejected after exact marker waits plus a complete cold recovery, restart loop and soak passed with no missed action. |
| Local review claimed malformed static-gate JSON | Rejected as false: the config parsed and the canonical 17-step gate passed repeatedly. |

## Validation evidence

- Pure adapter behavior: `10/10 groups PASS`.
- Structural integration: one adapter, one glide writer, fourteen dispatch routes, three release routes, listener topology preserved.
- Canonical development static gate: `17/17 PASS`, zero findings.
- Web Pass A / Pass B / recovery: each `34/34 PASS`, interaction and restart `10/10` PASS.
- Android Pass A / Pass B: each matrix `28/28 PASS`; interaction, custom-name persistence, restart `10/10` and soak PASS.
- Android focused recovery after `pm clear`: action latencies all below `500 ms`, restart `10/10`, soak `30.156 s`, zero process losses and unexpected diagnostics.
- Fresh QA APK: `142892688` bytes, SHA-256 `3C692EA18959CE18FBFE310C6322760340274EE3ACB6CCDA5D62E55E2F63FF79`.
- Canonical M2_PLUS: `12/12 PASS`, zero findings; profile SHA-256 `D2CA3C0FE56D1DEA198584EC80D7CF4E440667B0DB38BD430B7A27B530DE3EB4`.

## Hygiene and residual limits

- No new TODO/FIXME/HACK/XXX/debugger path is accepted in the bounded diff.
- The corrected failed Android attempt remains only as evidence under ignored `temp`; it is not shipped.
- QA builds and screenshots are not production artifacts.
- Collision callbacks and power-up lifecycle remain explicitly owned by M03.5 and M03.6.
- Release remains blocked independently by signing/distribution, immutable Web deployment and final cleanup approval.

## Verdict

M03.4 is safe to checkpoint. M03.5 may begin from this input boundary without carrying a duplicate handler, alternate debounce or second gameplay-state owner.
