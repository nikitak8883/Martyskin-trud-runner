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

# Уровень 6: Павлин-инспектор

**ID:** `level06_peacock_inspector`  
**Тема:** инспекция, контроль, павлинья важность, акты и регламенты  
**Ключевые мотивы:** павлиньи эмблемы, штампы, акты, контрольные рамки, трибуны, таблички проверок  
**Прогрессия:** зал ожидания проверки / коридор замечаний / главная трибуна / стена актов

### Файлы для уровня 06

```text
assets/resources/backgrounds/level06/level06_bg_far.png
assets/resources/backgrounds/level06/level06_bg_mid.png
assets/resources/backgrounds/level06/level06_bg_near.png
assets/resources/backgrounds/level06/level06_track_backdrop.png
assets/resources/backgrounds/level06/level06_grade_fog.png
assets/resources/backgrounds/level06/progression/level06_props_start.png
assets/resources/backgrounds/level06/progression/level06_props_mid.png
assets/resources/backgrounds/level06/progression/level06_props_end.png
```

#### 1) `level06_bg_far.png`
Создай дальний фон для 2D runner уровня «Павлин-инспектор». Тема: инспекция, контроль, павлинья важность, акты и регламенты. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: павлиньи эмблемы, штампы, акты, контрольные рамки, трибуны, таблички проверок. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level06_bg_mid.png`
Создай средний тематический фон для уровня «Павлин-инспектор». Это главный слой идентичности уровня: инспекция, контроль, павлинья важность, акты и регламенты. Он должен показывать мир уровня через: павлиньи эмблемы, штампы, акты, контрольные рамки, трибуны, таблички проверок. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level06_bg_near.png`
Создай ближний декоративный слой для уровня «Павлин-инспектор» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: павлиньи эмблемы, штампы, акты, контрольные рамки, трибуны, таблички проверок. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level06_track_backdrop.png`
Создай track backdrop для дорожки уровня «Павлин-инспектор» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: инспекция, контроль, павлинья важность, акты и регламенты. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level06_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Павлин-инспектор» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level06_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Павлин-инспектор». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: зал ожидания проверки. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level06_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Павлин-инспектор». Этап: коридор замечаний. Отдельные тематические prop-объекты по мотивам: павлиньи эмблемы, штампы, акты, контрольные рамки, трибуны, таблички проверок. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level06_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Павлин-инспектор». Этап: стена актов. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.
