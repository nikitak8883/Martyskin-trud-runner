# Независимый аудит и рекомендуемый план после external audit v4

Дата: 2026-08-09  
Статус документа: `INDEPENDENT_AUDIT_COMPLETE / RECOMMENDED_EXECUTION_OVERLAY / RELEASE_BLOCKED`

## 1. Граница проверки

Проверены live source, встроенный external audit v4 и его manifest, текущая
ветка/HEAD, Cocos/package/lock contract, сцена, `GameRoot`, стартовый компонент,
assets/import boundaries, project scripts, quality gates, M03.2 evidence и
execution DAG. Cocos Creator, asset import, build/export, emulator, deployment,
Git merge/rebase/push и внешние сервисы не запускались.

External ZIP использован как snapshot и advisory input, а не как новый runtime
proof. Его SHA-256 `E1863AB38C6B20FDB7A548CFC3029E2049BECA199D0C0F3DC74480253FC53F80`
совпадает с sidecar; внутренний manifest подтверждён для `149/149` entries.

## 2. Независимый вердикт

`PARTIALLY_WORKING / ENGINEERING_BASELINE_USABLE / RELEASE_BLOCKED`

- Cocos source и M03.2 contract пригодны для следующего bounded strangler slice.
- Последнее принятое runtime QA относится к 2026-07-23; оно не является свежим
  доказательством текущего release candidate.
- External roadmap направленно верен, но live RDX-01 уже исправил его stale Git,
  index, JDK, schema и dependency assumptions.
- Текущий 72-unit DAG структурно валиден и ацикличен, но его `65 mandatory`
  denominator является текущей плановой базой, а не окончательным total: три
  batch-controller units должны материализовать дочерние патчи после inventory.
- Release нельзя объявлять до production identity, immutable Web topology,
  release-assurance checks и исправленной post-cleanup RC-последовательности.

## 3. Подтверждённая live база

| Область | Подтверждённый факт | Следствие |
|---|---|---|
| Engine | Cocos Creator `3.8.8` | Не обновлять engine внутри M03/TC-01. |
| Package | `playwright-core 1.61.1`; npm lockfile v3; installed version совпадает | Package/lock change для M03.3A не нужен. |
| Scene | Одна `assets/scenes/main.scene`, один enabled `GameRoot` на Canvas | Scene/meta rebinding вне M03.3A/B. |
| GameRoot | 5 434 строки; SHA-256 `BBD19424A1B1E13ABDC0A9FA689E234AD738E8DC687F267EE3624B7961BD28F1` | Только strangler extraction, не rewrite. |
| Session FSM | 14 states, 44 changed edges, 58 accepted pairs, 138 rejected, один writer | M03.2 invariant обязателен во всех следующих M03 cycles. |
| Deferred work | 15 `scheduleOnce`; reset/transition cancellation owner не формализован | M03.3B/C и M03.6/7 должны ввести epoch/cleanup ownership до удаления legacy paths. |
| Assets | `assets/resources` отделён от крупных raw pools вне `assets`; meta audit: 0 missing / 0 orphan | Не импортировать raw pools и не запускать broad asset conversion до M04. |
| Scripts | Нет project npm scripts; есть отдельные validators/generators/build/QA helpers | Каждый tool классифицировать по side effects; generators только в своём unit. |
| Android toolchain | Config ссылается на отсутствующий JDK 17.0.19; найден JDK 17.0.20; ambient JDK 21 недопустим как silent fallback | `TC-01` обязателен до Android-dependent M03.3C. |
| Git | `codex/mtr-source-freeze-v3`; `origin/main` — отдельная Pages artifact line без merge-base | Не merge/rebase; публикация только через будущую projection/deploy схему. |

## 4. Существенные расхождения и риски

1. Reference `DevEventLog` нарушает собственный payload byte bound при
   `maxPayloadBytes=2`: overflow marker сам больше лимита.
2. Reference array sanitation использует `slice()` и может выполнить accessor
   элемента; нужен descriptor-based обход.
3. JavaScript own-key discovery материализует полный список ключей до output
   limits; M03.3C обязан передавать только малые allowlisted payload literals.
4. `GameRoot` остаётся единым владельцем слишком многих подсистем; широкая
   переработка уничтожит rollback attribution.
5. `TC-01` — реальный toolchain blocker для M03.3C, но не для pure M03.3A/B.
6. `M04-C-FAMILIES`, `M05-E2`, `M10-C` скрывают неизвестное число фактических
   child patches; total нельзя объявлять окончательным до inventory.
7. Structural DAG validator доказывает schema/coverage/count/cycle invariants,
   но не semantic sufficiency gates, полноту slice и истинность evidence.
8. Текущая M12 цепочка допускает build/index до optional cleanup и не задаёт
   безопасный `cleanup waived/no-op` outcome.
9. QA7 не выделяет в явный gate dependency/license/SBOM, secret scan, platform
   exposure/data policy, asset rights и install-over upgrade continuity.
10. Release signing identity, backup ownership и upgrade policy не утверждены.
11. Fresh Web/Android evidence должно создаваться только для runtime-changing
    units; исторические green reports нельзя переносить на новый RC.

## 5. Правила декомпозиции

Каждый unit обязан иметь один owner, bounded inputs/outputs, явные dependencies,
acceptance gate, rollback map и stop conditions. Нельзя объединять units, если
ошибка одного лишает возможности атрибутировать regressions. Batch-controller
не считается implementation item: после inventory он разворачивается в
`one family/screen/optimization = one child checkpoint`, а denominator
пересчитывается без ретроспективного изменения уже принятых evidence.

Статусы различаются:

- `implementation complete` — exact diff принят;
- `engineering validation complete` — нужные static/runtime planes прошли;
- `release accepted` — отдельный RC/release gate, signing, rights и deployment;
- `conditional not applicable` — только по записанному owner decision, не PASS.

## 6. Полная рекомендуемая последовательность

### P0 — plan/toolchain hardening

#### `RDX-02` — semantic roadmap hardening

- Inputs: этот audit, live v4 DAG, M12/cleanup instructions.
- Output: уточнённый DAG с expansion policy, release-assurance units и corrected
  RC/cleanup topology.
- Acceptance: schema + negative fixtures + semantic review; source ledger не
  переписывается.
- Stop: нельзя придумывать child totals до inventory.

#### `TC-01` — fail-closed Android toolchain

- Exact-major JDK 17 discovery, approved path contract, запрет fallback на 21.
- Проверить Cocos 3.8.8, NDK 23.2.8568313, API 35, Gradle 8.11.1 без upgrade.
- Gate: config/no-build preflight; первый fresh build только в M03.3C P4.
- Rollback: вернуть только toolchain probe/config diff; не менять SDK globally.

### P1 — M03 ownership seams

#### `M03.3A` — pure bounded DevEvent contract

- Add: types, disabled-by-default ring buffer, deterministic sanitation/export,
  local behavioral test, cross-platform structural gate, Cocos metadata.
- No diff: `GameRoot`, scenes, resources, package/lock, build config.
- Gate: strict TS, boundary suite, full project no-emit, unchanged M03.2,
  canonical static gate.

#### `M03.3B` — lifecycle epoch

- Pure `LifecycleEpoch`: capture/current/advance/overflow/stale guard.
- Gate: deterministic stale acceptance/rejection; no `GameRoot` integration.
- Rollback: remove isolated module/tests/meta.

#### `M03.3C` — one GameRoot adapter

- Dependencies: M03.3B + TC-01.
- Wire only transition/reset/epoch events; release remains hard-disabled.
- Gate P4: static, fresh Web, fresh Android emulator, reset/restart loops,
  bounded export, zero duplicate events, M03.2 parity.
- Stop: any second state writer, release log, or callback ownership ambiguity.

#### `M03.4` — InputActionRouter

- One intent path for keyboard/touch/HUD/pause; preserve 220 ms debounce/order.
- Gate: duplicate-listener scan and Web/emulator input matrix.

#### `M03.5` — CollisionRouter

- Typed platform/pickup/bonus/hazard/NPC/finish events.
- Preserve current side-effect order before moving ownership.
- Gate: recorded-order fixtures plus runtime collision matrix.

#### `M03.6` — PowerUpLifecycle

- Inject tick/epoch; own spawn/collect/activate/tick/expire/cleanup.
- Gate: death/retry/reset/transition loops and no stale visual/physics effect.

#### `M03.7A` / `M03.7B` — decouple, then delete

- A proves one owner for timers/listeners/state while legacy path remains.
- B removes only proven-superseded paths after M2_PLUS, hidden-reference scan
  and rollback proof.

### P2 — assets, skins/bonuses, UI

#### `M04-A/B` — inventory and fail-visible contracts

- Canonical asset/provenance/rights/atlas/bundle registry.
- Validate alpha/matte/meta/reference/quarantine; generate manifest-bound contact
  sheets only as declared outputs.

#### `M04-C-PILOT` then `M04-C-FAMILY[n]`

- One low-risk atlas pilot, then one measured co-visible family per child.
- Each child: inventory identity, before metrics, transform, Web/emulator visual
  parity, draw/memory/load/artifact metrics, rollback.
- Instantiate `n` after M04-A/B; update execution denominator then.

#### `M04-D/E/CLOSE`

- Dynamic atlas only by measured allowlist.
- Explicit bundle preload/load/release/content-version owner.
- Close on draw-call, waste, memory, load and build-size evidence.

#### `M06-A..F` — skins and bonuses before UI migration

- Stable SkinRegistry → baked-primary BonusVisualResolver → full frame routing →
  lifecycle loops → selected bundle residency → old stack removal last.
- Required matrix: eight skins × poses × bonuses on Web/emulator.

#### `M05-A..D`, `M05-E-BATCH[n]`, `M05-F`

- Tokens/9-slice allowlist → SafeArea owner → Layout → shared renderer.
- Materialize one bounded non-HUD screen batch per child after UI inventory.
- Gameplay HUD last; close with 14 screens × five viewports, Cyrillic/touch/mask,
  overdraw and no ghost layers.

### P3 — content, feedback, persistence

#### `M07-A..G`

- All-level schema; level 1/8/15 pilot; deterministic remaining batches;
  current/next preload and previous release.

#### `M08-A..F`

- Audio/VFX inventory/maps/buses → deterministic cooldown/priority/limits →
  legacy adapters → readability budgets → pooling/lifetime cleanup → Web unlock
  and soak.

#### `M09-A..G`

- Versioned profile-scoped save envelope/checksum → stable achievement/record
  manifests → idempotent backup migration → corruption/unknown-version recovery
  → UI separation/profile isolation → bounded local QA telemetry → golden tests.
- No network telemetry without a separate product/privacy decision.

### P4 — measured performance

#### `M10-A/B`

- Reproducible Web/emulator budgets and baseline; rank measured bottlenecks.

#### `M10-C-OPT[n]` / `M10-D/E`

- One optimization family per child; instantiate after profiling.
- Reject no-benefit or quality-regressing changes.
- Finish with module regression, restart loops and release soak.

### P5 — release assurance and corrected RC chain

#### `RA-01` — dependencies, licenses, SBOM and secrets

- Inventory direct/transitive production dependencies and licenses; machine SBOM;
  bounded secret scan with reviewed false positives; no credential contents in evidence.

#### `RA-02` — platform/network/data exposure

- Android permissions, exported components, cleartext/network policy and declared
  data handling; Web third-party requests/CSP/headers where applicable.

#### `RA-03` — asset rights closure

- Every shipped visual/audio/font has owner, source/provenance, allowed use and
  release disposition; unresolved rights block publication.

#### Corrected `M12/M02` order

1. `M12-A`: immutable candidate source/content/toolchain freeze.
2. `M12-B`: independent QA7 RC1.
3. `M12-C`: bounded fixes only.
4. `M12-D`: re-freeze after fixes.
5. `M12-E`: independent QA7 RC2.
6. `M12-F`: build verified Web + production-valid arm64 APK; AAB conditional.
7. `M12-CLEAN-PLAN`: protected post-build cleanup dry-run and owner choice:
   approved batches or explicit `waived/no-op`.
8. `M12-CLEAN-APPLY`: apply only approved batches. If source changes, require a
   new freeze, targeted/full gates, rebuild and artifact re-index; if no-op,
   retain the prior immutable identity with a signed decision record.
9. `M02-WEB`: deterministic source projection, immutable Pages artifact and live
   manifest parity; never merge/rebase unrelated `main` history.
10. `RA-04`: install-over/upgrade continuity for the approved signed APK/package
    identity and save migration; AAB path only when Play is approved.
11. `M02-RC`: bind source/content/artifact hashes, ABI/version/certificate,
    deployment identity, rights and limitations.
12. `M12-FINAL`: final evidence index, protected archive and release summary.

### Conditional scope

- `M02-AAB`: only after explicit Google Play approval.
- `M10-PHYSICAL`: only after explicit physical-device authorization.
- `M11-A..E` (expanded as needed): PCG/DDA remains disabled-by-default and does
  not block the base release.

## 7. Стоимость и сроки

| Scope | Incremental software/service cost | Planning range |
|---|---|---|
| M03.3A/B and local static gates | `0`: existing local Cocos/Node/Python, no new dependency | days, not weeks |
| TC-01 | `0`: configuration/probe only | 2–4 engineering days |
| Mandatory engineering roadmap | Labor dominates; hosted quotas/subscriptions are not assumed free | approximately 38–60 engineering weeks, provisional |
| Google Play/AAB | Conditional; account/service terms must be checked when approved | outside mandatory base |
| External advisory review | Optional, privacy-gated, may be paid | not an acceptance dependency |
| New/licensed assets | Unknown until M04/RA-03 rights inventory | owner decision |

Ranges are estimates, not release promises. Calendar duration depends on the
number of family/screen/optimization children, defects, owner decisions and
fresh runtime QA. No purchase is required for M03.3A.

## 8. Acceptance policy for the nearest cluster

`M03.3A` is accepted only when all are true:

1. exact/frozen 12-code registry and disabled default;
2. validated config boundaries and fixed-capacity deterministic ring;
3. finite/plain-data sanitizer never executes property/array accessors;
4. payload and export enforce serialized UTF-8 byte limits, including minimum 2;
5. snapshots/events/payload copies are immutable; serialization is stable;
6. `clear()` preserves monotonic sequence within the log instance;
7. strict module TS and complete-project no-emit pass;
8. M03.2 matrix remains 14/58/138/1;
9. canonical 12-step static gate passes;
10. zero diff to GameRoot, scenes, resources, package/lock and build configs;
11. Cocos editor/import/build/runtime/deploy remain unexecuted for this pure unit;
12. rollback is removal of the isolated qa contract, validators, gate entry and
    evidence/status overlay only.

После acceptance следующий безопасный unit — `M03.3B`; `TC-01` выполняется
параллельно и остаётся обязательным до `M03.3C`.
