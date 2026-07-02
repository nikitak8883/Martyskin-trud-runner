# Мартышкин труд - установка, запуск и публикация

Дата: 2026-06-12

## Готовые артефакты

- Android APK: `C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk`
- APK SHA256: `56C9496A31BEA98D4BE362B2BD212665845C598E7004228A02EA957313B2C1E8`
- Web build: `C:\Test\MTRCocosCreator\releases\web`
- Checksums: `C:\Test\MTRCocosCreator\releases\checksums\SHA256SUMS.txt`
- GitHub Pages: `https://nikitak8883.github.io/Martyskin-trud-runner/`
- GitHub commit: `67b49efd97ec92d45f741c46c81ccfb05b0c5c66`

## Установка APK через ADB

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r "C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

Если Android откажет из-за несовпадающей подписи предыдущей установки:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.martyskin.trudrunner
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install "C:\Test\MTRCocosCreator\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

## Локальный запуск Web

```powershell
cd C:\Test\MTRCocosCreator\releases\web
python -m http.server 8101 --bind 127.0.0.1
```

Открыть:

```text
http://127.0.0.1:8101/
```

## Публикация Web

Web-версия уже выгружена в репозиторий:

```text
https://github.com/nikitak8883/Martyskin-trud-runner
```

Ветка `main`, commit `67b49efd97ec92d45f741c46c81ccfb05b0c5c66`.

## Google Drive

APK подготовлен и проверен. Raw upload APK в Google Drive в этой сессии заблокирован доступными инструментами: exposed Drive tools поддерживают импорт Docs/Sheets/Slides, но не дают callable `upload_file` для `application/vnd.android.package-archive`.
