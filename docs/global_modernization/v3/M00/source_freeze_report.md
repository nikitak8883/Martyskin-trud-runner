# M00 source freeze report

Status: `PASS`

## Outcome

The previously uncommitted accepted game line now has an immutable source checkpoint, explicit Pages topology, deterministic content fingerprint, two offline bundles and a successful restore rehearsal.

- Source commit before M00: `76bac6c2e9f5e112489aa8a922dce48c3fd9970b`
- Frozen source commit: `12670452ae4580ef5c685ff986476daf91522978`
- Frozen source tree: `9faa768c9b81f94b7745c917b6d7d49b7cef884c`
- Branch: `codex/mtr-source-freeze-v3`
- Annotated tag: `mtr-source-freeze-v3-20260719`
- Tag object: `d7042a1ff424259f11e958592daab7af20dfc610`
- Pages gitlink: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
- Source manifest: 4170 files / 925653734 bytes / aggregate SHA-256 `E3C72CE3D41BAA9EA54D9941A6A91312DFD38A94112C99ADC02D935915A8EDFD`

The parent source root still has no remote. The complete source and Pages bundles are therefore the approved local backup surface. No push was attempted.

## Source hygiene

The pre-freeze dirty-tree partition covered all 633 project entries with no manual-review residue. The first full committed-tree manifest then exposed evidence inherited from older commits. Before the tag was created, M00 removed 402 evidence files / 545794907 bytes from the index only:

- non-Markdown and nested raw evidence under `docs/qa/`;
- old `docs/restore/` sessions;
- two skin contact-sheet evidence files.

All files remain physically available on this machine and are protected by scoped ignore rules. Immediate `docs/qa/*.md` checkpoint summaries remain source-controlled. No APK, AAB, archive, signing material, secret or Tasks package is present in the frozen source tree.

## Git topology

The workspace has exactly two Git roots. The formerly invalid mode-160000 gitlink now has a valid `.gitmodules` mapping to the existing public Pages remote. The parent commit contains only `.gitmodules` plus the gitlink, never deployment-tree blobs.

Long-term source-build-to-Pages Actions deployment remains deferred until a source remote is approved and M01/M02 establish reproducible build/parity gates.

## Validation cycles

1. Classification/scope: all dirty entries partitioned; staged scope and secret/build/evidence deny-list passed.
2. Static/contracts: TypeScript, config, 1528 assets, 576 skin frames, 14 UI IR screens, JSON/YAML/Python/PowerShell/JS syntax passed.
3. Git/topology: `.gitmodules`, gitlink, Pages clean state, `git diff --check`, annotated tag and both bundle verifications passed.
4. Restore: initial failures were fixed and the final short-path/longpaths restore repeated manifest, topology and all static gates successfully.
5. Post-execution plan/index audit: 13 modules, 95 unique work packages, zero dependency cycles, zero invalid statuses, M00 complete and M01.1 ready.
6. Final anchor/regression audit: 10/10 hash assertions across 8 artifacts, both bundle verifications, config, TypeScript and topology passed.

## Logged failures and permanent measures

- Skill Compass incorrectly ranked `gh-fix-ci`; Codex rejected it because no CI failure existed and used retrieval-first/safe-patch flow.
- `local_worker.retrieve_context` hung again; it was bounded, terminated, and its empty cache tail removed. Direct local retrieval remains the fallback until the router is fixed.
- Imported Markdown hard breaks triggered `git diff --check`; `.gitattributes` now scopes the intentional Markdown rule, while five real extra EOF blanks were removed.
- The first topology verifier indexed one-character strings; array normalization was fixed and retested.
- One `git add` was invoked from the project directory with a root-relative path; it staged nothing, was logged, and was repeated from the Git root.
- The first JS syntax command placed `--check` after the file; the corrected contract is `node --check <file>`.
- The first mixed syntax harness decoded PNG as UTF-8; extension filtering now occurs before text reads.
- An unquoted PowerShell `HEAD^{tree}` was parsed incorrectly; literal quoting is now mandatory.
- Full-tree manifesting exposed preexisting tracked raw evidence; source-only ignore and index-retention policy now prevents recurrence.
- Standard Windows restore hit MAX_PATH; short restore roots plus `core.longpaths=true` are now mandatory.
- Fresh TypeScript validation lacked generated Cocos declarations; M01 must seed or generate the ignored five-file Cocos type contract before invoking `tsc`.
- Final review found `core.autocrlf`-dependent working bytes for two historical JSON indexes. The evidence anchor now separates canonical Git-byte SHA-256 from the recorded Windows working-tree SHA-256, and scoped `.gitattributes` rules keep future M00/current-audit machine records LF-stable.

## Rollback

- Runtime/source checkpoint rollback: switch to parent commit `76bac6c2e9f5e112489aa8a922dce48c3fd9970b` or revert the bounded source checkpoint.
- Frozen state recovery: clone the source and Pages bundles using the commands in `restore_rehearsal_report.md`.
- Local evidence was never deleted; removing the new ignore policy and re-adding selected evidence is possible, but is not recommended for source history.

## Completion record

```yaml
module_id: M00
status: pass
source_commit_before: 76bac6c2e9f5e112489aa8a922dce48c3fd9970b
source_commit_after: 12670452ae4580ef5c685ff986476daf91522978
content_manifest_version: mtr-v3-freeze-12670452ae45
files_created:
  - docs/global_modernization/v3/M00/source_content_manifest.json
  - docs/global_modernization/v3/M00/evidence_anchor.json
  - docs/global_modernization/v3/M00/restore_validation_summary.json
  - docs/global_modernization/v3/M00/restore_rehearsal_report.md
  - tools/codex/build_source_content_manifest.py
qa_results:
  - D4 classification PASS
  - static/contracts PASS
  - Git/topology PASS
  - offline restore PASS
open_findings:
  - source remote absent
  - M01 fail-closed quality runner not implemented
  - M02 release recovery and artifact parity not implemented
rollback_available: true
next_safe_action: M01.1 validator and harness inventory
```
