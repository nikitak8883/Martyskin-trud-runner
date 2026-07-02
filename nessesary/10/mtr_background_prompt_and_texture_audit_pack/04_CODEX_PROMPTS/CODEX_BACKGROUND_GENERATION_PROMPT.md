# Codex Prompt — Background Generation + Texture Audit

Используй `MTR_BACKGROUND_MASTER_PROMPTS_ALL_15_LEVELS.md` как источник промтов для генерации инженерно-правильных фонов.

Для каждого уровня создавать:

```text
levelXX_bg_far.png
levelXX_bg_mid.png
levelXX_bg_near.png
levelXX_track_backdrop.png
levelXX_grade_fog.png
levelXX_props_start.png
levelXX_props_mid.png
levelXX_props_end.png
```

Требования:

- сохранять канон уровня;
- не менять названия уровней;
- соблюдать стиль последнего texture pack;
- true RGBA alpha для transparent layers;
- no checkerboard;
- no white matte;
- no UI/player/HUD in backgrounds;
- Russian-only readable text.

Перед интеграцией `9.zip` учесть audit: первые 30 PNG не имеют настоящего alpha channel.
