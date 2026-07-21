# Tool and code adaptation backlog

Цель — подготовить исполнимую основу без активации непроверенного upstream code.

## T01 — Unified quality runner

Upstream: `tools/powershell/run-mtr-quality-gate.ps1`  
Disposition: `rewrite_before_use`

Обязательные свойства:

- typed registry команд вместо произвольного shell text как основной API;
- explicit executable + argument array;
- timeout с принудительным завершением process tree;
- абсолютный project-root containment для cwd/report;
- раздельные stdout/stderr и exit code;
- mandatory/skipped/stale → fail closed;
- атомарная запись JSON, соответствующая canonical release-gate schema;
- self-tests: pass, fail, timeout, missing tool, malformed config, skipped mandatory step.

## T02 — Android artifact verifier

Upstream: `verify-android-artifact.ps1`  
Disposition: `rewrite_before_use`

Проверять:

- existence, SHA-256, package, versionCode/versionName, min/target SDK;
- ABI из ZIP entries;
- `apksigner` exit code и ожидаемый certificate fingerprint;
- запрет x86_64-only для device release;
- AAB через bundletool только при Play target;
- negative fixtures: corrupt APK, wrong signer, missing arm64, missing native tools.

## T03 — Git topology detector

Upstream: `verify-git-topology.ps1`  
Disposition: `rewrite_before_use`

Нужны `.git` directory и file markers, `git rev-parse`, `git worktree list --porcelain`, gitlink mode, `.gitmodules`, submodule status, exclusions для generated trees и bounded traversal.

## T04 — Pages sync/deploy

Upstream: `sync-pages-dry-run.ps1`, workflow example  
Disposition: `blocked_by_reproducible_build_and_parity`

Source remote одобрен: `mtr-source-v3` и Pages `main` используют один URL, но разные ветки. До Apply обязательны reproducible build command, resolved-path guards, запрет destination внутри source, manifest diff, protected `.git/.nojekyll`, approval token и post-copy parity.

## T05 — Content manifests

Upstream: `build_content_manifest.py`, `compare_content_manifests.py`  
Disposition: `adapt`

Разделить:

1. canonical logical content manifest — shared IDs/config/assets;
2. Web artifact manifest;
3. Android artifact manifest;
4. run metadata.

Fingerprint не должен зависеть от absolute root/generatedAt. Comparator проверяет schema/content/source/platform metadata и выдаёт typed mismatch categories.

## T06 — Evidence index/retention

Upstream: `index_evidence.py`, `cleanup_dry_run.py`  
Disposition: `adapted_m01_5_complete`

Полный M00 SHA index сохранён неизменным. M01.5 добавил protected/retained_recent/rotatable classification, current/index source identity, честный `UNAVAILABLE_UNTIL_M02_2` content status, три verified accepted-run links и delete-incapable path-guarded dry-run. Никакого delete до отдельного approval и backup/rollback manifest.

## T07 — PNG/asset validator

Upstream: `scan_png_assets.py`  
Disposition: `do_not_replace_existing`

Расширять текущие `validate-assets.py` и `scan_and_fix_white_matte_edges.py`: alpha/matte, enclosed white islands, trim, pivot, meta/reference, provenance, quarantine, contact sheets. Любой auto-fix сначала работает на копии/fixture.

## C01 — State machine seam

Upstream: `GameSessionStateMachine.ts`  
Перед активацией: transition table enforcement, invalid-transition result, idempotence, bounded event log, reset cleanup и adapters к существующему порядку событий.

## C02 — Audio router seam

Upstream: `AudioEventRouter.ts`  
Перед активацией: real priority queue, per-event/bus max simultaneous, cooldown clock injection, Web unlock, cancellation/reset, deterministic tests.

## C03 — Save repository seam

Upstream: `SaveRepository.ts`  
Перед активацией: backup corrupt raw payload, checksum/version validation, explicit migration failures, atomic write adapter, idempotent fixtures и запрет тихой потери данных.

## C04 — Input/collision/power-up/skin seams

Upstream: остальные TypeScript files  
Перед активацией: stable event contracts, duplicate-handler prevention, lifecycle cleanup, missing-frame hard failure in QA, Cocos-specific adapters and tests. Reference files не импортируются напрямую.

## Dependency environment

- Использовать Cocos-bundled TypeScript 3.8.8 line. Текущий воспроизводимый project-only gate: `tsc -p tsconfig.json --noEmit --skipLibCheck --lib es2020,dom --isolatedModules false`; прямой `tsc -p ... --noEmit` не является валидным gate.
- JSON Schema validator должен быть pinned в изолированном tool environment; глобальный Python не менять молча.
- CI активируется только после локальной эквивалентности команд и не должен требовать Cocos build там, где runner не воспроизводим.
