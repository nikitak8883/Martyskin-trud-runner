# M01.6 CI / local command parity

Date: 2026-07-21  
Status: `PASS / DOCUMENTED LOCAL EQUIVALENT ACTIVE / CI INSTALLED`

## Decision

The canonical source branch is `mtr-source-v3` in the sole approved repository:

```text
https://github.com/nikitak8883/Martyskin-trud-runner.git
```

Both GitHub Actions jobs and a local operator invoke exactly this command from the source-project root:

```text
python tools/codex/quality-gate/bootstrap.py -- --project-root . --config tools/codex/quality-gate/static-gates.json --output temp/quality-gate-m01-6/report.json --content-version mtr-static-gates-v1
```

There is no CI-only wrapper, alternate config, implicit shell composition, global dependency install, or reduced local command.

## Workflow contract

- Workflow: `.github/workflows/mtr-static-gates.yml`
- Triggers: push and pull request for `mtr-source-v3`, plus manual dispatch.
- Matrix: `ubuntu-latest`, `windows-latest`.
- Python: `3.13`.
- Permissions: read-only repository contents.
- Concurrency: one current run per workflow/ref; stale runs are cancelled.
- Timeout: 30 minutes per matrix job.
- Action dependencies: pinned to full immutable commit SHA values.
- Evidence: machine-readable report plus separate stdout/stderr captures, retained as a 14-day workflow artifact.

The workflow deliberately does not run Cocos Creator, Web runtime, Android builds, an emulator, Pages deployment, or a physical device. Those remain separate mandatory P4/M2_PLUS/QA7/RC2 evidence and cannot become green through this static workflow.

## Exact static command set

All seven steps are mandatory and are executed by the accepted M01.3 typed runner with argument arrays and per-process timeouts:

1. M01.2 schema/registry/adapter/fixture contracts.
2. M01.3–M01.4 isolated quality-gate tests.
3. M01.5 evidence-retention tests.
4. strict asset contracts with `--fail-on-white-matte`.
5. strict skin/bonus contracts with `--fail-on-warnings`.
6. UI IR contracts.
7. level-select PNG verification in `--verify-only` mode.

## Accepted local-equivalent run

- Source commit: `a2b213c41ee896f90f8c70857b25fd20ab712428`
- Source clean: `true`
- Dirty override: `false`
- Source stable during run: `true`
- Gate status: `PASS`
- Mandatory steps: `7/7 PASS`
- Findings: `0`
- Duration: `28212 ms`
- Schema engine: pinned isolated `jsonschema 4.26.0`, Draft 2020-12
- Gate config SHA-256: `BE7EF372C6A082B6E957B064382D593F3BE0287AC744B16B042E7CFCFB4A04F0`
- Local report SHA-256: `902693EF81F78B3786A971E58B3D20E79F572D8ED41CB8F9D1D86F97C25D9D04`

Nested suites reported 46 discovered / 44 passed / 2 expected platform skips for the quality runner and 13 discovered / 12 passed / 1 expected Windows symlink-privilege skip for evidence retention. Every mandatory typed-runner step itself is `PASS`; no mandatory gate is skipped.

## CI evidence boundary

The source workflow is installed and its YAML parses locally. Remote matrix results become authoritative only after the corresponding source commit is pushed and both jobs complete. A future CI failure does not invalidate the local command contract; it blocks the source branch until the same command passes on the failing runner.

## Rollback

Revert the M01.6 workflow/config commit. This removes CI orchestration only; it does not modify or remove M01.2–M01.5 tools, runtime assets, builds, evidence, Pages, or release files.

