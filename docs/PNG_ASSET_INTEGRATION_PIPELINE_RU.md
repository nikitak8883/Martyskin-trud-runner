# PNG Asset Integration Pipeline

Этот документ описывает подготовленный каркас для быстрой интеграции новых тематических ассетов в Android и Web версии.

## Главное правило

Не использовать JPG, скриншоты с телефона, WebP и PNG с нарисованной шахматной подложкой. Для runtime-интеграции нужны исходные PNG с настоящим alpha-каналом.

Текущие JPG-листы из телефона не импортируются как финальные игровые ассеты: в них потеряна прозрачность, поэтому автоматическая вырезка даст белые/серые поля, ореолы и неправильные края.

## Куда класть будущую поставку

Создать отдельную папку, например:

```powershell
New-Item -ItemType Directory -Force C:\Test\MTRCocosCreator\incoming\theme_png_20260603
```

Положить туда все 20 исходных `.png` листов с прозрачностью.

## Dry-run проверка

```powershell
cd C:\Test\MTRCocosCreator
python tools\mtr_last_iteration_asset_pipeline.py --project-root . --source-dir nessesary\9 --report qa\last_iteration_asset_pipeline_report.json --preview qa\asset-previews\last_iteration_asset_preview.png
```

Ожидаемо:

- `errors = 0`;
- `sourcePngCount >= 20`;
- `entryCount > 0`;
- preview показывает отдельные вырезанные объекты без белых прямоугольников и шахматной подложки.

Если dry-run ругается на JPG/нет alpha/один огромный компонент, интеграцию останавливать и заменить исходники.

## Применение

```powershell
cd C:\Test\MTRCocosCreator
python tools\mtr_last_iteration_asset_pipeline.py --project-root . --source-dir nessesary\9 --clean --report qa\last_iteration_asset_pipeline_report.json --preview qa\asset-previews\last_iteration_asset_preview.png
```

Скрипт создаёт:

- `assets/resources/objectives/themed/<theme>/<category>/*.png`;
- `assets/resources/config/last_iteration_asset_manifest.generated.json`;
- `assets/scripts/generated/ThemeAssetCatalog.generated.ts`;
- preview sheet в `qa/asset-previews/last_iteration_asset_preview.png`.

## Как игра использует каталог

`GameRoot.ts` уже подключает:

- `THEMED_ALL_RUNTIME_KEYS`;
- `themedPlatformKeysForLevel`;
- `themedObstacleKeysForType`.

Пока каталог пуст, игра использует текущие рабочие ассеты. После `--apply` новые тематические платформы и препятствия попадают в runtime-пулы по уровням без ручного переписывания основной логики.

## Проверки после применения

```powershell
cd C:\Test\MTRCocosCreator
powershell -ExecutionPolicy Bypass -File tools\validate-mtr-config.ps1
```

Затем собрать Web:

```powershell
& "C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe" --project C:\Test\MTRCocosCreator --build "configPath=C:\Test\MTRCocosCreator\build-web-mobile.json"
```

И Android:

```powershell
& "C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe" --project C:\Test\MTRCocosCreator --build "configPath=C:\Test\MTRCocosCreator\build-android.json"
cd C:\Test\MTRCocosCreator\native\engine\android
.\gradlew.bat :CocosGame:assembleDebug
```

## Минимальный QA

Проверить:

- меню;
- выбор скина;
- уровень 1;
- уровень с офисной темой;
- уровень с инспекцией;
- уровень с логистикой/Волгой;
- отсутствие белых пятен;
- отсутствие цельных листов вместо отдельных объектов;
- корректные подписи препятствий;
- отсутствие старого “примата в кружочке”;
- музыка стартует с начала при запуске каждого уровня;
- голосовые реакции тише музыкальной темы.

## Принцип маппинга

Порядок приоритета:

1. основной тематический пул уровня;
2. дополнительный пул той же темы;
3. общий safety/control пул;
4. shared fallback только если это явно разрешено планом.

Запрещено смешивать темы без логической причины: офисные столы не становятся строительными платформами, фермерские объекты не становятся архивом, а generic-наборы не заменяют тематический визуальный язык.
