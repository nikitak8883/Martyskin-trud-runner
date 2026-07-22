# M02.3 reproducible Web build and runtime report

Date: 2026-07-22  
Status: `PASS FOR M02.3 / RELEASE STILL BLOCKED`

## Accepted boundary

- Build target: `web-mobile`, Cocos Creator `3.8.8`.
- Parent checkpoint at build time: `c2cd1b50ec4ff18582ddc9f29fe7f4a4c6367cb9`.
- Published source checkpoint: `e4e412ddac3a8044fb9d6f626148f813965eaa3e` on `mtr-source-v3`.
- Shared logical content identity: `mtr-v3-source-a5c4bdbb2fca`.
- Identity baseline: `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2`.
- Identity file SHA-256: `F8362EC17295FD646E335C501B40A24871E3B40C1CBA22B6A4C0F36AD9313395`.
- This package changed only QA runner dependency/resolution and reports. Packaged gameplay, assets, scenes and build configuration did not change, so the M02.2 bump policy does not require a new content identity.

## Build evidence

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 `
  -ConfigPath build-web-mobile.json `
  -LogDest creator-web-m02_3-20260722.log `
  -TimeoutSeconds 1200
```

Result:

- wrapper exit: `0`; Cocos raw exit: `36`, accepted only because the Cocos log contains the terminal `build Task (web-mobile) Finished` marker;
- build duration reported by Cocos: `47.057 s`;
- platform artifact state: `BUILT`;
- favicon post-process: copied and linked, `PASS`;
- Cocos build log SHA-256: `CA4DF7F5EABFE7D8099C3EF89579F9823386CB70768FA34A5762393F339A8488`;
- stderr contains only the known Cocos compression-default and empty-engine-cache warnings; the build completed and runtime gates below found no product warnings/errors.

## Web artifact verification

The verification enumerated every regular file in normalized relative-path order and hashed the UTF-8 records `path<TAB>bytes<TAB>sha256`, joined by LF.

| Check | Result |
| --- | --- |
| File count | `4,815` |
| Total bytes | `120,421,881` |
| Aggregate SHA-256 | `7C8917130192B155D9F72C9BE5D1927CDFD1BE952598BEB91B4AD59C0209361C` |
| Runtime aliases | `index.html`, `index.js`, `application.js`, `style.css`, `favicon.png`: `5/5 present` |
| Runtime payload | `assets/main/index.js` |
| Current menu route | present |
| Native QA startup bridge | present |
| Styled name flow | present |
| New bonus PNG pack | present |
| Developer unlock flow | verified; value redacted from evidence |
| Browser `prompt(...)` call | absent |

Key entry hashes:

| File | SHA-256 |
| --- | --- |
| `index.html` | `967A9AE97A789292CDE1F8B78A618C9E42EC5EF0B2A294A65978CD29B9B345F1` |
| `index.js` | `4317CB547B4D105F69346B925D961DF7F951002FD5A4AAAE807A361AA1AD49CD` |
| `application.js` | `359F85DD922E2568AA991AF95A5C356A0102042C8918252987BFBD37F2153EB2` |
| `favicon.png` | `10723157F93394878E8BA16FDF514E14D5E688079DE6A8C63371FA40FF420C76` |

## Browser and runtime QA

The in-app Browser first verified the page identity, a single `2560x1440` backing canvas rendered at `1280x720`, a visible level-1 gameplay frame, and zero captured warnings/errors. The repository runner then executed the full deterministic matrix.

Reproducible runner:

- `playwright-core` pinned exactly to `1.61.1` in `package-lock.json`;
- Node `v24.16.0`;
- managed Chromium `149.0.7827.55`;
- only an absolute, existing executable is accepted; `MTR_PLAYWRIGHT_BROWSER_EXECUTABLE` is the explicit override;
- runner metadata is embedded in every raw summary.

Accepted post-review matrix:

- `34/34 PASS` across UI screens, 15 levels and responsive profiles;
- portrait touch gate: `PASS`;
- jump/dash/pause/resume interaction: `PASS`;
- restart loop: `10/10 PASS`;
- console errors/warnings, page errors and request failures: `0`;
- raw local summary: `docs/qa/20260722_m02_3_web/web_matrix_interaction_post_review.json`;
- raw summary SHA-256: `2175AFFF1A4F1E04AA5EFF5AA0246B33870F894E3311DBBB9B584966C06C588E`.

Accepted soak:

- target/actual: `300 s / 300.561 s`;
- complete: `true`; final state: `playing`;
- input bursts: `39`; clear-state transitions acknowledged: `3`;
- FPS samples: `10`; minimum `60.08`, average `60.52`;
- heap samples: `10`; first `21,799,110`, last `39,992,153` bytes. This is an observation, not a leak verdict; performance ownership remains M10.
- console errors/warnings: `0/0`;
- five milestone/final screenshots were captured locally;
- raw local summary: `docs/qa/20260722_m02_3_web/web_soak_300s.json`;
- raw summary SHA-256: `84C666899C83182E2DBBA03842D69DC0CFD4D8D3F53A9F932B21FD33C8B9CC09`.

## Review and static gates

- The first server invocation passed a boolean through nested `powershell -File` and was rejected as a string. The accepted typed invocation is direct `& .\tools\Start-MtrWebServer.ps1 -StopExisting:$false`; no product code changed.
- The frontend skill referenced a stale screenshot entrypoint. The actual Browser API `tab.screenshot(...)` succeeded; the mismatch is recorded as tooling evidence.
- CodeRabbit CLI could not run because its Windows path requires WSL and WSL is not installed. No CodeRabbit result is claimed.
- Bounded local-worker diff review verdict: `accept`; its path-resolution edge case was fixed by rejecting relative/nonexistent candidates.
- Post-fix matrix rerun: `34/34`, restart `10/10`, `PASS`.
- Development static gate `qg.20260722073124.cb31e1f5e6da`: `8/8 PASS`, zero findings, source stable; dirty-source authorization was explicit and is not the final clean acceptance.
- Gate report SHA-256: `D16302BCB05060DA538FABBB9D25E317E40A996AF528E167A99FBF34D0E03AE4`.
- Clean-source gate after commit `aef19b0a0f5e11237fafbb2e457b21be6951380e`: run `qg.20260722073434.cb31e1f5e6da`, `8/8 PASS`, zero findings, source clean/stable, no override.
- Clean report SHA-256: `A849306A7DEFAB0EBA6AFFCF183B6744E07015EE058D706E1922B25051EB6D29`.

## Limitations and next gate

- No Pages deployment or live-URL parity is claimed; M02.7 remains blocked by the topology decision.
- No signing claim is made; production signing remains blocked by M02.1.
- No Android artifact or runtime claim is made here.
- Next safe package: M02.4 x86_64 emulator build/install/launch/matrix/restart/soak from the same shared identity.

Rollback: revert `package.json`, `package-lock.json`, `tools/codex/run_web_playwright_function.js`, `web_build_report.md`, `M02_3_CODE_REVIEW_REPORT.md`, `M02_3_VALIDATION_SUMMARY.json`, `CONTROL_LOG_CHECKPOINT_20260722_M02_3_COMPLETE.md`, and the M02.3 index updates together. Build outputs and ignored raw QA evidence are disposable and can be regenerated.
