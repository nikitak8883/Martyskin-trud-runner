# M01.5 code-review report

Дата: 2026-07-21  
Итог: `PASS FOR BOUNDED M01.5 / RELEASE BLOCKED`

## Scope reviewed

- dependency-free retention classifier, reviewed config and canonical CLI;
- index/root/path containment, Windows invalid/reserved names and reparse handling;
- existence, size, modification-time and unindexed-file reconciliation for 801 files;
- protected/recent/rotatable precedence and full classification coverage;
- exact output allowlist, protected-input/Git/corpus revalidation and atomic write;
- negative tests and M01.2–M01.4 regression;
- proof that M01.5 exposes no evidence delete, move or apply path; failed atomic-report temp cleanup is separately bounded.

## Confirmed findings and fixes

| Finding | Severity | Resolution |
| --- | --- | --- |
| Free `--output` could target an unrelated project file outside evidence | high | Policy and CLI must now equal the single reviewed M01.5 report path; output remains project-contained and outside evidence/protected inputs. |
| Policy/index/accepted links were hashed initially but not revalidated at the atomic-write boundary | high | Added final hash revalidation plus Git HEAD and a second complete corpus metadata pass. |
| `is_symlink()` alone did not explicitly reject every Windows reparse point | high | Every existing path component now checks `FILE_ATTRIBUTE_REPARSE_POINT`; resolved containment remains mandatory. |
| Same-size normal drift was not visible without a 1.05 GB rehash | medium | Index `modifiedAt` is reconciled within a 1 ms tolerance in both corpus passes; content rehash remains explicitly false and documented. |
| Historical rollback ZIPs and replay scripts initially classified as rotatable review candidates | high | `*backup*` and replay/harness source extensions are protected; the canonical corpus was regenerated and audited for anchor-like rotatable names. |
| Windows-invalid/reserved output or index names could fail late | medium | Added control-character, `< > " | ? *`, trailing-dot/space and CON/PRN/AUX/NUL/COM/LPT rejection. |

## QA and reviewer evidence

- M01.5 unit suite: 13 discovered, 12 passed, 0 failed, 1 expected Windows privilege skip.
- Canonical corpus: 801 indexed = 801 discovered; missing/size/mtime/unindexed counts are all zero.
- Classification: 68 protected, 207 retained recent, 526 rotatable review-only; no deletion occurred.
- Fixed-identity rerun produced byte-identical JSON.
- Isolated M01.3–M01.4 suite: 46 discovered, 44 passed, 0 failed, 2 expected platform skips.
- Direct M01.2 contract regression: PASS.
- First local-worker review raised concrete output/revalidation concerns; each was fixed and retested.
- Broad Qwen3.6 review exhausted its bounded output and returned no validated final content; it is recorded as unavailable, not PASS.
- CodeRabbit CLI could not be installed because its official installer rejects native Windows and WSL is absent; no CodeRabbit result is claimed.
- Final Codex line review found no remaining blocking defect in the bounded patch.

## Residual boundaries

- M00 SHA-256 values are trusted after two full path/size/mtime reconciliation passes; M01.5 intentionally does not reread 1.05 GB of payload data.
- Windows symlink creation is unavailable without privilege, so that mutation test is skipped; direct reparse detection and resolved containment execute in production code.
- `rotatable` is not deletion approval. Backup/rollback manifest, explicit approval and post-cleanup rebuild/QA remain mandatory in M12.
- Content identity remains unavailable until M02.2.
- No game runtime, build, Web runtime, Android target, deployment, signing or physical device was touched.

No blocking defect remains inside the bounded M01.5 implementation.
