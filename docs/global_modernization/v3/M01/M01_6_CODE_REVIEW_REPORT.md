# M01.6 code review report

Date: 2026-07-22  
Verdict: `PASS FOR BOUNDED M01.6`

## Diff scope

- one cross-platform GitHub Actions workflow;
- one typed M01.3 static-gate config;
- one exact local/CI command in the quality-gate README;
- one non-destructive source-publication amendment.

No Cocos runtime, gameplay source, asset, build configuration, Pages tree, Android target, release artifact, evidence corpus, or physical device changed.

## Review findings

| Concern | Result |
| --- | --- |
| CI and local commands can drift | Prevented: both surfaces invoke one literal command and one tracked config. |
| External actions float by mutable major tag | Prevented: checkout, setup-python and upload-artifact use full commit SHA values with readable version comments. |
| CI receives unnecessary write credentials | Prevented: `contents: read` and `persist-credentials: false`. |
| Matrix failures can be hidden | Prevented: `fail-fast: false`; both Windows and Linux jobs report independently. |
| CI can produce a false release green | Prevented: workflow is explicitly static-only; P4/M2_PLUS runtime slots remain mandatory. |
| Missing/skipped tool can pass | Prevented by the M01.3 fail-closed runner and seven mandatory enabled steps. |
| Cocos or device work can run accidentally | Prevented: config contains only platform-independent Python validators and test commands. |
| Local dependency state can diverge | Pinned Draft 2020-12 environment is created/reused by `bootstrap.py`; global Python is not mutated. |
| Child `python` steps can escape the pinned environment | Prevented: bootstrap prepends its venv to `PATH`, sets `VIRTUAL_ENV`, removes inherited `PYTHONHOME`, and the hosted reports resolve all seven steps inside that venv. |
| Windows checkout can change lock/config byte identity | Prevented: targeted `.gitattributes` rules preserve LF for workflow, quality-gate, schema/registry and evidence-retention contracts; final Windows/Linux lock and config SHA-256 values are identical. |
| Oversized parent backup can reach GitHub | Prevented by publishing the project subtree as `mtr-source-v3`; no history rewrite or deletion. |

## Validation

- JSON config parse: `PASS`.
- Workflow YAML parse: `PASS`.
- `git diff --check`: `PASS` after removing one extra EOF blank found during staging review.
- Development run: `7/7 PASS` with explicit dirty-source authorization.
- Clean-source run: `7/7 PASS`, no override, no findings, stable source.
- Final hosted run `29895079941`: Ubuntu and Windows both `PASS`, 7/7 mandatory steps and 0 findings on source `34dd70086a98c11a41a73e17460ed78426456be5`.
- Hosted quality-gate tests: 47 discovered / 45 passed / 2 expected skips on each OS.
- Hosted evidence-retention tests: 13/13 passed on each OS.

## Residual boundary

M01.6 proves only the bounded static command contract. P4/M2_PLUS/QA7/RC2 runtime, signing, Web/Android parity and release evidence remain mandatory and blocked until their own work packages run. Any future failed CI job again blocks the source branch and must be fixed by rerunning the same command, not by weakening or conditionally skipping a step.
