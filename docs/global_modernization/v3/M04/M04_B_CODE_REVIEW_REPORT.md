# M04-B code, contract and QA review

Date: `2026-08-21`  
Verdict: `PASS / OPEN FINDINGS 0`

## Review boundary

- `tools/validate-assets.py`, its fixtures and regression tests.
- Contact-sheet generator, schema, canonical index and static-gate integration.
- Project-only roadmap, rollback and checkpoint records.
- Fresh Web and Android-emulator evidence; no physical-device or deployment scope.

## Findings and dispositions

| Finding | Disposition |
| --- | --- |
| Some recursive reads could follow a source or metadata symlink/junction outside the allowed root | Fixed with resolved-path guards before reads; direct containment and escape regression cases pass. |
| Contact-sheet generation could leave obsolete generator-owned pages after category/page-count changes | Fixed with bounded exact-owner cleanup under the selected output root; unrelated files are retained and tested. |
| Generator accepted `.png`/`.jpg` while the validator also governed `.jpeg` | Fixed by using the same three extensions and adding a classifier regression case. |
| Initial full post-review static gate hit a one-off Windows `WinError 5` in the pre-existing atomic-writer self-test | Preserved as failure receipt; isolated rerun passed immediately and the complete second gate passed `25/25`. No M04-B or product defect reproduced. |
| Local advisory questioned `Path.resolve()`, alpha `getbbox()` and Cocos `uuid@submeta` semantics | Rejected after direct reconciliation: resolved paths cover Windows junction/symlink targets, a zero alpha plane is exactly the `None` bbox case, and lowercase hex submeta suffixes are the Cocos 3.8.8 contract. |

Accepted and fixed findings: `3`. Rejected non-reproducible findings: `3`. Open findings: `0`.

## Independent and direct evidence

- Local coding reviewer accepted the contact-sheet/schema/tests/gate diff with no findings.
- Validator review findings were manually reconciled against exact functions and regression tests; confirmed path issues were fixed before the second review.
- Local coder lifecycle cleanup is verified; only the embedding helper remains loaded.
- M04-B unit/contract tests: `14/14 PASS`.
- Strict asset scan: blockers `0`.
- Static gate: final `25/25 PASS`, findings `0`.
- Web and Android-emulator runtime evidence passed in full; representative screenshots were visually inspected.

## Residual limits

- Contact-sheet PNG/HTML files are reproducible local temp evidence and remain ignored.
- The canonical 1.28 MB JSON index is intentionally complete and tracked; no binary snapshot is used as recovery context.
- The APK is deterministic x86_64 debug emulator evidence, not a production arm64 release.
- M04-C must begin with one measured pilot and cannot infer authorization for broader repacking.
