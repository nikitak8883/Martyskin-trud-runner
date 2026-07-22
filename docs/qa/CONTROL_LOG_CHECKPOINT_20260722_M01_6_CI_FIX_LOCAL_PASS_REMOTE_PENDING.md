# Control log / checkpoint — M01.6 CI portability fix

Дата: 2026-07-22  
Parent branch: `codex/mtr-source-freeze-v3`  
Parent commit before patch: `68d9ba9321c18e4be0447e79253e4b9a712f3e04`  
Published source branch: `mtr-source-v3`  
Published source commit before patch: `2293be127534d8be23066e4597c14d72201e7aca`  
Repository: `https://github.com/nikitak8883/Martyskin-trud-runner.git`  
Result: `LOCAL PASS / REMOTE CI FIX NOT YET PUSHED / RELEASE BLOCKED`

## Completed in this slice

- Read the full GitHub Actions job logs and downloaded both evidence artifacts for failed run `29827757787`.
- Confirmed that Windows failed only because Pillow was absent from the isolated quality-gate lock.
- Confirmed that Linux had the same missing-Pillow failures plus a path-guard defect: POSIX absolute executable paths such as `/opt/.../python` were incorrectly classified as Windows root/device paths.
- Added exact `Pillow==12.3.0` to the hash-addressed isolated quality-gate environment and updated its lock self-test/documentation.
- Corrected the path guard so genuine Windows `\\...`, `\\??\\...` and `\\Device\\...` forms remain rejected while POSIX `/...` executable paths remain valid.
- Added a Linux-only regression test for POSIX absolute executables.
- No game runtime, assets, Web build, Android build, emulator, physical device, Pages deployment or release artifact was changed.

## Local validation

Canonical command with the explicit development-only dirty-source authorization:

```text
python tools/codex/quality-gate/bootstrap.py -- --project-root . --config tools/codex/quality-gate/static-gates.json --output temp/quality-gate-m01-6/report-dirty.json --content-version mtr-static-gates-v1 --allow-dirty-source
```

- Gate status: `PASS`
- Run ID: `qg.20260722052611.be7ef372c6a0`
- Mandatory steps: `7/7 PASS`
- Findings: `0`
- Duration: `31969 ms`
- Python: `3.13.14`
- Gate config SHA-256: `BE7EF372C6A082B6E957B064382D593F3BE0287AC744B16B042E7CFCFB4A04F0`
- Isolated lock SHA-256: `C8515C52B56E335827EB3D4B38C0996C59EF751DBB171B6FABFED81571CA5B74`
- Source was dirty only because this bounded patch was under test; `dirty_authorized=true` is not acceptable as final CI evidence.

Passed steps:

1. `m01-2-contracts`
2. `quality-gate-self-tests`
3. `evidence-retention-self-tests`
4. `asset-contracts`
5. `skin-bonus-contracts`
6. `ui-ir-contracts`
7. `level-select-icons`

## Bounded patch files

- `tools/codex/quality-gate/runner.py`
- `tools/codex/quality-gate/requirements.lock`
- `tools/codex/quality-gate/README.md`
- `tools/codex/quality-gate/tests/test_runner.py`
- `tools/codex/quality-gate/tests/test_bootstrap.py`
- this checkpoint

## Authoritative boundary

- M01.6 is not yet complete remotely: the latest published source commit still has failed Windows and Linux jobs in run `29827757787`.
- The local patch is validated but has not yet been subtree-split, pushed or rerun on GitHub-hosted Windows/Linux.
- Existing M01.6 documents that say remote CI is pending or imply final completion must be reconciled only after both hosted jobs pass on the new source commit.
- M01.7 and M02.2 were not started.

## Restart procedure

1. Verify this bounded parent commit and confirm that unrelated untracked user paths remain untouched.
2. Create a fresh `git subtree split` for `MTRCocosCreator_portable_transfer_20260617/MTRCocosCreator`.
3. Push only that split to `origin` branch `mtr-source-v3`; do not force-push and do not change remote `main` or historical remote `codex`.
4. Wait for `static-gates (windows-latest)` and `static-gates (ubuntu-latest)` and inspect their machine-readable artifacts if either fails.
5. After both jobs pass, update the M01.6 report/summary with the final source SHA and run/job IDs, run the hygiene gate, and only then mark M01.6 complete.
6. Resume with M01.7, then M02.2.

The clean diagnostic worktree `C:\Projects\MTR-source-v3-ci-smoke` remains detached at `2293be127534d8be23066e4597c14d72201e7aca` and may be removed after the final hosted CI pass. User-owned unrelated worktrees and untracked directories must remain untouched.
