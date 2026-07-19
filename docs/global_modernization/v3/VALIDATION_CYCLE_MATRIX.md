# Validation cycle matrix — merged project policy

Этот документ разрешает конфликт между v3 risk-based cycles, минимумом 4 циклов в AGENTS и уже принятой Tasks/4 QA7.

## Основной принцип

«Четыре цикла» — это четыре независимых инженерных gate, а не четыре одинаковых запуска. Повторное использование старого evidence запрещено, если patch затрагивает проверяемый runtime.

## D4 — docs/schema/planning

1. Integrity: source hash, safe extraction, manifest coverage.
2. Syntax/contract: JSON/YAML parse, schema fixtures, script parse/compile/tests.
3. Compatibility: live paths, ownership, dependencies, AGENTS/lore and prior-plan reconciliation.
4. Independent plan review: conflicts, missing outputs, rollback, stop conditions, next action.

Runtime/emulator не запускается, если runtime не менялся.

## P4 — любой bounded runtime patch

1. Static/contract gate: diff scope, TypeScript/config/schema/assets.
2. Web targeted gate: affected route/interaction, console, screenshot/metric.
3. Android emulator targeted gate: install/launch/affected flow/logcat. Только эмулятор по умолчанию.
4. Regression/review gate: adjacent behavior, cleanup paths, code review, hygiene, report/checkpoint.

Любой fail исправляется и соответствующий gate повторяется до PASS; нельзя переносить дефект в следующий work package.

## M2+ — module integration

- Pass A: functional seam + минимальный representative slice + parity.
- Pass B: measured optimization/regression + adjacent integration matrix.
- Focused recovery pass обязателен для GameRoot, save migration, signing, release и любого найденного failure path.
- Каждый pass внутри себя выполняет P4.

## QA7 — domain matrix, сохранённая из Tasks/4

1. Build/static/smoke.
2. Visual/UI — 14 экранов, 5 viewport profiles, Cyrillic, touch targets, no ghost/double labels.
3. Gameplay/physics — jump/glide/dash/pause/collisions/completion/fail/10 restarts.
4. Skins/bonuses — 8 skins, poses, bonuses, expiry/death/retry/transition, no residue.
5. Audio/VFX — buses, unlock, persistence, event spam, pooling/readability.
6. Performance — Web + Android emulator baseline/soak; physical device только по явному разрешению.
7. Release/cleanup — artifacts, hashes, parity, dry-run, post-change critical regression.

## RC2 — release candidate

- RC cycle 1: полный applicable QA7 из immutable source/content version.
- RC cycle 2: независимый повтор после всех fixes/optimizations; stale evidence не используется.
- Final parity: logical content manifest, Web artifact, Android artifact, signing/ABI/version, deployment source/live smoke.
- Если Play target не утверждён, AAB помечается `not_applicable`, а не fake PASS.
- Если physical device не разрешён, device performance остаётся `not_executed_by_policy`; это не подменяется emulator evidence.

## Evidence contract каждого gate

```yaml
gate_id:
run_id:
started_at:
finished_at:
source_commit:
worktree_state:
content_version:
platform:
command:
exit_code:
status: pass|fail|blocked|not_applicable
artifacts: []
sha256: []
open_findings: []
rerun_of:
```

## Stop conditions

- source отличается от checkpoint;
- unreviewed destructive action;
- Cocos/toolchain mismatch;
- unknown test failure;
- Web/Android logical content mismatch;
- missing rollback for migration;
- signing secret exposure;
- fatal console/logcat, black screen, missing asset, white matte, ghost layer;
- cleanup затрагивает protected evidence/runtime;
- resource gate сообщает небезопасное состояние.

## Текущая planning-фаза D4

| Gate | Результат |
| --- | --- |
| D4.1 ZIP/manifest integrity | PASS |
| D4.2 syntax/tests | PASS_WITH_LIMITATION: 2/2 tests; JSON Schema dependency отсутствует |
| D4.3 live compatibility | PASS_WITH_25_RECORDED_CONFLICTS |
| D4.4 independent plan audit | PASS_WITH_BLOCKERS; см. `PLAN_AUDIT_20260719.md` |
