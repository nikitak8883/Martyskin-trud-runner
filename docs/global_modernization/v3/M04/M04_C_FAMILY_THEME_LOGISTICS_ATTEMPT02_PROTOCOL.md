# Logistics attempt02: preregistered protocol, not acceptance

The JSON companion freezes the next independent comparison before another
descriptor or timed experiment sample. Attempt01 remains rejected at `61/63`.
Its acceptance object and comparison math are inherited without overrides.
New descriptor identity does not authorize source/art/runtime-code changes.

Revision 4 is the active design. Review found that the bootstrap previously
trusted boot/AVD stdout without checking the probe exit result; revision 2 pins
that safety correction. The exact revision-1 JSON predecessor is retained and
hashed. No attempt02 timed sample or candidate descriptor existed before this
revision; thresholds, order, sample counts and cache definitions are unchanged.
Revision 3 additionally cancels the owned Web marker timeout on success/error,
avoiding a spurious 45s CLI lifetime after an early terminal. It preserves the
exact revision-2 predecessor and the revision-1 lineage. No game metric interval
or acceptance formula changes, and no attempt02 timed sample has been observed.

Revision4 retains the exact revision3 JSON/hash and the full 3->2->1 lineage.
It changes only the Web CLI tooling pin after the hosted-CI correction: browser
dependency loading follows valid CLI input, so malformed-input static checks do
not need Playwright. All other protocol fields and all eight other tooling pins
are identical to revision3, including cold boots, settle/wait intervals, samples,
silence, thresholds, topology and acceptance. Inputs and timed samples remain
NOT_RUN. A full static failure caught the stale revision3 pin; it is preserved
as failed evidence, not overwritten or excused as a product/runtime pass.

## Ordered execution

Current preparation supplement2026-10-01: step2's7CBC APK is the historical
pre-native-repair baseline example, NOT an admitted current input. The clean
native repair D323FA64 requires matching repair/runtime semantics in BOTH states
and a new source-specific build/staging manifest. Do not silently reuse either
APK or relabel old qualification samples. No actual input admission is done.
`atlas_input_integrity.py` now supplies only all-file byte sealing/verification;
see `docs/qa/ATLAS_INPUT_INTEGRITY_20261001.md`. Semantic build/artifact/source/
descriptor/parity and native/Web QA gates remain required separately. Protocol
JSON revisions and all nine frozen tooling pins are unchanged.

1. Finish qualification of the silent/cold-boot tooling. Its functional QA and
   gallery smoke runs are **not experiment samples**. Keep the original failed
   candidate and verified unpacked rollback reports intact.
2. Pin baseline input provenance (current verified unpacked APK SHA-256
   `7CBCDCADA60E0A4B6B1D7F4869FC61C20E0B47D6A9FBB363B6E0DB709F4BCFA4`,
   Web export source lineage) and copy only the Web runtime plus APK to a new
   ignored experiment staging directory. Require all-file hashes, exact artifact
   reports and the current source inventory. Baseline staging is **not done** at
   preregistration; the companion's input-admission fields are prerequisites.
3. Create exactly one new recursive logistics descriptor with the JSON's UUID,
   unchanged packing configuration and the same 26 corrected source PNGs/meta.
   Build Web, then Android, serially. Stage/pin both candidate inputs **before**
   any timed baseline/candidate sample. Preserve the original baseline exports;
   no builds or model calls can overlap measurements.
4. Android: four fixed pairs, AB/BA/AB/BA. Cold boot separately for each state
   (eight boots), install the pinned state APK in emulator user 0, settle 30s,
   record first process launch, wait 20s and record a force-stopped relaunch.
   Always verify host `-no-audio` and media stream 3 at zero. Do not clear data,
   uninstall, wipe, claim disk/shader-coldness or in-process warm cache.
5. Stop only the verified owned AVD. Web: same four pairs, eight fresh Chromium
   processes/contexts, explicit `--mute-audio`, same 1280x720 viewport and one
   loopback server. Refuse a foreign listener instead of killing it. Use unique
   evidence IDs; logical metric phase remains `baseline` or `candidate`.
6. Compare first-launch and warm-storage Android cohorts separately for all
   four pairs, with the existing 63-check comparator and inherited exact visual
   gates. Each independent candidate repeat is the next registered pair, last
   wrapping to first, with the same cohort. Do not compare a screenshot with
   itself. The one Web sample per state participates in both cohort comparisons
   but is not counted twice as independent evidence.
7. Keep every ordered sample, including slow/failing ones. No best-of, arbitrary
   outlier removal, modified thresholds or repeat-only-the-failure rescue. All
   eight comparisons must pass before full QA, review, M2_PLUS and ownership.
   Infrastructure/safety failure means incomplete, never acceptance; a
   performance/visual failure means rejection and verified unpacked rollback.

## Evidence boundaries

Protocol-only preregistration does not prove input admission, execution, causal
attribution, atlas acceptance, physical performance, signing or Release. Optional
Perfetto diagnostics must be separate from the timed acceptance samples. The
software-rendered emulator is a controlled relative test, not a phone benchmark.
Any change to the frozen design or pinned tooling before measurement requires a
documented successor protocol, never silent edits after observing results.

Source PNG/meta, gallery layout, levels, collision, saved games and product audio
settings remain unchanged. Baseline/candidate staging copies are temporary
benchmark inputs only, not extra runtime assets, release archives or repo mirrors.
