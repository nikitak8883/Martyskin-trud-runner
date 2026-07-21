# M00 Git topology decision

Date: 2026-07-19  
Status: accepted for the source-freeze checkpoint

## Decision

The workspace keeps two explicit Git authorities:

1. `C:\Projects\Monkey Work` is the primary source repository for the Cocos project and engineering documentation.
2. `C:\Projects\Monkey Work\_github\Martyskin-trud-runner` is the Web deployment repository and remains pinned in the parent as a formal Git submodule.

The missing `.gitmodules` mapping is restored with the existing public remote:

```text
https://github.com/nikitak8883/Martyskin-trud-runner.git
```

The source checkpoint will update only the parent gitlink to the clean deployment HEAD `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`. It will not stage any child-repository files.

## Evidence

- Parent root: `C:\Projects\Monkey Work`
- Parent branch before freeze: `main`
- Parent HEAD before freeze: `76bac6c2e9f5e112489aa8a922dce48c3fd9970b`
- Parent remote: absent
- Existing index entry: mode `160000`, commit `5b3e1dbe858a58f377e7a316a3ace0211286e743`
- Pages root: `C:\Projects\Monkey Work\_github\Martyskin-trud-runner`
- Pages branch: `main`
- Pages HEAD: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
- Pages status: clean and aligned with `origin/main`
- Nested Git roots found: exactly two
- Previous failure: `git submodule status` returned `no submodule mapping found in .gitmodules`

## Operating policy

- Parent staging must use explicit pathspecs.
- Never run `git add .` from the parent root.
- Parent commits may contain `.gitmodules` and the submodule gitlink, never the Pages working-tree blobs.
- Web deployment changes are committed and pushed from the Pages repository only.
- A source commit does not authorize a Pages push.
- Until a primary source remote is approved, every accepted source checkpoint receives an annotated tag and an offline Git bundle.
- When a primary source remote exists, M02 may replace this topology with a source-build-to-Pages-artifact workflow after parity validation.

## Rejected alternatives

### Leave the invalid gitlink unchanged

Rejected because clone/submodule commands fail and the deployment dependency is ambiguous.

### Remove the gitlink and silently ignore the nested repository

Rejected because the source checkpoint would no longer pin the exact Web deployment state.

### Move the Pages repository now

Rejected for M00 because moving a working repository is broader than the source-freeze seam and adds avoidable rollback risk.

## Rollback

Revert the bounded M00 checkpoint. This restores the previous gitlink and removes the `.gitmodules` mapping without deleting or rewriting the child repository.

## Deferred decision

The preferred long-term Actions artifact deployment remains blocked until a primary source remote and its publication policy are explicitly approved.

## 2026-07-21 source-publication amendment

The previously deferred source remote is now approved with one repository URL only:

```text
https://github.com/nikitak8883/Martyskin-trud-runner.git
```

Branch ownership is intentionally separated inside that repository:

- `main` remains the published Web/Pages artifact line;
- `mtr-source-v3` is the canonical source and engineering line;
- the historical `codex` branch is left untouched.

The local parent repository contains a legacy tracked backup bundle larger than GitHub's per-file limit. It is not project source and must never be pushed. Source publication therefore uses the history-preserving `MTRCocosCreator` subtree, where the project becomes repository root. This also places `.github/workflows/` at the valid GitHub Actions entry point. No force push, remote history rewrite, Pages mutation, or backup deletion is authorized by this amendment.
