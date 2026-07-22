# M03.1 code and evidence review

Date: 2026-07-22  
Verdict: `PASS FOR BOUNDED INVENTORY / M03 FINDINGS DEFERRED TO THEIR OWN PACKAGES`

## Review boundary

- `assets/scripts/GameRoot.ts` and `assets/scenes/main.scene` were read only.
- `tools/codex/analyze-game-root.js` uses the Cocos-bundled TypeScript compiler API and has no package/lockfile dependency.
- Generated JSON is deterministic, source-hashed and parse-diagnostic aware.
- The human report reconciles the AST evidence with direct inspection of state, input, collision, power-up, timer/listener, scene and persistence paths.

## Review checks

| Risk | Result |
| --- | --- |
| Inventory generated from stale or copied source | Rejected: live source path and SHA-256 are embedded; repeated output hash is stable. |
| Regex-only method/call extraction | Rejected: TypeScript AST parser `5.8.2` returned zero parse diagnostics. |
| Runtime behavior changed during audit | Rejected: no runtime source, scene, asset or build file is modified. |
| Hidden physical-device action | Rejected: no ADB command or physical serial was used. |
| Existing coupling presented as fixed | Rejected: all eight findings are explicitly deferred to M03.2–M03.7. |
| Wholesale rewrite proposed | Rejected: accepted sequence uses strangler adapters and one responsibility per patch. |
| Collision/input order omitted | Rejected: current event order, duplicate pause route and debounce are recorded. |
| Timer/listener cleanup overclaimed | Rejected: listener symmetry is proven; missing transition/reset cancellation is recorded as a migration risk. |

## Independent advisory and static gate

- The bounded local heavy reviewer produced no validated final content after its single bounded finalizer retry (`finish_reason=length`), so its output was rejected rather than treated as a pass. The heavy model was explicitly unloaded and verified absent.
- A narrower NPU quick review returned `status=ok` with zero findings. Its model was also unloaded and verified absent after use.
- The staged-file CodeRabbit pass found one major analyzer completeness issue: constructors and get/set accessors were excluded. The analyzer now includes all three declaration kinds, names constructors deterministically, and records member kind/counts. A temporary 1-property/1-constructor/2-accessor/1-method fixture passed and was deleted after validation.
- Final CodeRabbit re-review covered all nine staged M03.1 files and returned zero findings.
- Final development static gate `qg.20260722094323.cb31e1f5e6da`: `8/8 PASS`, zero findings, source stable with explicit dirty-source authorization; report SHA-256 `55517CBA1D6E48AF4353BD6169D36AC7217D5CCDA0DC2CFBA231F1AA1BECF463`.

## Verdict

M03.1 satisfies its D4 inventory objective and establishes a reproducible baseline for M03.2. It does not satisfy the full M03 acceptance criteria and does not change release readiness.
