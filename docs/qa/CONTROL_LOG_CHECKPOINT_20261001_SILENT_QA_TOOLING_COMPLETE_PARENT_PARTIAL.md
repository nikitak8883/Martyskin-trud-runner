# Control log / checkpoint — silent QA tooling

- Status: `completed` for mandatory host-silent QA and bounded tooling;
  `partial` for logistics atlas/native runtime; Release remains blocked.
- Roadmap position: `P2 / M04-C-FAMILY-THEME-LOGISTICS`, parent
  `M04-C-FAMILIES`, source package `M04.5`.
- Progress: `20/73` mandatory execution units (`27.3973%`). This prerequisite
  does not add an execution unit or mark the atlas child complete.
- Evidence: static `32/32`, four unit cycles `27/27 +10/10 +17/17`, Web
  `34/34 x2` and restart `10/10 x2`. Android retained order is `28/28`,
  **27/28 FAIL**, then a separate settled cold-boot `28/28` control.
  `29` hash-bound receipts; all Android audio policies prove stream3 zero and
  matching `-no-audio`, actual Chromium startup proves `--mute-audio`.
- Remaining: `53` mandatory + `7` conditional execution units; source ledger
  `28/95`, `57` mandatory + `10` conditional source packages. Release blockers
  `M02.1`, `M02.7`, `M12.7` stay open.
- Next: investigate/establish the native bootstrap acceptance boundary in
  `ANDROID-NATIVE-BOOTSTRAP-001`, then pin immutable baseline/candidate inputs
  and run every sample of attempt02 protocol revision3.

## User instruction now mandatory

For every emulator/test run through the rest of implementation, fully suppress
audible game output. Android: host `-no-audio`, media stream3 verified zero and
fail closed before launch. Web: explicit `--mute-audio`. Keep real audio logic
and user/product settings intact so audio behavior can still be tested silently.
Rule is in project `AGENTS.md`; static gates and runtime entrypoints enforce it.

## Verified implementation

Opt-in cold boot refuses reuse/physical override and proves fresh AVD boot with
successful probes and no snapshot load/save; default ordinary startup is unchanged.
No wipe, uninstall, data clear or automatic foreign-session stop was performed.
The silent guard no longer guesses a host process. Web atlas evidence IDs cannot
traverse paths or relabel metric phase. The owned terminal timer is cleaned up.

Attempt02 design has four fixed AB/BA/AB/BA pairs, 16 Android first-launch/warm-
storage samples and8 fresh-browser Web samples; all8 paired-cohort comparisons
must pass the same63 inherited checks. Exact independent repeat mapping, cache
limitations, input hashes and no-build/no-model exclusivity are preregistered.
Revisions1/2 are preserved exact predecessors of revision3; all revisions happened
before any candidate descriptor or timed attempt02 sample. Inputs/runtime are
**NOT_RUN**. Tooling QA is not substituted for those samples.

## Preserved open finding

Cold-boot confirmation is not a native first-frame guarantee. Immediate first-menu
launch hit activity/resource recreation and failed `27/28`; later cases passed.
The new settled run passed `28/28`, but no native code was patched and the issue
is still open. Preserve its blank screenshot/log/summary and distinguish it from
atlas attempt01's still-unconfirmed load/FPS cause. Never hide it with timeout
relaxation or an automatic success retry.

## Reproduction anchors and cleanup

- Runtime source anchor: `7f58cf86e6f30ae032bafb1a1252961f05c833fc`; current APK
  SHA-256 `7CBCDCADA60E0A4B6B1D7F4869FC61C20E0B47D6A9FBB363B6E0DB709F4BCFA4`.
- Receipts: `docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_SILENT_QA_VALIDATION.json`.
- Review: `docs/qa/SILENT_QA_TOOLING_CODE_REVIEW_20261001.md`.
- Failure: `docs/qa/ANDROID_NATIVE_BOOTSTRAP_001_20261001.md`.
- Protocol: `docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_ATTEMPT02_PROTOCOL.json`.
- Local output root: `temp/qa-silent-boot-20261001`; all failed and passing
  reports are retained. No stale runtime backup/assets or whole-repo mirror added.
- No physical QA, new APK build, Release signing, Pages deployment, global config,
  hooks, model downloads, inference fallback or unrelated-work cleanup performed.
- Emulator and owned server8133 are stopped. Resume from `CURRENT_STATE.md` and
  this checkpoint, not from the old faster atlas repeat. Technical goal stays active.
