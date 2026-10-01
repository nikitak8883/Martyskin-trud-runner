# Attempt02 staged byte-integrity prerequisite — not input admission

Parent:P2/M04-C-FAMILY-THEME-LOGISTICS/M12.7. Roadmap20/73 (27.3973%),
53 mandatory +7 conditional remain; source28/95. This prerequisite adds no unit
credit and does not admit actual experiment inputs, fix attempt01's61/63 failure,
close native overlay/Web QA, or provide atlas/Release acceptance.

## Gap and implementation

Revision4 requires all-file staged Web/APK/artifact/source-inventory pins plus
before/after state verification. Existing protocol test checks its declared
fields, not actual staged files. New standard-library-only
`tools/codex/atlas_input_integrity.py` supplies the required byte-integrity layer.

- Stream SHA-256 for ALL regular files in caller-selected project `temp/`
  staging, including Unicode paths, not only a nominated subset. Exact file
  membership/order/count/length/content verified; mtimes are not content hashes.
- Deterministic UTF-8 seal, no machine paths/time. Protocol revision4/attempt ID
  and externally supplied canonical lowercase protocol SHA pinned; only protocol
  CRLF->LF is normalized, not staged binaries/JSON/images/APKs.
- Verification requires independently retained exact seal SHA. A changed seal
  cannot validate itself using a checksum inside its own altered content.
- Strict shape/keys and typed canonical equality reject duplicated JSON keys,
  aliases, missing/unlisted/renamed files, bool/float counts and admission claims.
- Portable relative paths reject traversal, ADS/colon, backslashes, reserved
  Windows names, trailing spaces/dots and non-NFC names. Project/source paths
  cannot be staging/output. Links/reparse points/hardlinks rejected, parent
  components checked. Zero/unavailable file ID rejected.
- Handle/path identity,size,mtime and appropriate platform metadata checked
  around reads; complete second scan detects observed mid-snapshot changes.
  1MiB hash chunks,32MiB bounded seal/protocol reads,100000 entry/file cap;
  over-budget input fails, never truncates.
- Output must be outside staging in an existing project temp directory. Exclusive
  temporary creation/fsync/atomic hard-link publication does not overwrite old
  output. Unsupported filesystem or collision fails; no replace/copy fallback.
  Cleanup removes only the caller-created temporary file with matching identity.

Quiescent, caller-owned staging is mandatory. These checks are point-in-time
integrity evidence, not OS write protection or an adversarial race-proof sandbox.
Empty directories, ACLs and alternate streams are not build-file content covered
by this seal. Keep independently pinned hashes and re-verify before AND after
every measured state. Never repin a failure or read mutable build trees directly
as if they were frozen experiment inputs.

## Invocation and acceptance boundary

`seal` requires `--project-root`, `--staging-root temp/<owned-stage>`,
`--expected-protocol-sha256 <independent-lowercase-pin>`,
`--seal temp/<new-seal>.json`. Parent directories must already exist; no automatic
copying/build/model/server/measurement occurs. Record returned `seal_sha256`
independently in the experiment control record BEFORE any sample.

`verify` takes the SAME fields plus mandatory
`--expected-seal-sha256 <independent-seal-pin>`. Duplicate/abbreviated/unknown
options are rejected. Exit0 means only `byte_integrity_only`; output always says
`input_admission:false`, `experiment_runtime:NOT_RUN`, `release_accepted:false`.

The seal is NOT the complete paired input-admission manifest. Still required:
actual baseline/candidate clean source lineage, exact artifact reports, native/
runtime/source-art parity, corrected26-source inventory, descriptor configuration/
UUID checks, actual build outputs/installed APK evidence and permitted current
Web QA/native preflight. Do not invoke timed launchers with this seal alone.
Existing nine frozen tooling pins/protocol revisions remain unchanged.

## Verification and prevention

Fixture suite24 methods includes real CLI success/failure, same-length mutation,
add/delete/rename, external-pin tamper, strict shape/counts/duplicates/ordering,
protocol drift, limits, actual Windows junction/POSIX symlink rejection without
target traversal, hardlinks, open-handle and between-scan mutation, publication
collision/fsync failure/owned cleanup and portable metadata identity.

First run18/21 failed on a false Windows ctime path/handle guard after mutation/
rename. Actual Python3.13.14 stats probe established the discrepancy; Windows
fingerprint uses explicit birthtime now, while POSIX keeps metadata-change ctime.
Content/identity/size/mtime/SHA/double-scan requirements are retained. Windows
ctime is deprecated in [official Python3.13 os documentation](https://docs.python.org/3.13/library/os.html#os.stat_result);
the cross-API diagnosis is local measured evidence, not a claim from that page.
Follow-up22/22 passed. Expanded24-method test then exposed one misplaced fixture
assertion (NameError), corrected;24/24 passed. Failed evidence retained privately.
Four final cycles and clean/source-pinned canonical/hosted gates are separate
receipts in the final handoff, not inferred from a single positive test.

New mandatory static step `atlas-input-integrity-contracts` grows gate36->37;
this is a validation-step denominator change, NOT roadmap progress/count change.
No runtime/native/PNG/meta/shared/build/lock/global config changes, no new APK,
no descriptor/staged actual inputs/timed samples. Silent Android/Web rules remain
mandatory. This tooling suite does not imply full emulator/browser/visual QA.
Web server policy rejection is not bypassed; no phone/signing/main/Pages change.
Rollback only this new tool/test/static-step/documentation slice, preserving
protocol pins, failed predecessor receipts and unrelated user work.
