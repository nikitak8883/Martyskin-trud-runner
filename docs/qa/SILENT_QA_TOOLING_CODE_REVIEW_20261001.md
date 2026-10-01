# Silent QA and cold-boot preparation: scoped code review

Scope: project instructions, seven Android silent guards, opt-in boot policy,
three Web launchers, atlas evidence identity/timer ownership, protocol lineage,
static gates and roadmap receipts. No source art, metadata, native/gameplay code,
build settings, lockfiles, signing identity or global configuration changed.

## Corrected findings

1. **Wrong-host inference:** the audio guard formerly trusted the only emulator
   process when its AVD could not be matched. Removed the guess; fail closed.
2. **Implicit Web silence:** added explicit `--mute-audio` to every project Web
   QA launcher and records its configuration without changing product audio.
3. **Non-cold reuse:** `-ColdBoot` requires emulator-only/EnsureEmulator, rejects
   resident sessions, disables snapshot load/save, checks fresh start/AVD identity
   and successful boot probes. It never wipes data or stops a foreign AVD.
4. **Probe stdout without exit proof:** successful text from a failed ADB probe
   no longer establishes AVD/boot readiness. Revision2 preserves the prior
   protocol and pins this correction before any timed attempt02 sample.
5. **Receipt overwrite:** validated unique evidence IDs isolate later atlas
   screenshots while logical metric phase remains baseline/candidate. Old failed
   atlas evidence stays unchanged; path/traversal negative controls reject early.
6. **Timer tail:** the atlas marker timeout is cancelled on success and exception.
   Revision3 pins this without changing the 45s deadline or game sample intervals.
   Live atlas CLI smoke finishes in ~9.1s instead of retaining a stale timer.
7. **Hosted shell portability:** the new mock gate invokes native `pwsh`, not
   Windows-only `powershell`; this matches the Windows/Linux hosted matrix.
   Native PowerShell7 execution is checked locally. Hosted acceptance is separate
   and must be verified against the published source, not inferred from this run.

## Validation and limits

- Four unit cycles: `27/27` silent/boot groups, `10/10` Web ID/timer checks,
  `17/17` protocol/negative controls. Mock suites perform no device operations.
- Web `34/34 x2`, interaction PASS and restart `10/10 x2`; actual Chromium parent
  matching the running QA node contains `--mute-audio`. Atlas smoke PASS with
  all26 original sources and a unique evidence ID; generic launcher-only smoke
  PASS is explicitly **not** another game QA cycle.
- Android all-run order: PASS `28/28`, FAIL `27/28`, then separate settled PASS
  `28/28`. Every case is host-silent and media stream3 remains zero. The failed
  first bootstrap is not discarded or overridden by the positive control.
- Full static gate `32/32 PASS`, zero findings, pinned isolated Python environment.
  Roadmap schema/dependency validation PASS after the documentation update;
  counts remain `20/73`, zero dependency cycles. `29` bound receipts rehash PASS.
- Early boot activity/resource recreation remains an open technical issue:
  `ANDROID-NATIVE-BOOTSTRAP-001`. No proven product fix, no attribution of the
  previous atlas performance failure, no new atlas/M2_PLUS/Release acceptance.
- Host preflight and process checks are bounded snapshots, not an interprocess
  lock. The preregistered orchestration must serialize jobs and revalidate owned
  process/input identities; no global inference/runtime changes are justified.
- No external CodeRabbit or model patch review was run. Codex is the final
  reviewer; no new external diff scope/privacy authority or model inference was
  needed for this narrow deterministic tooling patch.

## Skill verdicts

```json
{
  "skill": "experiment-review",
  "verdict": "needs_patch",
  "summary": "Silent tooling and protocol lineage are verified; native bootstrap acceptance remains open and experiment inputs/runtime are NOT_RUN.",
  "evidence": ["docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_SILENT_QA_VALIDATION.json", "docs/qa/ANDROID_NATIVE_BOOTSTRAP_001_20261001.md"],
  "actions": ["Establish/fix the native bootstrap acceptance boundary before timed input admission", "Pin both staged inputs and execute every preregistered sample without best-of selection"],
  "risk": "medium",
  "requires_worktree": false,
  "requires_model": "none"
}
```

Safe-patch-loop result: **PASS for the silence/tooling implementation**, partial
for parent atlas/runtime acceptance. First mock-run errors were incorrect test
expectations (`volume` field and mute-error text), corrected and rerun; source
patch context mismatches failed atomically and made no partial edits. A direct
roadmap CLI attempt used system Python/wrong arguments; it is not acceptance.
The successful roadmap check used the pinned venv and catalog arguments.

## Rollback / hygiene

- Roll back only this project-scoped tooling patch from its Git commit; preserve
  the independently reviewed lifebuoy fix and old attempt01 rejection.
- Protocol predecessors are intentional immutable audit artifacts, not duplicate
  runtime assets. Temporary QA images/logs/scripts are retained bound evidence,
  outside `assets/` and excluded from source projection by Git ignore rules.
- AVD and owned loopback server8133 are stopped. No build/model job overlapped
  timed atlas smoke, and no phone/foreign server/global settings were changed.
- Release blockers `M02.1`, `M02.7`, `M12.7` remain. This review is not Release.
