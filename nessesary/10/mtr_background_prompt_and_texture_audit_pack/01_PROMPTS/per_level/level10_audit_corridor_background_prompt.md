# Персональный мастер-промт фона

## Общие инженерные правила для всех генераций

- Стиль: тот же сатирический мультяшно-полуреалистичный стиль, что в последних PNG-наборах UI/объектов: тёплое дерево, состаренные таблички, мягкий свет, джунглево-индустриальный абсурд, русские надписи.
- Не ломать стиль предыдущего пака: не уходить в плоский vector, pixel-art, 3D-render, cyberpunk или реалистичную фотографию.
- Игровая зона должна быть читаемой: нижняя треть/track lane менее контрастная, без ярких банановых дуг, без активных-looking табличек.
- Читаемый текст только на русском. Если текст фоновый — низкий контраст, не как UI/hazard.
- Не рисовать игрока, HUD, кнопки, collectibles-цепочки и active hazards в base-фонах.
- Фоновые обезьяны допустимы только как мелкий декор, не как главный gameplay-субъект.
- PNG с прозрачностью: для near/track/fog/progression props требовать true RGBA alpha, transparent background, no checkerboard, no white matte, no solid backdrop.
- Для bg_far/bg_mid допустим opaque PNG без alpha, но файл всё равно сохранять как PNG. Если генератор умеет alpha — alpha можно оставить полностью opaque.
- Размеры: base layers 2560×1440 или 2048×1152, progression sheets 2048×1024 / 1536×1024, строго PNG.
- Нейминг файлов не менять.

### Общий negative prompt

Do not include UI, player character, touch buttons, score, HUD, pause button, banana collectible arcs, active obstacles in player lane, English readable text, white background, checkerboard transparency preview, JPEG artifacts, cropped important edges, random mixed themes, photorealistic humans, gore, weapons, logos, watermarks, signatures.

---

# Уровень 10: Коридор проверок

**ID:** `level10_audit_corridor`  
**Тема:** аудит, коридоры контроля, пропуска, печати  
**Ключевые мотивы:** длинные коридоры, двери проверки, печати, лампы, журналы, пропуска  
**Прогрессия:** начало коридора / зона аудита / архив проверок / дверь «ещё раз»

### Файлы для уровня 10

```text
assets/resources/backgrounds/level10/level10_bg_far.png
assets/resources/backgrounds/level10/level10_bg_mid.png
assets/resources/backgrounds/level10/level10_bg_near.png
assets/resources/backgrounds/level10/level10_track_backdrop.png
assets/resources/backgrounds/level10/level10_grade_fog.png
assets/resources/backgrounds/level10/progression/level10_props_start.png
assets/resources/backgrounds/level10/progression/level10_props_mid.png
assets/resources/backgrounds/level10/progression/level10_props_end.png
```

#### 1) `level10_bg_far.png`
Создай дальний фон для 2D runner уровня «Коридор проверок». Тема: аудит, коридоры контроля, пропуска, печати. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: длинные коридоры, двери проверки, печати, лампы, журналы, пропуска. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level10_bg_mid.png`
Создай средний тематический фон для уровня «Коридор проверок». Это главный слой идентичности уровня: аудит, коридоры контроля, пропуска, печати. Он должен показывать мир уровня через: длинные коридоры, двери проверки, печати, лампы, журналы, пропуска. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level10_bg_near.png`
Создай ближний декоративный слой для уровня «Коридор проверок» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: длинные коридоры, двери проверки, печати, лампы, журналы, пропуска. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level10_track_backdrop.png`
Создай track backdrop для дорожки уровня «Коридор проверок» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: аудит, коридоры контроля, пропуска, печати. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level10_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Коридор проверок» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level10_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Коридор проверок». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: начало коридора. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level10_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Коридор проверок». Этап: зона аудита. Отдельные тематические prop-объекты по мотивам: длинные коридоры, двери проверки, печати, лампы, журналы, пропуска. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level10_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Коридор проверок». Этап: дверь «ещё раз». Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.
