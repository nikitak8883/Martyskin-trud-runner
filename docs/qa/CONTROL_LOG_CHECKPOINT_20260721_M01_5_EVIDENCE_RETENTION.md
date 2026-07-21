# Control log / checkpoint — M01.5 evidence retention

Дата: 2026-07-21  
Branch: `codex/mtr-source-freeze-v3`  
Source commit before patch: `2a7d3311bb5dad602ce0e6af56113e421220ba12`  
Result: `PASS FOR M01.5 / RELEASE BLOCKED`

## Completed

- Added a dependency-free, index-first retention classifier under `tools/codex/evidence-retention/`.
- Bound output to one reviewed M01.5 path and implemented project/evidence containment, Windows invalid/reserved-name guards and reparse rejection.
- Added initial and pre-write verification for policy, index, accepted-run links, Git HEAD and the complete evidence corpus.
- Classified all 801 indexed files / 1,051,135,677 bytes:
  - protected: 68 files / 43,470,213 bytes;
  - retained_recent: 207 files / 393,576,403 bytes;
  - rotatable review-only: 526 files / 614,089,061 bytes.
- Recent groups are `20260714_two_cycle_resume` and `20260713_two_cycle_audit`.
- Rollback backup ZIPs, final reports and replay/harness scripts are protected.
- Verified three accepted-run links.
- Content identity is honestly marked `UNAVAILABLE_UNTIL_M02_2`.
- No evidence file was deleted, moved, renamed or rewritten.

## Validation

- M01.5 unit suite: 13 discovered; 12 pass; 1 expected Windows symlink-privilege skip.
- Canonical dry-run: PASS, 801 indexed = 801 discovered; 0 missing, size drift, mtime drift or unindexed.
- Fixed generatedAt/sourceCommit rerun: byte-identical PASS.
- M01.3–M01.4 isolated regression: 44 executable pass, 2 expected platform skips.
- M01.2 direct regression: PASS with 8 schemas, 11 positive, 20 negative, 25 deterministic reruns, 3 mutation guards and 9 report-shape smokes.
- First local review findings were fixed and retested; final Codex line review PASS.
- Heavy local review and CodeRabbit were not counted as PASS because neither produced a valid review result on this Windows host.

## Corrected QA harness issues

- Registered the dynamic Python 3.13 test module before dataclass execution.
- Removed PowerShell date coercion from the deterministic rerun harness.
- Reran M01.3–M01.4 through its pinned bootstrap after system Python correctly lacked global `jsonschema`.

## Rollback

- Revert only the bounded M01.5 source commit when created.
- The raw evidence corpus needs no rollback because M01.5 did not mutate it.
- M00 source bundle, evidence anchor and historical SHA index remain unchanged.

## Restart boundary

- M01.5 is complete.
- Release remains blocked and no runtime modernization has started.
- Next work package is M01.6, currently blocked on the primary source remote decision; after that decision, implement CI or the documented mandatory local equivalent with exact local/CI command parity.
