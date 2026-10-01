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

### T07.1 — Byte-stable PNG serialization

Disposition: `implemented_targeted_pass_hosted_receipt_required`. Shared tool-only
Pillow12.3.0 + locked zlib-ng1.0.0/codec2.2.5 serializer preserves original PNG
bytes without refreshing provenance/goldens or changing runtime assets. Full
29-sheet regeneration and reviewed normalization pass; negative container/codec
controls remain fail closed. See `docs/qa/PNG_SERIALIZATION_CONTRACT_20261001.md`.
Final source-pinned hosted gate is separate from local diagnostic qualification.

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

### C05 — Android native bootstrap readiness/recreation

New observed follow-up `ANDROID-NATIVE-BOOTSTRAP-001`: confirmed cold boot alone
does not guarantee a ready first native activity. Immediate first-menu QA failed
`27/28`; a separate settled cold-boot matrix passed `28/28`. Both remain evidence.
See `docs/qa/ANDROID_NATIVE_BOOTSTRAP_001_20261001.md`. Investigate and establish
the native lifecycle acceptance boundary before logistics attempt02 input
admission/final `M12.7`; do not hide the failure with a retry or longer timeout.
This is a prerequisite within existing units, not a new completed roadmap item.

### C06 — Atlas harness terminal timer ownership

Disposition: `implemented_and_runtime_qualified`. The atlas Web runtime function
now clears its 45s terminal timer on success/error; `10/10` tests verify ID
isolation and terminal ownership without filesystem writes. CLI overhead is not
the measured game load metric. Attempt02 protocol revision3 records/pins this
correction, preserving both predecessors. No metric collection interval changes.

## Dependency environment

- Cocos-specific project compilation retains the Creator3.8.8 bundled compiler/engine definitions. Pure Node contract tests use the isolated `tools/codex/node-test-toolchain` lock with TypeScript5.8.2, byte-identical main compiler to this Creator installation; no ambient/global fallback. Текущий воспроизводимый project-only gate: `tsc -p tsconfig.json --noEmit --skipLibCheck --lib es2020,dom --isolatedModules false`; прямой `tsc -p ... --noEmit` не является валидным gate.
- JSON Schema validator должен быть pinned в изолированном tool environment; глобальный Python не менять молча.
- CI активируется только после локальной эквивалентности команд и не должен требовать Cocos build там, где runner не воспроизводим.

### CI portability follow-up — current local prerequisites

Implemented: locked compiler/default loader for nine tests, pre-execution SHA and
version checks/negative controls; `.pac` LF checkout with binary-byte preservation
roundtrip; symlink/junction cleanup retaining the outside sentinel; M03.7B source-
projection proof with exact whole-tree/10blob equivalence and ancestry checks.
Original cleanup/provenance/atlas contracts stay immutable. Four cycles pass
`19/19 +18/18 +14/14`; hosted acceptance must bind to the new published source.

Still open: Linux reviewed-PNG reproduction raw SHA and contact-sheet canonical
index portability. Diagnose serializer/encoder/input pin differences separately;
do not rewrite raw provenance or replace exact-byte gates with pixel-only checks
to get green CI. Then return to `ANDROID-NATIVE-BOOTSTRAP-001` and atlas attempt02.
