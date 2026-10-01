# Logistics source correction and rejected atlas review

Date: `2026-10-01`  
Anchor: `d9175adcdbb5a6fe072063fd7ffd9275b364daf8`  
Unit: `M04-C-FAMILY-THEME-LOGISTICS`, source package `M04.5`.

## Decision and boundaries

Atlas attempt01 is **REJECTED**, not accepted: `61/63` frozen comparison gates
pass, but Android load and relative FPS fail. Its faster repeat does not replace
the failed first sample. The `.pac` and `.pac.meta` are removed. Thresholds remain
unchanged, and no acceptance artifact is issued for this attempt.

The independently reviewed lifebuoy alpha correction is retained. Final rollback
runtime evidence is recorded in the validation summary and control checkpoint.
The atlas child and aggregate work package remain partial/pending respectively.
Review is Codex-local; no external CodeRabbit submission or local model inference
was used for this slice.

## Corrected findings

1. The lifebuoy's enclosed center contained an opaque checkerboard. A matching
   imagegen cutout replaces the source; the reviewed central alpha region is
   strictly zero. Its resource key, 244x232 canvas, original PNG metadata bytes,
   UUID, pivot and import trim rectangle are preserved.
2. Initial normalization lost a low-alpha fringe and no longer matched the import
   trim rectangle. Bounded transparent-only re-trim/refit now converges to the
   pinned alpha bounds or fails; repeatability is tested against the exact hash.
3. The legacy cutter could overwrite the corrected sprite. A pinned source and
   original metadata outside `assets/` provide explicit restoration. The cutter
   checks pins before its destructive extraction stage and restores the reviewed
   source before validation. Original sheet/hash/bounds remain lineage, not a
   false claim that the new art came from the old sheet.
4. Restoration needed complete prevalidation. All records' paths, hashes, alpha,
   import identity and unique manifest match are validated before writing any
   target. Source and metadata payload bytes are snapshotted and rehashed. Both
   target PNG and metadata paths have containment/symlink resolution checks.
   This is not a multi-file transaction; interruption is detectable and rerunnable.
5. Source/manifest/contact-sheet fingerprints became stale. Canonical inventories
   were regenerated and checked; no rejected logistics descriptor remains in
   accepted measured ownership.
6. Atlas performance measurements could overlap builds/QA. A read-only Win32
   preflight now blocks those processes before atlas gameplay mutation and strips
   raw command lines from emitted evidence. Fourteen deterministic tests and a
   live negative control pass. Ancestors are excluded to avoid self-blocking.
   This is a start-time snapshot, not a lock, and is wired only to the two atlas
   measurement entrypoints; orchestration must still serialize other QA.
7. Entry-point README/master-plan headers still named earlier completed children
   while their next-action lines named logistics. Active headers now agree on the
   partial logistics state, and source-freeze non-goals are explicitly historical.
8. The first temporary M2_PLUS preparation emitted shortened child gate IDs.
   All eight child checks passed, but the strict profile correctly returned
   `BLOCKED` for eight `CHILD_GATE_ID_MISMATCH` findings. Its first report is
   preserved. Preparation now reads each exact gate ID from the authoritative
   profile slot catalog, and all child gates/profile are rerun; no validator or
   profile constraint is relaxed.
9. Raw pinned Cocos metadata used CRLF bytes, while Git's canonical blob uses LF.
   Depending on the checkout host, that could invalidate restoration pins. Two
   exact metadata paths now declare `eol=crlf`; original metadata bytes remain
   unchanged. A 13th regression test verifies Git clean/smudge roundtrips with
   `core.autocrlf=false` and `true` in isolated temporary repos; four complete
   source-test cycles pass. No global Git configuration or broad asset rewrite.

## Preserved failures and open follow-ups

- Attempt01 load `4756 ms` exceeds `2953.75 ms`; median FPS `4` is below `5.1`.
  Visual parity and draw reductions pass but cannot override these gates.
- Candidate full Android matrices were `27/28` and `25/28` due slow sprite-load
  diagnostics while native build work overlapped. Those reports remain failed.
  Host-load/cache causality is unconfirmed; do not label it as established.
- Generic legacy `write_png_with_meta` still regenerates unreviewed UUIDs on a
  full sheet recut. Full recut is **NOT_RUN**. The narrow reviewed override is not
  a certification of that entire pipeline. A separate identity-preservation
  task is required before future full regeneration.
- Follow the preregistered experiment instructions; no best-of selection,
  threshold weakening, unrelated theme batch or unconditional topology change.

## Reviewed implementation seams

- The 26-source logistics gallery uses the existing DEBUG-only route and derives
  its keys from runtime-enabled hazards/platforms; production selection/save/
  collision/sound logic is unchanged.
- Unit tests cover invalid later records without partial apply, bad hashes,
  traversal, opaque-center regression, UUID drift, lineage, preflight ordering,
  runtime drift, idempotence and exact normalized-source reproduction.
- Android uses only the virtual target and user 0. Host `-no-audio` and verified
  media-stream volume zero provide silence without altering production settings.
- No models/configs/hooks were copied into the project. No global configuration,
  physical device, signing, Pages deployment or Release acceptance was changed.

Release remains blocked by `M02.1`, `M02.7` and `M12.7`.
