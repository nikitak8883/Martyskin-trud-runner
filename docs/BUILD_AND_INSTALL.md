# Build and install: Android + Web

Проект: корень текущего checkout (`MTRCocosCreator`)  
Движок: Cocos Creator 3.8.8  
Общая игровая логика Web и Android: `assets/scripts/GameRoot.ts`

## 1. Проверка перед сборкой

```powershell
$project = (Resolve-Path .).Path
powershell -ExecutionPolicy Bypass -File "$project\tools\validate-mtr-config.ps1" -ProjectRoot $project
```

Ожидаемый результат:

```text
MTR config OK: 15 levels, 15 bitmap backgrounds, 15 story themes, Russian obstacle labels present.
```

## 2. Перегенерация фоновых текстур

Используй только если обновлялись исходные картинки или `background_sources.json`.

```powershell
powershell -ExecutionPolicy Bypass -File "$project\tools\asset_generation\build-martyshkin-backgrounds.ps1" -ProjectRoot $project
```

Фоны лежат в `$project\assets\resources\backgrounds`.

## 3. Сборка Web

```powershell
$project = (Resolve-Path .).Path
powershell -NoProfile -ExecutionPolicy Bypass -File "$project\tools\Run-MtrCocosBuild.ps1" `
  -ProjectRoot $project `
  -ConfigPath "build-web-mobile.json"
```

Результат: `$project\build\web-mobile`.

## 4. Локальный запуск Web

```powershell
cd "$project\build\web-mobile"
.\start-web.bat
```

Открой `http://127.0.0.1:8088/`.

Не открывай `index.html` двойным кликом: Cocos runtime требует HTTP-сервер, иначе браузер блокирует загрузку import-map и модулей.

## 5. Сборка Android APK

Сначала выполни read-only fail-closed preflight. Он проверяет exact Adoptium
`17.0.20`, SHA-256 JDK-файлов, Cocos `3.8.8`, SDK/API/NDK/CMake и существующий
generated export, но не запускает Cocos, Gradle, adb или emulator:

```powershell
$project = (Resolve-Path .).Path
powershell -NoProfile -ExecutionPolicy Bypass -File "$project\tools\Run-MtrCocosBuild.ps1" `
  -ProjectRoot $project `
  -ConfigPath "build-android.json" `
  -ValidateAndroidToolchainOnly
```

Для реальной сборки используй тот же wrapper. Он применяет validated JDK только
к дочерним Cocos/Gradle processes, перед Cocos блокирует неполный или
несовместимый существующий export и восстанавливает окружение в `finally`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$project\tools\Run-MtrCocosBuild.ps1" `
  -ProjectRoot $project `
  -ConfigPath "build-android.json"
```

APK:

```text
$project\build\android\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk
```

## 6. Установка на телефон через ADB

По умолчанию release/QA-приёмка выполняется только на emulator. Физическое
устройство требует отдельного явного разрешения и не является частью TC-01.

1. На телефоне открой `Настройки > О телефоне`.
2. Нажми `Номер сборки` 7 раз.
3. Открой `Настройки > Для разработчиков`.
4. Включи `Отладка по USB`.
5. Если есть `Установка через USB`, включи её тоже.
6. Подключи телефон кабелем USB.
7. Разблокируй телефон и подтверди RSA-запрос.
8. Проверь устройство:

```powershell
$adb = "C:\Users\nikit\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$serial = "R5CY933XP7P"
& $adb devices -l
& $adb -s $serial get-state
& $adb -s $serial shell pm list users
```

9. Установи APK строго в основной профиль (`user 0`):

```powershell
& $adb -s $serial install --user 0 -r "$project\build\android\proj\build\CocosGame\outputs\apk\debug\CocosGame-debug.apk"
```

10. Запусти:

```powershell
& $adb -s $serial shell am start --user 0 -n "com.martyskin.trudrunner/com.cocos.game.AppActivity"
```

## 7. Частые ошибки установки

- `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: удали старую версию другой подписи:

```powershell
& $adb -s $serial shell pm uninstall --user 0 com.martyskin.trudrunner
```

Если конфликт подписи сохраняется после удаления только из `user 0`, остановись:
не удаляй пакет из рабочего профиля или для всех пользователей без отдельного
явного разрешения.

- `device unauthorized`: подтверди RSA-запрос на телефоне.
- `INSTALL_FAILED_USER_RESTRICTED`: включи `Установка через USB`.
- `INSTALL_FAILED_NO_MATCHING_ABIS`: текущая debug-сборка рассчитана на ARM; для x86_64-эмулятора нужна отдельная ABI-сборка.

## 8. Установка без ADB

1. Передай APK на телефон.
2. Открой APK через `Файлы` или `Downloads`.
3. Разреши установку неизвестных приложений для этого приложения.
4. Подтверди установку.

Debug APK может показывать предупреждение Play Protect. Для публичной раздачи нужна release-сборка с собственной подписью.
