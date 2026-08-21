# M04-B implementation plan

Date: `2026-08-21`  
Execution unit: `M04-B` (`M04.3 + M04.4`)  
Gate: `P4`  
Status: `COMPLETE`

## Boundary and invariants

- Extend fail-visible pre-import validation and create manifest-linked contact sheets only.
- Do not move, repack, recompress, trim, delete or reimport runtime assets.
- Keep `assets/resources` as the current bundle and keep every `atlasUuid` empty until M04-C.
- Treat Web and Android as one logical content line; Android runtime QA is emulator-only.
- Preserve unrelated root worktree changes and publish only the project subtree.

## Ordered implementation cycles

1. Baseline the M04-A manifest, source inventory and accepted validator output — complete.
2. Add naming, metadata, trim, pivot, alpha/null-frame, bundle, provenance, quarantine, hidden-reference and path-containment checks with negative fixtures — complete.
3. Generate deterministic HUD/menu/runner/bonuses/obstacles/backgrounds/VFX sheets and a schema-validated canonical index — complete.
4. Run direct tests, strict asset scan, full static gate, fresh Web cycles and fresh Android-emulator cycles — complete.
5. Reconcile independent review, run hygiene/rollback gates, update roadmap/checkpoint and publish the bounded subtree — implementation and validation complete; publication is recorded after commit in Hermes.

## Acceptance contract

- Every governed PNG/JPG/JPEG is classified exactly once and linked to one atlas group and ownership scope.
- Any invalid import contract or hidden path/reference is blocking, never warning-only.
- Generated sheets are local evidence; only the canonical JSON index is tracked.
- No open review finding, static finding, unexpected runtime diagnostic or process loss is accepted.
- The next unit is `M04-C-PILOT`, limited to one measured co-visible atlas family.
