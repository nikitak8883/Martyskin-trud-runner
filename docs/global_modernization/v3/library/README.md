# MTR v3 curated planning library

Эта папка содержит только безопасный project-local subset Tasks/5.

## Активные части

- `templates/` — шаблоны отчётов; допускается адаптация под проект.
- `drafts/schemas/` — предлагаемые JSON schemas, пока не канонические.
- `drafts/reference_code/typescript/` — компилируемые reference seams, не runtime implementation.

## Жёсткие границы

- Ничего под `drafts/` нельзя импортировать из `assets/` или считать активным contract без M01 schema/adaptation gate.
- Внешние PowerShell/Python scripts и workflows намеренно не скопированы в project tools.
- Live AGENTS, lore, v2 manifests и принятые validators имеют приоритет.
- Source package сохраняется в Tasks/5; эта папка не зеркалирует весь архив.

## Проверено

- 9 JSON schema files parse как JSON;
- 8 TypeScript files проходят Cocos-bundled TypeScript `--noEmit --strict --target ES2020`;
- 6 templates скопированы без изменения;
- исходные SHA-256 подтверждены внутренним manifest пакета.

## До активации

Следовать `../TOOL_AND_CODE_ADAPTATION_BACKLOG.md` и `../WORK_PACKAGE_INDEX.yaml`. Любая схема получает canonical `$id`, version/migration policy, fixtures и negative tests. Любой reference seam получает adapter к текущему `GameRoot.ts` и parity tests.
