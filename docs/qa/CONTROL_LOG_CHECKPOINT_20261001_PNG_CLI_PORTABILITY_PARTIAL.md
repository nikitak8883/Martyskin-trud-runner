# PNG/CLI portability prerequisite checkpoint

- Status: `completed` for implementation/targeted checks; `partial` for final
  source-pinned hosted/native/parent atlas/Release acceptance.
- Roadmap position: existing `M01.6`/`M12.7` prerequisites, before
  `P2 / M04-C-FAMILY-THEME-LOGISTICS` admission.
- Progress: `20/73` (`27.3973%`), source `28/95`; no denominator or credit change.
- Evidence: previous exact hosted Windows33/34/Linux31/34; all four earlier
  corrections pass, real rollback10/10. Complete pixels/filter equality and exact
  locked compressor30/30 on both hosts; four final Windows6/6 cycles with stable
  source/goldens, full29-sheet index SHA unchanged. New mandatory PNG guard10/10,
  reviewed13/13, contact7/7, bootstrap7/7, four missing-browser negatives. Final
  clean local/hosted35-step receipts follow the source commit.
- Remaining:53 mandatory +7 conditional units; source57 mandatory +10
  conditional. Native bootstrap, immutable attempt02 admission/measurements and
  final signing/Pages/M12.7 remain open; runtime QA for this tools-only patch NOT_RUN.
- Next: exact published CI verification, then native-bootstrap diagnosis/fix and
  isolated preregistered atlas experiment. Never retry away first-boot failure.

## Scope and review

`Run-MtrWebAtlasPilotQa.js` now validates malformed args without loading its
runtime-only browser dependency; actual launch dependency and silence flag stay.
Shared PNG serialization fixes the actual encoder difference without replacing
byte comparisons by semantic-only checks or refreshing original provenance.
Dependency is exact and isolated; guard tests check version/build/runtime,
CRC/truncation, metadata/order, dimensions/mode/interlace, decompression limits,
filter selectors/termination, idempotence, original raw bytes and decoded pixels.
Four cycles bind helper/consumer/test/lock and golden inputs. Detailed diagnosis,
predecessor hashes and sources: `PNG_SERIALIZATION_CONTRACT_20261001.md`.

No gameplay code/art/meta/native/build settings/root dependency changes, model execution,
global config/hooks, CodeRabbit transmission, signing, deployment or physical
device access. Product and reference PNGs are unchanged. A new hash-addressed
quality-gate cache is expected; prior qualified cache and failed evidence stay.
No repository-wide cleanup or unrelated user-file edits.

Parent source at start: root `0892b246be861a4ba89cbf6eb71b31b369e9e809`, published
`bfeb49a46a070c83c6c7db80ffbac787e465fe84`. Scoped source publication is to the
same approved `mtr-source-v3` branch, not `main`/Pages. Post-push ignored handoff
and Hermes checkpoint record actual commit/tree/CI receipt IDs without embedding
a future/self-referential source hash. Rollback is the single scoped commit.

## Full-gate follow-up before publication

Root94de9c8's clean full35-step gate failed34/35 on the intentionally frozen
revision3 Web CLI tooling pin. Receipt SHA
`4E87FC1045F324915BD04385F0B9E68F7E2A1860BF3D731C715FF9A6C6697CEF`
is retained in `temp/ci-portability-20261001/png-cli-postcommit-static/report.json`.
Revision4 is a preregistered successor, not a refresh after measurement: exact
revision3 is archived with SHA
`E746CB44C3A186A811C88EFE761ECA61361BE6A299B0AC614B5C320F74FBD2C2`.
The full3->2->1 lineage is checked; every other field and eight tool pins remain
identical. New negative controls reject old revision, post-sample revision and
bad predecessor pin. Inputs/runtime remain NOT_RUN. Publish only after the
follow-up clean full gate passes. The scoped rollback now covers the PNG/CLI
commit and its protocol-lineage follow-up; neither has deployed product builds.

The first new lineage test expected an explicit revision1 number; inspection
proved the immutable first preregistration predates that field. The test now
checks its exact inherited SHA/schema/attempt identity without editing history.
Final protocol guard has20 groups/negative controls; four combined follow-up
cycles and the clean35-step gate are required, never an inferred green.

Task-generated probe cache inventory: Linux Pillow239 files/21067736 bytes;
Linux zlib-ng21/337806; Windows zlib-ng21/240082; failed ensurepip venv6/285,
including links. A guarded native PowerShell cleanup of the three link-free
package directories was rejected by execution policy before launch. Nothing
was deleted and no alternate shell/tool bypass was attempted. These small
diagnostic dependency copies and failed-venv links remain explicitly classified
for later approved cleanup; raw diagnostic PNGs/reports are retained evidence.
