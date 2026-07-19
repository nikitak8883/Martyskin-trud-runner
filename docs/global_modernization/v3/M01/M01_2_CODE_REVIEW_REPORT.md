# M01.2 code-review report

Дата: 2026-07-19  
Итог: `PASS FOR BOUNDED M01.2 / M01.3 NOT YET IMPLEMENTED`

## Diff scope

- 3 canonical Draft 2020-12 schemas;
- 18-entry adapter registry;
- 11 dependency-free active adapters and canonical envelope runtime guard;
- 11 positive + 20 negative fixtures;
- deterministic contract/self-test;
- compatibility and library documentation.

Runtime, Cocos assets/scripts, native project, Web build, Pages, Android build/emulator/device и release outputs не затронуты.

## Review cycle 1 — adapter/runtime guard

Локальный Lemonade coding reviewer сообщил 3 potential issues:

1. `_require_path` якобы не проверяет итоговый тип — отклонено как false positive: проверка присутствовала изначально.
2. Path guard мог быть понятнее и строже — принято. Проверка перенесена на raw normalized segments; запрещены empty/dot/parent/NUL/ADS segments, absolute/drive paths.
3. Missing `source_report` якобы мог дать `KeyError` — прямого `KeyError` не было, потому что context валидируется до dispatch. Тем не менее error taxonomy исправлена: missing/wrong context теперь даёт `INVALID_CONTEXT`, а malformed native report — `MALFORMED_SOURCE`.

Добавлены negative fixtures для wrong native type и missing trusted report context. После правок второй локальный review: `potential_bugs=0`, verdict `accept`.

## Review cycle 2 — schemas/registry

Reviewer дважды сообщил неподтверждённые замечания об усечённом registry и отсутствующих constraints. Фактическая проверка:

- registry и schemas парсятся как JSON;
- `source_report.schema_name` и `schema_version` имеют `type=string` + `minLength=1`;
- PowerShell 7.6.3 `Test-Json` принимает registry, обе fixture suites и generated envelope;
- permissive Draft 2020 boolean schema для finding `expected/actual` была валидной, но заменена явным union всех JSON types для читаемости;
- envelope schema дополнительно кодирует conditional invariants: stale/non-applicable/blocking evidence не может иметь `PASS`, а `FAIL/BLOCKED` требует blocking finding;
- fixture schema условно требует `status` для envelope и `error_code` для adapter error.

Оставшиеся schema-review сообщения классифицированы как false positives от усечённого advisory context и не превращены в изменения без доказательства.

## External CodeRabbit status

CodeRabbit CLI отсутствует. Предписанный installer требует `sh`; в текущей Windows-среде отсутствуют `sh`, `bash` и WSL. Поэтому CodeRabbit review не запускался и не заявляется как пройденный. Это не блокирует bounded M01.2, поскольку выполнены независимые deterministic checks и локальный second-pass review, но prerequisite явно сохранён.

## Architecture findings

| Check | Result |
| --- | --- |
| Unknown schema can become PASS | PASS — rejected with `UNSUPPORTED_SCHEMA` |
| Historical/data document can become current PASS | PASS — rejected with `NON_ACTIVE_SOURCE` |
| Exit-zero false-ready Web probe | PASS — `runtimeReady=false` becomes `FAIL` |
| Android loose toolchain invocation | PASS — missing strict flag becomes `BLOCKED` |
| Physical device accepted as emulator | PASS — target policy becomes `BLOCKED` |
| Stale/source drift | PASS — blocking findings and no PASS |
| Absolute/traversal/ADS path | PASS — rejected before dispatch |
| Shell-composed command | PASS — none; only command id and flags metadata |
| Adapter writes files/processes | PASS — none; CLI outputs stdout only |
| Runtime imports docs library | PASS — none introduced |
| Registry/code drift | PASS — 11/11 handlers exact parity |

## Validation evidence

- Python in-memory compile: 2/2.
- Contract test: PASS.
- Positive fixtures: 11/11.
- Negative fixtures: 20/20.
- Deterministic envelope reruns: 25/25.
- Invalid-envelope mutations rejected: 3/3.
- Existing report-shape smoke: 9/9, compatibility claim only.
- `Test-Json`: registry, positive suite, negative suite, representative envelope — 4/4 PASS.
- Existing static regression: config 15/15, Cocos TypeScript, assets 1528/0, skins 576/576, UI IR 14/14, icons 15/15 and Git topology — PASS.
- `git diff --check`: PASS.

## Accepted limitation / next gate

Python `jsonschema`/`fastjsonschema` отсутствуют глобально и не устанавливались. M01.3 обязан закрепить isolated pinned Draft 2020-12 engine рядом с typed runner. До этого новые adapters являются неактивной project-library реализацией и не могут выдавать release PASS.

## Verdict

M01.2 соответствует bounded objective, имеет rollback и закрывает schema/adapter/fixture seam. Следующий допустимый пакет — M01.3 typed runner. Release status остаётся blocked.
