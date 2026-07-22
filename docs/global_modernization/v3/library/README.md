# MTR v3 curated planning library

Эта папка содержит только безопасный project-local subset Tasks/5.

## Активные части

- `templates/` — шаблоны отчётов; допускается адаптация под проект.
- `schemas/` — canonical M01 quality-evidence и typed-runner contracts с versioned `$id`.
- `adapters/` — allowlisted, dependency-free adapters current reports в canonical envelope; активируются только project-local M01.3 runner.
- `fixtures/quality_evidence/` — positive/negative contract fixtures.
- `tests/validate_m01_2_contracts.py` — deterministic registry/adapter/runtime-guard self-test.
- `drafts/schemas/` — предлагаемые JSON schemas, пока не канонические.
- `drafts/reference_code/typescript/` — компилируемые reference seams, не runtime implementation.

## Жёсткие границы

- Ничего под `drafts/` нельзя импортировать из `assets/` или считать активным contract без M01 schema/adaptation gate.
- Ничего под `adapters/` нельзя импортировать из `assets/`; activation выполняет только `tools/codex/quality-gate/`, не Cocos runtime.
- Внешние PowerShell/Python scripts и workflows намеренно не скопированы в project tools.
- Live AGENTS, lore, v2 manifests и принятые validators имеют приоритет.
- Source package сохраняется в Tasks/5; эта папка не зеркалирует весь архив.

## Проверено

- 17 JSON schema files (canonical plus drafts) parse как JSON;
- 8 canonical quality schemas проходят pinned Draft 2020-12 validation; M01.3/M01.4 runner/profile self-tests и fail-closed mutations проходят;
- M01.5 retention tool классифицирует 801/801 indexed evidence files без delete capability; path/drift guards и 13-test suite проходят;
- M01.6 один typed static command проходит локально 7/7 и используется без расхождений в Windows/Linux Actions matrix;
- M01.7 fail-closed summary корректно блокирует release при 8 отсутствующих mandatory evidence slots;
- M02.2 shared content identity проходит 3/3 Web/Android preflights и обязательный восьмой local/Windows/Linux static gate;
- 8 TypeScript files проходят Cocos-bundled TypeScript `--noEmit --strict --target ES2020`;
- 6 templates скопированы без изменения;
- исходные SHA-256 подтверждены внутренним manifest пакета.

## Следующий слой

Следовать `../TOOL_AND_CODE_ADAPTATION_BACKLOG.md` и `../WORK_PACKAGE_INDEX.yaml`. M03.1 read-only GameRoot inventory завершён; следующий bounded package — M03.2 typed session-transition adapter. Остальные runtime seams активируются только по одному после adapter parity gates.
