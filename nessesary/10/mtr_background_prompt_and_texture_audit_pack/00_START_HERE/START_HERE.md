# START HERE — Background Prompts + Texture Pack Audit

## Что внутри

```text
01_PROMPTS/MTR_BACKGROUND_MASTER_PROMPTS_ALL_15_LEVELS.md
01_PROMPTS/per_level/*.md
02_AUDIT/MTR_TEXTURE_PACK_9_MISSING_TEXTURES_AUDIT.md
03_CONFIG/uploaded_pack_9_asset_summary.json
04_CODEX_PROMPTS/CODEX_BACKGROUND_GENERATION_PROMPT.md
```

## Как использовать

1. Сначала прочитать audit по `9.zip`.
2. Затем использовать per-level prompt для нужного уровня.
3. Генерировать не одну картинку, а 8 PNG на уровень:
   - 5 base layers;
   - 3 progression prop sheets.
4. Для transparent PNG требовать true RGBA alpha, не checkerboard.
