# CODEX_ANDROID_UPDATE_MASTER_TASK.md

## Mission

Держать Martyskin Trud Runner в единой Cocos Creator runtime-схеме для Android и Web: один набор конфигов, один набор уровней, один канон ассетов, без старых фоновых экранов, старых player skin fallback-ресурсов и устаревших release-ссылок.

## Active Inputs

- `assets/resources/config/levels.json` - 15 уровней, синхронизированных с `nessesary/10/mtr_level_canon_manifest.json`.
- `assets/resources/config/strings_ru.json` - русские UI-строки.
- `assets/resources/config/bonus_visual_states.json` - визуальные состояния бонусов.
- `assets/resources/config/background_manifest_texture10.json` - текущий manifest новых фонов.
- `assets/resources/backgrounds/level01.jpg` ... `level15.jpg` - runtime-фоны 1920x886.
- `assets/resources/backgrounds_preview/level01.jpg` ... `level15.jpg` - preview-фоны 640x295.
- `assets/resources/objectives/themed/last_iteration/` - тематические игровые объекты, вырезанные из `nessesary/9`.
- `assets/resources/characters/player_skins/` - единственный активный namespace скинов игрока; `player_skins_v2` допустим только как code-level redirect для старых ключей.
- `nessesary/10/Levels/` - исходные PNG-фоны по номерам уровней.
- `tools/asset_generation/build_martyshkin_texture10_backgrounds.py` - воспроизводимый pipeline фонов.
- `tools/mtr_last_iteration_asset_pipeline.py` - воспроизводимый pipeline объектных текстур `nessesary/9`.

## Rules

1. Android и Web используют одинаковые `assets/resources/config/*`.
2. Retired background families, procedural background fallback and retired skin namespaces do not return.
3. Retired background seed prompts are not a source for backgrounds: the active source is `nessesary/10/Levels`.
4. Не заменять фон градиентом, сеткой или абстрактным экраном.
5. Не удалять русские надписи, но старые конфликтующие строки после замены не оставлять.
6. Не делать бананы лимонами и не делать примата без ног.
7. Release APK и Web release должны собираться из чистого Cocos build, а не из старых экспортов.

## Required Order

1. Прочитать `AGENTS.md` и обязательные документы из него.
2. Проверить shared configs и runtime namespaces.
3. Проверить `GameRoot.ts`: загрузку фонов, меню, старт игры, player skin namespace, обработчики ввода, cleanup listeners.
4. Проверить объектные пулы уровней и соответствие тем.
5. Проверить сборочные зависимости Android/Web.
6. Собрать Web и Android.
7. Выполнить минимум 4 QA-цикла.
8. Выполнить post-cleanup.
9. Повторить old-value scan.

## Acceptance

- Android запускается и проходит меню -> старт -> gameplay.
- Web запускается локально и с GitHub Pages.
- Все 15 уровней имеют новые тематические bitmap-фоны.
- Кнопка запуска видима на главном меню.
- Retired level names, retired background manifests, retired skin namespaces and retired APK links are absent from the active workspace.
- APK лежит в `releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk`.
- Web лежит в `releases/web` и опубликован в GitHub Pages.
