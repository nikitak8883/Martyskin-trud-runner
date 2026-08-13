# M03.7A code and runtime review

Date: 2026-08-13  
Verdict: `PASS FOR BOUNDED OWNERSHIP SEAM / RELEASE REMAINS BLOCKED`

## Review boundary

- UI drawing callbacks may emit typed intents but may not directly navigate, start a level, preview/confirm a skin or operate the developer gate.
- The lifecycle owner may schedule and cancel callbacks and listeners but may not own gameplay rules, rendering or persistence.
- Existing mutation methods are retained behind the bridge so M03.7A remains rollback-safe. Their hidden-reference audit and selective removal belong to M03.7B.
- QA routes are debug/developer/query gated. Android evidence is emulator-only.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| UI callbacks directly called transition, level-start, skin and developer-gate methods | Fixed: all affected callbacks now emit one of six validated intents through `GameplayUiIntentAdapter`. |
| Skin preview wrote `pendingSkinSelection` inside draw code | Fixed: preview is an intent; mutation and preload/voice side effects remain behind the GameRoot bridge. |
| Listeners were registered in multiple statements with no single cleanup owner | Fixed: eight registrations now pass through `GameRuntimeLifecycleOwner.registerListener`; destroy invokes all matching unsubscriptions. |
| Scheduled work could survive a transition into an unrelated screen | Fixed: every accepted changed transition cancels session callbacks; a pending start-gate survival case found during review was corrected and retested. |
| A stale session callback could execute after reset/retry | Prevented by epoch capture plus cancellation. Unit, Web and Android probes verify session cancellation and stale rejection. |
| Component verification work should survive ordinary pause/resume | Preserved as a distinct component scope and proven by the exact `componentSurvived=1` runtime marker. |
| Owner keys might imply callback replacement semantics | Rejected as a defect: wrappers are held by object identity in a `Set`; keys are observability labels and do not deduplicate callbacks. |
| Reviewer suggested missing touch-cancel cleanup | Rejected after source verification: the matching `TOUCH_CANCEL` unsubscribe is present with the other seven listener removals. |
| Reviewer suggested missing UI actions | Rejected: all six scoped actions are declared, behavior-tested, structurally scanned and exercised by runtime QA. |

Accepted findings: `1` transition-cleanup gap. Fixed findings: `1`. Open findings: `0`.

## Cross-platform contract review

```json
{
  "skill": "android-web-contract-check",
  "verdict": "approve",
  "summary": "Web and Android use the same six-action adapter, lifecycle owner, exact eight-check marker and startup-query contract.",
  "evidence": [
    "Web ownership A/B exact 8/8",
    "Android-emulator ownership A/B/recovery exact 8/8",
    "15-level startup-query parity PASS",
    "M2_PLUS 12/12 PASS"
  ],
  "actions": ["Proceed to bounded M03.7B hidden-reference and rollback proof"],
  "risk": "low",
  "requires_worktree": false,
  "requires_model": "none"
}
```

## Hygiene and residual limits

- No conflict markers, unresolved TODO/FIXME/HACK markers, direct scoped UI mutations or unowned scheduler/listener routes remain in the touched scope.
- Generated builds, screenshots, local-model outputs and detailed runtime JSON stay ignored and are not staged.
- QA localhost ports `18767` and `18768` are closed.
- Unrelated repository-root changes remain preserved and excluded.
- Historical reports are immutable; no old checkpoint was used as fresh acceptance evidence.
- M03.7B may delete only paths proven superseded and rollback-safe. M12.7 remains the separate owner-selected final cleanup gate.

## Verdict

M03.7A is safe to checkpoint. No accepted code-review finding remains open inside the unit.

