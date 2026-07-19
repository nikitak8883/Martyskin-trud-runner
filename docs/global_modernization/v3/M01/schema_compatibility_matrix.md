# M01.2 — schema compatibility matrix

Дата: 2026-07-19  
Статус: `PASS / M01.2 COMPLETE / M01.3 COMPLETE / M01.4 READY`  
Область: contracts, adapters, fixtures, tests и project-local typed runner; game runtime, builds, Pages и Android-устройства не изменялись.

## Решение

Канонический namespace quality evidence:

```text
https://schemas.mtr.local/quality/v1/
```

Нативные отчёты валидаторов сохраняются без переписывания. Одобренный adapter читает их как immutable input и создаёт `mtr.quality_evidence_envelope` v1, содержащий:

- исходную schema/version, project-relative path и SHA-256 отчёта;
- source commit и logical content version;
- platform/target/profile identity;
- tool path, SHA-256, typed command id, strict-mode и фактические flags;
- start/finish/duration;
- только `PASS`, `FAIL` или `BLOCKED`;
- typed findings с field/path/expected/actual/fix.

`PASS` запрещён для stale, non-applicable, source-mismatched, target-mismatched или blocking evidence. Неизвестная/битая схема не конвертируется в green envelope, а возвращает typed adapter error.

## Канонические schemas

| Schema | `$id` | Назначение |
| --- | --- | --- |
| `quality_evidence_envelope.schema.json` | `.../quality-evidence-envelope.schema.json` | единый immutable result contract |
| `quality_adapter_registry.schema.json` | `.../quality-adapter-registry.schema.json` | source→adapter ownership и migration policy |
| `quality_fixture_suite.schema.json` | `.../quality-fixture-suite.schema.json` | positive/negative fixture contract |

Все три используют JSON Schema Draft 2020-12, имеют уникальный canonical `$id` и запрещают неизвестные top-level поля.

M01.3 добавляет два canonical runner contracts: `quality_gate_config.schema.json` для executable/argument arrays и `quality_gate_report.schema.json` для atomic source-bound результата. Итого canonical quality schemas: `5`.

## Активная compatibility matrix

| Current source shape | Canonical source name | Adapter | PASS rule | False-green защита |
| --- | --- | --- | --- | --- |
| `mtr.asset_validation.v1` | без изменения | `asset_validation` | blockers/references/matte = 0 | требует strict invocation, `--fail-on-white-matte`, strict native policy |
| `mtr.skin_bonus_matrix_validation.v1` | без изменения | `skin_bonus_matrix` | 576/576-equivalent count parity, blockers/warnings = 0 | требует `--fail-on-warnings` и `policy.failOnWarnings=true` |
| `mtr.ui_ir_validation.v1` | без изменения | `ui_ir_validation` | problemCount=0 и full screen coverage | warnings остаются видимыми; profile promotion отложен до M01.4 |
| `statusSchemaVersion: 2` | `mtr.android_toolchain_status.v2` | `android_toolchain_status` | `qaReady=true`, blockers=0 | требует `-FailOnNotReady`, emulator-only policy и target serial binding |
| `mtr.android_emulator_matrix.v1` | без изменения | `android_emulator_matrix` | status/pass/case parity, zero failures | physical serial и target mismatch дают `BLOCKED` |
| `mtr.android_emulator_interaction.v1` | без изменения | `android_emulator_interaction` | touch/name/restart/soak all pass | guard, exact emulator serial, full restart/soak/process-liveness required |
| `mtr.web_matrix_interaction.v1` | без изменения | `web_matrix_interaction` | aggregate, interaction и restart parity | aggregate `pass` без подциклов не принимается |
| `mtr.web_soak.v1` | без изменения | `web_soak` | complete duration, input>0, no console diagnostics | adapter создаёт explicit status, которого нет в native report |
| topology `schema_version: 1` | `mtr.git_topology.v1` | `git_topology` | parent source, gitlink, clean Pages HEAD agree | source commit и Pages identity обязательны |
| `mtr_source_content_fingerprint` v1 | `mtr.source_content_fingerprint.v1` | `source_content_fingerprint` | commit/content/aggregate identity valid | mismatch даёт `BLOCKED`, не исторический PASS |
| schema-less `runtimeReady` probe | `mtr.web_runtime_probe.legacy` | `web_runtime_probe_legacy` | runtime and requested marker explicitly ready | `runtimeReady=false` при process exit 0 становится `FAIL` |

## Неактивные источники

| Class | Source shapes | Политика |
| --- | --- | --- |
| `historical_only` | `mtr.module3_emulator_skin_bonus_qa.v1`, `mtr.web_playwright_qa.v1`, `mtr.qa.web_cycle.v1`, `mtr.qa.pause_checkpoint.v1`, `mtr.skin_contact_sheets.v1` | индексировать для истории, не принимать как current standalone PASS |
| `data_not_quality_evidence` | `mtr.player_skins.v1`, `mtr.ui_ir.screen.v1` | runtime/content data требует отдельного validator evidence |

Registry содержит ровно `18` классифицированных source families: `11 active`, `5 historical_only`, `2 data_not_quality_evidence`.

## v2/current/v3 reconciliation

- v2 module 10 разделён в v3 на M00 source recovery и M01 quality gate; старые отчёты не удаляются.
- Working current validators остаются владельцами native shape и exit semantics.
- v3 владеет только canonical envelope, registry, adapters и profile composition.
- Upstream `quality_gate_config.schema.json` и `release_gate_result.schema.json` остаются под `library/drafts/`: строковые commands несовместимы с обязательными typed executable/argument arrays. Их promotion принадлежит M01.3/M01.4.
- Runtime/content drafts (`save`, `skin`, `level`, `audio`, state machine) не активируются M01.2 и принадлежат своим модулям.

## Migration rules

1. Native report всегда сохраняется как source artifact; adapter не мутирует его.
2. M01.3 runner вычисляет report/tool SHA-256, times, source/content identity и target identity, затем вызывает adapter.
3. Adapter registry dispatch только по allowlisted source schema; `eval`, shell strings и heuristic PASS отсутствуют.
4. Missing/unknown/malformed/path-traversal input даёт typed error.
5. Stale, commit drift, target drift, missing strict flag и unauthorized physical target дают `BLOCKED` с blocking finding.
6. Native product/test failure даёт `FAIL` с blocking finding.
7. Только applicable + fresh + source-bound + target-bound evidence без blockers получает `PASS`.

## Fixtures и проверка

| Layer | Result |
| --- | --- |
| Canonical schema documents | 3/3 parse; namespace/IDs/top-level closure checked |
| Registry parity | 18/18 classified; 11/11 active handlers implemented |
| Positive fixtures | 11/11 → deterministic `PASS` |
| Negative fixtures | 20/20 → expected `FAIL`, `BLOCKED` или typed error |
| Deterministic rerun | 25/25 envelope-producing fixtures byte-structurally identical in memory |
| Runtime-guard mutations | 3/3 invalid envelopes rejected |
| Existing report-shape smoke | 9/9 current representative JSON shapes accepted |

Representative report smoke доказывает только совместимость shape. Он не переименовывает старые reports в свежий QA текущего HEAD.

## M01.3 activation overlay

- `tools/codex/quality-gate/runner.py` исполняет только typed arrays с `shell=False` и отдельными stdout/stderr captures;
- timeout завершает полное дерево процессов; Windows child-survival fixture подтверждает отсутствие остаточного процесса;
- config/cwd/output/evidence/artifact paths остаются под project root, UNC/ADS/device/traversal/symlink escape и output collisions блокируются;
- source HEAD/dirty state и hashes protected config/schema/adapter/registry/tool inputs повторно проверяются после шагов;
- stale/missing/malformed/mandatory-skipped/unauthorized-device evidence не может получить `PASS`;
- report валидируется pinned isolated Draft 2020-12 engine до atomic replacement.

## Dependency boundary

Глобальный Python не изменялся. M01.3 создаёт hash-addressed user-cache venv из exact `requirements.lock`; принят `jsonschema==4.26.0` с Draft 2020-12 и offline registry. Два конкурентных cold starts создают ровно одну валидную среду и не оставляют lock. Dependency M01.3 закрыт; profile policy принадлежит M01.4.

## Rollback

Никакие current validators или consumers не переключены на новый contract. Rollback M01.2 — удалить созданные `schemas/`, `adapters/`, `fixtures/`, `tests/` и этот matrix одним bounded revert; существующие QA команды продолжат работать без изменений.
