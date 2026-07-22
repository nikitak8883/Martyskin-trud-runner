# M02.3 code-review report

Date: 2026-07-22  
Verdict: `PASS FOR BOUNDED M02.3`

## Diff boundary

- exact `playwright-core` dev dependency plus npm lockfile;
- existing file-based Web matrix/soak runner changed from an undeclared `playwright` dependency to the pinned runtime;
- deterministic absolute browser executable resolution and embedded runner metadata;
- M02.3 reports and execution-index updates.

No gameplay source, scene, runtime asset, Cocos build config, Android project, signing material, Pages tree or production secret changed.

## Review findings

| Concern | Result |
| --- | --- |
| Undeclared Playwright made the harness non-reproducible | Fixed with exact `playwright-core@1.61.1` and lockfile integrity. |
| Browser selection could silently use a relative project path | Fixed: only absolute existing candidates are accepted. |
| Managed browser cache may be absent | Fail-closed error names the explicit env override and install command; system Chrome/Edge paths are bounded fallbacks. |
| Runtime summary could omit tool identity | Fixed: package, package version, executable, browser version and Node version are embedded. |
| A harness error could become a false PASS | Prevented: launch, navigation, function, matrix or soak failure sets non-zero exit; summaries are written only after the function returns. |
| Product warnings could be hidden | Only the exact known ReadPixels driver warning is ignored by the existing matrix; all other warnings/errors block PASS. |
| Patch could alter packaged content without identity bump | Prevented by scope: only QA tooling, lockfile and reports changed. |
| External reviewer could be misrepresented | CodeRabbit failure is recorded explicitly; no CodeRabbit result is claimed. |

## Independent review

- `local_worker.review_diff`, profile `coding_efficiency`: verdict `accept`.
- Suggested portability edge case was addressed before acceptance.
- Heavy local model was explicitly unloaded and verified absent after review.
- CodeRabbit CLI: unavailable because the official Windows route requires WSL; WSL is not installed. This is a reviewer availability gap, not a product failure.

## Verification after the review fix

- `node --check tools/codex/run_web_playwright_function.js`: `PASS`.
- `npm ci --ignore-scripts --no-audit --no-fund`: `PASS`, one exact package.
- post-review Web matrix: `34/34 PASS`, interactions `PASS`, restart `10/10 PASS`.
- 300-second soak: complete, zero console warnings/errors.
- development static gate: `8/8 PASS`, zero findings.

Final clean-source and hosted acceptance will be recorded after the bounded M02.3 commit is published. Release remains blocked.
