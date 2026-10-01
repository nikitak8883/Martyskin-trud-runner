# Logistics: next bounded experiment

Status: atlas child **partial**, attempt01 **rejected**, source alpha prerequisite
implemented. Do not treat the retained art correction as acceptance of the atlas.

1. Completed prerequisite: failed candidate matrices are preserved, both fresh
   unpacked rollback builds/galleries are verified, Web `34/34 x2` and Android
   `28/28 x2` pass. Final unpacked interaction/name persistence, restart `10/10`
   and `300.642 s` soak pass. Rollback content pixels match the corrected baseline
   exactly on both platforms. Recheck these pins if the current source drifts.
2. Resume from the control checkpoint and rejection record, not from candidate
   repeat metrics. Atlas attempt01 remains rejected. Emulator user 0 only, no
   physical device, no audio; builders and all timed runtime QA must be serialized.
3. Before another descriptor, freeze a new independent protocol: same host state,
   viewport, build, emulator snapshot/cold-boot policy and cache definition for
   baseline and candidate. No builds, other QA or model tasks during timed runs.
   Host preflight is a read-only start-time check, not a replacement for serialized
   orchestration. Preserve every measured sample; never choose a best repeat.
4. Investigate cold-vs-warm texture decode/upload and queue pressure. Attempt01
   load was 4756 ms vs baseline 2283 ms; FPS 4 vs 6. The repeat was faster but
   does not establish the cause. Full candidate cycles failed slow-load checks
   on level15 and menu/name/level screens while native build work overlapped.
5. If evidence supports it, preregister separate directory-local hazard/platform
   atlases rather than one recursive parent. Candidate identity/topology changes
   require a new frozen expected texture count, not weaker load/FPS/visual gates.
6. Only after every gate passes: register measured ownership, update fingerprints,
   contact sheets, rollback mapping, four complete QA cycles, M2_PLUS, review and
   execution completion. Keep M04.5 aggregate and release blockers open.

## Separate discovery: full legacy cutter identity

The existing `write_png_with_meta` generates UUIDs for unreviewed outputs on full
sheet regeneration. This patch restores pinned metadata for the reviewed source
only. Full cutter regeneration is NOT_RUN and is not approved by the narrow
restoration evidence. Preserve/fix generic import identity in a separately scoped
pipeline task before a future full regeneration; do not silently recut all assets.

## Reviewed source invariant

`reviewed_runtime_sources.json` pins generated and runtime sources plus original
metadata. Runtime hole pixels must remain fully transparent. Image source/hash,
manifest lineage, UUID, 244x232 canvas and import rectangle must all pass the
mandatory static gate. The original image remains recoverable from Git anchor
`d9175adcdbb5a6fe072063fd7ffd9275b364daf8`; no duplicate runtime backup is needed.
