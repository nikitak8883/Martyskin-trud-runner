# Control checkpoint — M03.1 complete; WSL and CodeRabbit ready

Date: 2026-07-22T12:46:28+03:00  
Status: `M03.1 PASS / WSL READY / CODERABBIT READY / M03.2 NEXT / RELEASE BLOCKED`

## Restart point

- Repository: `C:\Projects\Monkey Work`.
- Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`.
- Branch: `codex/mtr-source-freeze-v3`.
- Sole remote: `https://github.com/nikitak8883/Martyskin-trud-runner.git`.
- M02 review-fix commit: `25df6ea968613445d05d490030e75a3778eb0c60`.
- Accepted M03.1 implementation/evidence commit: `799f4e079c63a7a456f304a5b7be3c4f064dd3e2`.
- Shared content identity remains `mtr-v3-source-a5c4bdbb2fca`; M03.1 changed analysis tooling/docs only.
- Runtime source hash remains `22941AA58AF4A27DF103C5339D77D6E1D82028EE932740484CF7002B0EF507A2`.
- No physical Android device or ADB serial was used.

## WSL and CodeRabbit status

- WSL runtime `2.7.10.0`, kernel `6.18.33.2-2`, WSL2 active.
- Distribution: Ubuntu `26.04 LTS`, WSL version `2`.
- Linux user: `nikitak8883`, UID `1000`.
- CodeRabbit CLI: `0.7.0` at `/home/nikitak8883/.local/bin/coderabbit`.
- Authentication: `authenticated=true`, provider `github`, user/org `nikitak8883`.
- Completed doctor: `9 passed / 0 warnings / 0 failed`; repository and review backend/WebSocket checks passed.
- Windows persistent command: `C:\Users\nikit\bin\coderabbit.cmd` directly invokes the absolute Linux binary through `wsl.exe -d Ubuntu -- ...` and preserves arguments.
- Interactive login helper: `C:\Users\nikit\bin\coderabbit-auth.ps1`.
- WSL Git policy: `core.autocrlf=input`; only `/mnt/c/Projects/Monkey Work` is registered as `safe.directory` (no wildcard).
- Current Windows verification: `coderabbit --version` and `coderabbit auth status --agent` both pass.

No additional elevation or permanent broad permission is required for the accepted CLI workflow.

## CodeRabbit reviews and fixes

1. Committed M02.3–M02.5 review from base `c2cd1b50ec4ff18582ddc9f29fe7f4a4c6367cb9`: five findings (`4 major`, `1 minor`).
2. All five were verified and fixed in `25df6ea`: stale M02 status, incomplete rollback scope, developer-unlock value exposure in current evidence, unvalidated device-valid wording, and stale M02.4 clean-gate provenance.
3. Initial M03 uncommitted pass returned zero findings but reviewed only four tracked index files; this was not treated as full coverage because Git excludes untracked files from diff review.
4. New M03 files were explicitly staged and reviewed. CodeRabbit found one major analyzer completeness defect: constructor/get/set members were omitted.
5. The analyzer now includes methods, constructors and accessors. A temporary fixture with one property, one constructor, two accessors and one method passed, then was deleted.
6. Final re-review covered all nine M03.1 files and returned `0 findings`.

## M03.1 accepted evidence

- `GameRoot.ts`: `5,428` lines, `294,102` bytes.
- Class inventory: 170 fields, 267 methods, zero current constructors/accessors and zero serialized `@property` fields.
- Internal graph: 1,046 call occurrences / 613 unique caller→callee pairs.
- Lifecycle: 8 listener registrations / 8 matching removals; 15 `scheduleOnce` callbacks / zero explicit `unschedule*` calls.
- Persistence: 37 local-storage operations across 18 keys.
- Scene: 10 dynamic node patterns and 34 scene operations; `GameRoot` is attached to `Canvas` in `main.scene`.
- Generated inventory SHA-256: `20F1930860C00D5BB6727A32847340ED1506112E3B229504A132B639D7E3DB01` and deterministic across repeated runs.
- Final development static gate: `qg.20260722094323.cb31e1f5e6da`, `8/8 PASS`, zero findings, explicitly authorized dirty source stable; report SHA-256 `55517CBA1D6E48AF4353BD6169D36AC7217D5CCDA0DC2CFBA231F1AA1BECF463`.
- Clean-source static gate on `799f4e079c63a7a456f304a5b7be3c4f064dd3e2`: `qg.20260722094553.cb31e1f5e6da`, `8/8 PASS`, zero findings, source clean/stable and exact expected commit matched; report SHA-256 `3C69B73FEC5B8CC5645D2116065E68525016DD11FAB618A0555ECE779008331F`.

Canonical M03.1 files:

- `docs/global_modernization/v3/M03/game_root_inventory.md`
- `docs/global_modernization/v3/M03/game_root_inventory.generated.json`
- `docs/global_modernization/v3/M03/M03_1_VALIDATION_SUMMARY.json`
- `docs/global_modernization/v3/M03/M03_1_CODE_REVIEW_REPORT.md`
- `tools/codex/analyze-game-root.js`

## Global routing correction

Skill Compass incorrectly selected `security-ownership-map` for a non-security GameRoot ownership inventory because a generic `ownership` marker applied the full security boost.

- Corrected source: `C:\Projects\Optimization\LLM_local\codex_local_ai_integration_kit\codex_local_ai_integration_kit\local_worker\server.py`.
- Isolated committed fix: Optimization commit `9f5f06b` (`fix(local-worker): gate security ownership routing`).
- The security ownership skill now requires both ownership and explicit security/bus-factor/sensitive-code intent.
- Retrieval audit markers now cover code/architecture/read-only inventories.
- Dedicated regression tests: `3/3 PASS`; existing local-worker contract suite: `8/8 PASS` through the configured `.venv`.
- Corrected direct runtime route: `retrieval-first-code-audit`, score `0.8455`; generic runtime ownership gives security score `0.0`; explicit security ownership remains `1.0`.
- The running MCP process loaded the old module before the patch. The committed default becomes active after the next Codex client/MCP restart; until then Codex must override the stale recommendation deterministically.
- Pre-existing unrelated dirty Optimization changes were preserved and excluded from the isolated commit.

## Tooling incidents and prevention

- System Python lacked `httpx`; tests must use the exact MCP runtime `.venv\Scripts\python.exe`.
- The first Windows CodeRabbit shim used `bash -lc` and corrupted forwarded arguments; the accepted shim invokes the absolute Linux binary directly.
- CodeRabbit doctor emitted a complete 9/9 result but did not terminate before the outer 120-second bound; complete emitted evidence is accepted, the exit hang is tooling behavior rather than a failed doctor.
- One WSL diagnostic embedded `$()` inside a PowerShell double-quoted command and was interpreted by Windows. It performed no mutation. Future WSL diagnostics use direct argv-style commands (`wsl -d Ubuntu -- <executable> <args>`) without nested shell interpolation.
- Local `heavy_review` exhausted its bounded final output twice (`finish_reason=length`) and was rejected. The heavy model remained loaded after failure, so it was explicitly unloaded and verified absent. A compact NPU quick review returned zero findings and was also unloaded/verified.
- Retrieval returned stale asset-manifest chunks for the GameRoot query. M03.1 therefore used a deterministic Cocos TypeScript AST inventory instead of sending the whole source to a model.

## Hygiene and retained user data

- Temporary analyzer fixture/output were deleted after validation.
- No generated build, emulator, device, model or authentication debris was added to the project commit.
- User-owned untracked directories were not staged, modified or cleaned:
  - `Stiker pack/SG-1/`
  - `Tasks/4/_unpacked_20260702_145527/`
  - `Tasks/5/`
  - `project-library/corpora/`

## Next safe action

1. Restart Codex before trusting automatic Skill Compass routing, so Optimization commit `9f5f06b` is loaded by the MCP process.
2. Execute **M03.2 only**: add a typed `GameSessionState` transition contract around the existing sole writer `transitionTo`, preserve all currently valid transitions, reject invalid transitions deterministically, and keep UI/physics movement out of this patch.
3. Run the targeted state/input parity tests, static gate, CodeRabbit review, emulator runtime gate if runtime code changes, then checkpoint before M03.3.

Release remains blocked by production signing/distribution and approved Pages topology/deployment evidence.

