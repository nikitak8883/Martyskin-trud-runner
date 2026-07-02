# UI наборы для недостающих уровней 9–15

Формат: PNG RGBA, прозрачный фон, каждый набор отдельным файлом.

## Содержимое

Каждый лист содержит:
- заголовок уровня;
- карточку уровня normal/selected/locked;
- кнопки;
- 8–10 тематических иконок/объектов;
- короткие таблички/лейблы;
- элементы для вырезки под UI/UX.

## Файлы

- ui_level_09_banana_reactor_cards_icons_buttons_transparent.png
- ui_level_10_audit_corridor_cards_icons_buttons_transparent.png
- ui_level_11_night_shift_cards_icons_buttons_transparent.png
- ui_level_12_training_department_cards_icons_buttons_transparent.png
- ui_level_13_approval_tower_cards_icons_buttons_transparent.png
- ui_level_14_factory_ministry_cards_icons_buttons_transparent.png
- ui_level_15_martyshkin_core_cards_icons_buttons_transparent.png

## Интеграция

Не вставлять лист целиком.
Вырезать элементы по альфа-каналу, разложить по папкам:

```text
assets/resources/ui/levels/level09/
assets/resources/ui/levels/level10/
...
assets/resources/ui/levels/level15/
```

Рекомендуемые типы:
- level_card_normal
- level_card_selected
- level_card_locked
- level_icon
- level_title
- level_badge
- level_button
- level_label
- level_theme_prop

## Важно

Эти наборы закрывают недостающие уровни 9–15.
Следующая итерация не обязательна, если нужны именно UI-наборы для выбора уровней.
Если нужны ещё и отдельные gameplay-платформы/препятствия для уровней 9–15 — нужна отдельная итерация.
