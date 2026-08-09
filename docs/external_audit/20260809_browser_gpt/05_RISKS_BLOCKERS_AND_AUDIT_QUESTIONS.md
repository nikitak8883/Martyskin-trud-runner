# Риски, блокеры и вопросы для независимого аудита

## Blocking items

| Severity | ID | Fact | Required action |
| --- | --- | --- | --- |
| Blocked | B01 / M02.1 | Release target and signing identity are not decided. | User/product owner chooses direct APK or Play; records signing/backup policy. |
| Blocked | B02 / M02.7 | Approved immutable Web/Pages topology is absent. | User/repository owner approves topology before deployment. |
| Blocked | B03 / M12.7 | Cleanup is intentionally approval-gated. | Decide only after an accepted final build and dry-run. |
| High | R01 | `HEAD` and `origin/main` have no merge-base. | Perform a read-only Git topology audit before any merge/rebase/push. |
| High | R02 | `GameRoot` remains a 5,434-line concentration point. | Continue M03 strangler sequence; do not rewrite wholesale. |
| High | R03 | Final runtime evidence is from 2026-07-23. | Run a fresh baseline before claiming current runtime/release behaviour. |
| Medium | R04 | Input/pause has overlapping routes. | M03.4 must preserve timing and 220 ms debounce while converging ownership. |
| Medium | R05 | Deferred Cocos callbacks have no explicit reset/transition cancellation. | M03.3/M03.6/M03.7 must make cancellation/reset ownership explicit before legacy-path removal. |
| Medium | R06 | Assets dominate repository size and atlas/bundle governance is still pending. | Measure first in M04; avoid broad asset conversion. |
| Medium | R07 | Browser/Web remote main may include different history/content. | Treat remote as a separate baseline until reviewed. |

## Explicit decisions already made

- Cocos Creator 3.8.8 is the active engine baseline.
- Runtime QA default is emulator-only; physical-device testing needs a separate command.
- The sole configured remote is the GitHub repository named in the current-status document.
- `GameSessionState` is a contract around the sole writer, not a replacement game architecture.
- M11 PCG/DDA is conditional and explicitly non-release-blocking.
- External CodeRabbit review is advisory; no finding is automatically applied.

## Questions for the external auditor

1. Is the M03.3 → M03.7 seam order sufficiently safe, or should M03.3 lifecycle-token work be split before event logging?
2. Does a 5,434-line `GameRoot` with one scene justify earlier test seams before M04, or is M03 sequencing adequate?
3. Which M04–M10 packages can safely be grouped without losing rollback attribution and Android/Web parity?
4. Are the stated 38–58 engineering-week mandatory estimates credible under this acceptance model? If not, provide a revised itemized range and assumptions.
5. Does the absence of a merge-base warrant a new integration branch/worktree policy before any next code patch?
6. Which proof should be freshly regenerated first: static/contract, Web, Android emulator, or full parity baseline?
7. Are the current privacy boundaries adequate for external auditing, or is a smaller/more detailed source excerpt required?

## Non-risks that must not be misclassified

- The absence of raw Android screenshots from this ZIP is intentional; it is a privacy/size boundary.
- x86_64 emulator APK is not a failed release artifact; it is explicitly not a release artifact.
- `MTR_FSM_REJECT` count of zero in normal QA does not mean invalid transitions are untested; all invalid state pairs are covered by the pure exhaustive contract test.
- The historical M01.7 release-blocking report predates later M02/M03 evidence. It remains valid as a fail-closed policy proof, not as a current full release decision.

## Audit stop conditions

The external reviewer should stop and mark the result `blocked` rather than guessing if:

- source/roadmap files in the ZIP disagree on commit, state or dates;
- any requested claim depends on a build, raw log, credential or deployment not included;
- a recommendation would merge unrelated Git histories, publish a build, reveal a credential or delete artifacts;
- a proposed refactor spans more than one M03 responsibility without an explicit parity/rollback plan.
