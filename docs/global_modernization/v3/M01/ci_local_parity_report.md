# M01.6 CI / local command parity

Date: 2026-07-22  
Status: `PASS / LOCAL AND WINDOWS-LINUX CI ACCEPTED`

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

- Parent source commit: `792ddaaf5ce8fa7254ae17da9ab79c6fa21b3d80`
- Source clean: `true`
- Dirty override: `false`
- Source stable during run: `true`
- Gate status: `PASS`
- Mandatory steps: `7/7 PASS`
- Findings: `0`
- Duration: `32350 ms`
- Schema engine: pinned isolated `jsonschema 4.26.0`, Draft 2020-12
- Gate config SHA-256: `BE7EF372C6A082B6E957B064382D593F3BE0287AC744B16B042E7CFCFB4A04F0`
- Requirements lock SHA-256: `C8515C52B56E335827EB3D4B38C0996C59EF751DBB171B6FABFED81571CA5B74`
- Local report SHA-256: `5FD2F89F9A6DFA1F551BDED03A3EA44115303E3C3801852BE8B5145C5160C0BB`

The final hosted suites reported 47 discovered / 45 passed / 2 expected platform skips for the quality runner and 13/13 passes for evidence retention on both operating systems. Every mandatory typed-runner step itself is `PASS`; no mandatory gate is skipped.

## Accepted hosted CI evidence

- Workflow run: `29895079941`
- Source branch: `mtr-source-v3`
- Source commit: `34dd70086a98c11a41a73e17460ed78426456be5`
- Ubuntu job `88843412945`: `PASS`, 7/7, 0 findings, gate run `qg.20260722055444.be7ef372c6a0`, `29952 ms`.
- Windows job `88843412954`: `PASS`, 7/7, 0 findings, gate run `qg.20260722055521.be7ef372c6a0`, `39211 ms`.
- Both jobs record the same config SHA-256 and requirements-lock SHA-256 shown above.
- Both jobs resolve every configured `python` step from the bootstrap-owned pinned virtual environment.
- Workflow artifacts preserve each JSON report and separate stdout/stderr captures for 14 days.

The debugging sequence failed closed and was not weakened: clean source-checkout evidence assumptions, POSIX path classification, the missing Pillow lock, child-process runtime inheritance and checkout EOL drift were corrected in source. No mandatory step was disabled or made optional.

A future CI failure blocks the source branch until the same command passes on the failing runner; this static PASS is not a runtime or release PASS.

## Rollback

Revert the bounded M01.6 workflow/config/bootstrap/attributes commits. This removes CI orchestration and its isolated-runtime portability hardening only; it does not modify or remove game runtime assets, builds, evidence, Pages, or release files.
