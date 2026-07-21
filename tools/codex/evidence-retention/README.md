# M01.5 evidence-retention dry run

This tool classifies the existing M00 SHA-indexed corpus under `docs/qa/evidence` without deleting or moving anything.

## Safety contract

- the accepted evidence index is the only classification input;
- a lightweight filesystem pass checks containment, existence, size drift and unindexed files, but does not rehash the 1.05 GB corpus;
- index, policy and accepted-run links are read and hashed from one byte snapshot;
- absolute, traversal, alternate-data-stream, non-canonical and symlink-escape paths fail closed;
- the declared index root must resolve to the configured evidence root;
- output must remain inside the project and outside the evidence tree and protected inputs;
- CLI output must exactly match the reviewed M01.5 `outputPath`; arbitrary project-file overwrite is rejected;
- every indexed file receives exactly one class: `protected`, `retained_recent` or `rotatable`;
- `rotatable` means review candidate only; the code exposes no evidence delete/apply option;
- JSON output is written through `fsync` plus atomic replacement.
- policy, index, accepted-run links and corpus metadata are revalidated immediately before replacement.

`protected` has precedence over recent-group retention. Final JSON reports, named rollback backups, and replay/harness scripts are protected even when their historical paths look superseded. The two newest dated evidence groups and a named current failure corpus are `retained_recent`. Older non-anchor evidence is `rotatable`, but cannot be acted on by this implementation.

## Canonical dry run

```powershell
python .\tools\codex\evidence-retention\retention.py `
  --project-root . `
  --policy tools/codex/evidence-retention/retention.config.json `
  --output docs/global_modernization/v3/M01/evidence_retention_dry_run.json
```

For byte-identical reproduction, pass the committed report's `generatedAt` and `sourceIdentity.currentCommit` through `--generated-at` and `--source-commit`.

## Tests

```powershell
python -m unittest discover -s .\tools\codex\evidence-retention\tests -p "test_*.py" -v
```

The only unlink in the implementation cleans a same-directory `.tmp.<pid>` created by a failed atomic report write; it cannot target the evidence tree. No game build, Web runtime, Android target, deployment or physical device is involved in M01.5.
