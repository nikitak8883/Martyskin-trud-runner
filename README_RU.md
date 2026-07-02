# Мартышкин труд - Cocos Creator

Финальная clean-сборка Android/Web с объектными текстурами из `nessesary/9` и полностью замененными фонами уровней из `nessesary/10/Levels`.

## Главное

- Android APK: `releases/android/Martyshkin-Trud-texture10-clean-20260611-release.apk`
- Web release: `releases/web`
- GitHub Pages: `https://nikitak8883.github.io/Martyskin-trud-runner/`
- Финальный QA: `docs/FINAL_QA_REPORT.md`
- Установка и запуск: `docs/FINAL_INSTALL_RUN_GIT_GUIDE_RU.md`

## Текущая интеграция текстур

Объектные игровые текстуры остаются привязанными к тематическим пулам `nessesary/9`: платформы, препятствия, декор, таблички и усилители распределены по ролям уровня. Фоны больше не используют старые procedural/fallback-экраны: активная версия берет 15 готовых PNG-наборов из `nessesary/10/Levels`, нормализует их в runtime JPG и подключает через единый manifest.

## Проверка конфигурации

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Test\MTRCocosCreator\tools\validate-mtr-config.ps1" -ProjectRoot "C:\Test\MTRCocosCreator"
```

## Установка APK

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r "C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260611-release.apk"
```

Если Android отклонит обновление из-за другой подписи:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.martyskin.trudrunner
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install "C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260611-release.apk"
```

## Локальный запуск Web

```powershell
cd C:\Test\MTRCocosCreator\releases\web
python -m http.server 8101 --bind 127.0.0.1
```
