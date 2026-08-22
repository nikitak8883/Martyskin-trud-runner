# Интегрированная дорожная карта v4

## Текущее положение

- Source ledger: `28/95 complete`; mandatory `28/85`, осталось `57`; conditional `10`. `M04.5` остаётся pending до закрытия remaining family children.
- V4 remaining-scope execution ledger: `16/68 complete`, осталось `52`; conditional units `7`. Знаменатель расширен на inventory-derived children `M04-C-FAMILY-ACHIEVEMENT-UI`, `M04-C-FAMILY-RUNNER-COLLECTIBLES` и `M04-C-FAMILY-BONUS-ITEMS` и остаётся provisional для следующих M04/M05/M10 children.
- Текущий milestone: `M04-C-FAMILY-BONUS-ITEMS` complete; после `objective_npc`, `achievement_ui` и `runner_collectibles` принят четвёртый measured family `bonus_items` через два directory-local static atlas descriptors, final comparison `63/63`, P4 и M2_PLUS зелёные.
- Следующий unit: продолжение `M04-C-FAMILIES` — один новый accepted measured family на изолированный child checkpoint; broader batching не разрешён.
- Release: `BLOCKED`.

## Phase 0 — contracts, toolchain и publication model

### `RDX-01` — complete

- безопасный ingest v4;
- live drift/Git topology reconciliation;
- исправление v3 indexes;
- machine-readable v4 execution DAG;
- library adoption/rejection manifest;
- schema-first roadmap validator и отрицательные тесты;
- исторический 11-step static gate и повторный plan audit; текущий cumulative gate содержит 20 steps.

### `TC-01` — complete

Техническое задание:

1. закрепить точный Adoptium JDK `17.0.20`, approved path и SHA-256 критичных JDK-файлов;
2. запретить молчаливый fallback на любой ambient Java (текущая приемка наблюдает JDK 21, но ambient-версия не входит в build identity);
3. различать ambient Java и Android build Java в toolchain report;
4. проверить Cocos `3.8.8`, NDK `23.2.8568313`, API 35, Gradle wrapper `8.11.1`;
5. выполнить no-build config/preflight; fresh export/build остаётся обязательным deferred postcondition первого Android-dependent P4 (`M03.3C`);
6. не менять SDK/Cocos/Gradle версии в этом пакете.

### `PUB-01` — встроен в M02.7/M12

- воспроизводимый project-prefix tree projection;
- baseline tree equality proof;
- manifest diff и deny-list;
- dry-run against `origin/mtr-source-v3`;
- отдельный immutable Pages artifact deployment в `main`;
- никаких merge/rebase unrelated histories.

## Phase 1 — M03 ownership seams, 5–9 недель

1. `M03.3A` — complete: pure DevEvent types, validated bounded ring buffer, deterministic tests.
2. `M03.3B` — complete: pure lifecycle epoch + synchronous-entry stale callback guards/tests.
3. `M03.3C` — complete: один GameRoot adapter, release-off policy, reset/transition integration, полный P4.
4. `M03.4` — complete: один input router с сохранённым debounce/touch/keyboard order.
5. `M03.5` — complete: typed collision events без перестановки legacy order.
6. `M03.6` — complete: power-up lifecycle с injected tick/epoch, cleanup и Web/Android parity.
7. `M03.7A` — complete: typed UI intents, единый lifecycle owner и Web/Android cleanup parity при сохранённых legacy paths.
8. `M03.7B` — complete: hidden-reference/rollback proof, удалён только duplicate callback-guard layer; QA7 `7/7`, M2_PLUS `12/12`.

## Phase 2 — M04 → M06 → M05, 10–17 недель

### M04 assets

- inventory + canonical ownership/provenance schema;
- alpha/matte/meta/reference/quarantine validator;
- contact sheets;
- measured atlas pilots и family batches;
- dynamic atlas allowlist;
- bundle load/release ownership;
- before/after draw-call, memory, load, waste и artifact-size evidence.

### M06 skins/bonuses

- stable SkinRegistry IDs;
- baked-primary BonusVisualResolver;
- full frame routing and fail-visible missing frame;
- 8 skins × poses × bonuses Web/Android emulator matrix;
- switch/expire/death/retry/transition loops;
- selected bundle residency/release proof;
- old visual stack removal last.

### M05 UI

- tokens + 9-slice policy;
- SafeArea owner;
- layout containers;
- shared renderer/components;
- low-risk screen batches;
- gameplay HUD last;
- 14 screens × 5 viewports, Cyrillic, touch, masks, overdraw, no ghost layers.

## Phase 3 — M07 → M08 → M09, 8–14 недель

- M07: schema for all 15 levels, level 1/8/15 pilot, three migration batches, preload/release policy.
- M08: audio/VFX inventory and maps, buses/limits/cooldowns, adapters, pooling, Web unlock and soak.
- M09: storage inventory, versioned save envelope, achievements/records, idempotent backup migration, corruption/unknown-version recovery, profile isolation, bounded local QA telemetry.

## Phase 4 — M10, 4–7 недель

- budgets + reproducible Web/emulator baseline;
- measured bottleneck ranking;
- one optimization family per patch;
- reject no-benefit/quality-regressing changes;
- final performance regression/soak.

Physical device remains conditional and requires a separate command.

## Phase 5 — M02/M12 release closure, 3–6 недель + owner wait

1. signing/backup/upgrade ADR;
2. RC source/tag/content freeze;
3. independent QA7 RC1;
4. bounded fixes and independent QA7 RC2;
5. production-valid arm64 APK; AAB only if Play becomes approved;
6. deterministic source projection and immutable Pages deployment;
7. live manifest parity/smoke;
8. artifact/evidence index;
9. cleanup dry-run, owner-selected apply batches, rebuild/regression;
10. protected archive and final limitations.

## Conditional Phase 6 — M11, +8–14 недель

PCG/DDA не блокирует базовый release. Запускается только после отдельного решения: deterministic schema, reachability validator, seeded replay, 1000-seed fuzz, optional feature-flagged DDA and comparative telemetry.

## Правило продвижения

Ни один unit не становится complete без свежего gate, bounded rollback и machine-readable report. Полный порядок и зависимости находятся в `EXECUTION_UNIT_INDEX.json`.
