# Performance audit

Дата актуализации: 2026-05-08

## Что сделано

- Web и Android используют один Cocos Creator проект и общий `assets/scripts/GameRoot.ts`.
- 15 фоновых сцен оптимизированы до 1536x672 JPG, суммарно около 2.8 MB на диске.
- Фоны грузятся лениво через `resources.load(...)` только при входе в уровень.
- Runtime cache фоновых `SpriteFrame` ограничен тремя уровнями, чтобы не держать все 15 декодированных текстур в памяти.
- Процедурные элементы фона оставлены как лёгкий parallax/таблички поверх bitmap, без тяжёлых текстурных операций каждый кадр.
- Частицы, игровые объекты и лейблы используют существующие массивы/пулы, без постоянного создания новых Cocos Node для каждого кадра.
- Логика идёт через semi-fixed accumulator в `GameRoot.update`, механика не привязана напрямую к FPS.
- Проверка конфигурации вынесена в `tools/validate-mtr-config.ps1`.

## Графика и GPU

- Основной фон: один `Sprite` на уровень.
- Игровой слой: `Graphics` для процедурных объектов, табличек, бананов, препятствий, игрока, NPC и VFX.
- UI: переиспользуемый пул `Label`.
- В Web тяжёлые shader/post-processing эффекты не включены; glow/vignette/shake реализованы лёгкой 2D-отрисовкой.

## Что проверять после каждой сборки

1. Старт без белого экрана.
2. Главное меню и ввод имени.
3. Выбор скина.
4. Выбор уровня.
5. Уровень 1: фон стройки, бананы, препятствия, HP.
6. Уровень 4+: NPC, боковой урон и stomp сверху.
7. Пауза.
8. Настройки звука.
9. Рекорды.
10. Game over.
11. Level clear.
12. Финальный уровень 15.
13. Кириллица в UI и на табличках.
14. Network в Web: нет `404`, `MIME`, `import-map` ошибок.
15. Android install: нет `INSTALL_FAILED_*`.

## Ручной профилинг Android

```powershell
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell dumpsys gfxinfo com.martyskin.trudrunner framestats
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell dumpsys meminfo com.martyskin.trudrunner
```

Для живого FPS-профиля удобнее Android Studio Profiler:

1. Открой `C:\Test\MTRCocosCreator\build\android\proj`.
2. Запусти игру на устройстве.
3. Открой `View > Tool Windows > Profiler`.
4. Проверь CPU, Memory и Graphics/Frame Rendering.

## Ручной профилинг Web

1. Открой локальную сборку через HTTP.
2. Открой DevTools.
3. В `Performance` запиши 30-60 секунд геймплея.
4. Проверь длинные задачи, GC-пики и Network.
5. В `Memory` сделай heap snapshot до и после смены уровня.

## Известные компромиссы

- Текущие игровые объекты остаются procedural Cocos Graphics, потому что проект не содержит финального sprite atlas для каждого препятствия и анимации игрока. Объекты не являются прямоугольными заглушками: у них есть узнаваемые формы, русские надписи и анимация, но полноценный atlas можно добавить отдельным арт-проходом.
- Classic Cocos2d-x/C++ порт синхронизирован по данным и фонам, но его сборка зависит от локального `COCOS2DX_ROOT_PATH` и Web/Emscripten toolchain. Проверяемая Web/Android сборка выполняется через Cocos Creator.
