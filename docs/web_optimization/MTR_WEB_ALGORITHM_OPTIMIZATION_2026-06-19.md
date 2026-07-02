# MTR web algorithm optimization log — 2026-06-19

## Scope

Audit-only observations showed that the web build reached the main menu slowly and could render old fallback text/placeholder layers under the new PNG UI. This patch changes the web-side loading algorithm from broad eager preload to a shell-first, priority-routed pipeline.

## Code changed

- `assets/scripts/GameRoot.ts`
  - Added a minimal main-menu shell set: background, title, and primary forward button.
  - Deferred non-gate main menu buttons, but kept them at `critical` priority so they load before skin/gameplay/background warmups.
  - Changed web object preload to critical-first lazy chunking instead of full catalog blocking.
  - Added visible/critical/normal/idle sprite queue priority handling.
  - Added main-menu baked-button placeholder without runtime text fallback, preventing old under-text layers.
  - Kept native behavior compatible while reducing web cold-start contention.
- `tools/codex/MtrEntrypoint.psm1`
  - Added success-pattern polling and process-tree stop support for Cocos builds.
- `tools/Run-MtrCocosBuild.ps1`
  - Normalizes Cocos raw exit code `36` when the build log confirms success.

## Build evidence

- Command wrapper: `tools/Run-MtrCocosBuild.ps1`
- Config: `build-web-mobile.json`
- Build stamp: `20260619-web-menu-priority-shell`
- Result: `exitCode=0`, `rawExitCode=36`, `buildFinished=true`, `completedBySuccessPattern=true`
- Cocos log: `creator-20260619-web-menu-priority-shell.log`
- stdout: `logs/creator-20260619-web-menu-priority-shell.out.log`
- stderr: `logs/creator-20260619-web-menu-priority-shell.err.log`
- Router log: `logs/entrypoint-router-20260619.jsonl`

Smoke check:

```json
{"status":200,"length":2164,"title":"Cocos Creator | Martyshkin Trud Runner"}
```

## Browser QA evidence

- URL: `http://127.0.0.1:8123/index.html?qa=web-menu-priority-shell-20260619-1781886760521`
- Screenshot: `logs/web-qa-menu-priority-shell-20260619.png`
- Console log: `logs/web-qa-menu-priority-shell-20260619-console.json`
- Summary: `logs/web-qa-menu-priority-shell-20260619-summary.json`

Measured:

```json
{
  "runtimeAtMs": 7534,
  "webPreloadAtMs": 8701,
  "deferredButtonsAtMs": 7534,
  "gateReadyAtMs": 8701,
  "issueMsgs": []
}
```

Important runtime markers:

- `MTR_OBJECT_SPRITE_ENQUEUE_BATCH reason=menu-ui-critical:boot-main-menu:main_menu count=3 requested=3 priority=critical platform=web`
- `MTR_OBJECT_SPRITE_ENQUEUE_BATCH reason=main-menu-deferred-buttons:boot-main-menu count=5 requested=5 priority=critical platform=web`
- `MTR_MAIN_MENU_DEFERRED_BUTTON_PRELOAD_REQUESTED reason=boot-main-menu count=5 priority=critical platform=web`
- `MTR_MENU_UI_GATE_READY surface=main_menu`
- `MTR_WEB_OBJECT_PRELOAD_REQUESTED critical=27 strategy=web-critical-first-lazy-chunked fullCatalogDeferred=true themedFullCatalog=280`

Visual QA:

- Main menu renders with unified PNG button style.
- Old fallback text under PNG buttons is not visible.
- All six main-menu buttons are visible in the first Browser QA capture after gate readiness.
- No console errors, unhandled exceptions, `TypeError`, or `ReferenceError` were captured.

## Comparison notes

- Earlier focused QA showed main-menu gate around `15628ms`.
- First fastpath patch reduced gate to about `10053ms`.
- Shell-first patch reached gate around `8194ms`.
- Priority-shell patch kept gate around `8701ms`, but eliminated the residual delayed-button placeholder issue by prioritizing all main-menu PNG buttons ahead of the larger gameplay preload queue.

## Remaining engineering risk

The remaining expensive segment is before `MTR_BITMAP_RUNTIME_READY` (`~7.5s` in this run). That is likely Cocos engine/bootstrap and bundle initialization, not the main-menu UI gate itself. Next optimization pass should target build output size, bundle split/compression/cache policy, and Cocos boot path profiling.

## Stop point

This is a safe stop point: web build passes smoke, Browser QA passes, visual menu layering is clean, and logs are sufficient to resume from the exact optimization state.

Hermes resume checkpoint:

- Latest project checkpoint: `C:\Users\nikit\.hermes-proagents\checkpoints\by-project\MTRCocosCreator-d20b07d42eaf7ab3\LATEST.md`
- Checkpoint markdown: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260619T163454Z-web-menu-priority-shell-after-browser-qa-precompact-5pct.md`
- Checkpoint JSON: `C:\Users\nikit\.hermes-proagents\checkpoints\019edad0-65fd-7e22-8e94-21e18afa5d07\20260619T163454Z-web-menu-priority-shell-after-browser-qa-precompact-5pct.json`
- Threshold semantics verified: Hermes stores checkpoint threshold as `compact_limit * threshold_ratio`; therefore "5% before compact" is `threshold_ratio=0.95`.

Hermes cleanup preview:

- Dry run only: `dry_run=true`, `matched=113`, `protected=12`, `deletable=101`, `selected=10`, `deleted=0`.
- Prune audit log: `C:\Users\nikit\.hermes-proagents\context-prune-audit.jsonl`
- No checkpoint was deleted at this stop point; latest project checkpoint id `123` is protected by latest/keep-last rules.

Stop hygiene:

- Browser QA tabs finalized.
- Local web server process `5952` stopped.
- Final file-status probe passed after correcting a local PowerShell status-script syntax mistake; no project files were affected by that transient tooling error.
