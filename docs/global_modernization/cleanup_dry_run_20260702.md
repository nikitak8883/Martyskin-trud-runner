# Cleanup dry-run — 2026-07-02

Generated: 2026-07-02 15:44 +03:00  
Mode: dry-run only  
Deletion performed: no

## Purpose

Identify old tails, temporary files, generated junk, and stale artifacts before future modernization modules. This report does not authorize deletion by itself.

## Safe-to-review cleanup candidates

| Candidate | Type | Suggested action | Risk | Notes |
| --- | --- | --- | --- | --- |
| `tools\skins\__pycache__\inspect_skin_pngs.cpython-313.pyc` | Python cache | delete after approval | low | Generated cache, not source. |
| root `creator-*.log` files | historical build logs | archive or prune after evidence review | medium | Some may be unique build evidence; preserve release-relevant logs. |
| root `20260630-baseline-web.log` | historical QA log | keep until Module 1/9 baseline is superseded | medium | Useful baseline. |
| `Tasks\4\_unpacked_20260702_145527` | unpacked input | keep for now | low | Source for current modernization package. Delete only after local library is accepted and no further diff against source is needed. |
| `docs\qa\evidence\20260702_tasks4_audit` | audit evidence | keep | low | Created by current audit; needed to prove matte scan result. |
| nested `_github\Martyskin-trud-runner` parent-git modified marker | nested repo status | do not stage from parent | medium | Nested repo itself is clean; parent sees directory as modified. |

## Explicitly protected

- `assets\`
- `native\`
- `settings\`
- `build-*.json`
- `releases\android\*.apk`
- `docs\qa\evidence\20260630_next_big_patch\`
- `docs\skins_integration\`
- `C:\Projects\Monkey Work\Tasks\4\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2.zip`
- `C:\Projects\Monkey Work\Tasks\4\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2.zip.sha256.txt`

## Cleanup gate before deletion

Before any deletion:

1. Resolve absolute paths.
2. Verify paths stay inside intended workspace or explicitly named target directory.
3. Produce deletion list.
4. Confirm no runtime assets, release artifacts, source files, or required QA evidence are included.
5. Ask for explicit approval when deletion is destructive.
6. Re-run the smallest relevant validation after deletion.

## Current decision

No cleanup executed in this slice. Keep this report as the cleanup baseline for future modules.

## Cleanup executed for newly generated temporary files

During Module 1 validator syntax verification, `python -m py_compile .\tools\validate-assets.py` created `tools\__pycache__`. This was a fresh temporary artifact from the current run, not historical project evidence, and was removed immediately after verifying its resolved path stayed under:

`C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\tools`
