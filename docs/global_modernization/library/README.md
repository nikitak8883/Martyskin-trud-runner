# Tasks/4 modernization library — project-local normalized copy

Generated: 2026-07-02 15:44 +03:00  
Source: `C:\Projects\Monkey Work\Tasks\4\_unpacked_20260702_145527\MTR_CODEX_GLOBAL_MODERNIZATION_LIBRARY_v2`

This folder keeps the project-local operational subset of the Tasks/4 modernization library. It is intentionally documentation/schema/checklist only. It is not runtime game content.

## Contents

- `QA_MATRIX.md`
- `CODE_REVIEW_CHECKLIST.md`
- `RELEASE_GATE_CHECKLIST.md`
- `schemas\ui_ir.schema.yaml`
- `schemas\skin_manifest.schema.json`
- `schemas\atlas_manifest.schema.json`
- `schemas\qa_result.schema.json`

## Policy

- Treat these files as local project contracts.
- Runtime implementation must be validated against these contracts module-by-module.
- If the source Tasks/4 package changes, update this local copy through an explicit audit and record the source SHA-256.
- Do not place generated build outputs, binary assets, screenshots, or temporary logs in this folder.

