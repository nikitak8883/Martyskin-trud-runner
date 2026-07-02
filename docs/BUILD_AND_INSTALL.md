# Build and install: Android + Web

Проект: `C:\Test\MTRCocosCreator`  
Движок: Cocos Creator 3.8.8  
Общая игровая логика Web и Android: `assets/scripts/GameRoot.ts`

## 1. Проверка перед сборкой

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Test\MTRCocosCreator\tools\validate-mtr-config.ps1" -ProjectRoot "C:\Test\MTRCocosCreator"
```

Ожидаемый результат:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, 15 story themes, Russian obstacle labels present.
```

## 2. Перегенерация фоновых текстур

Используй только если обновлялись исходные картинки или `background_sources.json`.

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Test\MTRCocosCreator\tools\asset_generation\build-martyshkin-backgrounds.ps1" -ProjectRoot "C:\Test\MTRCocosCreator"
```

Фоны лежат в `C:\Test\MTRCocosCreator\assets\resources\backgrounds`.

## 3. Сборка Web

```powershell
$project="C:\Test\MTRCocosCreator"
$creator="C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe"
$out="$project\creator-web-current.out.log"
$err="$project\creator-web-current.err.log"

Start-Process -FilePath $creator `
  -ArgumentList @("--project",$project,"--build","configPath=build-web-mobile.json;logDest=creator-web-current.log") `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err `
  -WindowStyle Hidden `
  -Wait
```

Результат: `C:\Test\MTRCocosCreator\build\web-mobile`.

## 4. Локальный запуск Web

```powershell
cd "C:\Test\MTRCocosCreator\build\web-mobile"
.\start-web.bat
```

Открой `http://127.0.0.1:8088/`.

Не открывай `index.html` двойным кликом: Cocos runtime требует HTTP-сервер, иначе браузер блокирует загрузку import-map и модулей.

## 5. Сборка Android APK

Сначала сгенерируй Android-проект через Cocos Creator:

```powershell
$project="C:\Test\MTRCocosCreator"
$creator="C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe"
$out="$project\creator-android-current.out.log"
$err="$project\creator-android-current.err.log"

Start-Process -FilePath $creator `
  -ArgumentList @("--project",$project,"--build","configPath=build-android.json;logDest=creator-android-current.log") `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err `
  -WindowStyle Hidden `
  -Wait
```

Потом собери APK:

```powershell
$env:JAVA_HOME="C:\Program Files (x86)\Android\openjdk\jdk-17.0.14"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
cd "C:\Test\MTRCocosCreator\build\android\proj"
.\gradlew.bat assembleDebug --no-daemon
```

APK:

```text
C:\Test\MTRCocosCreator\build\android\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
```

## 6. Установка на телефон через ADB

1. На телефоне открой `Настройки > О телефоне`.
2. Нажми `Номер сборки` 7 раз.
3. Открой `Настройки > Для разработчиков`.
4. Включи `Отладка по USB`.
5. Если есть `Установка через USB`, включи её тоже.
6. Подключи телефон кабелем USB.
7. Разблокируй телефон и подтверди RSA-запрос.
8. Проверь устройство:

```powershell
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices -l
```

9. Установи APK:

```powershell
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" install -r "C:\Test\MTRCocosCreator\build\android\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk"
```

10. Запусти:

```powershell
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell monkey -p com.martyskin.trudrunner 1
```

## 7. Частые ошибки установки

- `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: удали старую версию другой подписи:

```powershell
& "C:\Users\nikit_rbe4ai3\AppData\Local\Android\Sdk\platform-tools\adb.exe" uninstall com.martyskin.trudrunner
```

- `device unauthorized`: подтверди RSA-запрос на телефоне.
- `INSTALL_FAILED_USER_RESTRICTED`: включи `Установка через USB`.
- `INSTALL_FAILED_NO_MATCHING_ABIS`: текущая debug-сборка рассчитана на ARM; для x86_64-эмулятора нужна отдельная ABI-сборка.

## 8. Установка без ADB

1. Передай APK на телефон.
2. Открой APK через `Файлы` или `Downloads`.
3. Разреши установку неизвестных приложений для этого приложения.
4. Подтверди установку.

Debug APK может показывать предупреждение Play Protect. Для публичной раздачи нужна release-сборка с собственной подписью.
