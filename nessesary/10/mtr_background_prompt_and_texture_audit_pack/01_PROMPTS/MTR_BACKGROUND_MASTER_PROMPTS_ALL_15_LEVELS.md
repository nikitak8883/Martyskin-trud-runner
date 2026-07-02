# Мартышкин труд Runner — мастер-промты для инженерно-правильных фоновых PNG


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

# Уровень 1: Стройплощадка примата

**ID:** `level01_construction_site`  
**Тема:** строительная площадка в джунглево-горной зоне  
**Ключевые мотивы:** краны, строительные леса, доски, трубы, бетономешалки, каски, конусы, русские таблички  
**Прогрессия:** вход на объект / центр стройки / большой баннер Мартышкин труд

### Файлы для уровня 01

```text
assets/resources/backgrounds/level01/level01_bg_far.png
assets/resources/backgrounds/level01/level01_bg_mid.png
assets/resources/backgrounds/level01/level01_bg_near.png
assets/resources/backgrounds/level01/level01_track_backdrop.png
assets/resources/backgrounds/level01/level01_grade_fog.png
assets/resources/backgrounds/level01/progression/level01_props_start.png
assets/resources/backgrounds/level01/progression/level01_props_mid.png
assets/resources/backgrounds/level01/progression/level01_props_end.png
```

#### 1) `level01_bg_far.png`
Создай дальний фон для 2D runner уровня «Стройплощадка примата». Тема: строительная площадка в джунглево-горной зоне. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: краны, строительные леса, доски, трубы, бетономешалки, каски, конусы, русские таблички. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level01_bg_mid.png`
Создай средний тематический фон для уровня «Стройплощадка примата». Это главный слой идентичности уровня: строительная площадка в джунглево-горной зоне. Он должен показывать мир уровня через: краны, строительные леса, доски, трубы, бетономешалки, каски, конусы, русские таблички. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level01_bg_near.png`
Создай ближний декоративный слой для уровня «Стройплощадка примата» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: краны, строительные леса, доски, трубы, бетономешалки, каски, конусы, русские таблички. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level01_track_backdrop.png`
Создай track backdrop для дорожки уровня «Стройплощадка примата» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: строительная площадка в джунглево-горной зоне. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level01_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Стройплощадка примата» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level01_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Стройплощадка примата». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: вход на объект. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level01_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Стройплощадка примата». Этап: центр стройки. Отдельные тематические prop-объекты по мотивам: краны, строительные леса, доски, трубы, бетономешалки, каски, конусы, русские таблички. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level01_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Стройплощадка примата». Этап: большой баннер Мартышкин труд. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 2: Банановая логистика

**ID:** `level02_banana_logistics`  
**Тема:** банановый склад, разгрузка, контейнеры, погрузочные линии  
**Ключевые мотивы:** склады, ящики, паллеты, тележки, конвейеры, кран-балки, русские таблички отгрузки  
**Прогрессия:** приём бананов / упаковка / отгрузка / зона возврата

### Файлы для уровня 02

```text
assets/resources/backgrounds/level02/level02_bg_far.png
assets/resources/backgrounds/level02/level02_bg_mid.png
assets/resources/backgrounds/level02/level02_bg_near.png
assets/resources/backgrounds/level02/level02_track_backdrop.png
assets/resources/backgrounds/level02/level02_grade_fog.png
assets/resources/backgrounds/level02/progression/level02_props_start.png
assets/resources/backgrounds/level02/progression/level02_props_mid.png
assets/resources/backgrounds/level02/progression/level02_props_end.png
```

#### 1) `level02_bg_far.png`
Создай дальний фон для 2D runner уровня «Банановая логистика». Тема: банановый склад, разгрузка, контейнеры, погрузочные линии. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: склады, ящики, паллеты, тележки, конвейеры, кран-балки, русские таблички отгрузки. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level02_bg_mid.png`
Создай средний тематический фон для уровня «Банановая логистика». Это главный слой идентичности уровня: банановый склад, разгрузка, контейнеры, погрузочные линии. Он должен показывать мир уровня через: склады, ящики, паллеты, тележки, конвейеры, кран-балки, русские таблички отгрузки. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level02_bg_near.png`
Создай ближний декоративный слой для уровня «Банановая логистика» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: склады, ящики, паллеты, тележки, конвейеры, кран-балки, русские таблички отгрузки. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level02_track_backdrop.png`
Создай track backdrop для дорожки уровня «Банановая логистика» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: банановый склад, разгрузка, контейнеры, погрузочные линии. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level02_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Банановая логистика» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level02_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Банановая логистика». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: приём бананов. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level02_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Банановая логистика». Этап: упаковка. Отдельные тематические prop-объекты по мотивам: склады, ящики, паллеты, тележки, конвейеры, кран-балки, русские таблички отгрузки. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level02_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Банановая логистика». Этап: зона возврата. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 3: Отдел бессмысленных заявлений

**ID:** `level03_useless_forms_department`  
**Тема:** офисная бюрократия, заявления, столы, документы  
**Ключевые мотивы:** столы, шкафы, папки, печати, заявления, очереди, таблички отделов  
**Прогрессия:** приёмная / окна заявлений / лабиринт столов / архивная дверь

### Файлы для уровня 03

```text
assets/resources/backgrounds/level03/level03_bg_far.png
assets/resources/backgrounds/level03/level03_bg_mid.png
assets/resources/backgrounds/level03/level03_bg_near.png
assets/resources/backgrounds/level03/level03_track_backdrop.png
assets/resources/backgrounds/level03/level03_grade_fog.png
assets/resources/backgrounds/level03/progression/level03_props_start.png
assets/resources/backgrounds/level03/progression/level03_props_mid.png
assets/resources/backgrounds/level03/progression/level03_props_end.png
```

#### 1) `level03_bg_far.png`
Создай дальний фон для 2D runner уровня «Отдел бессмысленных заявлений». Тема: офисная бюрократия, заявления, столы, документы. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: столы, шкафы, папки, печати, заявления, очереди, таблички отделов. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level03_bg_mid.png`
Создай средний тематический фон для уровня «Отдел бессмысленных заявлений». Это главный слой идентичности уровня: офисная бюрократия, заявления, столы, документы. Он должен показывать мир уровня через: столы, шкафы, папки, печати, заявления, очереди, таблички отделов. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level03_bg_near.png`
Создай ближний декоративный слой для уровня «Отдел бессмысленных заявлений» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: столы, шкафы, папки, печати, заявления, очереди, таблички отделов. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level03_track_backdrop.png`
Создай track backdrop для дорожки уровня «Отдел бессмысленных заявлений» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: офисная бюрократия, заявления, столы, документы. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level03_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Отдел бессмысленных заявлений» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level03_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Отдел бессмысленных заявлений». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: приёмная. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level03_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Отдел бессмысленных заявлений». Этап: окна заявлений. Отдельные тематические prop-объекты по мотивам: столы, шкафы, папки, печати, заявления, очереди, таблички отделов. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level03_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Отдел бессмысленных заявлений». Этап: архивная дверь. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 4: Джунгли примата

**ID:** `level04_primate_jungle`  
**Тема:** тропические джунгли, лианы, корни, камни, дикая среда  
**Ключевые мотивы:** лианы, деревья, ветви, камни, водопад, старые таблички, природные мостики  
**Прогрессия:** край джунглей / лиановый проход / водопад / старый объект труда в зарослях

### Файлы для уровня 04

```text
assets/resources/backgrounds/level04/level04_bg_far.png
assets/resources/backgrounds/level04/level04_bg_mid.png
assets/resources/backgrounds/level04/level04_bg_near.png
assets/resources/backgrounds/level04/level04_track_backdrop.png
assets/resources/backgrounds/level04/level04_grade_fog.png
assets/resources/backgrounds/level04/progression/level04_props_start.png
assets/resources/backgrounds/level04/progression/level04_props_mid.png
assets/resources/backgrounds/level04/progression/level04_props_end.png
```

#### 1) `level04_bg_far.png`
Создай дальний фон для 2D runner уровня «Джунгли примата». Тема: тропические джунгли, лианы, корни, камни, дикая среда. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: лианы, деревья, ветви, камни, водопад, старые таблички, природные мостики. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level04_bg_mid.png`
Создай средний тематический фон для уровня «Джунгли примата». Это главный слой идентичности уровня: тропические джунгли, лианы, корни, камни, дикая среда. Он должен показывать мир уровня через: лианы, деревья, ветви, камни, водопад, старые таблички, природные мостики. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level04_bg_near.png`
Создай ближний декоративный слой для уровня «Джунгли примата» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: лианы, деревья, ветви, камни, водопад, старые таблички, природные мостики. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level04_track_backdrop.png`
Создай track backdrop для дорожки уровня «Джунгли примата» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: тропические джунгли, лианы, корни, камни, дикая среда. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level04_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Джунгли примата» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level04_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Джунгли примата». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: край джунглей. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level04_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Джунгли примата». Этап: лиановый проход. Отдельные тематические prop-объекты по мотивам: лианы, деревья, ветви, камни, водопад, старые таблички, природные мостики. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level04_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Джунгли примата». Этап: старый объект труда в зарослях. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 5: Ферма сверхплана

**ID:** `level05_superplan_farm`  
**Тема:** ферма, сельхоз, ящики, заборы, тележки, курицы  
**Ключевые мотивы:** заборы, курицы, ящики, тележки, солома, пугала, таблички фермы  
**Прогрессия:** вход на ферму / склад урожая / куриная проверка / амбар сверхплана

### Файлы для уровня 05

```text
assets/resources/backgrounds/level05/level05_bg_far.png
assets/resources/backgrounds/level05/level05_bg_mid.png
assets/resources/backgrounds/level05/level05_bg_near.png
assets/resources/backgrounds/level05/level05_track_backdrop.png
assets/resources/backgrounds/level05/level05_grade_fog.png
assets/resources/backgrounds/level05/progression/level05_props_start.png
assets/resources/backgrounds/level05/progression/level05_props_mid.png
assets/resources/backgrounds/level05/progression/level05_props_end.png
```

#### 1) `level05_bg_far.png`
Создай дальний фон для 2D runner уровня «Ферма сверхплана». Тема: ферма, сельхоз, ящики, заборы, тележки, курицы. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: заборы, курицы, ящики, тележки, солома, пугала, таблички фермы. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level05_bg_mid.png`
Создай средний тематический фон для уровня «Ферма сверхплана». Это главный слой идентичности уровня: ферма, сельхоз, ящики, заборы, тележки, курицы. Он должен показывать мир уровня через: заборы, курицы, ящики, тележки, солома, пугала, таблички фермы. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level05_bg_near.png`
Создай ближний декоративный слой для уровня «Ферма сверхплана» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: заборы, курицы, ящики, тележки, солома, пугала, таблички фермы. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level05_track_backdrop.png`
Создай track backdrop для дорожки уровня «Ферма сверхплана» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: ферма, сельхоз, ящики, заборы, тележки, курицы. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level05_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Ферма сверхплана» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level05_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Ферма сверхплана». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: вход на ферму. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level05_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Ферма сверхплана». Этап: склад урожая. Отдельные тематические prop-объекты по мотивам: заборы, курицы, ящики, тележки, солома, пугала, таблички фермы. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level05_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Ферма сверхплана». Этап: амбар сверхплана. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



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



---

# Уровень 7: Фабрика вечного труда

**ID:** `level07_factory_of_eternal_labor`  
**Тема:** индустриальная фабрика, стимпанк, механизмы, трубы, пар  
**Ключевые мотивы:** трубы, пар, конвейеры, шестерни, котлы, рычаги, индустриальные настилы  
**Прогрессия:** вход в цех / конвейерная линия / котельная / главный механизм

### Файлы для уровня 07

```text
assets/resources/backgrounds/level07/level07_bg_far.png
assets/resources/backgrounds/level07/level07_bg_mid.png
assets/resources/backgrounds/level07/level07_bg_near.png
assets/resources/backgrounds/level07/level07_track_backdrop.png
assets/resources/backgrounds/level07/level07_grade_fog.png
assets/resources/backgrounds/level07/progression/level07_props_start.png
assets/resources/backgrounds/level07/progression/level07_props_mid.png
assets/resources/backgrounds/level07/progression/level07_props_end.png
```

#### 1) `level07_bg_far.png`
Создай дальний фон для 2D runner уровня «Фабрика вечного труда». Тема: индустриальная фабрика, стимпанк, механизмы, трубы, пар. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: трубы, пар, конвейеры, шестерни, котлы, рычаги, индустриальные настилы. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level07_bg_mid.png`
Создай средний тематический фон для уровня «Фабрика вечного труда». Это главный слой идентичности уровня: индустриальная фабрика, стимпанк, механизмы, трубы, пар. Он должен показывать мир уровня через: трубы, пар, конвейеры, шестерни, котлы, рычаги, индустриальные настилы. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level07_bg_near.png`
Создай ближний декоративный слой для уровня «Фабрика вечного труда» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: трубы, пар, конвейеры, шестерни, котлы, рычаги, индустриальные настилы. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level07_track_backdrop.png`
Создай track backdrop для дорожки уровня «Фабрика вечного труда» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: индустриальная фабрика, стимпанк, механизмы, трубы, пар. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level07_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Фабрика вечного труда» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level07_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Фабрика вечного труда». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: вход в цех. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level07_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Фабрика вечного труда». Этап: конвейерная линия. Отдельные тематические prop-объекты по мотивам: трубы, пар, конвейеры, шестерни, котлы, рычаги, индустриальные настилы. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level07_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Фабрика вечного труда». Этап: главный механизм. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 8: Архив важности

**ID:** `level08_archive_of_importance`  
**Тема:** архив, картотеки, шкафы, пыль, документы  
**Ключевые мотивы:** архивные шкафы, картотеки, стеллажи, папки, пыль, лампы, таблички важности  
**Прогрессия:** первые стеллажи / глубокий архив / секретный сектор / дверь к реактору

### Файлы для уровня 08

```text
assets/resources/backgrounds/level08/level08_bg_far.png
assets/resources/backgrounds/level08/level08_bg_mid.png
assets/resources/backgrounds/level08/level08_bg_near.png
assets/resources/backgrounds/level08/level08_track_backdrop.png
assets/resources/backgrounds/level08/level08_grade_fog.png
assets/resources/backgrounds/level08/progression/level08_props_start.png
assets/resources/backgrounds/level08/progression/level08_props_mid.png
assets/resources/backgrounds/level08/progression/level08_props_end.png
```

#### 1) `level08_bg_far.png`
Создай дальний фон для 2D runner уровня «Архив важности». Тема: архив, картотеки, шкафы, пыль, документы. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: архивные шкафы, картотеки, стеллажи, папки, пыль, лампы, таблички важности. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level08_bg_mid.png`
Создай средний тематический фон для уровня «Архив важности». Это главный слой идентичности уровня: архив, картотеки, шкафы, пыль, документы. Он должен показывать мир уровня через: архивные шкафы, картотеки, стеллажи, папки, пыль, лампы, таблички важности. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level08_bg_near.png`
Создай ближний декоративный слой для уровня «Архив важности» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: архивные шкафы, картотеки, стеллажи, папки, пыль, лампы, таблички важности. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level08_track_backdrop.png`
Создай track backdrop для дорожки уровня «Архив важности» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: архив, картотеки, шкафы, пыль, документы. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level08_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Архив важности» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level08_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Архив важности». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: первые стеллажи. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level08_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Архив важности». Этап: глубокий архив. Отдельные тематические prop-объекты по мотивам: архивные шкафы, картотеки, стеллажи, папки, пыль, лампы, таблички важности. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level08_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Архив важности». Этап: дверь к реактору. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 9: Банановый реактор

**ID:** `level09_banana_reactor`  
**Тема:** реактор, лабораторно-индустриальная зона, светящиеся банановые элементы  
**Ключевые мотивы:** реактор, колбы, трубы, кабели, жёлто-зелёное свечение, датчики, лабораторные знаки  
**Прогрессия:** вход в лабораторию / трубный сектор / сердце реактора / перегрев плана

### Файлы для уровня 09

```text
assets/resources/backgrounds/level09/level09_bg_far.png
assets/resources/backgrounds/level09/level09_bg_mid.png
assets/resources/backgrounds/level09/level09_bg_near.png
assets/resources/backgrounds/level09/level09_track_backdrop.png
assets/resources/backgrounds/level09/level09_grade_fog.png
assets/resources/backgrounds/level09/progression/level09_props_start.png
assets/resources/backgrounds/level09/progression/level09_props_mid.png
assets/resources/backgrounds/level09/progression/level09_props_end.png
```

#### 1) `level09_bg_far.png`
Создай дальний фон для 2D runner уровня «Банановый реактор». Тема: реактор, лабораторно-индустриальная зона, светящиеся банановые элементы. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: реактор, колбы, трубы, кабели, жёлто-зелёное свечение, датчики, лабораторные знаки. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level09_bg_mid.png`
Создай средний тематический фон для уровня «Банановый реактор». Это главный слой идентичности уровня: реактор, лабораторно-индустриальная зона, светящиеся банановые элементы. Он должен показывать мир уровня через: реактор, колбы, трубы, кабели, жёлто-зелёное свечение, датчики, лабораторные знаки. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level09_bg_near.png`
Создай ближний декоративный слой для уровня «Банановый реактор» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: реактор, колбы, трубы, кабели, жёлто-зелёное свечение, датчики, лабораторные знаки. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level09_track_backdrop.png`
Создай track backdrop для дорожки уровня «Банановый реактор» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: реактор, лабораторно-индустриальная зона, светящиеся банановые элементы. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level09_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Банановый реактор» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level09_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Банановый реактор». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: вход в лабораторию. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level09_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Банановый реактор». Этап: трубный сектор. Отдельные тематические prop-объекты по мотивам: реактор, колбы, трубы, кабели, жёлто-зелёное свечение, датчики, лабораторные знаки. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level09_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Банановый реактор». Этап: перегрев плана. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



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



---

# Уровень 11: Ночная смена

**ID:** `level11_night_shift`  
**Тема:** ночная стройка/фабрика, фонари, кофе, усталость  
**Ключевые мотивы:** фонари, луна, ночные краны, лампы, кофе, дымка, сонные приматы  
**Прогрессия:** сумерки / полночь / зона фонарей / рассветный отчёт

### Файлы для уровня 11

```text
assets/resources/backgrounds/level11/level11_bg_far.png
assets/resources/backgrounds/level11/level11_bg_mid.png
assets/resources/backgrounds/level11/level11_bg_near.png
assets/resources/backgrounds/level11/level11_track_backdrop.png
assets/resources/backgrounds/level11/level11_grade_fog.png
assets/resources/backgrounds/level11/progression/level11_props_start.png
assets/resources/backgrounds/level11/progression/level11_props_mid.png
assets/resources/backgrounds/level11/progression/level11_props_end.png
```

#### 1) `level11_bg_far.png`
Создай дальний фон для 2D runner уровня «Ночная смена». Тема: ночная стройка/фабрика, фонари, кофе, усталость. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: фонари, луна, ночные краны, лампы, кофе, дымка, сонные приматы. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level11_bg_mid.png`
Создай средний тематический фон для уровня «Ночная смена». Это главный слой идентичности уровня: ночная стройка/фабрика, фонари, кофе, усталость. Он должен показывать мир уровня через: фонари, луна, ночные краны, лампы, кофе, дымка, сонные приматы. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level11_bg_near.png`
Создай ближний декоративный слой для уровня «Ночная смена» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: фонари, луна, ночные краны, лампы, кофе, дымка, сонные приматы. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level11_track_backdrop.png`
Создай track backdrop для дорожки уровня «Ночная смена» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: ночная стройка/фабрика, фонари, кофе, усталость. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level11_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Ночная смена» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level11_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Ночная смена». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: сумерки. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level11_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Ночная смена». Этап: полночь. Отдельные тематические prop-объекты по мотивам: фонари, луна, ночные краны, лампы, кофе, дымка, сонные приматы. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level11_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Ночная смена». Этап: рассветный отчёт. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 12: Учебный отдел плана

**ID:** `level12_training_department`  
**Тема:** учебный класс, доски, методички, тренажёры  
**Ключевые мотивы:** доски, плакаты, методички, учебные макеты, мел, парты, тренажёры  
**Прогрессия:** класс / полигон тренировки / экзаменационная зона / выход к башне

### Файлы для уровня 12

```text
assets/resources/backgrounds/level12/level12_bg_far.png
assets/resources/backgrounds/level12/level12_bg_mid.png
assets/resources/backgrounds/level12/level12_bg_near.png
assets/resources/backgrounds/level12/level12_track_backdrop.png
assets/resources/backgrounds/level12/level12_grade_fog.png
assets/resources/backgrounds/level12/progression/level12_props_start.png
assets/resources/backgrounds/level12/progression/level12_props_mid.png
assets/resources/backgrounds/level12/progression/level12_props_end.png
```

#### 1) `level12_bg_far.png`
Создай дальний фон для 2D runner уровня «Учебный отдел плана». Тема: учебный класс, доски, методички, тренажёры. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: доски, плакаты, методички, учебные макеты, мел, парты, тренажёры. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level12_bg_mid.png`
Создай средний тематический фон для уровня «Учебный отдел плана». Это главный слой идентичности уровня: учебный класс, доски, методички, тренажёры. Он должен показывать мир уровня через: доски, плакаты, методички, учебные макеты, мел, парты, тренажёры. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level12_bg_near.png`
Создай ближний декоративный слой для уровня «Учебный отдел плана» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: доски, плакаты, методички, учебные макеты, мел, парты, тренажёры. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level12_track_backdrop.png`
Создай track backdrop для дорожки уровня «Учебный отдел плана» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: учебный класс, доски, методички, тренажёры. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level12_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Учебный отдел плана» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level12_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Учебный отдел плана». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: класс. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level12_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Учебный отдел плана». Этап: полигон тренировки. Отдельные тематические prop-объекты по мотивам: доски, плакаты, методички, учебные макеты, мел, парты, тренажёры. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level12_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Учебный отдел плана». Этап: выход к башне. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 13: Башня согласований

**ID:** `level13_approval_tower`  
**Тема:** башня, этажи, лифты, подписи, согласования  
**Ключевые мотивы:** башня, лифты, лестницы, кабинеты, таблички отделов, подписи  
**Прогрессия:** нижние этажи / середина башни / кабинет главного согласования / выход в министерство

### Файлы для уровня 13

```text
assets/resources/backgrounds/level13/level13_bg_far.png
assets/resources/backgrounds/level13/level13_bg_mid.png
assets/resources/backgrounds/level13/level13_bg_near.png
assets/resources/backgrounds/level13/level13_track_backdrop.png
assets/resources/backgrounds/level13/level13_grade_fog.png
assets/resources/backgrounds/level13/progression/level13_props_start.png
assets/resources/backgrounds/level13/progression/level13_props_mid.png
assets/resources/backgrounds/level13/progression/level13_props_end.png
```

#### 1) `level13_bg_far.png`
Создай дальний фон для 2D runner уровня «Башня согласований». Тема: башня, этажи, лифты, подписи, согласования. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: башня, лифты, лестницы, кабинеты, таблички отделов, подписи. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level13_bg_mid.png`
Создай средний тематический фон для уровня «Башня согласований». Это главный слой идентичности уровня: башня, этажи, лифты, подписи, согласования. Он должен показывать мир уровня через: башня, лифты, лестницы, кабинеты, таблички отделов, подписи. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level13_bg_near.png`
Создай ближний декоративный слой для уровня «Башня согласований» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: башня, лифты, лестницы, кабинеты, таблички отделов, подписи. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level13_track_backdrop.png`
Создай track backdrop для дорожки уровня «Башня согласований» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: башня, этажи, лифты, подписи, согласования. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level13_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Башня согласований» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level13_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Башня согласований». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: нижние этажи. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level13_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Башня согласований». Этап: середина башни. Отдельные тематические prop-объекты по мотивам: башня, лифты, лестницы, кабинеты, таблички отделов, подписи. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level13_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Башня согласований». Этап: выход в министерство. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 14: Министерство фабричного труда

**ID:** `level14_factory_ministry`  
**Тема:** гибрид министерства и завода, трубы, штампы, пар  
**Ключевые мотивы:** трубы, штампы, министерские колонны, конвейеры, пар, кабинеты, механические печати  
**Прогрессия:** министерский вход / штамповочный цех / зал регламентов / ворота к сердцу

### Файлы для уровня 14

```text
assets/resources/backgrounds/level14/level14_bg_far.png
assets/resources/backgrounds/level14/level14_bg_mid.png
assets/resources/backgrounds/level14/level14_bg_near.png
assets/resources/backgrounds/level14/level14_track_backdrop.png
assets/resources/backgrounds/level14/level14_grade_fog.png
assets/resources/backgrounds/level14/progression/level14_props_start.png
assets/resources/backgrounds/level14/progression/level14_props_mid.png
assets/resources/backgrounds/level14/progression/level14_props_end.png
```

#### 1) `level14_bg_far.png`
Создай дальний фон для 2D runner уровня «Министерство фабричного труда». Тема: гибрид министерства и завода, трубы, штампы, пар. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: трубы, штампы, министерские колонны, конвейеры, пар, кабинеты, механические печати. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level14_bg_mid.png`
Создай средний тематический фон для уровня «Министерство фабричного труда». Это главный слой идентичности уровня: гибрид министерства и завода, трубы, штампы, пар. Он должен показывать мир уровня через: трубы, штампы, министерские колонны, конвейеры, пар, кабинеты, механические печати. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level14_bg_near.png`
Создай ближний декоративный слой для уровня «Министерство фабричного труда» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: трубы, штампы, министерские колонны, конвейеры, пар, кабинеты, механические печати. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level14_track_backdrop.png`
Создай track backdrop для дорожки уровня «Министерство фабричного труда» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: гибрид министерства и завода, трубы, штампы, пар. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level14_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Министерство фабричного труда» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level14_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Министерство фабричного труда». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: министерский вход. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level14_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Министерство фабричного труда». Этап: штамповочный цех. Отдельные тематические prop-объекты по мотивам: трубы, штампы, министерские колонны, конвейеры, пар, кабинеты, механические печати. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level14_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Министерство фабричного труда». Этап: ворота к сердцу. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.



---

# Уровень 15: Сердце Мартышкиного труда

**ID:** `level15_martyshkin_core`  
**Тема:** центральное ядро абсурда, главный механизм, финальное бананово-бюрократическое сердце  
**Ключевые мотивы:** гигантские шестерни, банановое ядро, свет, трубы, акты, штампы, символы всех уровней  
**Прогрессия:** внешнее кольцо / механизм / ядро / финальный баннер труда

### Файлы для уровня 15

```text
assets/resources/backgrounds/level15/level15_bg_far.png
assets/resources/backgrounds/level15/level15_bg_mid.png
assets/resources/backgrounds/level15/level15_bg_near.png
assets/resources/backgrounds/level15/level15_track_backdrop.png
assets/resources/backgrounds/level15/level15_grade_fog.png
assets/resources/backgrounds/level15/progression/level15_props_start.png
assets/resources/backgrounds/level15/progression/level15_props_mid.png
assets/resources/backgrounds/level15/progression/level15_props_end.png
```

#### 1) `level15_bg_far.png`
Создай дальний фон для 2D runner уровня «Сердце Мартышкиного труда». Тема: центральное ядро абсурда, главный механизм, финальное бананово-бюрократическое сердце. Дальний план: атмосфера, небо/дальний интерьер/дальние структуры, мягкая глубина, низкий контраст. Визуальные мотивы: гигантские шестерни, банановое ядро, свет, трубы, акты, штампы, символы всех уровней. Не добавлять активные объекты, UI или collectibles. Нижняя gameplay-зона должна быть спокойной. PNG, wide 16:9, seamless-friendly horizontal composition, no hard vertical seams.

#### 2) `level15_bg_mid.png`
Создай средний тематический фон для уровня «Сердце Мартышкиного труда». Это главный слой идентичности уровня: центральное ядро абсурда, главный механизм, финальное бананово-бюрократическое сердце. Он должен показывать мир уровня через: гигантские шестерни, банановое ядро, свет, трубы, акты, штампы, символы всех уровней. Добавь сатирические русские таблички низкого контраста, но они не должны выглядеть как интерактивные hazards. Композиция широкая, пригодная для parallax scrolling, без UI, без игрока, без активных предметов на дорожке.

#### 3) `level15_bg_near.png`
Создай ближний декоративный слой для уровня «Сердце Мартышкиного труда» с true transparent background RGBA. Только отдельные ближние элементы по краям и за gameplay lane, без сплошного фона. Мотивы: гигантские шестерни, банановое ядро, свет, трубы, акты, штампы, символы всех уровней. Оставь центральную дорожку визуально свободной. No checkerboard, no white matte, transparent alpha.

#### 4) `level15_track_backdrop.png`
Создай track backdrop для дорожки уровня «Сердце Мартышкиного труда» с true transparent background RGBA. Это спокойная подложка за платформами и игроком, не платформа и не obstacle. Низкий контраст, горизонтальная земля/пол/настил по теме: центральное ядро абсурда, главный механизм, финальное бананово-бюрократическое сердце. Не рисовать collectibles, UI, hazards. Должно помогать читаемости игрока и платформ.

#### 5) `level15_grade_fog.png`
Создай лёгкий color grade / fog / dust overlay для уровня «Сердце Мартышкиного труда» с true transparent background RGBA. Очень мягкий слой: пыль, пар, туман, лучи света или атмосферные частицы по теме уровня. Opacity должен быть низким, не затемнять всё, не скрывать gameplay. No checkerboard, transparent alpha.

#### 6) `level15_props_start.png`
Создай transparent RGBA progression prop sheet для начала уровня «Сердце Мартышкиного труда». Отдельные вырезаемые фоновые объекты, не целая сцена. Этап: внешнее кольцо. Объекты должны быть декором, а не активными obstacles. No checkerboard, transparent alpha, удобные промежутки между объектами.

#### 7) `level15_props_mid.png`
Создай transparent RGBA progression prop sheet для середины уровня «Сердце Мартышкиного труда». Этап: механизм. Отдельные тематические prop-объекты по мотивам: гигантские шестерни, банановое ядро, свет, трубы, акты, штампы, символы всех уровней. Удобно для вырезки и вставки в BG_MID/BG_NEAR. No checkerboard, transparent alpha.

#### 8) `level15_props_end.png`
Создай transparent RGBA progression prop sheet для финальной части уровня «Сердце Мартышкиного труда». Этап: финальный баннер труда. Сделай более выразительные, но не gameplay-confusing декорации. Объекты должны помогать ощущению прогресса уровня. No checkerboard, transparent alpha.
