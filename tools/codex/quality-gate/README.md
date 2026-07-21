# MTR typed quality gate and profiles (M01.3–M01.4)

This directory owns the active project-local command runner. It does not import into Cocos runtime and does not build, install or deploy the game by itself.

## Safety contract

- commands are `executable` plus an `arguments` array and always run with `shell=False`;
- `working_directory`, capture paths, native reports, declared artifacts, config and final report are resolved under the canonical project root;
- `..`, UNC and Windows alternate-data-stream paths are rejected;
- stdout and stderr are captured separately;
- timeout terminates the complete process tree (`taskkill /T /F` on Windows, a dedicated process group on POSIX);
- missing tools, mandatory skips, stale reports, source drift and malformed evidence block the gate;
- a dirty project source blocks the gate unless a caller explicitly enables the development-only `--allow-dirty-source` override;
- output topology is checked before execution, so reports, captures, native evidence, declared artifacts and protected inputs cannot overwrite one another;
- Git identity and dirty state are rechecked after all steps, and protected config/schema/adapter/registry/tool inputs are hash-checked for in-run mutation;
- the summary is validated before an atomic `fsync` + `os.replace` write;
- canonical evidence is produced only by the M01.2 allowlisted adapter registry;
- physical Android targets remain blocked unless the runner receives the explicit `--allow-physical-device` switch.

## Isolated validator

`bootstrap.py` creates a hash-addressed venv in the user cache, installs only exact versions from `requirements.lock`, verifies them, and exports the lock identity to the runner. It never installs into global Python. Concurrent first starts are serialized by a cache-local lock directory. Waiters allow the exact-package install timeout plus a bounded setup margin and never delete another process's lock. The environment marker is bound to the base interpreter; bootstrap refuses to rebuild the environment used by its current interpreter and instructs the operator to invoke the base Python instead.

Bootstrap only:

```powershell
python .\tools\codex\quality-gate\bootstrap.py --bootstrap-only
```

Run the bounded contract smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\codex\quality-gate\run.ps1 `
  -ConfigPath .\tools\codex\quality-gate\quality-gate.example.json `
  -OutputPath .\temp\quality-gate-m01-3-smoke.json `
  -ContentVersion m01.3-smoke
```

The wrapper returns `0` for `PASS`, `1` for `FAIL`, `2` for a valid `BLOCKED` report, and `3` for configuration/bootstrap/internal blocking errors.

Use `-AllowDirtySource` only for development self-tests while the project tree intentionally contains uncommitted changes. Release/profile configuration in M01.4 must not use that override.

## Configuration boundary

The v1 command config deliberately defines command execution and optional evidence adaptation only. M01.4 composes those atomic reports without changing the accepted M01.3 process runner.

When `evidence` is configured, the runner:

1. snapshots the native report before execution;
2. executes the declared tool;
3. requires the native report to be new or changed;
4. verifies that `tool_path` was actually executed and every declared strict flag appears in the argument array;
5. computes report/tool SHA-256, timestamps, source/content and target identity;
6. invokes the allowlisted adapter;
7. validates the envelope and final report with the pinned Draft 2020-12 engine.

`artifact_paths` are command outputs, not inputs. A missing or unchanged pre-existing declared artifact blocks the step.

## Self-test

```powershell
python .\tools\codex\quality-gate\bootstrap.py --module unittest -- `
  discover `
  -s .\tools\codex\quality-gate\tests `
  -p "test_*.py" `
  -v
```

The suite covers exact bootstrap locks, atomic bootstrap metadata, local-cache and foreign-lock safety, plus runner pass, fail, missing executable, process-tree timeout, mandatory and optional skips, malformed config, traversal/ADS/UNC paths, source mismatch, dirty-source authorization, output collisions, fresh and stale canonical evidence, stale declared artifacts, semantic rerun determinism, atomic replacement and false-green report mutation.

## M01.4 profile layer

The canonical catalog is `docs/global_modernization/v3/M01/quality_gate.config.json`. It contains exactly these typed profiles:

- `D4`: four documentation/schema/planning evidence slots;
- `P4`: static, targeted Web, targeted Android emulator, regression/review;
- `M2_PLUS`: complete pass A and pass B, plus four conditional focused-recovery slots;
- `QA7`: the seven Tasks/4 QA domains;
- `RC2`: independent QA7 cycles 1 and 2, final parity, conditional AAB and conditional physical-device evidence.

The catalog is an aggregator contract, not a shell command list. Every applicable binding must point to a fresh `mtr.quality_gate_report` produced by the M01.3 runner. The profile evaluator revalidates:

1. catalog, scope and child reports with the isolated Draft 2020-12 engine;
2. exact Git commit and content version;
3. child report time against the profile start time;
4. the child config SHA-256 and every declared child artifact SHA-256/size;
5. unique report paths, report bytes, run IDs and artifact paths across slots;
6. required Web/static/Android-emulator target envelopes;
7. cycle ordering for M2_PLUS and RC2;
8. Git and all protected inputs again before atomic output.

`NOT_APPLICABLE` is not a disabled step. It is available only to a `conditional` slot and requires an explicit false condition decision with a machine-readable reason. A true conditional decision becomes mandatory. A missing/unknown decision is a configuration error before evidence evaluation. Physical-device applicability additionally requires the explicit `-AllowPhysicalDevice` switch; emulator remains the default.

### Invocation scope

Create one ignored/temp JSON file per profile run. Its catalog hash must be the current SHA-256 of the canonical catalog, and all child reports must be generated after `started_at`:

```json
{
  "schema_version": 1,
  "contract": "mtr.quality_profile_scope",
  "profile_id": "D4",
  "run_id": "profile.m01-4.d4-final",
  "started_at": "2026-07-21T08:00:00.000Z",
  "source_commit": "0123456789abcdef0123456789abcdef01234567",
  "content_version": "m01.4-final",
  "profile_config_sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "condition_decisions": [],
  "evidence_bindings": [
    {
      "slot_id": "d4.integrity",
      "report_path": "temp/profile-run/d4-integrity.json"
    }
  ]
}
```

The shortened example intentionally lacks three mandatory bindings and uses placeholder identities; it demonstrates shape only and must block until populated with current values and all four reports.

Evaluate one complete scope:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\codex\quality-gate\run-profile.ps1 `
  -ScopePath .\temp\profile-run\scope.json `
  -OutputPath .\temp\profile-run\profile-report.json
```

The wrapper returns `0` for `PASS`, `1` for validated product/QA `FAIL`, `2` for a valid fail-closed `BLOCKED` aggregate, and `3` for malformed catalog/scope/bootstrap/internal configuration. `-AllowDirtySource` is development-only and is always rejected by RC2. A release claim must use a clean immutable source and fresh child evidence; profile composition by itself does not make the current release ready.
