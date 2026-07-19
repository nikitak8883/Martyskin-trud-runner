# MTR typed quality gate (M01.3)

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

`bootstrap.py` creates a hash-addressed venv in the user cache, installs only exact versions from `requirements.lock`, verifies them, and exports the lock identity to the runner. It never installs into global Python. Concurrent first starts are serialized by a cache-local lock directory. Waiters allow the exact-package install timeout plus a bounded setup margin and never delete another process's lock.

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

The v1 config deliberately defines command execution and optional evidence adaptation only. D4/P4/M2_PLUS/QA7/RC2 profile composition and mandatory/not-applicable policy belong to M01.4.

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
